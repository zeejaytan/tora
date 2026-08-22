#!/bin/bash
#SBATCH --job-name=tora-breakreal
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=100G
#SBATCH --time=01:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_breakreal_%j.log

set -euo pipefail

# Found by rendering the smoke build, not by reasoning: colour ran in horizontal
# bands around the bottles. Bands are rings, and a pot does not break into rings.
#
# The worry is about my own filter. Instances are chosen by the inverse Simpson
# index, which rewards a break whose pieces are all about the same size --
# and slicing a vessel into equal rings scores near-perfectly on that, better
# than a real break, which sheds a few small sherds. So the filter added to
# reject "one remnant plus chips" may be selecting stratified cuts instead, and
# silently, because balance is exactly what it was told to maximise.
#
# Measured as angular reach around the vessel's axis, which no viewpoint can
# distort, and compared between the breaks the filter picks and the ones it
# passes over. If picking by balance is what pulls in rings, the two differ.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

mkdir -p /data/gpfs/projects/punim2657/TORA/artifacts

python scripts/check_break_realism.py \
    --src /data/gpfs/projects/punim2657/TORA/dataset/breaking_bad_vol.hdf5 \
    --out /data/gpfs/projects/punim2657/TORA/artifacts/break_realism.png

echo ""
echo "=== Finished at $(date) ==="
