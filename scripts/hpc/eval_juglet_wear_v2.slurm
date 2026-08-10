#!/bin/bash
#SBATCH --job-name=tora-juglet-v2
#SBATCH --partition=gpu-a100
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=04:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_juglet_v2_%j.log

set -euo pipefail

# The Juglet, with the model trained on the CORRECTED wear simulation.
#
# Three checkpoints side by side so the comparison is honest: the untouched
# baseline, the first wear fine-tune (trained on the faulty simulation -- chips
# that perforated sherds and removed no material), and v2.
#
# The Juglet has NO valid ground truth. Its scan-layout "answer" was shown to be
# an invalid reassembly, so every number computed against it is meaningless. The
# renders are the result here; the pairwise arm below is scored against PF++
# pseudo-GT, which inherits PF++'s own errors and is form-level only.
#
# That is not a caveat to skip past. For archaeological reassembly with no known
# answer, visual inspection is the only honest instrument -- see
# docs/notes/JUGLET_TORA_TEST_PLAN.md.

echo "=== Juglet with wear-v2 checkpoint, $(date) on $(hostname) ==="

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
ENV_PREFIX=$TORA_ROOT/envs/tora
DATA_ROOT=$TORA_ROOT/dataset
LOG_ROOT=$TORA_ROOT/eval_runs
BASE=$TORA_ROOT/checkpoints/bbad_everyday_cka.ckpt
WEAR_V1=$TORA_ROOT/output/wear_finetune_28231335/last.ckpt
WEAR_V2=$TORA_ROOT/output/wear_finetune_v2_28885998/last.ckpt

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
for TAG in "baseline:$BASE" "wear_v1:$WEAR_V1" "wear_v2:$WEAR_V2"; do
    NAME="${TAG%%:*}"; CKPT="${TAG#*:}"
    if [ ! -f "$CKPT" ]; then
        echo "skipping $NAME -- no checkpoint at '$CKPT'"
        continue
    fi
    echo ""
    echo "########## WHOLE JUGLET [$NAME] ##########"
    python sample.py \
        ckpt_path="$CKPT" \
        data_root="$DATA_ROOT" \
        data=zeroshot/juglet_norm \
        log_dir="$LOG_ROOT/juglet_v2_${NAME}_${SLURM_JOB_ID}" \
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
for TAG in "baseline:$BASE" "wear_v1:$WEAR_V1" "wear_v2:$WEAR_V2"; do
    NAME="${TAG%%:*}"; CKPT="${TAG#*:}"
    if [ ! -f "$CKPT" ]; then continue; fi
    echo ""
    echo "########## JUGLET PAIRS [$NAME] ##########"
    python sample.py \
        ckpt_path="$CKPT" \
        data_root="$DATA_ROOT" \
        data=zeroshot/juglet_pairs \
        data.batch_size=8 \
        log_dir="$LOG_ROOT/juglet_v2_pairs_${NAME}_${SLURM_JOB_ID}" \
        model.n_generations=5
    python scripts/analyze_pairwise_oracle.py \
        --results-dir "$LOG_ROOT/juglet_v2_pairs_${NAME}_${SLURM_JOB_ID}/results" \
        --adjacency "$DATA_ROOT/juglet_pairs_adjacency.json" \
        --label "Juglet pairs [$NAME] (PF++ pseudo-GT, FORM-LEVEL)" || true
done

echo ""
echo "=== Finished at $(date) ==="
echo "Arm 1 is judged by eye -- there is no valid answer key for this pot."
echo "In arm 2, best-of-N saturates on 2-piece part_accuracy; read the mean."
