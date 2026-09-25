#!/usr/bin/env bash
# U10 tickets 03-04: the steps run inside a HELD allocation, one call per step.
#
# WHY A STEP SCRIPT AND NOT A JOB. The first contact with the U10 files is the part
# most likely to need a fix and a retry (a key the datamodule refuses, memory at 36
# sherds x batch 8), and each retry through `sbatch` is a queue wait. So the steps are
# pushed into one held node with the umbrella's gpu_session.sh:
#
#   GPU_SESSION_STATE=~/.tora_gpu_session GPU_SESSION_LOG_DIR=$TORA_ROOT/logs \
#       ./gpu_session.sh run 'bash $TORA_ROOT/repo/scripts/hpc/u10_session.sh smoke ceiling'
#
# Steps, in ticket 03's order:
#   freeze            batch norm cannot drift under the freeze (seconds)
#   gate              the adapter switches off cleanly on the untouched checkpoint
#   smoke ARM         8 batches, pose head FROZEN, own-place logged, reload through
#                     sample.py, then the STRICT weight diff must pass
#   leak ARM          the same 8 batches with the pose head TRAINABLE; the strict diff
#                     must FAIL. Proves the gate can see a head that moved, which the old
#                     --fail-on-frozen could not
#   epoch ARM         one full pass over the 349 breakages, timed, with GPU memory peak
#   train ARM [EP]    ticket 04: EP passes (default 20), choosing on own-place (solid)
#   baseline ARM      the untouched model's score on the same choosing set (lr 0)
#
# Ticket 06 (why the adapter hurts placement):
#   forget            untouched vs ticket 04's ceiling last.ckpt on Breaking Bad
#                     everyday validation (every n-th breakage, fixed), own place
#   noalign ARM [EP]  ticket 04's recipe with the alignment term off (repa_stop=0)
#   noalign_head ARM [EP]  the same, with the pose head trained too (GARF-like)
#
# Every step appends its ending to $TORA_ROOT/logs/job_status.log (docs/agents/slurm.md:
# trust the disk, not the watch) and writes its full output to $TORA_ROOT/logs/u10_*.log.
set -uo pipefail

STEP="${1:?step: freeze|gate|smoke|leak|epoch|train|baseline|forget|render|noalign|noalign_head|freshval}"
ARM="${2:-ceiling}"
EPOCHS="${3:-20}"
# Ticket 08 adds pooled (generic + ceiling), worn and noise (write_u10_worn.py).
case "$ARM" in ceiling|generic|pooled|worn|noise) ;;
  *) echo "arm must be ceiling, generic, pooled, worn or noise"; exit 2 ;; esac

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
DATA_ROOT=$TORA_ROOT/dataset
LOG_ROOT=$TORA_ROOT/eval_runs
STATUS_DIR=$TORA_ROOT/logs
CKPT=$TORA_ROOT/checkpoints/bbad_everyday_cka.ckpt
TAG="u10_${STEP}_${ARM}_${SLURM_JOB_ID:-nojob}_$(date +%H%M%S)"
OUT=$TORA_ROOT/output/$TAG
mkdir -p "$STATUS_DIR"
exec > >(tee -a "$STATUS_DIR/$TAG.log") 2>&1
trap 'rc=$?; echo "$(date -u +%FT%TZ) job ${SLURM_JOB_ID:-nojob} step $TAG exit $rc" >> "$STATUS_DIR/job_status.log"' EXIT

# The wear v3 recipe with ONE change: train_head=false, stated here and never left to
# the train.yaml default (true). U10's adapter must be the only thing that moves, so
# that "adapter off" is exactly the untouched model (ticket 03).
LORA=(lora.enabled=true lora.r=128 lora.alpha=256 lora.dropout=0.1 lora.last_n_blocks=6)
HEAD_FROZEN=(lora.train_head=false)
HEAD_TRAINS=(lora.train_head=true)

