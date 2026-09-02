#!/bin/bash
#SBATCH --job-name=tora-lora-vessels-v3
#SBATCH --partition=gpu-a100
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=10:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_lora_vessels_v3_%j.log

set -euo pipefail

# lora_bbad_vessels_v3 -- the rerun of job 29623885 on repaired data.
#
# WHAT THIS BUYS. The conservator's diagnosis of the gap: the dataset needs more
# variety in the SHAPES that get trained. We can make the relevant object's
# fragments worn, but we do not have the shape in training. The fine-tuning
# source had EIGHT ceramic vessels. This has 203 distinct vessel shapes in
# 1,169 training examples, split on the object so no shape appears on both
# sides.
#
# WHY THE DATA CHANGED, and why the previous run's numbers cannot simply be
# compared to these. Two defects were found in the corpus job 29623885 trained
# on, and only one of them is fixed by rebuilding:
#   1. 49.22% of fragment vertices sat exactly on a vertex of a neighbouring
#      fragment -- the break faces were congruent copies, so a sherd could be
#      seated by matching a surface to its own mirror image. No real sherd
#      offers that. v3 rebuilds those faces: 0.00% coincident.
#   2. 37% of the objects sectioned as a SOLID LUMP, not a vessel. Those are
#      now removed from train/val/test rather than flagged
#      (scripts/filter_lumps_from_splits.py), checked at the threshold by eye
#      in artifacts/lump_cut_boundary.png, not only in aggregate.
# So this is a different training set, not a longer run on the same one.
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
# WHAT THE FIRST ATTEMPT (job 29527496) GOT WRONG, so this one does not repeat
# it. The adapter plumbing was sound -- 24 projections wrapped, saved and
# reloaded correctly -- and the log printed '5,113,344 of 403,418,314 trainable
# (1.27%)'. That line was true when it was printed and false one epoch later.
# TORA's _freeze_encoder() re-enables requires_grad on the whole encoder unless
# frozen_encoder is set (it defaults to False, and no config here sets it), and
# on_train_epoch_start calls it every epoch. So the run was a FULL FINE-TUNE of
# the 403M-parameter model at lr 2e-4 for sixty epochs, with a LoRA attached --
# not an adapter run at all. 447 supposedly-frozen encoder weights moved, plus
# 39 batch-norm statistics that requires_grad never covered in the first place.
# All nine evaluation arms were discarded. Fixed by pin_encoder_frozen() and
# freeze_norm_stats(); checked at stage 1 and gated at stage 5 below, so the
# same mistake now costs minutes instead of a day.
#
#   One deviation, stated so it is not mistaken for a match: GARF also adapts
#   the feed-forward and timestep-embedding linears. We adapt the four attention
#   projections only, because that is what Gate C verified reversible. If this
#   run underperforms, widening the target set is the first knob to turn.
#
# NO REPLAY DATA. See config/data/main/bbad_vessels_v3.yaml for why.
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
OUT_ROOT=$TORA_ROOT/output/lora_vessels_v3_${SLURM_JOB_ID}
SMOKE=$TORA_ROOT/output/lora_vessels_v3_smoke_${SLURM_JOB_ID}
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

for f in "$DATA_ROOT/bbad_vessels_v3.hdf5" "$CKPT"; do
    [ -f "$f" ] || { echo "missing: $f"; exit 1; }
done
ls -la "$DATA_ROOT/bbad_vessels_v3.hdf5"

echo ""
echo "### 1/6  is the freeze a real freeze? (seconds, CPU) ###"
# requires_grad stops the optimiser, not batch norm. This is the thirty-line
# check that replaces the paragraph that failed to stop job 29527496.
python scripts/test_freeze_norm_stats.py     || { echo "frozen weights can still drift -- not training on top of that"; exit 1; }

echo ""
echo "### 2/6  Gate C again, on this checkpoint ###"
# Cheap, and it is the assumption everything below rests on: an adapter that
# cannot be switched off cleanly makes the on/off comparison meaningless.
python scripts/verify_lora_reversible.py --ckpt "$CKPT" \
    || { echo "Gate C failed -- not training an adapter that cannot be undone"; exit 1; }

