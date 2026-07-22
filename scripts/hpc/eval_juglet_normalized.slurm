#!/bin/bash
#SBATCH --job-name=tora-juglet-norm
#SBATCH --partition=gpu-a100-short
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_juglet_norm_%j.log

set -euo pipefail
echo "=== Juglet eval on scale-normalized data, started $(date) ==="
echo "Juglet source was 10.87 raw units vs synthetic 0.5 => absolute CD<0.01"
echo "part-accuracy threshold was ~22x too strict. Predictions are UNCHANGED"
echo "(dataset normalizes input either way); only the metrics are fixed."

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
ENV_PREFIX=$TORA_ROOT/envs/tora
DATA_ROOT=$TORA_ROOT/dataset
LOG_ROOT=$TORA_ROOT/eval_runs
BASE_CKPT=$TORA_ROOT/checkpoints/bbad_everyday_cka.ckpt
ROBUST_CKPT=$TORA_ROOT/output/real_finetune_robust_27793083/epoch-59.ckpt

module purge
module load Anaconda3/2024.02-1
module load CUDA/12.4.1
module load cuDNN/9.6.0.74-CUDA-12.4.1
eval "$(conda shell.bash hook)"
conda activate "$ENV_PREFIX"
export TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0"
export HF_HOME=$TORA_ROOT/.hf-cache
cd "$TORA_ROOT/repo"

for TAG in "baseline:$BASE_CKPT" "robust:$ROBUST_CKPT"; do
    NAME="${TAG%%:*}"; CKPT="${TAG#*:}"
    echo ""
    echo "### [$NAME] Juglet 9-piece, scale-normalized ###"
    python sample.py \
        ckpt_path="$CKPT" \
        data_root="$DATA_ROOT" \
        data=zeroshot/juglet_norm \
        log_dir="$LOG_ROOT/juglet_norm_${NAME}_${SLURM_JOB_ID}" \
        model.n_generations=5 \
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
echo "Viz: $LOG_ROOT/juglet_norm_{baseline,robust}_${SLURM_JOB_ID}/visualizations/"
