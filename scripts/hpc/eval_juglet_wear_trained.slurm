#!/bin/bash
#SBATCH --job-name=tora-juglet-wearft
#SBATCH --partition=gpu-a100-short
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_juglet_wearft_%j.log

set -euo pipefail

# THE REAL TEST: does the wear-trained checkpoint reassemble the JUGLET?
#
# The wear-trained model recovers seating on artificially-abraded pots
# (0.524 -> 0.797 at full wear, p=0.008). The Juglet is the genuine article:
# a real, worn, 9-fragment archaeological vessel.
#
# TWO ARMS, because the Juglet has NO valid ground truth:
#   1. WHOLE POT -- judged VISUALLY. This is the only honest instrument when no
#      correct answer exists, which is the normal archaeological situation. The
#      question is simply: does a vessel appear?
#   2. PAIRWISE -- judged against PF++ pseudo-GT, which is FORM-LEVEL only
#      (GARF Exp 9: the pieces do not truly touch, they merely form a plausible
#      shape). Baseline scored 1.63x mate-vs-non-mate separation here.
#
# Any scalar scored against the Juglet's shipped ground truth remains
# meaningless -- that file is the scan-table layout, not an assembly.

echo "=== Juglet with wear-trained checkpoint, $(date) on $(hostname) ==="

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
ENV_PREFIX=$TORA_ROOT/envs/tora
DATA_ROOT=$TORA_ROOT/dataset
LOG_ROOT=$TORA_ROOT/eval_runs
BASE=$TORA_ROOT/checkpoints/bbad_everyday_cka.ckpt
WEAR=$TORA_ROOT/output/wear_finetune_28231335/last.ckpt

module purge
module load Anaconda3/2024.02-1
module load CUDA/12.4.1
module load cuDNN/9.6.0.74-CUDA-12.4.1
eval "$(conda shell.bash hook)"
conda activate "$ENV_PREFIX"
export TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0"
export HF_HOME=$TORA_ROOT/.hf-cache
cd "$TORA_ROOT/repo"

# ---- Arm 1: whole 9-fragment Juglet, rendered for visual judgement ----
for TAG in "baseline:$BASE" "wearft:$WEAR"; do
    NAME="${TAG%%:*}"; CKPT="${TAG#*:}"
    echo ""
    echo "########## WHOLE JUGLET [$NAME] ##########"
    python sample.py \
        ckpt_path="$CKPT" \
        data_root="$DATA_ROOT" \
        data=zeroshot/juglet_norm \
        log_dir="$LOG_ROOT/juglet_wearft_${NAME}_${SLURM_JOB_ID}" \
        model.n_generations=5 \
        "+visualizer._target_=tora.visualizer.FlowVisualizationCallback" \
        "+visualizer.renderer=mitsuba" \
        "+visualizer.image_size=512" \
        "+visualizer.max_samples_per_batch=1" \
        "+visualizer.center_points=true" \
        "+visualizer.save_trajectory=false" \
        "+visualizer.save_procrustes_assembly=true" \
        "+visualizer.save_assembly_npz=true"
done

# ---- Arm 2: pairwise mating oracle (PF++ pseudo-GT, form-level only) ----
for TAG in "baseline:$BASE" "wearft:$WEAR"; do
    NAME="${TAG%%:*}"; CKPT="${TAG#*:}"
    echo ""
    echo "########## JUGLET PAIRS [$NAME] ##########"
    python sample.py \
        ckpt_path="$CKPT" \
        data_root="$DATA_ROOT" \
        data=zeroshot/juglet_pairs \
        data.batch_size=8 \
        log_dir="$LOG_ROOT/juglet_pairs_wearft_${NAME}_${SLURM_JOB_ID}" \
        model.n_generations=5
    python scripts/analyze_pairwise_oracle.py \
        --results-dir "$LOG_ROOT/juglet_pairs_wearft_${NAME}_${SLURM_JOB_ID}/results" \
        --adjacency "$DATA_ROOT/juglet_pairs_adjacency.json" \
        --label "Juglet pairs [$NAME] (PF++ pseudo-GT, FORM-LEVEL)" || true
done

echo ""
echo "=== Finished at $(date) ==="
echo "Judge arm 1 by eye. Remember best-of-N in arm 2 saturates on 2-piece"
echo "part_accuracy -- read the mean-over-generations statistic instead."