echo ""
echo "### 3/6  smoke: does the adapter actually train and reload? ###"
# Eight batches, one epoch. This is here because the expensive failure is
# silent: load_checkpoint_for_module is non-strict, and wrapping a projection
# renames its weight, so a train/sample mismatch loads NOTHING into every
# adapted layer and still prints a full table of numbers. Find that out in two
# minutes, not after five hours on an A100.
python train.py \
    data=main/bbad_vessels_v3 \
    data_root="$DATA_ROOT" \
    "${LORA_ON[@]}" \
    model.encoder_ckpt="$CKPT" \
    model.flow_model_ckpt="$CKPT" \
    model.optimizer.lr=2e-5 \
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
    log_dir="$LOG_ROOT/lora_v3_smoke_${SLURM_JOB_ID}" \
    || { echo "adapter did not reload -- fix the plumbing before the long run"; exit 1; }
echo "smoke passed: the adapter trains, saves and reloads"

echo ""
echo "### 4/6  train the adapter ###"
# THREE CHANGES FROM JOB 29623885, each because of what that run's log showed.
#
# lr 2e-5, not 2e-4. GARF's fine-tune inherits 2e-4 and that is the right order
# for an adapter in general -- but on THIS data it stopped buying anything at
# epoch 9 (val 0.805) and then drifted to 0.816 over the next fifty. Ten times
# smaller, for a fifth as long, is the version of that run worth having.
#
# 20 epochs, not 60. Fifty of the sixty were spent past the point where
# validation had stopped improving.
#
# VALIDATE EVERY EPOCH, AND SELECT ON IT. This is the one that actually cost us
# the last run. config/trainer/main.yaml checks validation every 10 epochs and
# has ModelCheckpoint save on TRAIN epoch end, so it wrote a checkpoint every
# epoch while comparing against a monitored value up to ten epochs stale -- and
# the file we kept was epoch-59, the last one, not the best one. Validating
# every epoch and saving at validation end makes save_top_k=1 mean what it says.
#
# Monitored on part_accuracy rather than the default object_chamfer because it
# is the quantity we report: the fraction of sherds seated. Chamfer would rank
# checkpoints acceptably here (same val set, so its size-dependence is a
# constant) but it is not the thing being bought.
python train.py \
    data=main/bbad_vessels_v3 \
    data_root="$DATA_ROOT" \
    "${LORA_ON[@]}" \
    model.encoder_ckpt="$CKPT" \
    model.flow_model_ckpt="$CKPT" \
    model.optimizer.lr=2e-5 \
    trainer.max_epochs=20 \
    ++trainer.check_val_every_n_epoch=1 \
    ++trainer.callbacks.0.monitor=val/overall/part_accuracy \
    ++trainer.callbacks.0.mode=max \
    ++trainer.callbacks.0.save_on_train_epoch_end=false \
    log_dir="$OUT_ROOT" || { echo "training failed"; exit 1; }

# save_top_k=1 leaves exactly one epoch-*.ckpt: the best epoch on
# val/overall/part_accuracy. last.ckpt is the FINAL epoch and is not it -- the
# previous run selected by modification time and so selected last.ckpt.
BEST=$(find "$OUT_ROOT" -name "epoch-*.ckpt" | sort)
N_BEST=$(echo "$BEST" | grep -c . || true)
[ "$N_BEST" = "1" ] || { echo "expected exactly one epoch-*.ckpt, found $N_BEST:"; echo "$BEST"; exit 1; }
echo "best-on-validation checkpoint: $BEST"
echo "(final epoch, kept for reference only: $OUT_ROOT/last.ckpt)"

echo ""
echo "### 5/6  GATE: did anything move that was supposed to be frozen? ###"
# Run BEFORE the nine evaluation arms, not after. Last time this same comparison
# was made only once the results looked odd, by which point the A100 hours and
# the write-up had already been spent on numbers that meant nothing. If a frozen
# weight moved, the on/off comparison is meaningless and evaluating it is waste.
python scripts/diff_adapter_checkpoint.py     --base "$CKPT" --trained "$BEST" --fail-on-frozen     || { echo "the freeze leaked again -- stopping before evaluation"; exit 1; }

