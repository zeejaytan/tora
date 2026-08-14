#!/bin/bash
#SBATCH --job-name=tora-perface
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=160G
#SBATCH --time=01:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_perface_%j.log

set -euo pipefail

# The conservator, looking at the exported sherd: one fracture edge appears to
# have lost less material than the other two. Nothing shown so far can settle
# that -- the sections were three cuts through ONE face. This splits the break
# region by which fragment each part mates with and measures each separately.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

OUT=/data/gpfs/projects/punim2657/TORA/wear_blunt_v3/per_face
mkdir -p "$OUT"
DATA=/data/gpfs/projects/punim2657/TORA/dataset/real_heldout_norm.hdf5

for OBJ in plate blue_pot; do
    echo ""
    echo "################ $OBJ ################"
    python scripts/removal_per_face.py \
        --src "$DATA" --dataset real_heldout_norm --object "$OBJ" \
        --out "$OUT/${OBJ}_faces.glb" || true
done
echo "=== done $(date) ==="
