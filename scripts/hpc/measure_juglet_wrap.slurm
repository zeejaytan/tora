#!/bin/bash
#SBATCH --job-name=tora-jugwrap
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=24G
#SBATCH --time=00:20:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_jugwrap_%j.log

set -euo pipefail

# Checks the conservator's correction against the object itself: Piece01 of the
# Juglet is said to be a complete rim, one fragment wrapping the full 360
# degrees. If so, a fragment that closes into a hoop is a normal way for a
# vessel to come apart, not a defect in bbad_vessels, and the filtering work was
# aimed at the wrong target.
#
# Identical instrument to check_band_coverage.py and show_ring_problem.py, so
# the two sets go through the same ruler and the comparison means something.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

mkdir -p /data/gpfs/projects/punim2657/TORA/artifacts

python scripts/measure_juglet_wrap.py \
    --dir /data/gpfs/projects/punim2657/Dataset/Juglet \
    --out /data/gpfs/projects/punim2657/TORA/artifacts/juglet_wrap.png

echo ""
echo "=== Finished at $(date) ==="
