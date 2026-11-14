#!/bin/bash
#SBATCH --job-name=tora-render
#SBATCH --partition=sapphire,cascade
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/logs/render_tora_attempt_%j.log

# wear-beyond-juglet 06/07 (U3): best TORA attempt per pot against the truth and its input
# (scripts/render_tora_attempt.py). Reads saved clouds and own_place.json only.
#   COND=worn CARDS="p142_d00 p132_d00 p149_d00" MODELS="pooled:34293851,34293854:clean-break;noise:34293852,34293855:rough 1x" \
#     sbatch scripts/hpc/render_tora_attempt.slurm
# Other sets (ticket 21): SET=csc_whole20miss_clean COPIES=<that set's copies.csv> picks runs
# u10_${SET}_${ARM}_*_${JOBID} instead of round 1's u10_csc_whole_${COND}_${ARM}_s*_${JOBID}.
# COMPLETE=3 renders the first 3 complete attempts in seed/attempt order (the (b) rule) instead of the best.
# MODELS: entries ARM:JOBID,JOBID:LABEL separated by ";" (labels may contain spaces).
set -uo pipefail
TORA_ROOT=/data/gpfs/projects/punim2657/TORA
: "${COND:?COND=clean|worn|coarsev3}" "${CARDS:?CARDS=}" "${MODELS:?MODELS=}"
COPIES=${COPIES:-/data/gpfs/projects/punim2657/CSC/runs/20261103-1446_e51a6a8_wear-copies/out/copies.csv}
SET=${SET:-csc_whole_${COND}}
OUT=$TORA_ROOT/eval_runs/render_wbj06_${SLURM_JOB_ID}
module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate "$TORA_ROOT/envs/tora"
cd "$TORA_ROOT/repo"
echo "=== render_tora_attempt on $(hostname), repo $(git rev-parse --short HEAD), COND=$COND, SET=$SET, out $OUT ==="
[ -f "$COPIES" ] || { echo "missing $COPIES"; exit 1; }
IFS=';' read -ra ENTRIES <<< "$MODELS"
for E in "${ENTRIES[@]}"; do
    ARM=${E%%:*}; REST=${E#*:}; IDS=${REST%%:*}; LABEL=${REST#*:}
    RUNS=()
    for ID in ${IDS//,/ }; do
        for d in "$TORA_ROOT"/eval_runs/u10_${SET}_${ARM}_*s*_${ID}; do [ -d "$d" ] && RUNS+=("$d"); done
    done
    echo "--- $LABEL ($ARM): ${#RUNS[@]} runs"
    [ ${#RUNS[@]} -gt 0 ] || { echo "no runs for $ARM $IDS"; exit 1; }
    python scripts/render_tora_attempt.py --runs "${RUNS[@]}" --copies "$COPIES" --cards $CARDS \
        --label "$LABEL" --out "$OUT" ${COMPLETE:+--complete "$COMPLETE"} || exit 1
done
echo "=== done $(date) ==="
