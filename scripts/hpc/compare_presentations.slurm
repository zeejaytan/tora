#!/bin/bash
#SBATCH --job-name=tora-present
#SBATCH --partition=sapphire,cascade
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:20:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/logs/compare_presentations_%j.log

# wear-beyond-juglet 06 (U3): do two runs of the same seed get the same presentation?
# Reads saved clouds only; no GPU, no sampling.
#   RUNS="dirA dirB ..." sbatch scripts/hpc/compare_presentations.slurm
set -uo pipefail
TORA_ROOT=/data/gpfs/projects/punim2657/TORA
: "${RUNS:?RUNS= space-separated eval_runs dirs, first is the reference}"
module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate "$TORA_ROOT/envs/tora"
cd "$TORA_ROOT/repo"
echo "=== compare_presentations on $(hostname), repo $(git rev-parse --short HEAD) ==="
R=(); for r in $RUNS; do R+=("$TORA_ROOT/eval_runs/$r"); done
python scripts/compare_presentations.py "${R[@]}"
