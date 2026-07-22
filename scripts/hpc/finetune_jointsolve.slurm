#!/bin/bash
#SBATCH --job-name=tora-finetune-jointsolve
#SBATCH --partition=gpu-a100
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=06:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_finetune_jointsolve_%j.log

set -euo pipefail

echo "=== TORA joint-solve fine-tune (multi-piece-only curriculum) started at $(date) on $(hostname) ==="
nvidia-smi | head -15 || true

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
REPO_DIR=$TORA_ROOT/repo
ENV_PREFIX=$TORA_ROOT/envs/tora
DATA_ROOT=$TORA_ROOT/dataset
# Warm-start from the robust replay checkpoint (keeps the recovered mating
# perception) rather than from the shipped synthetic-only base.
CKPT=$TORA_ROOT/output/real_finetune_robust_27793083/epoch-59.ckpt
LOG_DIR=$TORA_ROOT/output/real_finetune_jointsolve_${SLURM_JOB_ID}

module purge
module load Anaconda3/2024.02-1
module load CUDA/12.4.1
module load cuDNN/9.6.0.74-CUDA-12.4.1
eval "$(conda shell.bash hook)"
conda activate "$ENV_PREFIX"
export TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0"
export HF_HOME=$TORA_ROOT/.hf-cache
export WANDB_MODE=offline
mkdir -p "$LOG_DIR"

cd "$REPO_DIR"

echo ""
echo "### Joint-solve fine-tune: real (>=3 parts) + synthetic pig/rib (>=3 parts) replay ###"
echo "### Warm-started from robust epoch-59. Held out (never trained): bones/vert9,limb3,coxae ceramics/galli_pot,plate,blue_pot ###"
python train.py \
    data_root="$DATA_ROOT" \
    data=main/real_finetune_jointsolve \
    experiment_name=real_finetune_jointsolve_${SLURM_JOB_ID} \
    log_dir="$LOG_DIR" \
    model.encoder_ckpt="$CKPT" \
    model.flow_model_ckpt="$CKPT" \
    model.optimizer.lr=2e-5 \
    trainer.max_epochs=120 \
    trainer.check_val_every_n_epoch=10 \
    trainer.devices=1 \
    trainer.strategy=auto \
    trainer.num_nodes=1

echo ""
echo "=== Joint-solve fine-tune finished at $(date) ==="
echo "Checkpoints: $LOG_DIR/"
ls -la "$LOG_DIR" || true
