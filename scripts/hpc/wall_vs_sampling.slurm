#!/bin/bash
#SBATCH --job-name=tora-wallsamp
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --time=02:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_wallsamp_%j.log

set -euo pipefail

# How many of TORA's sampling cells fit through the wall of these vessels.
#
# This is the mechanism behind the fracture-channel result. TORA's own overlap
# rule flags ~43% of its 5000 points as contact, but only ~23% of those sit
# across a genuine fracture and ~18% are wall simply continuing across the
# join. The median mating angle is 90 degrees on every row, which is the
# arithmetic signature of that mixture rather than an absence of signal, and it
# is bimodal by vessel: bottles 152-177 degrees, bowls and vases 83-96. That
# split is what a wall-thickness effect looks like.
#
# So: wall thickness against sqrt(2 * area / 5000). Below 1 cell, one sampled
# point straddles the whole wall and the break face never gets a row of points
# to itself.
#
# THIS RUNS AS A BATCH JOB BECAUSE IT IS NOT A LOGIN-NODE CHECK. An earlier
# version of it was run interactively and sat at 374% CPU for 33 minutes on the
# login node before being killed. The measurement itself is cheap per fragment;
# there are simply a lot of fragments, and the erosion-sweep scans carry ~1M
# faces each.
#
# The estimator is checked against shells of known wall thickness FIRST, and the
# job stops if that fails. Two earlier versions of this script returned
# confident, wrong numbers -- one measuring local creases with a 64-neighbour
# probe that could not reach across the wall, one stopping at face centroids
# that sat away from where the ray actually crossed. Neither was caught by
# reading the code; both were caught by a second route to the same number
# disagreeing. A known answer is cheaper than either.

cd /data/gpfs/projects/punim2657/TORA

module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate ./envs/tora

export PYTHONPATH=repo:repo/scripts

echo "=== instrument check: shells of known wall thickness ==="
python repo/scripts/measure_wall_vs_sampling.py --selftest

echo ""
echo "=== training vessels (simulated breaks) ==="
python repo/scripts/measure_wall_vs_sampling.py --only bbad_vessels --limit 8

echo ""
echo "=== real scans (erosion sweep) ==="
python repo/scripts/measure_wall_vs_sampling.py --only erosion_sweep --limit 6

echo ""
echo "done"
