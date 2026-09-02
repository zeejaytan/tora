#!/bin/bash
#SBATCH --job-name=tora-ceramics-arms
#SBATCH --partition=gpu-a100-short
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_ceramics_arms_%j.log

set -euo pipefail

# EIGHT REAL BROKEN POTS. The second real-fracture test, after the Juglet.
#
# Fractura's ceramics subset (GARF, ICCV 2025) is eight vessels that were
# physically broken and scanned with an Artec Spider at 0.05 mm, not shattered
# in software: blue_pot, galli_pot, pink_bowl, plate and narrow_bottle1-4, 3 to
# 12 fragments each. Real fracture surfaces, which is the exact thing the
# Breaking Bad training data does not have.
#
# WHAT IT DOES AND DOES NOT SETTLE. These are modern breaks with no burial
# wear, so they test the fracture surface and nothing else; the Juglet remains
# the only object that is both really broken and really worn. The GARF paper
# does not document how the ground-truth poses were established, but the
# conservator has confirmed these eight are in their correct assembly, so a bad
# score here is the method failing, not the answer key being wrong.
#
# Data lives in dataset/ceramics.hdf5, a symlink onto the 3 GB
# fractura_real.hdf5. Load it by that name: the loader matches the file stem
# against a key inside the file, and "fractura_real" is not one of them.
#
# The config is left exactly as prior runs used it (anchor-fixed, min 3 / max
# 12 parts, all eight pots pass) so these numbers sit next to jobs 24342475 and
# 24343146 without adjustment.
#
# Usage:
#   ARMS=baseline sbatch scripts/hpc/eval_ceramics_arms.slurm
#   sbatch --dependency=afterok:<lora job> scripts/hpc/eval_ceramics_arms.slurm
#   TRAINED_CKPT=/path/to/epoch-N.ckpt sbatch scripts/hpc/eval_ceramics_arms.slurm

echo "=== ceramics arms started at $(date) on $(hostname) ==="
nvidia-smi | head -15 || true

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
ENV_PREFIX=$TORA_ROOT/envs/tora
DATA_ROOT=$TORA_ROOT/dataset
LOG_ROOT=$TORA_ROOT/eval_runs
CKPT=$TORA_ROOT/checkpoints/bbad_everyday_cka.ckpt
DRAWS=${DRAWS:-10}
ARMS=${ARMS:-"adapter_on adapter_off baseline"}

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

for f in "$DATA_ROOT/ceramics.hdf5" "$CKPT"; do
    [ -e "$f" ] || { echo "missing: $f"; exit 1; }
done

# Only go looking for the adapter if an arm actually needs it, so the baseline
# can be scored before the training run has finished.
if [[ "$ARMS" == *adapter* ]] && [ -z "${TRAINED_CKPT:-}" ]; then
    # save_top_k=1 leaves exactly one epoch-*.ckpt -- the best epoch on
    # validation, not the last. More than one means the checkpointing changed
    # and picking by date would silently take the final epoch again, which is
    # what made job 29623885 uninterpretable. Stop rather than guess.
    FOUND=$(find "$TORA_ROOT/output" -path "*lora_vessels_v3_*" -name "epoch-*.ckpt" | sort)
    N=$(echo "$FOUND" | grep -c . || true)
    [ "$N" = "1" ] || { echo "expected exactly one v3 adapter checkpoint, found $N:"; echo "$FOUND"; exit 1; }
    TRAINED_CKPT="$FOUND"
    echo "adapter under test: $TRAINED_CKPT"
fi
echo "untouched baseline: $CKPT"
echo "draws per pot:      $DRAWS"
echo "arms:               $ARMS"

run_arm () {
    NAME=$1; C=$2; shift 2
    echo ""
    echo "########## $NAME : $DRAWS draws on each of the 8 pots ##########"
    python sample.py ckpt_path="$C" data_root="$DATA_ROOT" \
        data=zeroshot/fractura/ceramics data.batch_size=8 data.num_workers=4 \
        "$@" \
        log_dir="$LOG_ROOT/ceramarm_${NAME}_${SLURM_JOB_ID}" \
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

# adapter_off is NOT the untouched baseline: the pose head was retrained and
# has no off switch. Three arms, not two.
DONE_DIRS=()
for ARM in $ARMS; do
    case "$ARM" in
        adapter_on)  run_arm adapter_on  "$TRAINED_CKPT" "${LORA_ON[@]}" lora.active=true ;;
        adapter_off) run_arm adapter_off "$TRAINED_CKPT" "${LORA_ON[@]}" lora.active=false ;;
        baseline)    run_arm baseline    "$CKPT"         lora.enabled=false ;;
        *) echo "unknown arm: $ARM"; exit 1 ;;
    esac
    DONE_DIRS+=("$LOG_ROOT/ceramarm_${ARM}_${SLURM_JOB_ID}")
done

echo ""
echo "### pot by pot, in fragments seated ###"
python scripts/summarise_ceramics_arms.py --runs "${DONE_DIRS[@]}" || true

echo ""
echo "### renders ###"
find "$LOG_ROOT" -path "*ceramarm_*_${SLURM_JOB_ID}*" \
    \( -name "*.png" -o -name "*.npz" \) | sort | head -60

echo ""
echo "=== Finished at $(date) ==="
echo "Do not quote object_chamfer or translation_error raw: they are in each"
echo "pot's own units and the scales here run near 77. The summariser prints"
echo "offset as a fraction of the pot instead."
