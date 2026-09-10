#!/bin/bash
#SBATCH --job-name=tora-ribbonview
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=00:20:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_ribbonview_%j.log

set -euo pipefail

# Look at the walk before trusting its length.
#
# measure_strip_feasibility reports how far a profile can be traced along a
# break ribbon. That number is identical whether the walk follows the break or
# short-cuts across the wall between the ribbon's two edges, so AGENTS.md's
# "render the measured quantity itself, per-vertex, unbinned" applies before
# any of it is quoted. This colours every selected break-face point by its
# walking distance from one end of the longest path and draws the path.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

D=/data/gpfs/projects/punim2657/TORA/dataset
O=/data/gpfs/projects/punim2657/TORA/eval_runs/sherd_scale
mkdir -p "$O"

python scripts/render_traceable_ribbon.py \
    --juglet "$D/juglet_gt.hdf5" \
    --out    "$O/juglet_traceable_ribbon.png"

echo "=== done $(date) ==="
