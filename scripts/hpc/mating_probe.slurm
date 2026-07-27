#!/bin/bash
#SBATCH --job-name=tora-mating-probe
#SBATCH --partition=gpu-a100-short
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_mating_probe_%j.log

set -euo pipefail

# C2 — paper-faithful mating linear probe on the ON-PATH conditioning features c.
# Replaces the dead overlap_head readout. Arms run in validation order:
#   1. pairs_synth   -- labeled synthetic control, MUST reach AUC >= 0.75
#   2. pairs_real_norm / real_heldout_norm -- fresh real fracture
#   3. juglet_norm   -- real, WORN (object under test)
# A collapse on (3) relative to (2) is TORA's analogue of GARF Exp-10 blindness.

echo "=== TORA C2 mating probe started at $(date) on $(hostname) ==="
nvidia-smi | head -15 || true

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

for DS in pairs_synth real_heldout_norm juglet_norm; do
    echo ""
    echo "########## arm: $DS ##########"
    python mating_probe.py \
        ckpt_path="$CKPT" \
        data_root="$DATA_ROOT" \
        data=zeroshot/$DS || echo "arm $DS failed (continuing)"
done

echo ""
echo "=== Finished at $(date) ==="
echo "Read the synthetic arm FIRST: if it misses AUC>=0.75 the probe is not a"
echo "usable instrument and the other arms must not be interpreted."
