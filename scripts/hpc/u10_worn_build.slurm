#!/bin/bash
#SBATCH --job-name=tora-u10worn
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=96G
#SBATCH --time=04:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/logs/u10_worn_build_%j.log

# U10 ticket 08 (tora .scratch/u10-juglet-ceiling/issues/08): build ONE arm's pooled
# training file from u10_generic + u10_ceiling. Submit once per arm:
#   sbatch --export=ALL,MODE=worn  scripts/hpc/u10_worn_build.slurm
#   sbatch --export=ALL,MODE=noise scripts/hpc/u10_worn_build.slurm
#   sbatch --export=ALL,MODE=noise,SCALE=50 ...   # ticket 09 dose sweep: one level, u10_noise_d050
#   1. write_u10_worn.py: break-face recession (or RMS-matched jitter) + manifest.
#   2. the Juglet through the same contact ruler, for the reference.
#   3. check_u10_loader.py: TORA's loader keeps every object the split lists.
# Steps 2-3 run even if one fails; the job exits non-zero if any did.
set -uo pipefail
ROOT=/data/gpfs/projects/punim2657/TORA
trap 'rc=$?; echo "$(date -u +%FT%TZ) job ${SLURM_JOB_ID:-nojob} step u10_worn_build ${MODE:-?} exit $rc" >> "$ROOT/logs/job_status.log"' EXIT
: "${MODE:?set MODE=worn or MODE=noise}"

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora

CSC=$ROOT/../CSC/work/u10_corpus_30888410
DATA=$ROOT/dataset
SCALE=${SCALE:-0}
NAME=u10_${MODE}; [ "$SCALE" = 0 ] || NAME=$(printf 'u10_%s_d%03d' "$MODE" "$SCALE")
echo "building $NAME"
WORK=$ROOT/work/u10_worn_${MODE}_${SLURM_JOB_ID}
mkdir -p "$WORK"
cd "$ROOT/repo" || exit 2
git log -1 --format='repo %h %s'

python scripts/write_u10_worn.py --src "$DATA" --csc "$CSC" --mode "$MODE" --out "$WORK" \
    --scale-pct "$SCALE" --workers "${SLURM_CPUS_PER_TASK:-32}" || { echo "build failed"; exit 1; }
bad=0
echo "=== juglet reference, same ruler"
python scripts/write_u10_worn.py --measure "$DATA/juglet_gt.hdf5" --dataset juglet_gt \
    | tee "$WORK/juglet_ruler.jsonl" || bad=1
echo "=== loader"
python scripts/check_u10_loader.py --juglet "$DATA/juglet_gt.hdf5" \
    --out "$WORK/${NAME}_loader.png" "$WORK/${NAME}.hdf5" || bad=1

ls -lh "$WORK"
echo "WORK=$WORK"
exit $bad
