#!/bin/bash
#SBATCH --job-name=tora-lora-vessels
#SBATCH --partition=gpu-a100
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=12:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_lora_vessels_%j.log

set -euo pipefail

# lora_bbad_vessels -- step 4 of WEAR_V3_PLAN.md: "train lora_gb, evaluate on
# and off against the Juglet and the worn sweep."
#
# WHAT THIS BUYS. The conservator's diagnosis of the gap: the dataset needs more
# variety in the SHAPES that get trained. We can make the relevant object's
# fragments worn, but we do not have the shape in training. The fine-tuning
# source had EIGHT ceramic vessels. bbad_vessels has 371 distinct vessel shapes,
# 3,159 examples, split on the object so no shape appears on both sides.
#
# WHY AN ADAPTER RATHER THAN MORE FINE-TUNING. wear_v1 bought +0.235 seating on
# worn material by losing 0.115 on fresh, and there was no way to undo it. An
# adapter switches off to the base model bit-for-bit, so the do-no-harm arm
# below is guaranteed by construction rather than hoped for.
#
# RECIPE, read off GARF's configs/experiment/finetune.yaml rather than from
# memory. Rank 128, alpha 256, dropout 0.1, pose head unfrozen, lr 2e-4.
#
#   Two corrections to what WEAR_V3_PLAN.md says about GARF:
#   - It says adapters go in the FINAL transformer block. GARF's target regex
#     matches transformer_layers.<N> for EVERY N -- all of them. We follow GARF:
#     all 6 blocks.
#   - It does not mention the learning rate. GARF's fine-tune inherits lr 2e-4,
#     ten times the 2e-5 the full fine-tune here used. That is right for an
#     adapter, where only a small percentage of the weights move.
#
#   One deviation, stated so it is not mistaken for a match: GARF also adapts
#   the feed-forward and timestep-embedding linears. We adapt the four attention
#   projections only, because that is what Gate C verified reversible. If this
#   run underperforms, widening the target set is the first knob to turn.
#
# NO REPLAY DATA. See config/data/main/bbad_vessels.yaml for why.
#
# HOW TO READ THE RESULT -- WEAR_V3_PLAN.md section 7, both learned the hard
# way: not on part accuracy, which read 0.80 on a Juglet assembly the render
# showed was scattered, and rotation error with ~40 degrees as the collapse
# threshold rather than 10. Renders are produced for the Juglet arm and must be
# looked at before any of this is written up.

echo "=== lora_bbad_vessels started at $(date) on $(hostname) ==="
nvidia-smi | head -15 || true

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
ENV_PREFIX=$TORA_ROOT/envs/tora
DATA_ROOT=$TORA_ROOT/dataset
LOG_ROOT=$TORA_ROOT/eval_runs
OUT_ROOT=$TORA_ROOT/output/lora_vessels_${SLURM_JOB_ID}
SMOKE=$TORA_ROOT/output/lora_vessels_smoke_${SLURM_JOB_ID}
CKPT=$TORA_ROOT/checkpoints/bbad_everyday_cka.ckpt

LORA_ON=(lora.enabled=true lora.r=128 lora.alpha=256 lora.dropout=0.1 lora.last_n_blocks=6 lora.train_head=true)

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

for f in "$DATA_ROOT/bbad_vessels.hdf5" "$CKPT"; do
    [ -f "$f" ] || { echo "missing: $f"; exit 1; }
done
ls -la "$DATA_ROOT/bbad_vessels.hdf5"

echo ""
echo "### 1/5  Gate C again, on this checkpoint ###"
# Cheap, and it is the assumption everything below rests on: an adapter that
# cannot be switched off cleanly makes the on/off comparison meaningless.
python scripts/verify_lora_reversible.py --ckpt "$CKPT" \
    || { echo "Gate C failed -- not training an adapter that cannot be undone"; exit 1; }

echo ""
echo "### 2/5  smoke: does the adapter actually train and reload? ###"
# Eight batches, one epoch. This is here because the expensive failure is
# silent: load_checkpoint_for_module is non-strict, and wrapping a projection
# renames its weight, so a train/sample mismatch loads NOTHING into every
# adapted layer and still prints a full table of numbers. Find that out in two
# minutes, not after five hours on an A100.
python train.py \
    data=main/bbad_vessels \
    data_root="$DATA_ROOT" \
    "${LORA_ON[@]}" \
    model.encoder_ckpt="$CKPT" \
    model.flow_model_ckpt="$CKPT" \
    model.optimizer.lr=2e-4 \
    trainer.max_epochs=1 \
    ++trainer.limit_train_batches=8 \
    ++trainer.limit_val_batches=4 \
    ++trainer.check_val_every_n_epoch=1 \
    log_dir="$SMOKE" || { echo "smoke training failed"; exit 1; }

SMOKE_CKPT=$(find "$SMOKE" -name "*.ckpt" -printf "%T@ %p\n" 2>/dev/null | sort -rn | head -1 | cut -d" " -f2)
[ -n "$SMOKE_CKPT" ] || { echo "smoke produced no checkpoint"; exit 1; }
echo "smoke checkpoint: $SMOKE_CKPT"