module purge
module load Anaconda3/2024.02-1 CUDA/12.4.1 cuDNN/9.6.0.74-CUDA-12.4.1
eval "$(conda shell.bash hook)"
conda activate "$TORA_ROOT/envs/tora"
export TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0"
export HF_HOME=$TORA_ROOT/.hf-cache
export WANDB_MODE=offline
cd "$TORA_ROOT/repo"
echo "=== $TAG on $(hostname) at $(date), repo $(git rev-parse --short HEAD) ==="

if [ "$ARM" = pooled ]; then FILES=("$DATA_ROOT/u10_generic.hdf5" "$DATA_ROOT/u10_ceiling.hdf5")
else FILES=("$DATA_ROOT/u10_$ARM.hdf5"); fi
for f in "${FILES[@]}" "$CKPT"; do
    [ -f "$f" ] || { echo "missing: $f"; exit 1; }
done

# Train with the choosing score on, validating every pass, keeping the pass with the
# most sherds in their own place on the solid sherds (what could be glued).
train() {  # train LOG_DIR HEAD_ARGS... -- EXTRA...
    local dir="$1"; shift
    python train.py \
        data=main/u10_$ARM \
        data_root="$DATA_ROOT" \
        "${LORA[@]}" "$@" \
        model.encoder_ckpt="$CKPT" \
        model.flow_model_ckpt="$CKPT" \
        'model.extra_metrics=[own_place]' \
        model.optimizer.lr="${LR:-2e-5}" \
        ++trainer.check_val_every_n_epoch=1 \
        ++trainer.callbacks.0.monitor=val/overall/own_place_solid \
        ++trainer.callbacks.0.mode=max \
        ++trainer.callbacks.0.save_on_train_epoch_end=false \
        log_dir="$dir"
}

gpu_peak() {  # sample GPU memory every 5 s in the background; print the peak on exit
    ( peak=0; while sleep 5; do
        m=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1)
        [ "${m:-0}" -gt "$peak" ] && peak=$m && echo "$peak" > "$OUT.gpu_peak_mib"
      done ) &
    GPU_WATCH=$!
}

