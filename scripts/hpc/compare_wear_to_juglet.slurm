#!/bin/bash
#SBATCH --job-name=tora-vsjuglet
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=160G
#SBATCH --time=03:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_vsjuglet_%j.log

set -euo pipefail

# The wear model exists to generate training data. The question that decides
# whether it is fit for that is not whether it obeys a physical rule -- it does,
# that is established -- but whether a sherd we wear resembles a sherd the
# ground wore. The Juglet is the only real worn pot here with a valid assembly.
#
# Run against three fresh objects, not one. A single pairing cannot tell a
# difference in wear from a difference between two pots.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

D=/data/gpfs/projects/punim2657/TORA/dataset

for OBJ in blue_pot plate galli_pot; do
    echo ""
    echo "############### real Juglet vs simulated wear on $OBJ ###############"
    python scripts/compare_wear_to_juglet.py \
        --gt "$D/juglet_gt.hdf5:juglet_gt" \
        --sim "$D/real_heldout_norm.hdf5:real_heldout_norm:$OBJ" || true
done

echo ""
echo "=== done $(date) ==="