# Load it back through the real sampling path. assert_adapter_present raises if
# the checkpoint carried no adapter tensors, if any expected one is absent, or
# if every lora_B is still zero -- which would mean the adapter is exactly the
# base model and either nothing was learned or nothing was loaded.
python sample.py ckpt_path="$SMOKE_CKPT" data_root="$DATA_ROOT" \
    data=zeroshot/juglet_gt data.batch_size=1 \
    "${LORA_ON[@]}" lora.active=true \
    model.n_generations=1 \
    ++trainer.limit_test_batches=1 \
    log_dir="$LOG_ROOT/lora_smoke_${SLURM_JOB_ID}" \
    || { echo "adapter did not reload -- fix the plumbing before the long run"; exit 1; }
echo "smoke passed: the adapter trains, saves and reloads"

echo ""
echo "### 3/5  train the adapter ###"
python train.py \
    data=main/bbad_vessels \
    data_root="$DATA_ROOT" \
    "${LORA_ON[@]}" \
    model.encoder_ckpt="$CKPT" \
    model.flow_model_ckpt="$CKPT" \
    model.optimizer.lr=2e-4 \
    trainer.max_epochs=60 \
    log_dir="$OUT_ROOT" || { echo "training failed"; exit 1; }

BEST=$(find "$OUT_ROOT" -name "*.ckpt" -printf "%T@ %p\n" 2>/dev/null | sort -rn | head -1 | cut -d" " -f2)
echo "using checkpoint: $BEST"

echo ""
echo "### 4/5  three arms: adapter ON, adapter OFF, untouched baseline ###"
# The OFF arm is the same file with the adapter disabled. It should reproduce
# the baseline exactly; if it does not, the switch is broken and every ON number
# is uninterpretable. It is a control, not a result.
run_arm () {
    NAME=$1; C=$2; shift 2
    LORA_ARGS=("$@")

    echo ""
    echo "########## $NAME : WORN sweep (the gain we are buying) ##########"
    python sample.py ckpt_path="$C" data_root="$DATA_ROOT" \
        data=zeroshot/erosion_sweep data.batch_size=4 \
        "${LORA_ARGS[@]}" \
        log_dir="$LOG_ROOT/lorav_sweep_${NAME}_${SLURM_JOB_ID}" \
        model.n_generations=3 || true
    python scripts/analyze_erosion_sweep.py \
        --results-dir "$LOG_ROOT/lorav_sweep_${NAME}_${SLURM_JOB_ID}/results" \
        --calibration "$DATA_ROOT/erosion_sweep.calibration.json" || true

    echo ""
    echo "########## $NAME : FRESH objects (what we might be paying with) ##########"
    python sample.py ckpt_path="$C" data_root="$DATA_ROOT" \
        data=zeroshot/real_heldout_norm data.batch_size=4 \
        "${LORA_ARGS[@]}" \
        log_dir="$LOG_ROOT/lorav_fresh_${NAME}_${SLURM_JOB_ID}" \
        model.n_generations=3 || true

    echo ""
    echo "########## $NAME : THE JUGLET, against the hand reassembly ##########"
    # The only real worn archaeological pot here with a valid answer key. Read
    # it knowing a piece is MISSING: leaving that gap open is correct, and any
    # metric that rewards contact everywhere will punish the right answer.
    RUN="$LOG_ROOT/lorav_juglet_${NAME}_${SLURM_JOB_ID}"
    python sample.py ckpt_path="$C" data_root="$DATA_ROOT" \
        data=zeroshot/juglet_gt data.batch_size=1 \
        "${LORA_ARGS[@]}" \
        log_dir="$RUN" \
        model.n_generations=5 \
        "+visualizer._target_=tora.visualizer.FlowVisualizationCallback" \
        "+visualizer.renderer=mitsuba" \
        "+visualizer.image_size=512" \
        "+visualizer.max_samples_per_batch=1" \
        "+visualizer.center_points=true" \
        "+visualizer.save_trajectory=false" \
        "+visualizer.save_procrustes_assembly=true" \
        "+visualizer.save_assembly_npz=true" || true
}

run_arm adapter_on  "$BEST" "${LORA_ON[@]}" lora.active=true
run_arm adapter_off "$BEST" "${LORA_ON[@]}" lora.active=false
run_arm baseline    "$CKPT" lora.enabled=false

echo ""
echo "### 5/5  collect the renders ###"
find "$LOG_ROOT" -path "*lorav_juglet_*_${SLURM_JOB_ID}*" \
    \( -name "*.png" -o -name "*.npz" \) | sort

echo ""
echo "=== Finished at $(date) ==="
echo "Read it as a trade, not a score. The worn sweep and the Juglet are what we"
echo "are buying; the fresh run is what we might be paying with. adapter_off"
echo "should match baseline -- if it does not, stop and fix the switch before"
echo "believing anything else here."
echo ""
echo "LOOK AT THE JUGLET RENDERS BEFORE WRITING ANY OF THIS UP. Part accuracy"
echo "read 0.80 on an assembly that was visibly scattered."
