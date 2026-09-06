#!/bin/bash
#SBATCH --job-name=tora-fragment-drop
#SBATCH --partition=gpu-a100-short
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_fragment_drop_%j.log

set -euo pipefail

# DOES A MISSING SHERD MAKE THE MODEL MISPLACE THE SHERDS IT STILL HAS?
#
# The Juglet is incomplete: one visible piece was never recovered and no
# reassembly can put it back (scripts/build_juglet_ground_truth.py). NONE of the
# eight Fractura pots TORA reassembles is missing anything, and every benchmark
# this model was trained and tested on hands back all the parts. That is a clean
# difference between the Juglet and every object TORA succeeds on, it is not
# wear, and nobody has measured it.
#
# The umbrella question intent/U4 names the two outcomes, and they demand
# opposite responses:
#
#   GRACEFUL DEGRADATION  it seats the fragments it has and leaves the gap open.
#                         Nothing to fix; incompleteness is not the Juglet's
#                         problem.
#   DESTABILISATION       absence makes it misplace fragments that ARE present,
#                         because the assembly is scored whole and a hole wants
#                         filling. Then the Juglet's missing piece becomes a
#                         leading explanation ahead of wear, and generative
#                         completion becomes load-bearing for Thesis Aim 3.
#
# Eight sherds clustered against one side with no vessel closing -- which is
# what the Juglet's arms actually do -- is what destabilisation looks like.
#
# WHAT IS BEING VARIED. One fragment, removed before the point cloud is sampled,
# so the loader behaves exactly as it does on a genuinely incomplete pot. Rank k
# means the k-th LARGEST fragment by surface area. Rank 1 is refused by the
# dataset itself, and that refusal matters: `_transform` picks the anchor as
# argmax(counts) and counts rise with area, so rank 1 IS the anchor -- the
# fragment handed to the model already seated. Dropping it would hand the model
# a different starting sherd, which is a different task, not a missing piece.
#
# THE CONFOUND, STATED RATHER THAN SUPPRESSED. Removing a mesh does not leave
# the others untouched. The 5000-point budget is shared out by area over the
# TOTAL area, so every surviving fragment is re-sampled; the pot is re-centred
# on what remains and re-normalised by its new max|v|. That is not a bug -- it
# is what an incomplete pot does -- but it means "dropped differs from whole" is
# not by itself a finding. Two things bound it:
#
#   the CPU gate below, which measures the disturbance and states the bar in
#   percent of pot size before any GPU time is spent; and
#   the RESEED arm, the same whole pots run again under a different seed, which
#   is the score-level floor for "the same pot, drawn twice".
#
# AND THE DIRECTION CARRIES THE ARGUMENT. Removing a sherd also removes a sherd
# to place, and fewer pieces is an EASIER task. So a drop arm that scores the
# same or better is graceful degradation with the confound working against it,
# and only a drop arm that scores WORSE, despite the smaller task, is evidence
# of destabilisation.
#
# STATED IN ADVANCE SO IT CAN FAIL. If absence destabilises, the kept sherds'
# median turn should RISE when one fragment is removed, by more than the reseed
# floor, on a majority of the five pots TORA reassembles cleanly -- blue_pot,
# pink_bowl, narrow_bottle4, narrow_bottle2, galli_pot -- and should rise
# further at rank 2 (a big sherd gone) than at the highest rank a pot allows (a
# small one). If instead the median change is inside the reseed floor, or
# negative, then absence is handled gracefully, the Juglet's missing piece is
# NOT what stops it, and candidate 3 on intent/O8 is ruled out.
#
# WHAT WOULD MEAN THE MEASUREMENT IS BROKEN RATHER THAN THE METHOD: the gate
# reporting the kept sherds coming back a different SHAPE beyond re-sampling
# noise, or the anchor changing identity between arms. Either stops the job.
#
# The pots are run NORMALISED (max|v| = 0.5). Ceramics ships in millimetres, at
# which the model is out of band by two orders of magnitude and every pot fails
# for a reason that has nothing to do with missing pieces (job 29891327).
#
# Usage:
#   sbatch scripts/hpc/eval_fragment_drop.slurm
#   RANKS="2 3" DRAWS=10 sbatch scripts/hpc/eval_fragment_drop.slurm

