#!/bin/bash
#SBATCH --job-name=tora-dosesweep
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --time=03:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_dosesweep_%j.log

set -euo pipefail

# How hard can we open these joins before the break-face shape stops being the
# object's own?
#
# WHY THIS RUNS BEFORE THE REBUILD, AND WHY THE TARGET CHANGED.
#
# The rebuild is meant to make the training joins start where real joins start.
# The figure quoted for that was a ~30x dose increase, and it was read off
# `joint_gap` in measure_gap_as_network_sees.py -- a 10th percentile of
# nearest-neighbour distance over ALL 5000 sampled points, the great majority
# of which are nowhere near a join. On a fragment where ~11% of points sit on
# the break, that statistic is a mixture and it saturates at the sampling
# floor: fresh reads 0.277 with 44% of its vertices EXACTLY COINCIDENT, which
# is a floor, not a separation. Driving it to the real 0.62 by recession alone
# needs ~3.4% of object retreat -- seventeen times the dose already excluded
# for costing one object 6.6% of its curve. That target was an artefact of the
# ruler, not a property of the material.
#
# The quantity that does measure the thing is the CONTACT BAND
# (measure_join_uniformity.py), in % of object:
#
#                          p10      p50      p90
#   real erosion e000     0.167    0.640    3.492
#   train fresh           0.000    0.000    0.391
#   train worn_moderate   0.015    0.155    0.614     (recession 0.10%)
#
# So p50 needs about 4x the current dose, not 30x. That is still twice the
# 0.20% that was excluded, so the cost has to be measured rather than assumed
# -- which is what this script was built to do, and it is reused here with a
# wider dose ladder rather than rewritten.
#
# Note the p90 column before reading any of this as a plan. The real join is
# heterogeneous; a uniform retreat moves all three percentiles together and
# cannot produce that tail. Whether it can is what the sweep will show.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

python scripts/test_recession_curve.py \
    --bbad /data/gpfs/projects/punim2657/TORA/dataset/breaking_bad_vol.hdf5 \
    --fine /data/gpfs/projects/punim2657/TORA/dataset/real_heldout_norm.hdf5 \
    --doses 0.0005,0.0010,0.0020,0.0030,0.0040,0.0060 \
    --render /data/gpfs/projects/punim2657/TORA/artifacts/recession_dose_sweep.png

echo ""
echo "=== Finished at $(date) ==="
