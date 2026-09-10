#!/bin/bash
#SBATCH --job-name=tora-strip
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_strip_%j.log

set -euo pipefail

# Can a strip long enough for the ISO filter rules be laid on these break faces?
#
# Round 1 of the wear-ruler grilling settled the SHAPE of the measuring patch:
# a strip along the break ribbon, not a disc, because the Juglet's 1.79 mm wall
# (job 30385552) cannot hold the 2.88 mm disc its own 0.29-0.48 mm point
# spacing demands. It did not settle the SIZE, and surface-roughness metrology
# fixes that with two ratios to numbers we have already measured:
#
#   ISO 3274        sampling interval <= cutoff / 5   ->  lambda_c >= 5 x spacing
#   ISO 21920/4288  evaluation length = 5 cutoffs     ->  strip >= 25 x spacing
#
# On the Juglet's 0.48 mm that is lambda_c >= 2.4 mm and a strip >= 12 mm long.
# THAT IS AN ASSERTION UNTIL MEASURED. A 65 mm juglet's break ribbons may not
# run 12 mm unbroken, and if they do not, either the cutoff comes down below
# what the spacing supports, or the evaluation-length rule gets broken
# deliberately and said out loud. Nothing downstream of Q8 is safe until this
# job answers.
#
# Reads e000 only: this is about how the objects are SAMPLED, not about wear.
# Selection is wear_fracture_spectrum.mating_faces (near another sherd AND
# facing it, recall 99.5-99.8%); faces are never pooled.
#
# Cheap: KD-tree ball queries and 2x2 eigendecompositions at 300 sampled
# centres per face. No quadrics, no meshing, no GPU.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

D=/data/gpfs/projects/punim2657/TORA/dataset
O=/data/gpfs/projects/punim2657/TORA/eval_runs/sherd_scale
mkdir -p "$O"

python scripts/measure_strip_feasibility.py \
    --erosion "$D/erosion_ceramics.hdf5" \
    --raw     "$D/fractura_real.hdf5" \
    --juglet  "$D/juglet_gt.hdf5" \
    --out     "$O/strip_feasibility.json"

echo "=== done $(date) ==="
