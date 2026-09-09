#!/bin/bash
#SBATCH --job-name=tora-ceramics-arms
#SBATCH --partition=gpu-a100-short
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_ceramics_arms_%j.log

set -euo pipefail

# EIGHT REAL BROKEN POTS. The second real-fracture test, after the Juglet.
#
# Fractura's ceramics subset (GARF, ICCV 2025) is eight vessels that were
# physically broken and scanned with an Artec Spider at 0.05 mm, not shattered
# in software: blue_pot, galli_pot, pink_bowl, plate and narrow_bottle1-4, 3 to
# 12 fragments each. Real fracture surfaces, which is the exact thing the
# Breaking Bad training data does not have.
#
# WHAT IT DOES AND DOES NOT SETTLE. These are modern breaks with no burial
# wear, so they test the fracture surface and nothing else; the Juglet remains
# the only object that is both really broken and really worn. The GARF paper
# does not document how the ground-truth poses were established, but the
# conservator has confirmed these eight are in their correct assembly, so a bad
# score here is the method failing, not the answer key being wrong.
#
# NORMALISE THE SOURCE, OR THE RUN MEANS NOTHING. Job 30336653 ran all three
# arms against `zeroshot/fractura/ceramics`, which loads the RAW scan file:
# ceramics arrive at max|v| 54.9-187.3 raw units, so `scales` reached 77.4. The
# model was trained on scales in [0.375, 0.811]. `scales` is a CONDITIONING
# INPUT to the flow model at every denoising step, not bookkeeping, so at 77
# every arm is being asked about an object a hundred times larger than anything
# it has seen -- and every arm duly floored at 1/n_parts, the free anchor, on
# seven of eight pots. That is the input being out of domain, not the method
# failing, and it is a DIFFERENT fault from the scoring-units bug below that
# happens to share the word "units".
#
# The same eight pots normalised (scales 0.386-0.412, ticket 11 job 30293058)
# score blue_pot 5/5 at rung e000. So this job now defaults to the normalised
# ladder built by ticket 11, `zeroshot/erosion_ceramics`: the same eight pots at
# rung e000 (unworn) plus four abrasion rungs each, 40 objects. That also
# retires the six-object real_heldout_norm file whose sweep was half bones.
#
# SOURCE=fractura/ceramics is kept for reproducing the old runs and WILL be out
# of the trained band. The guard below refuses it unless SCALE_OK=1 is set.
#
# Data lives in dataset/erosion_ceramics.hdf5 (normalised once before erosion)
# and dataset/ceramics.hdf5, a symlink onto the 3 GB fractura_real.hdf5. Load
# either by that stem: the loader matches the file stem against a key inside
# the file, and "fractura_real" is not one of them.
#
# max_samples_per_batch is 8, not the 1 earlier runs used. All eight pots fit in
# one batch, so 1 saved the point clouds for a single pot -- and the npz is the
# only thing that lets a score be recomputed without GPU time. It is what
# exposed the units bug below on two pots; save it for all eight.
#
# THE UNITS BUG IS FIXED; DO NOT RESCORE BY HAND. Commit 0d6a85f (2026-09-02
# 14:58) moved part_accuracy into the unit-length box the benchmark states its
# threshold in. `part_accuracy` is now the corrected number and
# `part_accuracy_absolute` the legacy stored-units one, kept as the marker that
# a result is post-fix. Before that fix every real object scored exactly
# 1/n_parts -- the anchor, free by construction -- because millimetre-scale
# ceramics (scale ~61) were asked to land ~15,000x more precisely than
# normalised Breaking Bad fragments (scale ~0.5). The one baseline arm that
# completed, job 29886425, finished at 14:11 and is therefore PRE-fix: it can
# not be compared against arms from this run, which is why baseline is rerun
# here rather than reused.
#
# TWO THINGS THAT STILL NEED CARE, both from the wear v3 read-out
# (docs/notes/LORAV3_29880370_RESULT.md):
#   - part_accuracy is a RELABELLED count. compute_part_acc runs a Hungarian
#     assignment, so a sherd standing in another sherd's place is credited. The
#     saved npz is what separates that from own-place seating; on the Juglet,
#     70% of one arm's credit turned out to be relabelling.
#   - the free anchor counts as a seated fragment, and is skipped in the
#     rotation sum while dividing by all fragments. Read through
#     scripts/readout.py, which names it, never off the printed tables.
#
# Anchor-fixed, as every prior run on these pots. Note that numbers from this
# job do NOT sit beside jobs 24342475 / 24343146 / 29886425 without adjustment:
# those predate both the unit-box scoring fix and the normalised source.
#
# Usage:
#   sbatch scripts/hpc/eval_ceramics_arms.slurm                  # 3 arms, ladder
#   DRAWS=20 ARMS=baseline sbatch scripts/hpc/eval_ceramics_arms.slurm
#   TRAINED_CKPT=/path/to/epoch-N.ckpt sbatch scripts/hpc/eval_ceramics_arms.slurm
#   SOURCE=zeroshot/fractura/ceramics SCALE_OK=1 BATCH=8 sbatch ...   # raw, out of band

