#!/bin/bash
#SBATCH --job-name=tora-beforeafter
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=160G
#SBATCH --time=01:30:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_beforeafter_%j.log

set -euo pipefail

# The previous export gave the conservator five identically shaped copies at the
# same coordinates with no before, no after and no scale -- nothing to read.
# This replaces it with a section across the break face (fresh and worn as two
# lines, removed material shaded between) and a mesh laid out in a row.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

OUT=/data/gpfs/projects/punim2657/TORA/wear_blunt_v3/before_after
mkdir -p "$OUT"
DATA=/data/gpfs/projects/punim2657/TORA/dataset/real_heldout_norm.hdf5

for OBJ in plate blue_pot; do
    echo ""
    echo "################ $OBJ ################"
    python scripts/show_blunting_before_after.py \
        --src "$DATA" --dataset real_heldout_norm --object "$OBJ" \
        --out-dir "$OUT" || true
done

ls -la "$OUT"
echo "=== done $(date) ==="
