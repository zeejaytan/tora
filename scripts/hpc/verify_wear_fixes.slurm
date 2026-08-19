#!/bin/bash
#SBATCH --job-name=tora-wearfix
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=160G
#SBATCH --time=06:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_wearfix_%j.log

set -euo pipefail

# Verify the two wear fixes on real geometry, not on the synthetic pair.
#
# FIX 1, the under-worn rim. Blunting measured how far a point stood proud of
# the MEAN of its neighbours, and near the edge of a break face those neighbours
# all lie inward, so the mean is dragged with them. Measured before the fix:
# 7-9% of available relief removed within one cutoff of an edge against 93-99%
# well inside. A fitted plane extrapolates instead of averaging, so the bias
# should go. THIS is the number that has to move.
#
# FIX 2, scan-realistic variants become the default. Nothing to verify here
# geometrically; it is a change of mix. But the spectrum test must still pass,
# because a fitted envelope is a different ruler and could have broken the
# teeth/curve behaviour that was established with the old one.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

DATA=/data/gpfs/projects/punim2657/TORA/dataset/real_heldout_norm.hdf5
OUT=/data/gpfs/projects/punim2657/TORA/wear_rimfix
mkdir -p "$OUT"

for OBJ in plate blue_pot; do
    echo ""
    echo "################ RIM EFFICIENCY: $OBJ ################"
    python scripts/export_blunting_diagnostic.py \
        --src "$DATA" --dataset real_heldout_norm --object "$OBJ" \
        --out "$OUT/${OBJ}.glb" || true
done

for OBJ in blue_pot plate coxae vert9; do
    echo ""
    echo "################ SPECTRUM: $OBJ ################"
    python scripts/validate_wear_spectrum.py \
        --src "$DATA" --dataset real_heldout_norm --object "$OBJ" \
        --mode blunt --no-chips || true
done

echo ""
echo "=== Finished at $(date) ==="
echo "The rim table is the point. Efficiency near the edge should no longer sit"
echo "at 7-9% against 93-99% inside; flat across the bins means the bias is gone."
