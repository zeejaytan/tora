#!/bin/bash
#SBATCH --job-name=tora-eval-artifact
#SBATCH --partition=gpu-a100
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=06:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_artifact_%j.log

set -euo pipefail

echo "=== TORA zero-shot artifact eval started at $(date) on $(hostname) ==="
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

# Same viz overrides as thin-walled: 1 viz sample per batch, mitsuba, no GIFs.
VIZ_ARGS=(
    "+visualizer._target_=tora.visualizer.FlowVisualizationCallback"
    "+visualizer.renderer=mitsuba"
    "+visualizer.image_size=512"
    "+visualizer.max_samples_per_batch=1"
    "+visualizer.save_trajectory=false"
)

# Artifact has samples up to max_parts=20 (zero-shot preset). Bump batch_size
# from preset 8 to 16 to fit within wall-clock — A100 80GB has headroom.
ART_DIR=$LOG_ROOT/artifact_zeroshot_${SLURM_JOB_ID}
echo ""
echo "=== Zero-shot eval: bbad_artifact (3738 val samples, max_parts=20) ==="
python sample.py \
    ckpt_path="$CKPT" \
    data_root="$DATA_ROOT" \
    data=zeroshot/bbad_artifact \
    data.batch_size=16 \
    data.num_workers=8 \
    log_dir="$ART_DIR" \
    "${VIZ_ARGS[@]}"

echo ""
echo "=== Eval finished at $(date) ==="
echo "Results: $ART_DIR/results/"
echo "Viz:     $ART_DIR/visualizations/"
