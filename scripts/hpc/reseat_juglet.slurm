#!/bin/bash
# pr-workspace .scratch/uneven-wear/issues/08 (U20): re-seat the Juglet snug, with no sherd
# inside another by more than one scan spacing (tolerant, the new truth) and strict beside it
# (scripts/separate_juglet_overlap.py). juglet_gt.hdf5 is only read; md5 before and after.
# Writes $RUN_DIR/out only: juglet_gt_snug.hdf5 (+ _strict where met), juglet_gt_snug.json,
# the worst/typical and every-join section renders.
#
# Submit from the login node through new_run.sh:
#   git -C $T/repo fetch origin
#   git -C $T/repo show $SHA:scripts/hpc/reseat_juglet.slurm > $TMPDIR/reseat.slurm
#   $P/agent/pr-workspace/scripts/new_run.sh $T $T/repo $SHA reseat-juglet $TMPDIR/reseat.slurm
# ASIDE (A:B:x,y,z:R, ';'-separated) names spots set aside by the conservator; default: the
# tip of sherd 0 inside sherd 7 (2026-11-08 trial: it alone drives 4-7 degree turns).
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_%x_%j.log
#SBATCH --job-name=tora-reseat-jug
#SBATCH --partition=sapphire,cascade
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=10:00:00
set -euo pipefail
: "${RUN_DIR:?submit through new_run.sh}" "${SOURCE_COMMIT:?}" "${CANONICAL:?}"
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
P=/data/gpfs/projects/punim2657
PY=$P/TORA/envs/tora/bin/python
JUG=$P/TORA/dataset/juglet_gt.hdf5
ASIDE=${ASIDE-"0:7:-0.110,-0.065,0.235:2.5"}
source $P/agent/pr-workspace/scripts/run_from_commit.sh "$CANONICAL" "$SOURCE_COMMIT" "$RUN_DIR"
cd "$SRC"
md5sum "$JUG" | tee -a "$RUN_DIR/source.txt"
echo "set aside: ${ASIDE:-none}" | tee -a "$RUN_DIR/source.txt"

echo "=== G0 self-test (boxes with known answers)"
$PY -u scripts/selftest_separate_juglet.py

A=(); IFS=';' read -ra SP <<< "$ASIDE"; for s in "${SP[@]}"; do [ -n "$s" ] && A+=(--set-aside "$s"); done
set +e
$PY -u scripts/separate_juglet_overlap.py --juglet "$JUG" --out-dir "$RUN_DIR/out" \
    --workers "$SLURM_CPUS_PER_TASK" "${A[@]}"
rc=$?
set -e
echo "=== reference unchanged?"
md5sum "$JUG" | tee -a "$RUN_DIR/source.txt"
exit $rc
