#!/bin/bash
#SBATCH --job-name=tora-brkface
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=180G
#SBATCH --time=01:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_brkface_%j.log

set -euo pipefail

# Which sherd points are ACTUALLY break face, labelled from the intact pot.
#
# This is the gate for job 30356470, and it replaces three failed proxies:
# the off-face gate (a pot wall is also locally one surface, so it passes),
# the 2D face render (projects through a hollow object), and both ribbon-width
# tests (a break runs around the sherd as a closed loop, and the selection is
# already banded to the neighbour's proximity -- 2.7-6.7 mm, the wall thickness
# to within 2x -- so band width cannot separate them). Job 30357114 refused all
# eight pots on a test that a perfect selection would also have failed; job
# 30357469's own control fired on five of eight.
#
# `fractura_real.hdf5` holds `full_mesh` per pot: the vessel before it broke,
# 1.0-6.2 M vertices. Original-surface points lie on it, break-face points lie
# inside the wall. No proxy.
#
# Read the 'whole sherd' column first. On a thin-walled pot the break face must
# be a minority of each sherd's surface; near 100% means the intact mesh and the
# rescaled erosion pieces are not in the same frame and nothing else counts.
#
# Memory is the constraint, not time: a KD-tree over up to 1.5 M intact vertices
# plus every vertex of every sherd. Minutes per pot.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

D=/data/gpfs/projects/punim2657/TORA/dataset

python scripts/label_break_faces_from_full_mesh.py \
    --erosion "$D/erosion_ceramics.hdf5" \
    --raw     "$D/fractura_real.hdf5" \
    --rungs e000

echo "=== done $(date) ==="