echo "=== ceramics arms started at $(date) on $(hostname) ==="
nvidia-smi | head -15 || true

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
ENV_PREFIX=$TORA_ROOT/envs/tora
DATA_ROOT=$TORA_ROOT/dataset
LOG_ROOT=$TORA_ROOT/eval_runs
CKPT=$TORA_ROOT/checkpoints/bbad_everyday_cka.ckpt
DRAWS=${DRAWS:-10}
ARMS=${ARMS:-"adapter_on adapter_off baseline"}
SOURCE=${SOURCE:-zeroshot/erosion_ceramics}
BATCH=${BATCH:-4}

if [[ "$SOURCE" == *fractura/ceramics* && "${SCALE_OK:-0}" != "1" ]]; then
    echo "REFUSING: $SOURCE is the raw millimetre scan file (scales ~77) and the"
    echo "model was trained on scales in [0.375, 0.811]. That is what made job"
    echo "30336653 uninterpretable. Use SOURCE=zeroshot/erosion_ceramics, or set"
    echo "SCALE_OK=1 if you are deliberately reproducing an out-of-band run."
    exit 1
fi

LORA_ON=(lora.enabled=true lora.r=128 lora.alpha=256 lora.dropout=0.1 lora.last_n_blocks=6 lora.train_head=true)

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

for f in "$DATA_ROOT/$(basename "$SOURCE").hdf5" "$CKPT"; do
    [ -e "$f" ] || { echo "missing: $f"; exit 1; }
done

echo ""
echo '########## gate: the SOURCE must sit inside the trained scale band ##########'
# The block above refuses one source BY NAME. That is a paragraph, not a gate:
# any other raw-unit file walks straight past it. This one reads the data.
# `scales` is a CONDITIONING INPUT -- the object extent is sinusoidally encoded
# and fed to the flow model at every denoising step -- so a source outside the
# band the model was trained on is compromised before the first draw. Job
# 30336653 spent three GPU-hours proving that again at scales ~77.
SRC_HDF5="$DATA_ROOT/$(basename "$SOURCE").hdf5"
SCALE_OK="${SCALE_OK:-0}" python - "$SRC_HDF5" <<'PYEOF'
import os, sys, h5py, numpy as np
LO, HI = 0.375, 0.811          # scripts/readout.py: TRAINED_SCALE_BAND
# `scales` is np.max(np.abs(pts_gt)) AFTER the dataset centres the sampled
# cloud (tora/data/dataset.py:427), not the raw stored extent. Centring on the
# vertex centroid reproduces it to ~2% (blue_pot: 0.4052 here vs 0.4117 fed),
# which is close enough to catch an order-of-magnitude error and NOT close
# enough to adjudicate the band edge -- so this warns near the edge and refuses
# only on a gross violation. The exact per-draw check is the summariser's, on
# the `scales` the model actually received.
GROSS = 3.0                    # a factor-3 miss is never a borderline call
bad = []
with h5py.File(sys.argv[1], "r") as f:
    for ds in sorted(f.keys()):
        for tag in sorted(f[ds].keys()):
            g = f[ds][tag]["pieces"]
            V = np.concatenate([g[k]["vertices"][:] for k in g.keys()], 0)
            est = float(np.abs(V - V.mean(0)).max())
            if not (LO <= est <= HI):
                bad.append((tag, est))
gross = [(t, v) for t, v in bad if v > HI * GROSS or v < LO / GROSS]
if bad:
    for tag, v in bad[:8]:
        print(f"  {tag:24s} scales ~ {v:.3f}   outside [{LO}, {HI}]")
    if len(bad) > 8:
        print(f"  ... {len(bad)} object(s) outside the band in total")
if gross and os.environ.get("SCALE_OK") != "1":
    sys.exit(f"FAIL: {len(gross)} object(s) miss the trained band by more than "
             f"{GROSS}x -- this is the fault that made job 30336653 "
             f"uninterpretable. Normalise the source, or set SCALE_OK=1 to "
             f"reproduce an out-of-band run on purpose.")
if gross:
    print("SCALE_OK=1: continuing on a grossly out-of-band source. These numbers")
    print("are not comparable to any in-band run; label them out-of-band wherever")
    print("they are quoted.")
