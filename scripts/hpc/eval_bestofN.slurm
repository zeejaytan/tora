#!/bin/bash
#SBATCH --job-name=tora-bestofN
#SBATCH --partition=gpu-a100
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=06:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_bestofN_%j.log

set -euo pipefail

echo "=== TORA best-of-N sweep (N=10) started at $(date) on $(hostname) ==="
nvidia-smi | head -15 || true

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
REPO_DIR=$TORA_ROOT/repo
ENV_PREFIX=$TORA_ROOT/envs/tora
DATA_ROOT=$TORA_ROOT/dataset
CKPT=$TORA_ROOT/checkpoints/bbad_everyday_cka.ckpt
LOG_ROOT=$TORA_ROOT/eval_runs

module purge
module load Anaconda3/2024.02-1
module load CUDA/12.4.1
module load cuDNN/9.6.0.74-CUDA-12.4.1
eval "$(conda shell.bash hook)"
conda activate "$ENV_PREFIX"
export TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0"
export HF_HOME=$TORA_ROOT/.hf-cache
export WANDB_MODE=offline

cd "$REPO_DIR"

# Skip viz: we already have PNGs from job 24194551. Here we only need per-sample
# per-generation metric JSONs to derive N=1,3,5,10 curves post-hoc via filtering.
OUT_DIR=$LOG_ROOT/bestofN_${SLURM_JOB_ID}

echo ""
echo "=== Running sample.py with model.n_generations=10 on thin-walled (3933 samples) ==="
python sample.py \
    ckpt_path="$CKPT" \
    data_root="$DATA_ROOT" \
    data=main/bbad_thinwalled \
    data.batch_size=32 \
    data.num_workers=8 \
    model.n_generations=10 \
    log_dir="$OUT_DIR"

echo ""
echo "=== Run finished at $(date) ==="
echo "Results: $OUT_DIR/results/"
echo "Derive N=1/3/5/10 curves post-hoc by filtering generation_idx in JSONs."
