#!/bin/bash
#SBATCH --job-name=tora-juglet-draws
#SBATCH --partition=gpu-a100
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_juglet_draws_%j.log

set -euo pipefail

# THE ONLY REAL TEST WE HAVE, DRAWN ENOUGH TIMES TO BE READ.
#
# Every other arm in this project is simulated somewhere. The vessel validation
# set is Breaking Bad -- models shattered by software. The erosion sweep is real
# pots with abrasion we applied ourselves. The fresh held-out set is real pots
# that were never broken in the ground. The Juglet is the one vessel that was
# worn by burial, broken by accident, and reassembled by hand by a conservator.
#
# It is the only such vessel, but it is no longer the only real-fracture test.
# An earlier version of this comment said fractura_real.hdf5 was "a 68-byte
# stub": it is not, and never was. It is a symlink, and ls reports a symlink's
# size as the length of the path it points at -- 68 characters. The file behind
# it is 3.0 GB and holds 8 real broken ceramic vessels, 16 bones and 3 eggs.
# Use dataset/ceramics.hdf5 (a symlink onto the same file, named so the loader
# finds the ceramics split); fractura_real.hdf5 itself has no matching
# data_split key. Those 8 pots have real fracture surfaces but no burial wear,
# and their ground-truth poses are not documented in the GARF paper -- look at
# them before scoring against them.
#
# WHY THIS JOB EXISTS AT ALL. Nine fragments means every part-accuracy score is
# a multiple of 1/9 = 0.111. The whole spread between the three arms on job
# 29623885 -- 0.511 adapter_on, 0.622 baseline, 0.644 adapter_off -- was one to
# two sherds, drawn five times each. That cannot be separated from sampling
# noise, so "the adapter hurts on the Juglet" was never actually established.
# Twenty draws per arm gives a distribution instead of a number.
#
# WHAT IT STILL CANNOT TELL YOU, and no number of draws will fix:
#
#   It is ONE POT. Twenty draws measure how consistently the model handles this
#   pot. They say nothing about the next pot. A clear result here is a lead.
#
#   A PIECE IS MISSING. The vessel is incomplete. A reconstruction that leaves
#   that gap open is CORRECT; one that closes it is wrong. Any metric rewarding
#   contact everywhere penalises the right answer, which is why the renders --
#   not the table -- are the instrument on this object.
#
#   THE ANSWER KEY WAS WRONG ONCE. Every Juglet score before the correction was
#   measured against the scan-table layout, the arrangement the sherds happened
#   to be lying in, 26 to 177 degrees from the real assembly. This uses
#   zeroshot/juglet_gt, built from the hand reassembly. Never juglet_norm.
#
# Usage, after the adapter run has finished:
#   TRAINED_CKPT=/path/to/epoch-N.ckpt sbatch scripts/hpc/juglet_draws.slurm
# or let it find the newest v3 adapter on its own.

echo "=== juglet draws started at $(date) on $(hostname) ==="
nvidia-smi | head -15 || true

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
ENV_PREFIX=$TORA_ROOT/envs/tora
DATA_ROOT=$TORA_ROOT/dataset
LOG_ROOT=$TORA_ROOT/eval_runs
CKPT=$TORA_ROOT/checkpoints/bbad_everyday_cka.ckpt
DRAWS=${DRAWS:-20}

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

# The adapter to test. save_top_k=1 leaves exactly one epoch-*.ckpt in the
# training output -- the best epoch on validation, not the last. If there is
# more than one, something changed in the checkpointing and picking by date
# would silently select the final epoch again, which is the error that made
# job 29623885 uninterpretable. So stop instead of guessing.
if [ -z "${TRAINED_CKPT:-}" ]; then
    FOUND=$(find "$TORA_ROOT/output" -path "*lora_vessels_v3_*" -name "epoch-*.ckpt" | sort)
    N=$(echo "$FOUND" | grep -c . || true)
    [ "$N" = "1" ] || { echo "expected exactly one v3 adapter checkpoint, found $N:"; echo "$FOUND"; exit 1; }
    TRAINED_CKPT="$FOUND"
fi
for f in "$DATA_ROOT/juglet_gt.hdf5" "$CKPT" "$TRAINED_CKPT"; do
    [ -f "$f" ] || { echo "missing: $f"; exit 1; }
done
echo "adapter under test: $TRAINED_CKPT"
echo "untouched baseline: $CKPT"
echo "draws per arm:      $DRAWS"

run_arm () {
    NAME=$1; C=$2; shift 2
    echo ""
    echo "########## $NAME : $DRAWS draws on the Juglet ##########"
    python sample.py ckpt_path="$C" data_root="$DATA_ROOT" \
        data=zeroshot/juglet_gt data.batch_size=1 \
        "$@" \
        log_dir="$LOG_ROOT/jugdraw_${NAME}_${SLURM_JOB_ID}" \
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

# adapter_off is NOT the untouched baseline: the pose head was retrained and has
# no off switch. Three arms, not two.
run_arm adapter_on  "$TRAINED_CKPT" "${LORA_ON[@]}" lora.active=true
run_arm adapter_off "$TRAINED_CKPT" "${LORA_ON[@]}" lora.active=false
run_arm baseline    "$CKPT"         lora.enabled=false

echo ""
echo "### the spread, in sherds ###"
python scripts/summarise_juglet_draws.py \
    --runs "$LOG_ROOT/jugdraw_adapter_on_${SLURM_JOB_ID}" \
           "$LOG_ROOT/jugdraw_adapter_off_${SLURM_JOB_ID}" \
           "$LOG_ROOT/jugdraw_baseline_${SLURM_JOB_ID}" || true

echo ""
echo "### renders, one per draw ###"
find "$LOG_ROOT" -path "*jugdraw_*_${SLURM_JOB_ID}*" \
    \( -name "*.png" -o -name "*.npz" \) | sort

echo ""
echo "=== Finished at $(date) ==="
echo "LOOK AT THE RENDERS. On this pot part accuracy once read 0.80 on an"
echo "assembly that was visibly scattered, and a missing piece means the"
echo "correct reconstruction leaves a gap that contact-rewarding metrics"
echo "will mark down. The table ranks; the pictures decide."
