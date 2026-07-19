#!/bin/bash
#SBATCH --job-name=tora-eval-fractura
#SBATCH --partition=gpu-a100-short
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_fractura_%j.log

set -euo pipefail

echo "=== TORA Fractura subset eval started at $(date) on $(hostname) ==="
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

# Same viz overrides as prior runs (1 mitsuba render per batch, no GIFs).
VIZ_ARGS=(
    "+visualizer._target_=tora.visualizer.FlowVisualizationCallback"
    "+visualizer.renderer=mitsuba"
    "+visualizer.image_size=512"
    "+visualizer.max_samples_per_batch=1"
    "+visualizer.save_trajectory=false"
)

# Five Fractura zero-shot subsets (counts after min/max_parts filter):
#   bone_syn_pig (21), bone_syn_rib (11), ceramics (8), egg (3), bones (16)
SUBSETS=(bone_syn_pig bone_syn_rib ceramics egg bones)

for SUBSET in "${SUBSETS[@]}"; do
    OUT_DIR=$LOG_ROOT/fractura_${SUBSET}_${SLURM_JOB_ID}
    echo ""
    echo "=== Eval: ${SUBSET} ==="
    python sample.py \
        ckpt_path="$CKPT" \
        data_root="$DATA_ROOT" \
        data=zeroshot/fractura/${SUBSET} \
        data.batch_size=8 \
        data.num_workers=4 \
        log_dir="$OUT_DIR" \
        "${VIZ_ARGS[@]}"
    echo "Done: $OUT_DIR"
done

echo ""
echo "=== All Fractura subset evals finished at $(date) ==="
for SUBSET in "${SUBSETS[@]}"; do
    echo "  $SUBSET -> $LOG_ROOT/fractura_${SUBSET}_${SLURM_JOB_ID}/results/"
done
