#!/bin/bash
#SBATCH --job-name=u10-juglet
#SBATCH --partition=gpu-a100-short
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/logs/u10_juglet_%x_%j.log

# U10 ticket 05: one arm, 20 draws on the Juglet, with renders and assembly npz.
#
#   ARM=untouched sbatch scripts/hpc/u10_juglet_arm.slurm
#   ARM=generic   sbatch scripts/hpc/u10_juglet_arm.slurm
#   ARM=ceiling   sbatch scripts/hpc/u10_juglet_arm.slurm
#
# WHICH ADAPTER. The conservator's decision (2026-09-24), fixed before any Juglet draw:
# each adapter arm uses its LAST pass (last.ckpt, pass 19), not the pass ticket 04 kept.
# On the choosing vessels neither adapter beat the untouched model at any pass
# (ceiling .893 best vs .897 untouched; generic .949 vs .958), so choosing picked the
# least-changed pass. That set is too easy -- the untouched model already seats 90-96% --
# to see what U10 asks. The last pass is the adapter that actually learned the shapes.
# Declared here, so the Juglet is never what chose it.
#
# Settings are job 30130049's (ticket 01's untouched baseline): zeroshot/juglet_gt (the
# hand reassembly, never juglet_norm), batch 1, n_generations 20, mitsuba 512 renders.
# The one difference: adapter arms keep the pose head frozen (lora.train_head=false),
# matching how they were trained.
set -uo pipefail

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
STATUS_DIR=$TORA_ROOT/logs
trap 'rc=$?; echo "$(date -u +%FT%TZ) job ${SLURM_JOB_ID:-nojob} step u10_${SET:-juglet}_${ARM:-?} exit $rc" >> "$STATUS_DIR/job_status.log"' EXIT

ARM="${ARM:?ARM=untouched|generic|ceiling}"
DRAWS=${DRAWS:-20}
# SET=fractura: the eight unworn Fractura pots (scripts/make_fractura_fresh.py), same
# arms and draws, scored pot by pot. No --pot-mm: they have no measured height.
# SET=csc_whole_{clean,worn,coarsev3}: wear-beyond-juglet ticket 06 (pr-workspace, U3), the
# 21 broken CSC pots read from the CSC run that made them. No --pot-mm: it only changes the
# printed text (own_place.py mm()), seating is 7% of each pot's own size; the mm come from
# that run's copies.csv in ticket 07. --reconcile: the evaluator must agree with the scorer.
SET="${SET:-juglet}"
DATA_ROOT=$TORA_ROOT/dataset
SETARGS=(); EXTRA=()
case "$SET" in
  juglet)   DATA=zeroshot/juglet_gt;     FILE=juglet_gt.hdf5;      BATCH=1; POTMM=(--pot-mm 65) ;;
  fractura) DATA=zeroshot/fractura_fresh; FILE=fractura_fresh.hdf5; BATCH=4; POTMM=() ;;
  csc_whole_clean|csc_whole_worn|csc_whole_coarsev3)
            DATA=zeroshot/csc_whole; FILE=$SET.hdf5; BATCH=4; POTMM=()
            DATA_ROOT=/data/gpfs/projects/punim2657/CSC/runs/20261103-1446_e51a6a8_wear-copies/out
            SETARGS=("data.dataset_names=[$SET]"); EXTRA=(--reconcile) ;;
  # wear-beyond-juglet 21-23 (TORA mirrors GARF): round 2 (10-20 sherds) and round 3 (sherds
  # missing), the same files GARF read. Round 3 is scored against the whole pot's size
  # (own_place --pot-size copies.csv) and centred and scaled by the whole pot of the SAME
  # condition (WHOLEPOT, set here so the pairing cannot be got wrong), which needs PAIRED=1.
  csc_whole20_clean|csc_whole20_worn4)
            DATA=zeroshot/csc_whole; FILE=$SET.hdf5; BATCH=4; POTMM=()
            DATA_ROOT=/data/gpfs/projects/punim2657/CSC/runs/20261104-1554_cd2549b_wear-copies20/out
            SETARGS=("data.dataset_names=[$SET]"); EXTRA=(--reconcile) ;;
  csc_whole20_coarsev3_1)
            DATA=zeroshot/csc_whole; FILE=$SET.hdf5; BATCH=4; POTMM=()
            DATA_ROOT=/data/gpfs/projects/punim2657/CSC/runs/20261104-2009_551759c_wear-copies20-cv1/out
            SETARGS=("data.dataset_names=[$SET]"); EXTRA=(--reconcile) ;;
  csc_whole20miss_clean|csc_whole20miss_worn4)
            DATA=zeroshot/csc_whole; FILE=$SET.hdf5; BATCH=4; POTMM=()
            DATA_ROOT=/data/gpfs/projects/punim2657/CSC/runs/20261106-1423_46dfd26_wear-miss20/out
            SETARGS=("data.dataset_names=[$SET]")
            EXTRA=(--reconcile --pot-size "$DATA_ROOT/copies.csv")
            [ -n "${PAIRED:-}" ] || { echo "$SET needs PAIRED=1 (whole-pot frame)"; exit 2; }
            W=/data/gpfs/projects/punim2657/CSC/runs/20261104-1554_cd2549b_wear-copies20/out/csc_whole20_${SET#csc_whole20miss_}.hdf5
            [ -z "${WHOLEPOT:-}" ] || [ "$WHOLEPOT" = "$W" ] || { echo "WHOLEPOT must be $W for $SET"; exit 2; }
            WHOLEPOT=$W ;;
  *) echo "SET must be juglet, fractura, csc_whole_{clean,worn,coarsev3}, csc_whole20_{clean,worn4,coarsev3_1} or csc_whole20miss_{clean,worn4}"; exit 2 ;;
