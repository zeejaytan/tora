#!/bin/bash
#SBATCH --job-name=tora-eval-juglet
#SBATCH --partition=gpu-a100-short
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_juglet_%j.log

set -euo pipefail

echo "=== TORA Juglet zero-shot eval started at $(date) on $(hostname) ==="
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
mkdir -p "$LOG_ROOT" "$HF_HOME"

cd "$REPO_DIR"

VIZ_ARGS=(
    "+visualizer._target_=tora.visualizer.FlowVisualizationCallback"
    "+visualizer.renderer=mitsuba"
    "+visualizer.image_size=512"
    "+visualizer.max_samples_per_batch=1"
    "+visualizer.center_points=true"
    "+visualizer.save_trajectory=false"
)

OUT_DIR=$LOG_ROOT/juglet_${SLURM_JOB_ID}
echo ""
echo "=== Eval: juglet (1 sample, 9 parts) ==="
python sample.py \
    ckpt_path="$CKPT" \
    data_root="$DATA_ROOT" \
    data=zeroshot/juglet \
    data.batch_size=1 \
    data.num_workers=4 \
    log_dir="$OUT_DIR" \
    "${VIZ_ARGS[@]}"

echo ""
echo "=== Finished at $(date) ==="
echo "Results: $OUT_DIR/results/"
echo "Viz:     $OUT_DIR/visualizations/"
