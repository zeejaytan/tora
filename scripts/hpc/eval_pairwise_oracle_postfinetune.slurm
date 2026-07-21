#!/bin/bash
#SBATCH --job-name=tora-pairwise-postft
#SBATCH --partition=gpu-a100-short
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=00:45:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_pairwise_postft_%j.log

set -euo pipefail

echo "=== TORA pairwise oracle POST-FINETUNE (real fracture) started at $(date) on $(hostname) ==="

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
REPO_DIR=$TORA_ROOT/repo
ENV_PREFIX=$TORA_ROOT/envs/tora
DATA_ROOT=$TORA_ROOT/dataset
CKPT=$TORA_ROOT/output/real_finetune_27792230/epoch-19.ckpt
LOG_ROOT=$TORA_ROOT/eval_runs

module purge
module load Anaconda3/2024.02-1
module load CUDA/12.4.1
module load cuDNN/9.6.0.74-CUDA-12.4.1
eval "$(conda shell.bash hook)"
conda activate "$ENV_PREFIX"
export TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0"
export HF_HOME=$TORA_ROOT/.hf-cache

cd "$REPO_DIR"

echo ""
echo "### Pairwise oracle (POST-finetune ckpt): REAL held-out bone/ceramic pairs ###"
python sample.py \
    ckpt_path="$CKPT" \
    data_root="$DATA_ROOT" \
    data=zeroshot/pairs_real \
    data.batch_size=8 \
    data.num_workers=4 \
    log_dir="$LOG_ROOT/pairs_real_postft_${SLURM_JOB_ID}" \
    model.n_generations=3

echo ""
echo "=== analysis ==="
python scripts/analyze_pairwise_oracle.py \
  --results-dir "$LOG_ROOT/pairs_real_postft_${SLURM_JOB_ID}/results" \
  --adjacency "$TORA_ROOT/logs_pairs_real_adjacency.json" \
  --label "real, POST-finetune"

echo ""
echo "=== Finished at $(date) ==="