esac
# ANCHOR_FREE=true|false overrides the data config's anchor_free (pr-workspace wear-beyond-juglet
# 18b): false = the largest sherd handed over at its true pose and held there (GARF's
# random_anchor=false); true = centred, true turn kept (juglet_gt / csc_whole's setting). Unset =
# the config's own value, so no earlier run changes. Pair it with LABEL= so folders do not collide.
if [ -n "${ANCHOR_FREE:-}" ]; then
    case "$ANCHOR_FREE" in true|false) SETARGS+=("data.anchor_free=$ANCHOR_FREE") ;;
        *) echo "ANCHOR_FREE must be true or false"; exit 2 ;; esac
fi
# PAIRED=1 seeds each object's presentation (points, input turns, point order) from (draw seed,
# object name) alone (data.presentation_seed, wear-beyond-juglet 19), so every model given the
# same seed sees byte-identical inputs. Unset = as before. Pair it with LABEL=.
PAIRED="${PAIRED:-}"
# WHOLEPOT=<complete-pot HDF5> centres and scales a set with sherds missing by the WHOLE pot
# (data.whole_pot_path, wear-beyond-juglet 20); needs PAIRED=1. Unset = as before.
WHOLEPOT="${WHOLEPOT:-}"
if [ -n "$WHOLEPOT" ]; then
    [ -n "$PAIRED" ] || { echo "WHOLEPOT needs PAIRED=1"; exit 2; }
    [ -f "$WHOLEPOT" ] || { echo "missing: $WHOLEPOT"; exit 1; }
fi
LOG_ROOT=$TORA_ROOT/eval_runs
CKPT=$TORA_ROOT/checkpoints/bbad_everyday_cka.ckpt
LORA=(lora.enabled=true lora.r=128 lora.alpha=256 lora.dropout=0.1 lora.last_n_blocks=6 lora.train_head=false)