echo "=== fragment drop started at $(date) on $(hostname) ==="
nvidia-smi | head -15 || true

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
ENV_PREFIX=$TORA_ROOT/envs/tora
DATA_ROOT=$TORA_ROOT/dataset
LOG_ROOT=$TORA_ROOT/eval_runs
CKPT=$TORA_ROOT/checkpoints/bbad_everyday_cka.ckpt
DRAWS=${DRAWS:-10}
# Rank k = the k-th largest fragment. 1 is the anchor and is refused. Pots with
# fewer than k fragments, or fewer than 3, drop out of that arm automatically.
RANKS=${RANKS:-"2 3 4 5 6"}
SEED=${SEED:-42}
RESEED=${RESEED:-1337}
POTS=${POTS:-"blue_pot galli_pot"}

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
echo '########## gate: what removing a sherd does to the sherds we keep ##########'
# Seconds on CPU, and it decides whether the next half hour of GPU means
# anything. It does NOT assert the kept fragments are untouched -- they cannot
# be, and a gate written loosely enough to pass would be worse than none. It
# asserts the right sherd is gone and the anchor did not change, and it MEASURES
# the disturbance so the result can be read against it.
python scripts/check_fragment_omission.py \
    --data "$DATA_ROOT/ceramics.hdf5" --dataset-name ceramics \
    --min-parts 3 --max-parts 12 --anchor-fixed --rank 2

echo ""
echo "checkpoint: $CKPT"
echo "draws:      $DRAWS per arm"
echo "ranks:      $RANKS"
echo "seeds:      $SEED (whole, drops), $RESEED (reseed control)"

run_arm () {
    NAME=$1; shift
    echo ""
    echo "########## $NAME ##########"
    DIR="$LOG_ROOT/drop_${NAME}_${SLURM_JOB_ID}"
    python sample.py ckpt_path="$CKPT" data_root="$DATA_ROOT" \
        data=zeroshot/fractura/ceramics data.batch_size=8 data.num_workers=4 \
        lora.enabled=false \
        +data.normalize_object_scale=true \
        model.n_generations="$DRAWS" \
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
    echo "$DIR"
}

# Every sherd present. This is what the drop arms are measured against.
run_arm whole seed="$SEED"

# The same whole pots again, nothing removed, different seed. This is the floor:
# any change smaller than what this arm shows is the sampler, not absence.
run_arm reseed seed="$RESEED"

for K in $RANKS; do
    run_arm "rank${K}" seed="$SEED" "+data.omit_rank=${K}"
done

DROPPED=()
for K in $RANKS; do
    D="$LOG_ROOT/drop_rank${K}_${SLURM_JOB_ID}"
    [ -d "$D/results" ] && DROPPED+=("$D")
done

echo ""
echo "### did the sherds we KEPT still go to the right place ###"
python scripts/summarise_fragment_drop.py \
    --whole "$LOG_ROOT/drop_whole_${SLURM_JOB_ID}" \
    --reseed "$LOG_ROOT/drop_reseed_${SLURM_JOB_ID}" \
    --dropped "${DROPPED[@]}" || true

echo ""
echo "### does the vessel still close -- LOOK before quoting any of the above ###"
if [ -d "$LOG_ROOT/drop_rank2_${SLURM_JOB_ID}/clouds" ]; then
    python scripts/render_fragment_drop.py \
        --whole "$LOG_ROOT/drop_whole_${SLURM_JOB_ID}" \
        --dropped "$LOG_ROOT/drop_rank2_${SLURM_JOB_ID}" \
        --pots $POTS \
        --out "$LOG_ROOT/drop_rank2_${SLURM_JOB_ID}/fragment_drop.png" || true
fi

echo ""
{ find "$LOG_ROOT" -path "*drop_*_${SLURM_JOB_ID}*" -name "*.png" | sort | head -40; } || true

echo ""
echo "=== Finished at $(date) ==="
