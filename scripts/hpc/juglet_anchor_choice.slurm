#!/bin/bash
#SBATCH --job-name=tora-anchor-choice
#SBATCH --partition=gpu-a100
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_anchor_choice_%j.log

set -euo pipefail

# DOES THE FIXED SHERD DECIDE WHICH OTHER SHERDS LAND? (.scratch/anchor-choice/)
#
# TORA holds one sherd at its true pose (the anchor) and places the rest. On the
# Juglet, baseline job 30130049, the sherds that share the longest break edge
# with the anchor (1 and 7) went home in 15 and 14 of 20 draws; the four that
# do not touch it at all (4, 5, 6, and 8 barely) went home 0-4 times. Across
# the 8 Fractura pots, sherds touching the anchor were placed right 0.61 of the
# time against 0.28 for the rest, within size bands. All of that is
# correlation. This job moves the anchor and watches whether the good placements
# move with it.
#
# Arms, the untouched baseline model, 20 draws each, same seed:
#   anchor0  default (largest sherd, 0). Same settings and seed as 30130049,
#            so it should reproduce [20,15,3,4,2,2,0,14,0] -- if it does not,
#            the comparison is sampler noise before it is anything else.
#   anchor6  the base (sherd 6). Neighbours 3,4,5,8.
#   anchor4  a lower-body sherd (4). Neighbours 2,5,6,7. A second, independent
#            placement of the anchor, so one arm cannot carry the finding alone.
#
# The catch, stated before the result: the model only ever trained with the
# LARGEST sherd held. A small held sherd is out of distribution. If every
# sherd gets worse in anchor6/anchor4, that is not a refutation -- it is the
# model not coping with the setup, and the test is inconclusive.

echo "=== anchor choice started at $(date) on $(hostname) ==="
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
        log_dir="$LOG_ROOT/anchor_${NAME}_${SLURM_JOB_ID}" \
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

run_arm anchor0
run_arm anchor6 +data.anchor_part=6
run_arm anchor4 +data.anchor_part=4

echo ""
find "$LOG_ROOT" -path "*anchor_*_${SLURM_JOB_ID}*" -name "*.npz" | sort
echo "=== Finished at $(date) ==="
