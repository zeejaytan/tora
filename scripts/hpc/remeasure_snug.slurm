#!/bin/bash
# pr-workspace .scratch/uneven-wear/issues/09 (U20): ticket 01's join fingerprint
# (scripts/measure_join_fingerprint.py) on the re-seated Juglet, juglet_gt_snug (ticket 08,
# run SNUG_RUN), beside the hand pose and the strict copy, all in the hand pose's
# millimetres (LONGEST scales each re-seated file so one file unit is the same mm).
# Writes $RUN_DIR/out only.
#
#   git -C $T/repo show $SHA:scripts/hpc/remeasure_snug.slurm > $TMPDIR/rms.slurm
#   $P/agent/pr-workspace/scripts/new_run.sh $T $T/repo $SHA remeasure-snug $TMPDIR/rms.slurm
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_%x_%j.log
#SBATCH --job-name=tora-remeasure-snug
#SBATCH --partition=sapphire,cascade
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=03:00:00
set -euo pipefail
: "${RUN_DIR:?submit through new_run.sh}" "${SOURCE_COMMIT:?}" "${CANONICAL:?}"
export PYTHONDONTWRITEBYTECODE=1
P=/data/gpfs/projects/punim2657
PY=$P/TORA/envs/tora/bin/python
JUG=$P/TORA/dataset/juglet_gt.hdf5
SNUG_RUN=${SNUG_RUN:-$P/TORA/runs/20261109-0008_57cd34b_reseat-juglet2}
source $P/agent/pr-workspace/scripts/run_from_commit.sh "$CANONICAL" "$SOURCE_COMMIT" "$RUN_DIR"
cd "$SRC"
md5sum "$JUG" "$SNUG_RUN"/out/juglet_gt_snug*.hdf5 | tee -a "$RUN_DIR/source.txt"
# longest side of each file, so the re-seated ones keep the hand pose's mm per unit
cat > "$RUN_DIR/longest.py" <<'EOF'
import sys, h5py, numpy as np
ext = []
for f in sys.argv[1:]:
    with h5py.File(f, "r") as h:
        g = h["juglet_gt"]["Juglet-000"]["pieces"]
        a = np.concatenate([g[k]["vertices"][:] for k in g])
        ext.append(float((a.max(0) - a.min(0)).max()))
print(" ".join(f"{65.0 * e / ext[0]:.4f}" for e in ext))
EOF
read -r L_HAND L_SNUG L_STRICT < <($PY "$RUN_DIR/longest.py" "$JUG" \
    "$SNUG_RUN/out/juglet_gt_snug.hdf5" "$SNUG_RUN/out/juglet_gt_snug_strict.hdf5")
echo "longest mm: hand $L_HAND snug $L_SNUG strict $L_STRICT" | tee -a "$RUN_DIR/source.txt"
$PY -u scripts/measure_join_fingerprint.py --out "$RUN_DIR/out" \
    --object "hand=$JUG:juglet_gt::$L_HAND" \
    --object "snug=$SNUG_RUN/out/juglet_gt_snug.hdf5:juglet_gt::$L_SNUG" \
    --object "strict=$SNUG_RUN/out/juglet_gt_snug_strict.hdf5:juglet_gt::$L_STRICT"
ls -la "$RUN_DIR/out"
