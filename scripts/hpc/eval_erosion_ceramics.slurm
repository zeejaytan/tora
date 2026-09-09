#!/bin/bash
#SBATCH --job-name=tora-erosion-ceramics
#SBATCH --partition=gpu-a100-short
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=03:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_erosion_ceramics_%j.log

set -euo pipefail

# TICKET .scratch/juglet-cause/issues/11 -- THE EROSION LADDER, ON POTS TORA
# CAN ACTUALLY REBUILD.
#
# WHY THIS EXISTS. Ticket 09 asked whether wear breaks a pot the way the Juglet
# is broken and answered on ONE object. The cause was not the method or the
# instrument -- both held. build_erosion_sweep.py's own docstring specifies
# "pots TORA CAN currently rebuild", but eval_erosion_sweep.slurm:51-52 passed
# no --objects filter and sourced real_heldout_norm.hdf5: six objects, three of
# them BONES (limb3, coxae, vert9). Three ceramics have ever been worn, and one
# of those assembles unworn. The filter existed and was never used.
#
# The Fractura `ceramics` group holds EIGHT real pots. The five never tested
# include narrow_bottle2 and narrow_bottle4, which TORA reassembles almost
# perfectly when fresh -- the controls this ladder has never had.
#
# NO LEAKAGE, and that is what makes all eight usable: the baseline was trained
# on synthetic Breaking Bad only, so no real pot was ever in its training set.
# "Held out" was never the constraint for this arm; the six-object file was.
#
# THE SCALE TRAP, handled in step 1. Ceramics are stored in raw scan units
# (max|v| 54.9-187.3, varying 3.4x between pots) against a model that has only
# been shown roughly 0.375-0.625. `scales` is a CONDITIONING INPUT to the flow
# model, not metric bookkeeping (see normalize_real_hdf5.py header). This is the
# fault that made blue_pot read 0% until it was rescored. The source is
# normalised ONCE, BEFORE erosion. `--normalize` on the build is deliberately
# NOT used: it recomputes the factor per variant AFTER erosion
# (build_erosion_sweep.py:124-129), which would let the scale drift across the
# rungs and put a second changing thing into the experiment.
#
# NOT SPLIT INTO CPU + GPU LEGS, deliberately. AGENTS.md rule 7 prefers the
# split, but a login-node smoke test measured the build at 29 s for two variants
# of a 1.28 M-vertex pot, so the whole CPU leg is ~15 min against 13.4 M
# vertices. A second queue wait costs more than 15 min of held card. If the
# build ever grows, split it to `sapphire` with -d afterok.
#
# STATED IN ADVANCE SO IT CAN FAIL. Prediction: EXCHANGE will be the common
# pattern at light and moderate wear -- abrasion removes the distinguishing
# detail from break faces, and a discrimination failure is an exchange. If the
# added pots instead SCATTER as they are worn, the Juglet's failure has the
# shape wear produces and route (b) has carried something across the bridge with
# no finer scan. Both outcomes are results and they point opposite ways. "The
# signature does not separate" is a third real answer and must be reported as
# one.
#
# THE FLOOR: if fewer than three ceramics pass their own e000 control, this is
# still n ~ 1, and the honest report is that TORA does not assemble enough real
# pottery unworn to support a ladder at all. That is a finding about the model
# and gets written back, not buried.
#
# Usage:
#   sbatch scripts/hpc/eval_erosion_ceramics.slurm
#   DRAWS=20 sbatch scripts/hpc/eval_erosion_ceramics.slurm

echo "=== erosion ladder (ceramics) started at $(date) on $(hostname) ==="
nvidia-smi | head -15 || true

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
ENV_PREFIX=$TORA_ROOT/envs/tora
DATA_ROOT=$TORA_ROOT/dataset
LOG_ROOT=$TORA_ROOT/eval_runs
CKPT=$TORA_ROOT/checkpoints/bbad_everyday_cka.ckpt

