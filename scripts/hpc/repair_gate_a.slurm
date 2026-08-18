#!/bin/bash
#SBATCH --job-name=tora-gateA
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=160G
#SBATCH --time=04:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_gateA_%j.log

set -euo pipefail

# GATE A of the wear v3 plan: what does REAL eroded fracture look like, and at
# what scale?
#
# The wear model has never been checked against real worn material. The Juglet
# cannot do it -- it records nothing finer than about 0.5% of object size while
# our blunting acts at 0.3-0.5%, so there is no overlap to compare in. RePAIR's
# fresco fragments are scanned at 0.05-0.2 mm and there are thousands.
#
# Measured in MILLIMETRES, because erosion is a physical process and every
# earlier comparison went wrong on which size something was a percentage of.
#
# Only the broken perimeter is measured. These are fresco plaques and the
# painted surface does much of the matching work in the original benchmark; we
# care only about how the worn fracture joins. The classification of which
# surface is fracture is RENDERED before any spectrum is trusted.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

python scripts/repair_fracture_spectrum.py \
    --dir /data/gpfs/projects/punim2657/TORA/repair/OPEN_DISCOVERY/pieces \
    --out-dir /data/gpfs/projects/punim2657/TORA/repair/analysis \
    --max-frags 20

echo ""
echo "=== Finished at $(date) ==="
echo "Look at the classification figure BEFORE reading the spectrum. If the"
echo "orange covers a flat face, the numbers describe the painted front."
