#!/bin/bash
#SBATCH --job-name=tora-bluntdiag
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=160G
#SBATCH --time=01:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_bluntdiag_%j.log

set -euo pipefail

# The conservator asked to see the model rather than a plot of it, and to see
# where the suspected fault is. Exports the sherd painted with what blunting
# removed, what was available to remove, how much of it actually came off, and
# where the break-face ribbon has its edge.
#
# The plate is the case in question -- a flat dish whose break face is a narrow
# ribbon. blue_pot is the control: a broad break face where blunting works.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

OUT=/data/gpfs/projects/punim2657/TORA/wear_blunt_v3
mkdir -p "$OUT"
DATA=/data/gpfs/projects/punim2657/TORA/dataset/real_heldout_norm.hdf5

for OBJ in plate blue_pot; do
    echo ""
    echo "################ $OBJ ################"
    python scripts/export_blunting_diagnostic.py \
        --src "$DATA" --dataset real_heldout_norm --object "$OBJ" \
        --out "$OUT/${OBJ}_blunting.glb" || true
done

ls -la "$OUT"/*.glb
echo "=== done $(date) ==="
