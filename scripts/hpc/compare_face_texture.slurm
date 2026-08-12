#!/bin/bash
#SBATCH --job-name=tora-facetex
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=160G
#SBATCH --time=02:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_facetex_%j.log

set -euo pipefail

# The plate blunts less than the other three. The numbers say its fracture
# texture sits at a coarser scale than the cutoff reaches. Draw it before
# believing it -- that is the rule, and four earlier views of wear in this
# project measured correctly while being too coarse to show the effect.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

OUT=/data/gpfs/projects/punim2657/TORA/wear_blunt_v3
mkdir -p "$OUT"

python scripts/compare_face_texture.py \
    --src /data/gpfs/projects/punim2657/TORA/dataset/real_heldout_norm.hdf5 \
    --dataset real_heldout_norm \
    --objects blue_pot plate coxae vert9 \
    --face-a blue_pot --face-b plate \
    --out "$OUT/face_texture.png"

echo "=== done $(date) ==="
