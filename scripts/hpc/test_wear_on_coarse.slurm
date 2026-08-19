#!/bin/bash
#SBATCH --job-name=tora-coarsewear
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=160G
#SBATCH --time=03:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_coarsewear_%j.log

set -euo pipefail

# The conservator's challenge: how does a coarse model stop you making it worn,
# when wear is blunting the fracture surface AND reducing the contact between
# the pieces?
#
# It does not, and my claim was too strong. It covers only the blunting half.
# Blunting needs fine texture to exist in the mesh; opening the joins needs no
# fine detail at all. And Gate A says real scans carry no fracture texture
# anyway, so the join-opening half is the one that survives digitisation and
# matters more for training data meant to resemble real material.
#
# Measured here rather than argued: what is available to blunt, what blunting
# actually moves, and what a small recession does to the joins -- on Breaking
# Bad vessels against blue_pot and plate as fine-mesh controls.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

python scripts/test_wear_on_coarse.py \
    --bbad /data/gpfs/projects/punim2657/TORA/dataset/breaking_bad_vol.hdf5 \
    --fine /data/gpfs/projects/punim2657/TORA/dataset/real_heldout_norm.hdf5

echo ""
echo "=== Finished at $(date) ==="