case "$STEP" in
  freeze)
    python scripts/test_freeze_norm_stats.py ;;

  gate)
    python scripts/verify_lora_reversible.py --ckpt "$CKPT" ;;

  smoke)
    train "$OUT" "${HEAD_FROZEN[@]}" trainer.max_epochs=1 \
        ++trainer.limit_train_batches=8 ++trainer.limit_val_batches=4 \
        || { echo "smoke training failed"; exit 1; }
    SMOKE_CKPT="$OUT/last.ckpt"
    [ -f "$SMOKE_CKPT" ] || { echo "smoke produced no last.ckpt"; exit 1; }
    python sample.py ckpt_path="$SMOKE_CKPT" data_root="$DATA_ROOT" \
        data=zeroshot/juglet_gt data.batch_size=1 \
        "${LORA[@]}" "${HEAD_FROZEN[@]}" lora.active=true \
        model.n_generations=1 ++trainer.limit_test_batches=1 \
        log_dir="$LOG_ROOT/$TAG" \
        || { echo "adapter did not reload"; exit 1; }
    python scripts/diff_adapter_checkpoint.py --base "$CKPT" --trained "$SMOKE_CKPT" --strict \
        || { echo "STRICT diff failed with the head frozen -- something besides the adapter moved"; exit 1; }
    echo "SMOKE PASS: trains with the head frozen, reloads, and only the adapter moved" ;;

  leak)
    train "$OUT" "${HEAD_TRAINS[@]}" trainer.max_epochs=1 \
        ++trainer.limit_train_batches=8 ++trainer.limit_val_batches=1 \
        || { echo "leak run failed to train"; exit 1; }
    if python scripts/diff_adapter_checkpoint.py --base "$CKPT" --trained "$OUT/last.ckpt" --strict; then
        echo "LEAK CHECK FAILED: the head trained and the strict gate did not notice"; exit 1
    fi
    echo "LEAK CHECK PASS: a trained head is caught by the strict gate" ;;

  epoch)
    gpu_peak
    t0=$(date +%s)
    train "$OUT" "${HEAD_FROZEN[@]}" trainer.max_epochs=1 || { kill $GPU_WATCH; echo "epoch failed"; exit 1; }
    kill $GPU_WATCH 2>/dev/null
    echo "ONE PASS ($ARM): $(( $(date +%s) - t0 )) s wall incl. validation and startup;" \
         "GPU peak $(cat "$OUT.gpu_peak_mib" 2>/dev/null || echo '?') MiB" ;;

  baseline)
    # The untouched model's choosing score, the yardstick every pass is read against.
    # Added after the ceiling run chose pass 0 and fell from 0.893 to 0.769 by pass 5.
    # lr=0 with the adapter's B still at its zero start is the untouched model exactly
    # (gate step: difference 0), and the adapter path keeps freeze_norm_stats on, which
    # lora.enabled=false would not. One training batch at lr 0, then the full validation.
    LR=0 train "$OUT" "${HEAD_FROZEN[@]}" trainer.max_epochs=1 ++trainer.limit_train_batches=1 \
        || { echo "baseline validation failed"; exit 1; }
    python scripts/diff_adapter_checkpoint.py --base "$CKPT" --trained "$OUT/last.ckpt" --strict \
        || { echo "lr=0 run still moved weights"; exit 1; }
    echo "BASELINE ($ARM): untouched model on this arm's choosing set, see val/overall/own_place_solid above" ;;

  train)
    train "$OUT" "${HEAD_FROZEN[@]}" trainer.max_epochs="$EPOCHS" || { echo "training failed"; exit 1; }
    BEST=$(find "$OUT" -name "epoch-*.ckpt" | sort)
    [ "$(echo "$BEST" | grep -c .)" = "1" ] || { echo "expected one epoch-*.ckpt: $BEST"; exit 1; }
    python scripts/diff_adapter_checkpoint.py --base "$CKPT" --trained "$BEST" --strict \
        || { echo "STRICT diff failed on the chosen checkpoint"; exit 1; }
    echo "TRAINED ($ARM): chosen $BEST" ;;

  forget)
    # Suspect 2: did training on 20 juglets wear away skill on ordinary objects?
    # Same fixed subset for both (limit_val_samples takes every n-th breakage).
    EVERY=(data=main/bbad_everyday data_root="$DATA_ROOT" data.batch_size=32 data.num_workers=8
           data.limit_val_samples="${EVERYDAY_N:-480}" 'model.extra_metrics=[own_place]' mode=validate)
    # ADAPTER= another adapter checkpoint (head frozen); SKIP_UNTOUCHED=1 when the
    # untouched score on this subset is already recorded (ticket 06: .920).
    CEIL=${ADAPTER:-$TORA_ROOT/output/u10_train_ceiling_31200602_163555/last.ckpt}
    [ -f "$DATA_ROOT/everyday.hdf5" ] && [ -f "$CEIL" ] || { echo "missing everyday or $CEIL"; exit 1; }
    if [ -z "${SKIP_UNTOUCHED:-}" ]; then
        echo "--- untouched ---"
        python sample.py ckpt_path="$CKPT" lora.enabled=false "${EVERY[@]}" log_dir="$OUT/untouched" \
            || { echo "untouched validation failed"; exit 1; }
    fi
    echo "--- adapter $CEIL ---"
    python sample.py ckpt_path="$CEIL" "${LORA[@]}" "${HEAD_FROZEN[@]}" lora.active=true \
        "${EVERY[@]}" log_dir="$OUT/ceiling" \
        || { echo "ceiling validation failed"; exit 1; }
    echo "FORGET done: compare VALIDATE val/overall/own_place_solid above" ;;

  render)
    # The lead's debugging look (ticket 06): every n-th practice breakage, one draw,
    # untouched / ticket 04's ceiling / ADAPTER, same seed, mitsuba 512.
    VIS=(data=main/u10_$ARM data_root="$DATA_ROOT" data.batch_size=1 data.num_workers=8
         data.limit_val_samples="${RENDER_N:-10}" model.n_generations=1
         "+visualizer._target_=tora.visualizer.FlowVisualizationCallback" "+visualizer.renderer=mitsuba"
         "+visualizer.image_size=512" "+visualizer.max_samples_per_batch=1" "+visualizer.center_points=true"
         "+visualizer.save_trajectory=false" "+visualizer.save_procrustes_assembly=true")
    [ "$ARM" = ceiling ] || { echo "render compares against the ceiling run only"; exit 2; }
    ORIG=$TORA_ROOT/output/u10_train_ceiling_31200602_163555/last.ckpt
    python sample.py ckpt_path="$CKPT" lora.enabled=false "${VIS[@]}" log_dir="$OUT/untouched" \
        || { echo "untouched render failed"; exit 1; }
    python sample.py ckpt_path="$ORIG" "${LORA[@]}" "${HEAD_FROZEN[@]}" lora.active=true "${VIS[@]}" \
        log_dir="$OUT/original" || { echo "original render failed"; exit 1; }
    python sample.py ckpt_path="${ADAPTER:?ADAPTER=checkpoint}" "${LORA[@]}" "${HEAD_FROZEN[@]}" \
        lora.active=true "${VIS[@]}" log_dir="$OUT/adapter" || { echo "adapter render failed"; exit 1; }
    echo "RENDER done: $OUT/{untouched,original,adapter}/visualizations" ;;

  noalign|noalign_head)
    # Suspect 1 (and 3): ticket 04's recipe scored on placement alone. repa_stop=0
    # switches alignment off after the first batch (on_train_batch_end).
    if [ "$STEP" = noalign ]; then HEAD=("${HEAD_FROZEN[@]}"); else HEAD=("${HEAD_TRAINS[@]}"); fi
    train "$OUT" "${HEAD[@]}" model.repa_stop=0 trainer.max_epochs="$EPOCHS" \
        || { echo "training failed"; exit 1; }
    # Head frozen: only the adapter may move. Head trained: the diff must fail, and
    # its listing is what records which tensors moved.
    python scripts/diff_adapter_checkpoint.py --base "$CKPT" --trained "$OUT/last.ckpt" --strict
    echo "$STEP ($ARM) diff exit $? (noalign expects 0, noalign_head expects non-zero)"
    echo "TRAINED $STEP ($ARM): $OUT" ;;

  freshval)
    # Ticket 08's guard: one fresh yardstick for every arm. Worn and noise validate on
    # their own worn copies while training, so each arm's last.ckpt (ADAPTER=) -- or the
    # untouched model, ADAPTER unset -- is scored again on u10_pooled's val set.
    FV=(data=main/u10_pooled data_root="$DATA_ROOT" data.batch_size=8 data.num_workers=8
        'model.extra_metrics=[own_place]' mode=validate)
    if [ -n "${ADAPTER:-}" ]; then
        python sample.py ckpt_path="$ADAPTER" "${LORA[@]}" "${HEAD_FROZEN[@]}" lora.active=true \
            "${FV[@]}" log_dir="$OUT" || { echo "freshval failed"; exit 1; }
    else
        python sample.py ckpt_path="$CKPT" lora.enabled=false "${FV[@]}" log_dir="$OUT" \
            || { echo "freshval (untouched) failed"; exit 1; }
    fi
    echo "FRESHVAL ($ARM, ${ADAPTER:-untouched}): see VALIDATE val/overall/own_place_solid above" ;;

  *) echo "unknown step $STEP"; exit 2 ;;
esac
