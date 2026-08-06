#!/bin/bash
#SBATCH --job-name=tora-reliefdiag
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_reliefdiag_%j.log

set -euo pipefail

# Check whether the smoothness measure can see anything at all on a thin-walled
# object. See scripts/diagnose_relief_thin_shell.py for why this is being asked.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

python scripts/diagnose_relief_thin_shell.py \
    --objects egg__egg1,egg__egg2,ceramics__blue_pot,ceramics__galli_pot