SRC_RAW=$DATA_ROOT/fractura_real.hdf5
SRC_NORM=$DATA_ROOT/ceramics_norm_src.hdf5
SWEEP=$DATA_ROOT/erosion_ceramics.hdf5
CALIB=$DATA_ROOT/erosion_ceramics.calibration.json

DRAWS=${DRAWS:-10}

module purge
module load Anaconda3/2024.02-1
module load CUDA/12.4.1
module load cuDNN/9.6.0.74-CUDA-12.4.1
eval "$(conda shell.bash hook)"
conda activate "$ENV_PREFIX"
export TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0"
export HF_HOME=$TORA_ROOT/.hf-cache
export WANDB_MODE=offline
cd "$TORA_ROOT/repo"

for f in "$CKPT" "$SRC_RAW"; do
    [ -e "$f" ] || { echo "missing: $f"; exit 1; }
done

echo ""
echo '########## gate 1: the checkout must POSTDATE the scoring fix ##########'
# Scoring on a pre-0d6a85f checkout would silently reproduce the retired
# size-dependent ruler and look like a confirmation. Costs one second.
if git merge-base --is-ancestor 0d6a85f HEAD; then
    echo "PASS: 0d6a85f (unit-box part accuracy) is an ancestor of $(git rev-parse --short HEAD)"
else
    echo "FAIL: this checkout PREDATES 0d6a85f. Every number would be on the retired ruler."
    exit 1
fi

echo ""
echo '########## step 1: normalise the ceramics source, ONCE, before erosion ##########'
if [ -e "$SRC_NORM" ]; then
    echo "already built: $SRC_NORM (delete to rebuild)"
else
    python scripts/normalize_real_hdf5.py \
        --src "$SRC_RAW" --dst "$SRC_NORM.tmp" --dataset-names ceramics
    mv "$SRC_NORM.tmp" "$SRC_NORM"
fi

echo ""
echo '########## gate 2: every ceramic must now read max|v| = 0.5 ##########'
# The whole point of step 1. If this does not hold, the model is being fed a
# conditioning value 100-190x outside anything it has seen, and nothing
# downstream means what it says.
python - "$SRC_NORM" <<'PYEOF'
import sys, h5py, numpy as np
bad = []
with h5py.File(sys.argv[1], "r") as f:
    for name in sorted(f["ceramics"].keys()):
        g = f["ceramics"][name]["pieces"]
        m = max(float(np.abs(g[k]["vertices"][:]).max()) for k in g.keys())
        flag = "ok" if abs(m - 0.5) < 1e-6 else "BAD"
        if flag == "BAD":
            bad.append((name, m))
        print(f"  {name:18s} max|v| = {m:.6f}  {flag}")
if bad:
    sys.exit(f"FAIL: not normalised: {bad}")
print("PASS: all ceramics at max|v| = 0.5")
PYEOF

echo ""
echo '########## step 2: build the ladder -- 8 pots x 5 rungs, NO --normalize ##########'
if [ -e "$SWEEP" ]; then
    echo "already built: $SWEEP (delete to rebuild)"
else
    python scripts/build_erosion_sweep.py \
        --src "$SRC_NORM" \
        --src-dataset ceramics \
        --strengths 0,0.25,0.5,0.75,1.0 \
        --out-hdf5 "$SWEEP.tmp" \
        --out-calibration "$CALIB" \
        --dataset-name erosion_ceramics
    mv "$SWEEP.tmp" "$SWEEP"
fi

echo ""
echo '########## gate 3: the scale must NOT have moved across the rungs ##########'
# By construction the factor is fixed (source normalised once, no --normalize on
# the build). If erosion moved the extent anyway, the experiment has two
# variables and the ladder is uninterpretable. Stop rather than report it.
python - "$SWEEP" <<'PYEOF'
import sys, re, h5py, numpy as np
from collections import defaultdict
rows = defaultdict(dict)
with h5py.File(sys.argv[1], "r") as f:
    d = f["erosion_ceramics"]
    for tag in sorted(d.keys()):
        obj, rung = tag.rsplit("_e", 1)
        g = d[tag]["pieces"]
        rows[obj][int(rung)] = max(
            float(np.abs(g[k]["vertices"][:]).max()) for k in g.keys())
