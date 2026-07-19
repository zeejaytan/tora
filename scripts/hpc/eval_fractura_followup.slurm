#!/bin/bash
#SBATCH --job-name=tora-fractura-followup
#SBATCH --partition=gpu-a100-short
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_fractura_followup_%j.log

# Combined follow-up job for the Fractura cross-framework comparison.
#   Test A (BoN=10):       re-run all 5 subsets with model.n_generations=10
#   Test C (anchor-free):  re-run all 5 subsets with data.anchor_free=true (BoN=3)
#   Test B (gate analysis): post-hoc on N=3 (job 24342475) + new N=10 results

set -euo pipefail

echo "=== TORA Fractura follow-up started at $(date) on $(hostname) ==="
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
    "+visualizer.save_trajectory=false"
)

SUBSETS=(bone_syn_pig bone_syn_rib ceramics egg bones)

# ---------- Test A: best-of-N=10 ----------
echo ""
echo "########## Test A: best-of-N=10 sweep ##########"
for SUBSET in "${SUBSETS[@]}"; do
    OUT_DIR=$LOG_ROOT/fractura_${SUBSET}_BoN10_${SLURM_JOB_ID}
    echo ""
    echo "=== A/${SUBSET} (n_generations=10) ==="
    python sample.py \
        ckpt_path="$CKPT" \
        data_root="$DATA_ROOT" \
        data=zeroshot/fractura/${SUBSET} \
        data.batch_size=8 \
        data.num_workers=4 \
        model.n_generations=10 \
        log_dir="$OUT_DIR" \
        "${VIZ_ARGS[@]}"
    echo "Done A/${SUBSET}: $OUT_DIR"
done

# ---------- Test C: anchor-free ablation ----------
echo ""
echo "########## Test C: anchor-free ablation (BoN=3) ##########"
for SUBSET in "${SUBSETS[@]}"; do
    OUT_DIR=$LOG_ROOT/fractura_${SUBSET}_anchorfree_${SLURM_JOB_ID}
    echo ""
    echo "=== C/${SUBSET} (anchor_free=true, n_generations=3) ==="
    python sample.py \
        ckpt_path="$CKPT" \
        data_root="$DATA_ROOT" \
        data=zeroshot/fractura/${SUBSET} \
        data.batch_size=8 \
        data.num_workers=4 \
        data.anchor_free=true \
        log_dir="$OUT_DIR" \
        "${VIZ_ARGS[@]}"
    echo "Done C/${SUBSET}: $OUT_DIR"
done

# ---------- Test B: agreement-gate post-hoc analysis ----------
echo ""
echo "########## Test B: agreement-gate post-hoc analysis ##########"
ANALYSIS_OUT=$TORA_ROOT/fractura_followup_${SLURM_JOB_ID}.md
python "$TORA_ROOT/analyze_fractura_followup.py" \
    --baseline-job 24342475 \
    --followup-job "$SLURM_JOB_ID" \
    --eval-root "$LOG_ROOT" \
    --output "$ANALYSIS_OUT"

echo ""
echo "=== All Fractura follow-up tests finished at $(date) ==="
echo "Analysis report: $ANALYSIS_OUT"
