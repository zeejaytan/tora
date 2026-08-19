#!/bin/bash
#SBATCH --job-name=tora-bbadbal
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_bbadbal_%j.log

set -euo pipefail

# GATE B, and it turned into a different question than the one asked.
#
# The plan was to choose a fracturing method for Geometric Breaks' 1,125
# vessels. Checking what we already hold first turned up 375 vessel objects in
# breaking_bad_vol.hdf5, already fractured with fracture modes by its authors.
#
# But piece COUNT flatters them: 89% of instances are effectively one remnant
# with chips knocked off, mean largest share 88.4%, mean effective piece count
# 1.43. A break that is 97% one piece is not a reassembly problem.
#
# The number that decides whether any of it is usable is how many distinct
# SHAPES have at least one well-balanced break -- the gap being filled is
# variety of form, and a thousand good breaks of four vases would not fill it.
# This scans every object and every instance to find out.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

python scripts/measure_bbad_balance.py \
    --src /data/gpfs/projects/punim2657/TORA/dataset/breaking_bad_vol.hdf5

echo ""
echo "=== Finished at $(date) ==="
