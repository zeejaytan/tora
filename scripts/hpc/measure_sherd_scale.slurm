#!/bin/bash
#SBATCH --job-name=tora-sherdscale
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=00:30:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_sherdscale_%j.log

set -euo pipefail

# How deep, in millimetres, is the wear at each rung of the erosion ladder?
#
# The wear operator scales its Gaussian to the SHERD, not the vessel:
# sigma = 0.5 * strength * 0.05 * max(mesh.extents). So e100 on a 20 mm sherd
# removes a quarter of what e100 on an 80 mm sherd removes, and the ladder is
# not one physical depth. max(mesh.extents) has never been recorded in this
# repo -- the only absolute figures anywhere are blue_pot 0.40-0.67 mm and
# plate 1.0-1.67 mm, in a docstring. Every other absolute wear number rests on
# an assumed "~40 mm sherd".
#
# This decides one thing the design is currently blocked on: which rungs move
# the surface further than the Juglet's own point spacing of 0.29-0.48 mm. A
# rung below that cannot be compared against the Juglet no matter how good the
# instrument is -- the reference cannot see a change that small. If e025 comes
# back below 0.29 mm on every pot, it is reported as unreadable rather than
# quoted.
#
# It also prints per-sherd wall thickness (2V/A) for the eight pots and for the
# Juglet. Neither exists in the repo, and patch radii are ratios to wall
# thickness, never millimetres carried between objects.
#
# Cheap: bounding boxes, areas and volumes at e000 only. No probing, no
# quadrics, no KD-trees. Minutes.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

D=/data/gpfs/projects/punim2657/TORA/dataset
O=/data/gpfs/projects/punim2657/TORA/eval_runs/sherd_scale
mkdir -p "$O"

python scripts/measure_sherd_scale.py \
    --erosion "$D/erosion_ceramics.hdf5" \
    --raw     "$D/fractura_real.hdf5" \
    --rung    e000 \
    --juglet  "$D/juglet_gt.hdf5" \
    --juglet-group juglet_gt \
    --out     "$O/sherd_scale.json"

echo "=== done $(date) ==="
