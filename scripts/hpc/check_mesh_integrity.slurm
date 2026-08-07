#!/bin/bash
#SBATCH --job-name=tora-meshint
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --time=03:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_meshint_%j.log

set -euo pipefail

# Conservator flagged holes appearing in the mesh as the wear series progresses.
# Quantify it, including on the untouched scans. See scripts/check_mesh_integrity.py.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

python scripts/check_mesh_integrity.py \
    --objects ceramics__plate,ceramics__blue_pot,egg__egg1,bones__limb3,ceramics__narrow_bottle3
