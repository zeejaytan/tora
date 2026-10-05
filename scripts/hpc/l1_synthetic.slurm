#!/bin/bash
#SBATCH --job-name=u17-l1-syn
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/rank_u17/u17_l1_syn_%j.log
set -euo pipefail
# U17 Layer 1 synthetic check: whole outer surface vs near-join-only (handle fix).
module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-1}"  # Spartan's profile sets 1; one python process here
cd /data/gpfs/projects/punim2657/TORA/repo
python scripts/l1_synthetic.py --near 3 5 8
