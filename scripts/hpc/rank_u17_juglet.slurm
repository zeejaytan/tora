#!/bin/bash
#SBATCH --job-name=u17-rank-jug
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/rank_u17/u17_rank_juglet_%j.log

set -euo pipefail

# U17 ticket 01 (.scratch/attempt-ranker/issues/01): GARF's 1,400 labelled Juglet
# attempts -> bundles -> gates -> Layer 1 ranking -> report. The ranker sees only
# $OUT/bundles; the key and the dataset are opened by the converter and report alone.
# Any gate failing stops the job before ranking (set -e).

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

P=/data/gpfs/projects/punim2657
OUT=$P/TORA/rank_u17/juglet_${SLURM_JOB_ID}
HDF5=$P/TORA/dataset/juglet_gt.hdf5
mkdir -p "$OUT"

RUNS=()
while read -r d; do
    RUNS+=("$P/GARF/logs/rwlora/$d/version_0/clouds/0.npz")
done < .scratch/attempt-ranker/juglet_runs.txt
echo "runs: ${#RUNS[@]}  (expect 70)"
[[ ${#RUNS[@]} -eq 70 ]]

echo "== convert"
python scripts/rank_convert.py --runs "${RUNS[@]}" --hdf5 "$HDF5" \
    --object juglet_gt/Juglet-000 --pot-mm 65 \
    --out "$OUT/bundles" --key "$OUT/key" --check 40

echo "== gates"
python scripts/check_attempt_ranker.py --bundles "$OUT/bundles" --n 20 \
    --forbid "$HDF5" "$OUT/key/idmap.json"

echo "== rank"
python scripts/rank_attempts.py --bundles "$OUT/bundles" --out "$OUT/ranks.json"

echo "== report"
python scripts/rank_report.py --ranks "$OUT/ranks.json" --key "$OUT/key/idmap.json" \
    --prereg .scratch/attempt-ranker/preregistration.md --out "$OUT/report.json" \
    --expect-genuine 2 --expect-near 19