worst = 0.0
print(f"  {'object':18s} " + " ".join(f"e{r:03d}" for r in (0, 25, 50, 75, 100)))
for obj in sorted(rows):
    vals = [rows[obj].get(r) for r in (0, 25, 50, 75, 100)]
    got = [v for v in vals if v is not None]
    drift = (max(got) - min(got)) / max(got) * 100 if got else 0.0
    worst = max(worst, drift)
    print(f"  {obj:18s} " + " ".join("  --  " if v is None else f"{v:.4f}" for v in vals)
          + f"   drift {drift:.3f}%")
print(f"\nworst drift across any ladder: {worst:.3f}%")
if worst > 1.0:
    sys.exit("FAIL: scale moved more than 1% across a ladder -- two variables, stop.")
print("PASS: scale held across every ladder")
PYEOF

echo ""
echo '########## step 3: evaluate the baseline, 10 draws, clouds saved ##########'
# Baseline arm only. wear_v1/wear_v2 carry their own finetuning regression
# (galli_pot loses 21-40 points at ZERO wear under wear_v2), so the baseline is
# the clean instrument here -- ticket 09 fixed that and it is unchanged.
# Renderer off: save_assembly_npz gives render_assembly_grid.py everything it
# needs, and the mitsuba pass was most of the previous job's runtime.
DIR="$LOG_ROOT/erosion_ceramics_${SLURM_JOB_ID}"
python sample.py \
    ckpt_path="$CKPT" \
    data_root="$DATA_ROOT" \
    data=zeroshot/erosion_ceramics \
    data.batch_size=4 \
    data.num_workers=4 \
    lora.enabled=false \
    model.n_generations="$DRAWS" \
    log_dir="$DIR" \
    "+visualizer._target_=tora.visualizer.FlowVisualizationCallback" \
    "+visualizer.renderer=none" \
    "+visualizer.center_points=true" \
    "+visualizer.save_trajectory=false" \
    "+visualizer.save_procrustes_assembly=true" \
    "+visualizer.save_assembly_npz=true"

echo ""
echo "### achieved wear per rung (compare against the Juglet's measured roughness) ###"
python - "$CALIB" <<'PYEOF'
import sys, json
from collections import defaultdict
cal = json.load(open(sys.argv[1]))
rows = defaultdict(dict)
for tag, v in cal.items():
    rows[v["object"]][v["strength"]] = v["relief_p90_mean"]
ss = [0.0, 0.25, 0.5, 0.75, 1.0]
print(f"  {'object':18s} " + " ".join(f"{s:>8.2f}" for s in ss))
for obj in sorted(rows):
    print(f"  {obj:18s} " + " ".join(
        f"{rows[obj][s]:8.5f}" if s in rows[obj] else "     -- " for s in ss))
print("\nA flat result is uninterpretable if the simulated wear plateaued below")
print("the Juglet's real roughness -- GARF's Exp 7 failed exactly there.")
PYEOF

echo ""
echo "### where the clouds are ###"
echo "  $DIR"
echo ""
echo "NEXT, on the laptop -- the analysis is free and does NOT belong in this job:"
echo "  1. fetch \$DIR/clouds to artifacts/wearsig_ceramics/"
echo "  2. read the e000 control FIRST and publish the exclusion list"
echo "  3. scripts/check_wear_failure_shape.py per pot, per rung, NO pooled mean"
echo "  4. render individual sherd placement at both ends of each ladder"
echo "  5. write back to intent/O8 AND intent/O7"
echo ""
echo "=== finished at $(date) ==="
