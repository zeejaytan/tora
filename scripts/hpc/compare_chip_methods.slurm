#!/bin/bash
#SBATCH --job-name=tora-chipcmp
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=160G
#SBATCH --time=04:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_chipcmp_%j.log

set -euo pipefail

# manifold3d is installed, so a chip can be a real boolean subtraction rather
# than a pressed dish. Both behave on synthetic slabs. Decide on real scans,
# which are the case that actually breaks boolean operations.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

python -c "import manifold3d, trimesh; print('boolean backend present, trimesh', trimesh.__version__)"

python scripts/compare_chip_methods.py
