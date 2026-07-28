#!/bin/bash
#SBATCH --job-name=tora-refine
#SBATCH --partition=gpu-a100-short
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=04:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_refine_%j.log

set -euo pipefail

# S2 — "good enough, not perfect": let the rough assembly settle.
#
# Diagnosis (C2b/C3): wear destroys the fine detail saying exactly HOW two faces
# seat, while leaving the coarse signal saying WHICH fragments are neighbours.
# So the model places fragments in the right neighbourhood and never closes the
# join. This refines that rough answer by asking only that neighbours TOUCH
# without overlapping -- never that worn surfaces match point-for-point.
#
# Uses NO ground truth: neighbours come from the model's own predicted layout.
# Ground truth is touched only afterwards, to score.
#
# Test bed: the C3 erosion sweep (worn pots WITH valid ground truth), where
# seating is known to fall 0.875 fresh -> 0.524 fully worn. Success = recovering
# seating at the WORN end, which is where the deficit lives.

echo "=== S2 seating refinement started at $(date) on $(hostname) ==="

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
ENV_PREFIX=$TORA_ROOT/envs/tora
DATA_ROOT=$TORA_ROOT/dataset
LOG_ROOT=$TORA_ROOT/eval_runs
CKPT=$TORA_ROOT/checkpoints/bbad_everyday_cka.ckpt
RUN=$LOG_ROOT/refine_src_${SLURM_JOB_ID}

module purge
module load Anaconda3/2024.02-1
module load CUDA/12.4.1
module load cuDNN/9.6.0.74-CUDA-12.4.1
eval "$(conda shell.bash hook)"
conda activate "$ENV_PREFIX"
export TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0"
export HF_HOME=$TORA_ROOT/.hf-cache
cd "$TORA_ROOT/repo"

echo ""
echo "### 1/2  assemble the worn pots, exporting 3D clouds ###"
python sample.py \
    ckpt_path="$CKPT" \
    data_root="$DATA_ROOT" \
    data=zeroshot/erosion_sweep \
    data.batch_size=4 \
    data.num_workers=4 \
    log_dir="$RUN" \
    model.n_generations=3 \
    "+visualizer._target_=tora.visualizer.FlowVisualizationCallback" \
    "+visualizer.renderer=none" \
    "+visualizer.save_trajectory=false" \
    "+visualizer.save_procrustes_assembly=true" \
    "+visualizer.save_assembly_npz=true" || true

echo ""
echo "### 2/2  let the assemblies settle, then re-score ###"
python scripts/refine_seating.py \
    --clouds-dir "$RUN/clouds" \
    --iters 60 \
    --out-json "$RUN/refinement.json"

echo ""
echo "=== Finished at $(date) ==="
