#!/bin/bash
# pr-workspace .scratch/uneven-wear/issues/12 (U20): write a test copy of the Juglet with the
# scan-flaw tip of sherd 0 (inside sherd 7) trimmed off (scripts/make_juglet_tipfix.py), at
# $RUN_DIR/out/juglet_gt.hdf5 (named so GARF's rwlora_arm.slurm reads it as SETS=$RUN_DIR/out/juglet_gt).
# juglet_gt itself is only read. Writes $RUN_DIR/out only.
#   git -C $T/repo show $SHA:scripts/hpc/juglet_tipfix.slurm > $TMPDIR/jtf.slurm
#   $P/agent/pr-workspace/scripts/new_run.sh $T $T/repo $SHA juglet-tipfix $TMPDIR/jtf.slurm
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_%x_%j.log
#SBATCH --job-name=tora-juglet-tipfix
#SBATCH --partition=sapphire,cascade
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=00:30:00
set -euo pipefail
: "${RUN_DIR:?submit through new_run.sh}" "${SOURCE_COMMIT:?}" "${CANONICAL:?}"
export PYTHONDONTWRITEBYTECODE=1
P=/data/gpfs/projects/punim2657
PY=$P/TORA/envs/tora/bin/python
JUG=$P/TORA/dataset/juglet_gt.hdf5
source $P/agent/pr-workspace/scripts/run_from_commit.sh "$CANONICAL" "$SOURCE_COMMIT" "$RUN_DIR"
cd "$SRC"
md5sum "$JUG" | tee -a "$RUN_DIR/source.txt"
$PY -u scripts/make_juglet_tipfix.py "$JUG" "$RUN_DIR/out/juglet_gt.hdf5" --json "$RUN_DIR/out/tipfix.json"
md5sum "$JUG" "$RUN_DIR/out/juglet_gt.hdf5" | tee -a "$RUN_DIR/source.txt"
ls -la "$RUN_DIR/out"
