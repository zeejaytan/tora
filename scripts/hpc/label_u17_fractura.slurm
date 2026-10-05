#!/bin/bash
#SBATCH --job-name=u17-label-frac
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/rank_u17/u17_label_fractura_%j.log

set -euo pipefail

# U17 ticket 04 (.scratch/attempt-ranker/issues/04): label GARF's Fractura attempts.
# The same 7 arms x ds1..10 as the Juglet's 70 labelled runs.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
# OMP_NUM_THREADS stays 1 (Spartan's profile): the long steps run one worker process per CPU.
cd /data/gpfs/projects/punim2657/TORA/repo

L=/data/gpfs/projects/punim2657/GARF/logs/rwlora
RUNS=()
while read -r d; do
    RUNS+=("$L/${d/juglet_gt/fractura_fresh}")
done < .scratch/attempt-ranker/juglet_runs.txt
for r in "${RUNS[@]}"; do [[ -d $r ]] || { echo "missing $r"; exit 1; }; done
echo "runs: ${#RUNS[@]}  (expect 70)"
[[ ${#RUNS[@]} -eq 70 ]]

OUT=/data/gpfs/projects/punim2657/TORA/rank_u17/fractura_labels_${SLURM_JOB_ID}.json
python scripts/label_attempts.py --runs "${RUNS[@]}" --out "$OUT"
