#!/bin/bash
#SBATCH --job-name=tora-ringpic
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=60G
#SBATCH --time=00:30:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_ringpic_%j.log

set -euo pipefail

# Draws the fragments on their own, looking down the vessel's axis. Every
# earlier view showed the vessel assembled, which is the one arrangement where a
# ring and a sherd look the same -- both are a patch of colour on a wall. Three
# measurements and two renders failed to settle this. From above, a sherd is an
# arc and a ring is a closed hoop, which is a difference no threshold can soften.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

mkdir -p /data/gpfs/projects/punim2657/TORA/artifacts

python scripts/show_ring_problem.py \
    --src /data/gpfs/projects/punim2657/TORA/dataset/bbad_vessels.hdf5 \
    --dataset bbad_vessels \
    --out /data/gpfs/projects/punim2657/TORA/artifacts/ring_problem.png

echo ""
echo "=== Finished at $(date) ==="
