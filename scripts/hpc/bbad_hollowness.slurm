#!/bin/bash
#SBATCH --job-name=tora-hollow
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=160G
#SBATCH --time=03:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_hollow_%j.log

set -euo pipefail

# The conservator's warning: some Breaking Bad meshes are solid, not thin-walled.
#
# That could disqualify the corpus for pottery. A sherd's fracture is a ribbon
# through a wall a few millimetres thick; a solid object's fracture is a broad
# face through the body. Different geometry, different wear, and a model trained
# on solid "vases" learns the wrong thing.
#
# Plausible rather than paranoid: fracture modes tetrahedralises the interior
# through a cage, so an input that is not watertight and hollow comes out solid
# whatever it looked like as a surface.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

python scripts/measure_bbad_hollowness.py \
    --src /data/gpfs/projects/punim2657/TORA/dataset/breaking_bad_vol.hdf5 \
    --out /data/gpfs/projects/punim2657/TORA/bbad_hollowness.png

echo ""
echo "=== Finished at $(date) ==="
echo "Look at the slices. A filled cross-section is a solid, whatever its class"
echo "label says, and it is not pottery."
