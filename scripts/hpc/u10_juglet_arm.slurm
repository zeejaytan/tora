#!/bin/bash
#SBATCH --job-name=u10-juglet
#SBATCH --partition=gpu-a100-short
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
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
trap 'rc=$?; echo "$(date -u +%FT%TZ) job ${SLURM_JOB_ID:-nojob} step u10_juglet_${ARM:-?} exit $rc" >> "$STATUS_DIR/job_status.log"' EXIT

ARM="${ARM:?ARM=untouched|generic|ceiling}"
DRAWS=${DRAWS:-20}
DATA_ROOT=$TORA_ROOT/dataset
LOG_ROOT=$TORA_ROOT/eval_runs
CKPT=$TORA_ROOT/checkpoints/bbad_everyday_cka.ckpt
LORA=(lora.enabled=true lora.r=128 lora.alpha=256 lora.dropout=0.1 lora.last_n_blocks=6 lora.train_head=false)

case "$ARM" in
  untouched) C=$CKPT; ARGS=(lora.enabled=false) ;;
  generic)   C=$TORA_ROOT/output/u10_train_generic_31200602_171624/last.ckpt; ARGS=("${LORA[@]}" lora.active=true) ;;
  ceiling)   C=$TORA_ROOT/output/u10_train_ceiling_31200602_163555/last.ckpt; ARGS=("${LORA[@]}" lora.active=true) ;;
  *) echo "arm must be untouched, generic or ceiling"; exit 2 ;;
esac

module purge
module load Anaconda3/2024.02-1 CUDA/12.4.1 cuDNN/9.6.0.74-CUDA-12.4.1
eval "$(conda shell.bash hook)"
conda activate "$TORA_ROOT/envs/tora"
export TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0"
export HF_HOME=$TORA_ROOT/.hf-cache
export WANDB_MODE=offline
cd "$TORA_ROOT/repo"
echo "=== u10 juglet $ARM on $(hostname) at $(date), repo $(git rev-parse --short HEAD) ==="
echo "checkpoint: $C"

for f in "$DATA_ROOT/juglet_gt.hdf5" "$C"; do
    [ -f "$f" ] || { echo "missing: $f"; exit 1; }
done

# The gate before any draw: an adapter arm whose file moved anything but the adapter
# is not the arm it claims to be.
if [ "$ARM" != untouched ]; then
    python scripts/diff_adapter_checkpoint.py --base "$CKPT" --trained "$C" --strict \
        || { echo "STRICT diff failed on $C -- not evaluating"; exit 1; }
fi

OUT=$LOG_ROOT/u10_juglet_${ARM}_${SLURM_JOB_ID}
python sample.py ckpt_path="$C" data_root="$DATA_ROOT" \
    data=zeroshot/juglet_gt data.batch_size=1 \
    "${ARGS[@]}" \
    log_dir="$OUT" \
    model.n_generations="$DRAWS" \
    "+visualizer._target_=tora.visualizer.FlowVisualizationCallback" \
    "+visualizer.renderer=mitsuba" \
    "+visualizer.image_size=512" \
    "+visualizer.max_samples_per_batch=1" \
    "+visualizer.center_points=true" \
    "+visualizer.save_trajectory=false" \
    "+visualizer.save_procrustes_assembly=true" \
    "+visualizer.save_assembly_npz=true" \
    || { echo "sampling failed"; exit 1; }

python scripts/own_place.py --run "$OUT" --pot-mm 65 --json "$OUT/own_place.json" \
    || { echo "own-place scoring failed (the draws are kept; score on CPU)"; exit 1; }
echo "=== done $(date): $OUT ==="
