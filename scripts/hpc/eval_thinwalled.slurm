#!/bin/bash
#SBATCH --job-name=tora-eval-thinwalled
#SBATCH --partition=gpu-a100-short
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_eval_%j.log

set -euo pipefail

echo "=== TORA eval started at $(date) on $(hostname) ==="
nvidia-smi | head -15 || true

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
REPO_DIR=$TORA_ROOT/repo
ENV_PREFIX=$TORA_ROOT/envs/tora
DATA_ROOT=$TORA_ROOT/dataset
CKPT=$TORA_ROOT/checkpoints/bbad_everyday_cka.ckpt
LOG_ROOT=$TORA_ROOT/eval_runs

# --- Modules & env ---
module purge
module load Anaconda3/2024.02-1
module load CUDA/12.4.1
module load cuDNN/9.6.0.74-CUDA-12.4.1
eval "$(conda shell.bash hook)"
conda activate "$ENV_PREFIX"
export TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0"
export PIP_CACHE_DIR=$TORA_ROOT/.pip-cache
export HF_HOME=$TORA_ROOT/.hf-cache
mkdir -p "$LOG_ROOT" "$HF_HOME"

# --- Build thinwalled.hdf5 if missing ---
if [ ! -f "$DATA_ROOT/thinwalled.hdf5" ]; then
    echo "--- Building thinwalled.hdf5 ---"
    python "$TORA_ROOT/prep_thinwalled.py"
fi

# Disable wandb (eval, no need to log to wandb)
export WANDB_MODE=offline

cd "$REPO_DIR"

# Visualization overrides (applied to both runs):
#   - FlowVisualizationCallback renders input / GT / each of the 3 generations.
#   - mitsuba renderer = paper-quality shaded point clouds (~5-10 s per PNG).
#   - max_samples_per_batch=1 keeps it tractable: 1 viz-sample per batch
#     (~123 viz samples over the full thin-walled run, not 3933).
#   - save_trajectory=false: no GIFs by default (each GIF is 25+ renders = expensive).
VIZ_ARGS=(
    "+visualizer._target_=tora.visualizer.FlowVisualizationCallback"
    "+visualizer.renderer=mitsuba"
    "+visualizer.image_size=512"
    "+visualizer.max_samples_per_batch=1"
    "+visualizer.save_trajectory=false"
)

# --- Smoke test: 50 samples of full bbad_everyday (validates setup + viz pipeline) ---
SMOKE_DIR=$LOG_ROOT/smoke_${SLURM_JOB_ID}
echo ""
echo "=== [1/2] Smoke test: 50 samples of bbad_everyday (with viz) ==="
python sample.py \
    ckpt_path="$CKPT" \
    data_root="$DATA_ROOT" \
    data=main/bbad_everyday \
    data.limit_val_samples=50 \
    data.batch_size=16 \
    data.num_workers=4 \
    log_dir="$SMOKE_DIR" \
    "${VIZ_ARGS[@]}"
echo "Smoke test done. Log dir: $SMOKE_DIR"

# --- Thin-walled eval: full Bowl/Cup/Plate/Mug/Teacup/Teapot/Vase val split (3933) ---
# Plus: viz for 1 sample per batch (~123 thin-walled samples rendered as PNG).
# To also dump trajectory GIFs for a tiny set, re-run with +visualizer.save_trajectory=true
# and data.limit_val_samples=20 in a follow-up job.
TW_DIR=$LOG_ROOT/thinwalled_${SLURM_JOB_ID}
echo ""
echo "=== [2/2] Full eval: bbad_thinwalled (3933 samples, with viz) ==="
python sample.py \
    ckpt_path="$CKPT" \
    data_root="$DATA_ROOT" \
    data=main/bbad_thinwalled \
    data.batch_size=32 \
    data.num_workers=8 \
    log_dir="$TW_DIR" \
    "${VIZ_ARGS[@]}"

echo ""
echo "=== Eval finished at $(date) ==="
echo "Smoke results:       $SMOKE_DIR/results/"
echo "Thin-walled results: $TW_DIR/results/"