case "$ARM" in
  untouched) C=$CKPT; ARGS=(lora.enabled=false) ;;
  generic)   C=$TORA_ROOT/output/u10_train_generic_31200602_171624/last.ckpt; ARGS=("${LORA[@]}" lora.active=true) ;;
  ceiling)   C=$TORA_ROOT/output/u10_train_ceiling_31200602_163555/last.ckpt; ARGS=("${LORA[@]}" lora.active=true) ;;
  # Ticket 08's arms have no default file: ADAPTER= is required (checked below).
  pooled|worn|noise|worn_d[0-9][0-9][0-9]|worn_d[0-9][0-9][0-9]nc|noise_d[0-9][0-9][0-9]) C=${ADAPTER:?ADAPTER= is required for arm $ARM}; ARGS=("${LORA[@]}" lora.active=true) ;;
  *) echo "arm must be untouched, generic, ceiling, pooled, worn or noise"; exit 2 ;;
esac
# Ticket 07: ADAPTER= another adapter checkpoint for this arm (head frozen), LABEL= a
# tag for its output folder (e.g. noalign), so ticket 05's runs are never overwritten.
if [ -n "${ADAPTER:-}" ]; then
    [ "$ARM" != untouched ] || { echo "ADAPTER needs an adapter arm"; exit 2; }
    C=$ADAPTER
fi
LABEL="${LABEL:-}"
# Ticket 10: SEEDS="42 1 2 ..." re-runs the arm once per sampling seed. The seed picks the
# presentation (sampled points, each sherd's random input turn) as well as the starts;
# every run before ticket 10 used 42 only. 42 keeps the old folder name, others add _s<n>.
SEEDS="${SEEDS:-42}"

module purge
module load Anaconda3/2024.02-1 CUDA/12.4.1 cuDNN/9.6.0.74-CUDA-12.4.1
eval "$(conda shell.bash hook)"
conda activate "$TORA_ROOT/envs/tora"
export TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0"
export HF_HOME=$TORA_ROOT/.hf-cache
export WANDB_MODE=offline
cd "$TORA_ROOT/repo"
echo "=== u10 $SET $ARM on $(hostname) at $(date), repo $(git rev-parse --short HEAD) ==="
echo "checkpoint: $C"
echo "anchor_free override: ${ANCHOR_FREE:-none (config)}; paired presentations: ${PAIRED:-no}; whole pot: ${WHOLEPOT:-no}"

for f in "$DATA_ROOT/$FILE" "$C"; do
    [ -f "$f" ] || { echo "missing: $f"; exit 1; }
done

# The gate before any draw: an adapter arm whose file moved anything but the adapter
# is not the arm it claims to be.
if [ "$ARM" != untouched ]; then
    python scripts/diff_adapter_checkpoint.py --base "$CKPT" --trained "$C" --strict \
        || { echo "STRICT diff failed on $C -- not evaluating"; exit 1; }
fi

for S in $SEEDS; do
OUT=$LOG_ROOT/u10_${SET}_${ARM}${LABEL:+_$LABEL}$([ "$S" = 42 ] || echo "_s$S")_${SLURM_JOB_ID}
python sample.py ckpt_path="$C" data_root="$DATA_ROOT" \
    data="$DATA" data.batch_size="$BATCH" "${SETARGS[@]}" \
    "${ARGS[@]}" \
    ${PAIRED:+"++data.presentation_seed=$S"} \
    ${WHOLEPOT:+"++data.whole_pot_path=$WHOLEPOT"} \
    seed="$S" \
    log_dir="$OUT" \
    model.n_generations="$DRAWS" \
    "+visualizer._target_=tora.visualizer.FlowVisualizationCallback" \
    "+visualizer.renderer=mitsuba" \
    "+visualizer.image_size=512" \
    "+visualizer.max_samples_per_batch=$BATCH" \
    "+visualizer.center_points=true" \
    "+visualizer.save_trajectory=false" \
    "+visualizer.save_procrustes_assembly=true" \
    "+visualizer.save_assembly_npz=true" \
    || { echo "sampling failed (seed $S)"; exit 1; }

python scripts/own_place.py --run "$OUT" "${POTMM[@]}" "${EXTRA[@]}" --json "$OUT/own_place.json" \
    || { echo "own-place scoring failed (seed $S; the draws are kept; score on CPU)"; exit 1; }
done
echo "=== done $(date): seeds $SEEDS ==="
