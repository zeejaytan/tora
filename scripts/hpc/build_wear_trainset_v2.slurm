#!/bin/bash
#SBATCH --job-name=tora-wearset2
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --time=06:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_wearset2_%j.log

set -euo pipefail

# Build the v2 worn training set on a CPU node.
#
# Split out from the fine-tune job on purpose: this is pure mesh work (27
# objects x 7 variants, ~820k vertices each) and would otherwise sit on an A100
# doing nothing GPU-shaped for an hour or more. The wear code is KD-tree bound
# and uses all cores, so a fat CPU node is the right place for it.
#
# Chain the fine-tune behind it with:
#   sbatch --dependency=afterok:<this job> scripts/hpc/finetune_wear_augmented_v2.slurm

echo "=== build wear_trainset_v2 started at $(date) on $(hostname) ==="

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
ENV_PREFIX=$TORA_ROOT/envs/tora
DATA_ROOT=$TORA_ROOT/dataset

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate "$ENV_PREFIX"
cd "$TORA_ROOT/repo"

python scripts/build_wear_trainset_v2.py \
    --src "$DATA_ROOT/real_finetune.hdf5" \
    --src-dataset real_finetune \
    --dataset-name wear_trainset_v2 \
    --out-hdf5 "$DATA_ROOT/wear_trainset_v2.hdf5"

echo ""
echo "=== Finished at $(date) ==="
echo "The last lines above report achieved SMOOTHNESS coverage. Read them before"
echo "training: if nothing in the set reaches the Juglet's 0.171, the model is"
echo "being trained on material easier than the object we are trying to solve."
