#!/bin/bash
#SBATCH --job-name=tora-wallnoise
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=96G
#SBATCH --time=02:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_wallnoise_%j.log

set -euo pipefail

# The all-object table says wear made 13 of 27 walls THICKER, up to +43%. Wear
# removes material and cannot do that. Measure the estimator's noise floor
# before using any of that table. See scripts/check_wall_estimator_noise.py.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

python scripts/check_wall_estimator_noise.py --seeds 12
