#!/bin/bash
#SBATCH --job-name=tora-rescore21
#SBATCH --partition=sapphire,cascade
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/logs/rescore_tora21_%j.log

# wear-beyond-juglet 21 (U3): own_place's whole-pot ruler forgot TORA clouds are in loader units
# (HDF5 / scale), so round 3's tolerance was `scale` (~0.43) times too short. On the saved round-3
# clouds of jobs 34485048/49: (1) scripts/check_whole_pot_ruler.py, (2) own_place rescore with the
# fixed key, written beside the old one as own_place_fixed21.json (the old file is kept).
#   sbatch scripts/hpc/rescore_tora21.slurm
set -uo pipefail
TORA_ROOT=/data/gpfs/projects/punim2657/TORA
COPIES=/data/gpfs/projects/punim2657/CSC/runs/20261106-1423_46dfd26_wear-miss20/out/copies.csv
module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate "$TORA_ROOT/envs/tora"
cd "$TORA_ROOT/repo"
echo "=== rescore_tora21 on $(hostname), repo $(git rev-parse --short HEAD), $(date) ==="
RUNS=()
for S in csc_whole20miss_clean_pooled_gate21_s1_34485048 csc_whole20miss_clean_pooled_gate21_s2_34485048 \
         csc_whole20miss_worn4_pooled_gate21_s1_34485049 csc_whole20miss_worn4_pooled_gate21_s2_34485049; do
    R=$TORA_ROOT/eval_runs/u10_$S
    [ -d "$R/clouds" ] || { echo "missing $R/clouds"; exit 1; }
    RUNS+=("$R")
done
echo "--- ruler check"
python scripts/check_whole_pot_ruler.py --copies "$COPIES" "${RUNS[@]}"; RC=$?
echo "ruler check exit $RC"
for R in "${RUNS[@]}"; do
    echo "--- rescore $(basename "$R")"
    python scripts/own_place.py --run "$R" --reconcile --pot-size "$COPIES" --json "$R/own_place_fixed21.json" \
        > "$TORA_ROOT/logs/rescore_tora21_${SLURM_JOB_ID}_$(basename "$R").txt" || RC=1
    tail -3 "$TORA_ROOT/logs/rescore_tora21_${SLURM_JOB_ID}_$(basename "$R").txt"
    cp "$R/own_place_fixed21.json" "$TORA_ROOT/logs/rescore_tora21_${SLURM_JOB_ID}_$(basename "$R")_own_place.json"
done
echo "=== done exit $RC $(date) ==="
exit $RC
