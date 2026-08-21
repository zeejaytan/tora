#!/bin/bash
#SBATCH --job-name=tora-reccurve
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=160G
#SBATCH --time=03:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_reccurve_%j.log

set -euo pipefail

# The conservator, 2026-08-20: "if erosion/recession is uniform, I don't see it
# will affect the curve, but run a quick test, if pass, build the training set."
#
# Right, and this is the check before the training set is built on it. Gate B
# showed blunting is inert on Breaking Bad's coarse vessel meshes while a small
# recession opens their joins 6-10%, so recession is the only wear tool that
# does anything on that corpus. What it costs the CURVE there was never
# measured -- on fine meshes the same dose cost 2.5-5.3%, from a per-vertex cap
# that read mesh sampling density rather than sherd thickness. That cap is now
# one number per piece.
#
# The vertex set and the normal frame are both fixed on the fresh geometry, so
# the measurement window cannot shrink with the dose and the ruler cannot
# co-rotate with what it measures -- the two faults found in the earlier
# spectrum test. The retreat itself is rendered per vertex, unbinned.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

python scripts/test_recession_curve.py \
    --bbad /data/gpfs/projects/punim2657/TORA/dataset/breaking_bad_vol.hdf5 \
    --fine /data/gpfs/projects/punim2657/TORA/dataset/real_heldout_norm.hdf5 \
    --render /data/gpfs/projects/punim2657/TORA/artifacts/recession_curve.png

echo ""
echo "=== Finished at $(date) ==="
