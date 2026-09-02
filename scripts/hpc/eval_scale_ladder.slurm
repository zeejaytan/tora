#!/bin/bash
#SBATCH --job-name=tora-scale-ladder
#SBATCH --partition=gpu-a100-short
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_scale_ladder_%j.log

set -euo pipefail

# IS THE FRACTURA FAILURE THE POTS, OR THE UNITS THEY WERE SAVED IN?
#
# `scales` is not metric bookkeeping. tora/modeling/tora.py reads it out of the
# batch and hands it to the flow model at every denoising step; the encoding
# manager turns it into a sinusoidal code and concatenates it onto ALL 5000
# points (tora/modeling/flow_model/embedding.py:151). It is a model input.
#
# Breaking Bad objects arrive at max|v| = 0.5, and training jitters that by
# random_scale_range (0.75, 1.25), so the model has only ever seen this input
# in roughly [0.375, 0.625]. Fractura's real subsets are stored in MILLIMETRES:
# the eight ceramics arrive at 44.7 to 119.9. That is 100-190x outside the
# training band, and far into the aliasing regime of an encoding whose top
# frequency is 2^9 = 512.
#
# scripts/normalize_real_hdf5.py says the opposite in its header -- "TRAINING
# AND INFERENCE ARE UNAFFECTED by this" -- which is why the raw-unit subsets
# were never re-run. That sentence is wrong.
#
# The paired evidence that prompted this: blue_pot, galli_pot and plate appear
# BOTH in real_heldout_norm.hdf5 (normalised, scale ~0.4) and in ceramics.hdf5
# (millimetres). Same meshes, piece for piece -- identical vertex and face
# counts, extents differing by one uniform factor (109.8x for blue_pot). Same
# checkpoint, same seed. Non-anchor rotation error: blue_pot 5.4 deg normalised
# vs 76.0 raw. That comparison is across two historical jobs whose sampler
# settings could not be fully recovered, so it is a lead, not the finding.
# THIS job runs every arm together, one settings set, one job id.
#
# WHAT IS BEING VARIED. Exactly one number. data.normalize_object_scale
# restates the object at max|v| = 0.5 BEFORE the [-1, 1] normalization, and
# data.scale_multiplier then restates it again -- which is precisely what
# saving the same scan in other units would do. The coordinates the network
# sees are unchanged; only `scales` moves. The CPU gate below asserts that
# before any GPU time is spent, and the job stops if it fails.
#
# STATED IN ADVANCE SO IT CAN FAIL. If storage units are the cause, arm B
# should drop all eight pots from 66-91 deg into roughly the 5-55 deg band,
# with blue_pot / galli_pot / plate near 5.4 / 33.5 / 54.5, and the ladder
# should degrade monotonically as the rung climbs away from 0.5, reaching arm
# A's numbers around rung 100. If the ladder is flat, the hypothesis is dead
# and the failure is in the material after all.
#
# Usage:
#   sbatch scripts/hpc/eval_scale_ladder.slurm
#   DRAWS=10 LADDER_DRAWS=5 sbatch scripts/hpc/eval_scale_ladder.slurm

echo "=== scale ladder started at $(date) on $(hostname) ==="
nvidia-smi | head -15 || true

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
ENV_PREFIX=$TORA_ROOT/envs/tora
DATA_ROOT=$TORA_ROOT/dataset
LOG_ROOT=$TORA_ROOT/eval_runs
CKPT=$TORA_ROOT/checkpoints/bbad_everyday_cka.ckpt
DRAWS=${DRAWS:-10}
LADDER_DRAWS=${LADDER_DRAWS:-5}
# Rung m puts the object at scale 0.5*m. 1 -> 0.5 (Breaking Bad's own
# convention), 200 -> 100, which brackets the ceramics' stored 45-120.
RUNGS=${RUNGS:-"2 5 10 30 100 200"}

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

for f in "$DATA_ROOT/ceramics.hdf5" "$CKPT"; do
    [ -e "$f" ] || { echo "missing: $f"; exit 1; }
done

echo ""
echo '########## gate: the knob must move scales and nothing else ##########'
# Costs seconds on CPU and decides whether the next 20 minutes of GPU mean
# anything. If normalising also perturbed the coordinates or the normals, a
# change in score would not isolate the conditioning input.
python scripts/check_scale_conditioning.py \
    --data "$DATA_ROOT/ceramics.hdf5" --dataset-name ceramics

echo ""
echo "checkpoint: $CKPT"
echo "draws:      $DRAWS (arms A/B), $LADDER_DRAWS (ladder)"
echo "rungs:      $RUNGS"

DONE_DIRS=()

run_arm () {
    NAME=$1; shift
    echo ""
    echo "########## $NAME ##########"
    DIR="$LOG_ROOT/scaleladder_${NAME}_${SLURM_JOB_ID}"
    python sample.py ckpt_path="$CKPT" data_root="$DATA_ROOT" \
        data=zeroshot/fractura/ceramics data.batch_size=8 data.num_workers=4 \
        lora.enabled=false \
        "$@" \
        log_dir="$DIR" \
        "+visualizer._target_=tora.visualizer.FlowVisualizationCallback" \
        "+visualizer.renderer=mitsuba" \
        "+visualizer.image_size=512" \
        "+visualizer.max_samples_per_batch=8" \
        "+visualizer.center_points=true" \
        "+visualizer.save_trajectory=false" \
        "+visualizer.save_procrustes_assembly=true" \
        "+visualizer.save_assembly_npz=true" || true
    DONE_DIRS+=("$DIR")
}

# Arm A -- exactly what the dataset ships: millimetres, scale 45-120.
run_arm A_raw_mm model.n_generations="$DRAWS"

# Arm B -- the same pots restated at Breaking Bad's own convention, scale 0.5.
run_arm B_normalized model.n_generations="$DRAWS" \
    +data.normalize_object_scale=true

# The ladder between them. Fewer draws each: these are for the shape of the
# curve, not for a headline number on any one rung.
for M in $RUNGS; do
    run_arm "rung${M}" model.n_generations="$LADDER_DRAWS" \
        +data.normalize_object_scale=true "+data.scale_multiplier=${M}"
done

echo ""
echo "### rotation against the number fed in ###"
python scripts/summarise_scale_ladder.py --runs "${DONE_DIRS[@]}" || true

echo ""
echo "### arms A and B, pot by pot, in fragments seated ###"
python scripts/summarise_ceramics_arms.py \
    --runs "$LOG_ROOT/scaleladder_A_raw_mm_${SLURM_JOB_ID}" \
           "$LOG_ROOT/scaleladder_B_normalized_${SLURM_JOB_ID}" || true

echo ""
echo "### renders (LOOK at A vs B on the same pot before quoting any of this) ###"
# head closes the pipe early; without the guard SIGPIPE trips pipefail and the
# whole job is reported FAILED after it has already succeeded.
{ find "$LOG_ROOT" -path "*scaleladder_*_${SLURM_JOB_ID}*" -name "*.png" | sort | head -40; } || true

echo ""
echo "=== Finished at $(date) ==="
