#!/bin/bash
# Export TORA Procrustes assembly proposal PNGs for Juglet deploy (or other zeroshot data).
set -euo pipefail

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
REPO_DIR=$TORA_ROOT/repo
ENV_PREFIX=$TORA_ROOT/envs/tora

module purge
module load Anaconda3/2024.02-1
module load CUDA/12.4.1
module load cuDNN/9.6.0.74-CUDA-12.4.1
eval "$(conda shell.bash hook)"
conda activate "$ENV_PREFIX"
export TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0"
export HF_HOME=$TORA_ROOT/.hf-cache
export WANDB_MODE=offline

JOB_SUFFIX=${SLURM_JOB_ID:-local}
OUT_DIR=${1:-$TORA_ROOT/eval_runs/juglet_procrustes_${JOB_SUFFIX}}

cd "$REPO_DIR"
python scripts/export_procrustes_assembly_viz.py \
  --ckpt "$TORA_ROOT/checkpoints/bbad_everyday_cka.ckpt" \
  --data-root "$TORA_ROOT/dataset" \
  --log-dir "$OUT_DIR"

echo "Visualizations: $OUT_DIR/visualizations/"
