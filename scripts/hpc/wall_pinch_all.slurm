#!/bin/bash
#SBATCH --job-name=tora-pinchall
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --time=04:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_pinchall_%j.log

set -euo pipefail

# How much of wear_trainset_v2 is actually sound?
#
# The roughness survey cleared objects that are in fact damaged -- limb6 passed
# it (-13.9% roughness, filed "ok") while losing 20% of its wall thickness at
# the break. So roughness is not a safe screen, and wall thinning is.
#
# This runs the wall test over every object in the training source, giving a
# real count of how many of the 189 variants can be kept.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

OBJ=$(python - <<'PY'
import h5py
h = h5py.File('/data/gpfs/projects/punim2657/TORA/dataset/real_finetune.hdf5', 'r')
print(','.join(sorted(h['real_finetune'].keys())))
PY
)
echo "objects: $OBJ"

python scripts/probe_wall_pinch.py \
    --objects "$OBJ" \
    --out-dir /data/gpfs/projects/punim2657/TORA/wall_pinch_all
