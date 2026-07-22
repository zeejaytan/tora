#!/bin/bash
#SBATCH --job-name=tora-eval-robust
#SBATCH --partition=gpu-a100-short
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_eval_robust_%j.log

set -euo pipefail

echo "=== Evaluating robust fine-tuned checkpoints started at $(date) on $(hostname) ==="

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
REPO_DIR=$TORA_ROOT/repo
ENV_PREFIX=$TORA_ROOT/envs/tora
DATA_ROOT=$TORA_ROOT/dataset
LOG_ROOT=$TORA_ROOT/eval_runs
FT_DIR=$TORA_ROOT/output/real_finetune_robust_27793083

module purge
module load Anaconda3/2024.02-1
module load CUDA/12.4.1
module load cuDNN/9.6.0.74-CUDA-12.4.1
eval "$(conda shell.bash hook)"
conda activate "$ENV_PREFIX"
export TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0"
export HF_HOME=$TORA_ROOT/.hf-cache

cd "$REPO_DIR"

for TAG in "best:epoch-59.ckpt" "last:last.ckpt"; do
    NAME="${TAG%%:*}"
    FILE="${TAG##*:}"
    CKPT="$FT_DIR/$FILE"

    echo ""
    echo "### [$NAME] Pairwise oracle: REAL held-out bone/ceramic pairs ###"
    python sample.py \
        ckpt_path="$CKPT" \
        data_root="$DATA_ROOT" \
        data=zeroshot/pairs_real \
        data.batch_size=8 \
        data.num_workers=4 \
        log_dir="$LOG_ROOT/pairs_real_robust_${NAME}_${SLURM_JOB_ID}" \
        model.n_generations=3

    echo ""
    echo "### [$NAME] Pairwise oracle analysis ###"
    python scripts/analyze_pairwise_oracle.py \
      --results-dir "$LOG_ROOT/pairs_real_robust_${NAME}_${SLURM_JOB_ID}/results" \
      --adjacency "$TORA_ROOT/logs_pairs_real_adjacency.json" \
      --label "real, robust fine-tune [$NAME]"

    echo ""
    echo "### [$NAME] Juglet deploy export (Procrustes proposed assembly) ###"
    python sample.py \
        ckpt_path="$CKPT" \
        data_root="$DATA_ROOT" \
        data=zeroshot/juglet_deploy_local02 \
        data.batch_size=1 \
        data.num_workers=4 \
        log_dir="$LOG_ROOT/juglet_robust_${NAME}_${SLURM_JOB_ID}" \
        model.n_generations=3 \
        "+visualizer._target_=tora.visualizer.FlowVisualizationCallback" \
        "+visualizer.renderer=mitsuba" \
        "+visualizer.image_size=512" \
        "+visualizer.max_samples_per_batch=1" \
        "+visualizer.center_points=true" \
        "+visualizer.save_trajectory=false" \
        "+visualizer.save_procrustes_assembly=true"
done

echo ""
echo "=== Finished at $(date) ==="
echo "Juglet viz: $LOG_ROOT/juglet_robust_{best,last}_${SLURM_JOB_ID}/visualizations/"
