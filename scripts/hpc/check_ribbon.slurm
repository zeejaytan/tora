#!/bin/bash
#SBATCH --job-name=tora-ribbon
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=00:30:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_ribbon_%j.log

set -euo pipefail

# Does the mating-normal selection land on the BREAK FACE, or on the vessel wall?
#
# This is the gate for job 30356470's numbers, not a postscript to them. Version 1
# selected the break face by proximity alone and took the pot wall with it, which
# voided every number it printed. Version 2 adds a normal-direction test, and I
# have so far checked that test with a synthetic slab pair and a 2D scatter of
# real sherds. Neither is sufficient:
#
#   - the off-face gate asks whether a patch is locally ONE surface. A pot's
#     outer wall is also locally one surface. The wall passes it cleanly.
#   - the 2D scatter projects through the object, so a ribbon along a break edge
#     and a broad patch on the far wall are drawn on top of each other.
#
# A break face is a ribbon as wide as the wall -- about 4.5 mm on these pots --
# and as long as the break. So measure the narrow extent of each selected face
# against that sherd's own wall thickness (2 x volume / area). One number per
# sherd, invariant to viewpoint. If it comes back at several wall thicknesses,
# version 2 is selecting wall like version 1 did and 30356470 is void too.
#
# Cheap: no probing, no quadrics. Minutes, not an hour.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

D=/data/gpfs/projects/punim2657/TORA/dataset

# every pot, fresh rung only -- the selection geometry does not depend on wear,
# and e000 is the rung the ceiling verdict rests on.
python scripts/check_mating_face_is_a_ribbon.py \
    --erosion "$D/erosion_ceramics.hdf5" \
    --raw     "$D/fractura_real.hdf5" \
    --rungs e000

echo "=== done $(date) ==="
