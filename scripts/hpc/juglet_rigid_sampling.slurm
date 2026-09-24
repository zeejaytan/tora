#!/bin/bash
#SBATCH --job-name=tora-rigid-sampling
#SBATCH --partition=gpu-a100
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_rigid_sampling_%j.log

set -euo pipefail

# NEVER MIRROR OR BEND A SHERD DURING SAMPLING (.scratch/juglet-cause/issues/15)
#
# model.rigid_from_t: from flow time t <= value, the model's clean estimate is
# snapped per sherd to the input sherd moved rigidly (det +1) at every step.
# Same trained model, same seed, 20 draws per arm:
#   held0 / held0_rigid           neck held, control vs rigid every step
#   held06 / held06_rigid         neck + base held, control vs rigid every step
#   held06_late                   neck + base held, rigid from t = 0.5

echo "=== rigid sampling started at $(date) on $(hostname) ==="
nvidia-smi | head -15 || true

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
ENV_PREFIX=$TORA_ROOT/envs/tora
DATA_ROOT=$TORA_ROOT/dataset
LOG_ROOT=$TORA_ROOT/eval_runs
CKPT=$TORA_ROOT/checkpoints/bbad_everyday_cka.ckpt
DRAWS=${DRAWS:-20}

module purge
module load Anaconda3/2024.02-1
module load CUDA/12.4.1
module load cuDNN/9.6.0.74-CUDA-12.4.1
eval "$(conda shell.bash hook)"
conda activate "$ENV_PREFIX"
export TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0"
export HF_HOME=$TORA_ROOT/.hf-cache
export WANDB_MODE=offline
cd "$TORA_ROOT/repo"

for f in "$DATA_ROOT/juglet_gt.hdf5" "$CKPT"; do
    [ -f "$f" ] || { echo "missing: $f"; exit 1; }
done

run_arm () {
    NAME=$1; shift
    echo ""
    echo "########## $NAME : $DRAWS draws on the Juglet ##########"
    python sample.py ckpt_path="$CKPT" data_root="$DATA_ROOT" \
        data=zeroshot/juglet_gt data.batch_size=1 lora.enabled=false \
        "$@" \
        log_dir="$LOG_ROOT/rigid_${NAME}_${SLURM_JOB_ID}" \
        model.n_generations="$DRAWS" \
        "+visualizer._target_=tora.visualizer.FlowVisualizationCallback" \
        "+visualizer.renderer=mitsuba" \
        "+visualizer.image_size=512" \
        "+visualizer.max_samples_per_batch=1" \
        "+visualizer.center_points=true" \
        "+visualizer.save_trajectory=false" \
        "+visualizer.save_procrustes_assembly=true" \
        "+visualizer.save_assembly_npz=true" || true
}

run_arm held0
run_arm held0_rigid '+model.rigid_from_t=1.0'
run_arm held06 '+data.anchor_part=[0,6]'
run_arm held06_rigid '+data.anchor_part=[0,6]' '+model.rigid_from_t=1.0'
run_arm held06_late '+data.anchor_part=[0,6]' '+model.rigid_from_t=0.5'

echo ""
find "$LOG_ROOT" -path "*rigid_*_${SLURM_JOB_ID}*" -name "*.npz" | sort
echo "=== Finished at $(date) ==="
