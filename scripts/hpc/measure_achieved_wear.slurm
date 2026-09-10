#!/bin/bash
#SBATCH --job-name=tora-achieved
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --time=00:40:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_achieved_%j.log

set -euo pipefail

# How far did each rung of the erosion ladder actually move the surface?
#
# Job 30385552 reported the NOMINAL kernel width per rung and it is not the
# wear depth. Two reasons: a wide kernel on a nearly-flat surface moves it very
# little, and the kernel saturates anyway -- erode_fracture_band queries at
# most knn = 48 surface samples from a fixed 20,000 per sherd, so once the
# radius holds 48 samples the extra radius does nothing and the nominal
# 0.05 * max(extents) * strength stops describing anything that happens.
#
# The ladder's topology is byte-identical across rungs, so this needs no model
# at all: subtract the vertex arrays. Vertex i at e000 and vertex i at e100 are
# the same point on the same pot, and the distance between them IS the wear
# depth in millimetres.
#
# What it decides: which rungs move the surface further than the Juglet's own
# break-face point spacing of 0.29-0.48 mm. A rung below that cannot be
# compared against the Juglet however well the new instrument works -- the
# reference has no points close enough together to register the change. This
# is the same question job 30385552 was asked; it answered with the wrong
# quantity.
#
# Cheap: array subtraction and percentiles. No probing, no KD-trees, no
# quadrics.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

D=/data/gpfs/projects/punim2657/TORA/dataset
O=/data/gpfs/projects/punim2657/TORA/eval_runs/sherd_scale
mkdir -p "$O"

python scripts/measure_achieved_wear.py \
    --erosion "$D/erosion_ceramics.hdf5" \
    --raw     "$D/fractura_real.hdf5" \
    --out     "$O/achieved_wear.json"

echo "=== done $(date) ==="