echo ""
echo "### 6/6  three arms: adapter ON, adapter OFF, untouched baseline ###"
# The OFF arm is the same file with the adapter disabled. It should reproduce
# the baseline exactly; if it does not, the switch is broken and every ON number
# is uninterpretable. It is a control, not a result.
run_arm () {
    NAME=$1; C=$2; shift 2
    LORA_ARGS=("$@")

    echo ""
    echo "########## $NAME : the VESSEL val set it was trained against ##########"
    # New in v3, and the arm the previous run was missing. Without the base
    # model's score on these same 117 held-out vessels there is no way to
    # separate "the adapter learned this material" from "this material is easy".
    # Shapes here are disjoint from training, so it is held-out; it is NOT
    # independent of the adapter's domain, and must not be quoted as a
    # generalisation result. That is what the three arms below are for.
    python sample.py ckpt_path="$C" data_root="$DATA_ROOT" \
        data=main/bbad_vessels_v3 data.batch_size=4 \
        "${LORA_ARGS[@]}" \
        log_dir="$LOG_ROOT/lorav3_vessels_${NAME}_${SLURM_JOB_ID}" \
        model.n_generations=3 || true

    echo ""
    echo "########## $NAME : WORN sweep (the gain we are buying) ##########"
    python sample.py ckpt_path="$C" data_root="$DATA_ROOT" \
        data=zeroshot/erosion_sweep data.batch_size=4 \
        "${LORA_ARGS[@]}" \
        log_dir="$LOG_ROOT/lorav3_sweep_${NAME}_${SLURM_JOB_ID}" \
        model.n_generations=3 || true
    python scripts/analyze_erosion_sweep.py \
        --results-dir "$LOG_ROOT/lorav3_sweep_${NAME}_${SLURM_JOB_ID}/results" \
        --calibration "$DATA_ROOT/erosion_sweep.calibration.json" || true

    echo ""
    echo "########## $NAME : FRESH objects (what we might be paying with) ##########"
    python sample.py ckpt_path="$C" data_root="$DATA_ROOT" \
        data=zeroshot/real_heldout_norm data.batch_size=4 \
        "${LORA_ARGS[@]}" \
        log_dir="$LOG_ROOT/lorav3_fresh_${NAME}_${SLURM_JOB_ID}" \
        model.n_generations=3 || true

    echo ""
    echo "########## $NAME : THE JUGLET, against the hand reassembly ##########"
    # THE ARM THAT ACTUALLY DECIDES THIS. Everything else is simulated
    # fracture: the vessel val set is Breaking Bad, the erosion sweep is real
    # pots with abrasion applied by us, the fresh set is real pots that were
    # never broken in the ground. This is the one real archaeological vessel,
    # worn by burial, broken by accident, with an answer key a conservator
    # produced by hand. There is no second one: fantastic_breaks and
    # fractura_real are not built on Spartan, so n = 1 object, permanently.
    #
    # Read it knowing a piece is MISSING: leaving that gap open is correct,
    # and any metric that rewards contact everywhere will punish the right
    # answer.
    #
    # 20 GENERATIONS, NOT 5. Nine fragments means every part-accuracy score
    # is a multiple of 1/9 = 0.111, and the entire spread between the three
    # arms last time (0.511 / 0.622 / 0.644, job 29623885) was one to two
    # sherds. Five draws cannot separate that from luck. Twenty gives a
    # distribution per arm instead of a number, and sample.py already writes
    # one json per generation, so the spread is readable afterwards without
    # any further code. The cost is minutes on a ten-hour allocation.
    RUN="$LOG_ROOT/lorav3_juglet_${NAME}_${SLURM_JOB_ID}"
    python sample.py ckpt_path="$C" data_root="$DATA_ROOT" \
        data=zeroshot/juglet_gt data.batch_size=1 \
        "${LORA_ARGS[@]}" \
        log_dir="$RUN" \
        model.n_generations=20 \
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
echo "### collect the renders ###"
find "$LOG_ROOT" -path "*lorav3_juglet_*_${SLURM_JOB_ID}*" \
    \( -name "*.png" -o -name "*.npz" \) | sort

echo ""
echo "=== Finished at $(date) ==="
echo "Read it as a trade, not a score. The worn sweep and the Juglet are what we"
echo "are buying; the fresh run is what we might be paying with. adapter_off"
echo "should match baseline -- stage 5 is what makes that claim safe to make,"
echo "and if it still does not match, the difference is in sampling, not weights."
echo ""
echo "LOOK AT THE JUGLET RENDERS BEFORE WRITING ANY OF THIS UP. Part accuracy"
echo "read 0.80 on an assembly that was visibly scattered."
