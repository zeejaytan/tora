#!/bin/bash
#SBATCH --job-name=tora-c2b-seeds
#SBATCH --partition=gpu-a100-short
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_c2b_seeds_%j.log

set -euo pipefail

# C2b robustness check. The Juglet is a SINGLE object, so one probe run rests on
# ~5000 sampled points of which only ~3% are contact points — roughly 50 in the
# held-out set. At that size the score is noisy, and in job 28200043 the
# encoder/Juglet arm's scrambled-label control came out at 0.39 instead of ~0.5
# (about 1.5 standard errors off), which the script flagged.
#
# This re-runs BOTH channels on the Juglet across 3 different point samplings.
# If the teacher-over-encoder gap holds across all three, it is real; if the
# scores swing wildly, the single-object limitation is doing the talking and the
# gap must not be quoted as established.

echo "=== C2b seed-robustness check started at $(date) on $(hostname) ==="

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
ENV_PREFIX=$TORA_ROOT/envs/tora
DATA_ROOT=$TORA_ROOT/dataset
CKPT=$TORA_ROOT/checkpoints/bbad_everyday_cka.ckpt

module purge
module load Anaconda3/2024.02-1
module load CUDA/12.4.1
module load cuDNN/9.6.0.74-CUDA-12.4.1
eval "$(conda shell.bash hook)"
conda activate "$ENV_PREFIX"
export TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0"
export HF_HOME=$TORA_ROOT/.hf-cache
cd "$TORA_ROOT/repo"

for SEED in 0 1 2; do
    for SRC in encoder teacher; do
        echo ""
        echo "########## seed=$SEED source=$SRC material=juglet_norm ##########"
        python mating_probe.py \
            ckpt_path="$CKPT" \
            data_root="$DATA_ROOT" \
            data=zeroshot/juglet_norm \
            seed=$SEED \
            +probe_features=$SRC \
            +probe_dim=64 || echo "arm seed=$SEED/$SRC failed (continuing)"
    done
done

echo ""
echo "=== Finished at $(date) ==="
