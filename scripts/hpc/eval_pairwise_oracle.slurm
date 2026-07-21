#!/bin/bash
#SBATCH --job-name=tora-pairwise-oracle
#SBATCH --partition=gpu-a100-short
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_pairwise_oracle_%j.log

set -euo pipefail

echo "=== TORA pairwise mating oracle (real vs synthetic bone) started at $(date) on $(hostname) ==="
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
mkdir -p "$LOG_ROOT"

cd "$REPO_DIR"

echo ""
echo "### Pairwise oracle: SYNTHETIC bone fracture pairs ###"
python sample.py \
    ckpt_path="$CKPT" \
    data_root="$DATA_ROOT" \
    data=zeroshot/pairs_synth \
    data.batch_size=8 \
    data.num_workers=4 \
    log_dir="$LOG_ROOT/pairs_synth_${SLURM_JOB_ID}" \
    model.n_generations=3

echo ""
echo "### Pairwise oracle: REAL bone/ceramic fracture pairs ###"
python sample.py \
    ckpt_path="$CKPT" \
    data_root="$DATA_ROOT" \
    data=zeroshot/pairs_real \
    data.batch_size=8 \
    data.num_workers=4 \
    log_dir="$LOG_ROOT/pairs_real_${SLURM_JOB_ID}" \
    model.n_generations=3

echo ""
echo "=== Pairwise oracle finished at $(date) ==="
echo "Results: $LOG_ROOT/pairs_synth_${SLURM_JOB_ID}/results/ , $LOG_ROOT/pairs_real_${SLURM_JOB_ID}/results/"
