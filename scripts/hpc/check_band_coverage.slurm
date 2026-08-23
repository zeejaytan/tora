#!/bin/bash
#SBATCH --job-name=tora-bandcov
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=100G
#SBATCH --time=02:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_bandcov_%j.log

set -euo pipefail

# Re-asks a question that was already answered wrong. check_break_realism.py
# used one 300-degree cutoff, reported 19% rings either way, and cleared the
# corpus. The training-set render then showed half the vessels breaking into
# stacked horizontal bands: a fragment covering 250 degrees is a band to the eye
# and was not a ring to that test.
#
# So this one sweeps the cutoff instead of picking one, reports arc/rise (a
# fragment's shape, which no threshold decides), tests whether bands track
# vessel slenderness, and prints the cost of dropping each class beside the
# benefit -- shape variety is the whole reason this set exists.
#
# Measured on the fresh breaks only; the worn copies are the same geometry.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

mkdir -p /data/gpfs/projects/punim2657/TORA/artifacts

python scripts/check_band_coverage.py \
    --src /data/gpfs/projects/punim2657/TORA/dataset/bbad_vessels.hdf5 \
    --dataset bbad_vessels \
    --out /data/gpfs/projects/punim2657/TORA/artifacts/band_coverage.png

echo ""
echo "=== Finished at $(date) ==="