elif bad:
    print(f"WARN: {len(bad)} object(s) sit modestly outside [{LO}, {HI}]. Not fatal --")
    print("normalising to max|v| = 0.5 sets the extent from the file origin, and a")
    print("squat or off-centre pot loses more than a tall one when the cloud is")
    print("re-centred. Read these objects knowing they are a mild extrapolation.")
else:
    print(f"PASS: every object estimates inside [{LO}, {HI}]")
PYEOF

# Only go looking for the adapter if an arm actually needs it, so the baseline
# can be scored before the training run has finished.
if [[ "$ARMS" == *adapter* ]] && [ -z "${TRAINED_CKPT:-}" ]; then
    # save_top_k=1 leaves exactly one epoch-*.ckpt -- the best epoch on
    # validation, not the last. More than one means the checkpointing changed
    # and picking by date would silently take the final epoch again, which is
    # what made job 29623885 uninterpretable. Stop rather than guess.
    # -not -path "*_smoke_*" : the training script writes a smoke-test run under
    # lora_vessels_v3_smoke_<jobid> beside the real one, so without this the
    # guard below counts three checkpoints and refuses to pick. That is what
    # stopped job 29888541 before either adapter arm ran.
    FOUND=$(find "$TORA_ROOT/output" -path "*lora_vessels_v3_*" \
                 -not -path "*_smoke_*" -name "epoch-*.ckpt" | sort)
    N=$(echo "$FOUND" | grep -c . || true)
    [ "$N" = "1" ] || { echo "expected exactly one v3 adapter checkpoint, found $N:"; echo "$FOUND"; exit 1; }
    TRAINED_CKPT="$FOUND"
    echo "adapter under test: $TRAINED_CKPT"
fi
echo "untouched baseline: $CKPT"
echo "draws per pot:      $DRAWS"
echo "arms:               $ARMS"

run_arm () {
    NAME=$1; C=$2; shift 2
    echo ""
    echo "########## $NAME : $DRAWS draws on each of the 8 pots ##########"
    python sample.py ckpt_path="$C" data_root="$DATA_ROOT" \
        data="$SOURCE" data.batch_size="$BATCH" data.num_workers=4 \
        "$@" \
        log_dir="$LOG_ROOT/ceramarm_${NAME}_${SLURM_JOB_ID}" \
        model.n_generations="$DRAWS" \
        "+visualizer._target_=tora.visualizer.FlowVisualizationCallback" \
        "+visualizer.renderer=mitsuba" \
        "+visualizer.image_size=512" \
        "+visualizer.max_samples_per_batch=$BATCH" \
        "+visualizer.center_points=true" \
        "+visualizer.save_trajectory=false" \
        "+visualizer.save_procrustes_assembly=true" \
        "+visualizer.save_assembly_npz=true" || true
}

# adapter_off is NOT the untouched baseline: the pose head was retrained and
# has no off switch. Three arms, not two.
DONE_DIRS=()
for ARM in $ARMS; do
    case "$ARM" in
        adapter_on)  run_arm adapter_on  "$TRAINED_CKPT" "${LORA_ON[@]}" lora.active=true ;;
        adapter_off) run_arm adapter_off "$TRAINED_CKPT" "${LORA_ON[@]}" lora.active=false ;;
        baseline)    run_arm baseline    "$CKPT"         lora.enabled=false ;;
        *) echo "unknown arm: $ARM"; exit 1 ;;
    esac
    DONE_DIRS+=("$LOG_ROOT/ceramarm_${ARM}_${SLURM_JOB_ID}")
done

echo ""
echo "### pot by pot, in fragments seated ###"
python scripts/summarise_ceramics_arms.py --runs "${DONE_DIRS[@]}" || true

echo ""
echo "### renders ###"
# NOT `find | sort | head`: head closes the pipe, find takes SIGPIPE, and under
# `set -o pipefail` the job exits 141 with every result already written. That is
# exactly how job 29888540 "FAILED". The subshell finishes before head runs.
LISTING=$(find "$LOG_ROOT" -path "*ceramarm_*_${SLURM_JOB_ID}*" \
    \( -name "*.png" -o -name "*.npz" \) | sort)
head -60 <<< "$LISTING"
echo "saved clouds (npz): $(grep -c '[.]npz$' <<< "$LISTING" || true)"

echo ""
echo "=== Finished at $(date) ==="
echo "Do not quote object_chamfer or translation_error raw: they are in each"
echo "pot's own units. The summariser prints offset as a fraction of the pot"
echo "instead, which is the number that survives a change of source."
