#!/bin/bash
#SBATCH --job-name=tora-anchor-2x2
#SBATCH --partition=gpu-a100-short
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_anchor2x2_%j.log

set -euo pipefail

# ROOT-CAUSE TEST — is the Juglet failure caused by the anchor setup rather
# than by the pot?
#
# Discovered confound: the Juglet is the ONLY evaluation that ran with
# data.anchor_free=true. Every case where TORA looked competent (real held-out
# objects, the piece-count sweep, both pairwise oracles) used false. Worse, the
# Juglet run paired data.anchor_free=true with model.anchor_free=false -- a
# combination that does not match how the checkpoint was trained, where the
# anchor fragment's input IS its target. Under the Juglet setting the anchor's
# input is re-centred while the model still pins its target to the stored pose,
# so the one fragment meant to be the fixed reference is described inconsistently.
#
# 2x2, so the pot and the setting are separated:
#   A  Juglet          + anchor_free=false  <- Juglet under the WORKING setting
#   B  Juglet          + anchor_free=true   <- reproduce the known failure
#   C  real held-out   + anchor_free=true   <- do GOOD objects break under it?
#   D  real held-out   + anchor_free=false  <- known-good control
#
# If A yields a vessel and/or C collapses, the cause is the anchor setup, not
# the Juglet. If A still fails while C stays fine, the cause is the pot itself
# (wear / piece count) and the anchor setting is exonerated.

echo "=== anchor-mode 2x2 started at $(date) on $(hostname) ==="

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
ENV_PREFIX=$TORA_ROOT/envs/tora
DATA_ROOT=$TORA_ROOT/dataset
LOG_ROOT=$TORA_ROOT/eval_runs
CKPT=$TORA_ROOT/checkpoints/bbad_everyday_cka.ckpt

module purge
module load Anaconda3/2024.02-1
module load CUDA/12.4.1
module load cuDNN/9.6.0.74-CUDA-12.4.1
eval "$(conda shell.bash hook)"
conda activate "$ENV_PREFIX"
export TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0"
export HF_HOME=$TORA_ROOT/.hf-cache
cd "$TORA_ROOT/repo"

VIS=(
  "+visualizer._target_=tora.visualizer.FlowVisualizationCallback"
  "+visualizer.renderer=mitsuba"
  "+visualizer.image_size=512"
  "+visualizer.max_samples_per_batch=1"
  "+visualizer.center_points=true"
  "+visualizer.save_trajectory=false"
  "+visualizer.save_procrustes_assembly=true"
  "+visualizer.save_assembly_npz=true"
)

# --- Juglet under both settings (visual judgement; scores are meaningless here) ---
for AF in false true; do
    echo ""
    echo "########## JUGLET  data.anchor_free=$AF ##########"
    python sample.py \
        ckpt_path="$CKPT" \
        data_root="$DATA_ROOT" \
        data=zeroshot/juglet_norm \
        data.anchor_free=$AF \
        log_dir="$LOG_ROOT/anchor2x2_juglet_af${AF}_${SLURM_JOB_ID}" \
        model.n_generations=3 \
        "${VIS[@]}"
done

# --- Real held-out objects under both settings (VALID ground truth => scores mean something) ---
for AF in true false; do
    echo ""
    echo "########## REAL HELD-OUT  data.anchor_free=$AF ##########"
    python sample.py \
        ckpt_path="$CKPT" \
        data_root="$DATA_ROOT" \
        data=zeroshot/real_heldout_norm \
        data.anchor_free=$AF \
        log_dir="$LOG_ROOT/anchor2x2_heldout_af${AF}_${SLURM_JOB_ID}" \
        model.n_generations=3
done

echo ""
echo "=== Finished at $(date) ==="
echo "Judge the Juglet arms VISUALLY (no valid reference exists for it)."
echo "Judge the held-out arms NUMERICALLY (they have real ground truth)."
