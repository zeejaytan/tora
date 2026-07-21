#!/bin/bash
#SBATCH --job-name=tora-finetune-real
#SBATCH --partition=gpu-a100-short
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=03:30:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_finetune_real_%j.log

set -euo pipefail

echo "=== TORA real-fracture fine-tune (data-vs-model-limitation test) started at $(date) on $(hostname) ==="
nvidia-smi | head -15 || true

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
REPO_DIR=$TORA_ROOT/repo
ENV_PREFIX=$TORA_ROOT/envs/tora
DATA_ROOT=$TORA_ROOT/dataset
CKPT=$TORA_ROOT/checkpoints/bbad_everyday_cka.ckpt
LOG_DIR=$TORA_ROOT/output/real_finetune_${SLURM_JOB_ID}

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
echo "### Fine-tuning on 21 real Fractura objects (bones/ceramics/egg), warm-started from bbad_everyday_cka.ckpt ###"
echo "### Held out (never trained on): bones/vert9,limb3,coxae ceramics/galli_pot,plate,blue_pot -- matches pairs_real.hdf5 ###"
python train.py \
    data_root="$DATA_ROOT" \
    data=main/real_finetune \
    experiment_name=real_finetune_${SLURM_JOB_ID} \
    log_dir="$LOG_DIR" \
    model.encoder_ckpt="$CKPT" \
    model.flow_model_ckpt="$CKPT" \
    model.optimizer.lr=2e-5 \
    trainer.max_epochs=30 \
    trainer.check_val_every_n_epoch=10 \
    trainer.devices=1 \
    trainer.strategy=auto \
    trainer.num_nodes=1

echo ""
echo "=== Fine-tune finished at $(date) ==="
echo "Checkpoints: $LOG_DIR/"
ls -la "$LOG_DIR" || true
