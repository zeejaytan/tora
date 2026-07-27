#!/bin/bash
#SBATCH --job-name=tora-piececount
#SBATCH --partition=gpu-a100-short
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_piececount_%j.log

set -euo pipefail

# C1 — piece-count sweep on a REAL, valid-GT object (galli_pot, 10 pieces).
# Tests H2: is TORA's mating signal pairwise, or does it need multi-piece
# context? Resolves the open contradiction (weak isolated-pair behaviour vs
# competent whole-object assembly). Real GT => no pseudo-GT caveat.

echo "=== TORA piece-count sweep started at $(date) on $(hostname) ==="
nvidia-smi | head -15 || true

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
REPO_DIR=$TORA_ROOT/repo
ENV_PREFIX=$TORA_ROOT/envs/tora
DATA_ROOT=$TORA_ROOT/dataset
LOG_ROOT=$TORA_ROOT/eval_runs
BASE_CKPT=$TORA_ROOT/checkpoints/bbad_everyday_cka.ckpt

module purge
module load Anaconda3/2024.02-1
module load CUDA/12.4.1
module load cuDNN/9.6.0.74-CUDA-12.4.1
eval "$(conda shell.bash hook)"
conda activate "$ENV_PREFIX"
export TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0"
export HF_HOME=$TORA_ROOT/.hf-cache
cd "$REPO_DIR"

echo ""
echo "### Build piece-count sweep (galli_pot, k=2,3,4,6,8,10) ###"
python scripts/build_piececount_sweep.py \
    --src "$DATA_ROOT/real_heldout_norm.hdf5" \
    --src-dataset real_heldout_norm \
    --object galli_pot \
    --ks 2,3,4,6,8,10 \
    --replicates 5 \
    --out-hdf5 "$DATA_ROOT/piececount_sweep.hdf5"

echo ""
echo "### Evaluate sweep [baseline] ###"
python sample.py \
    ckpt_path="$BASE_CKPT" \
    data_root="$DATA_ROOT" \
    data=zeroshot/piececount_sweep \
    data.batch_size=4 \
    data.num_workers=4 \
    log_dir="$LOG_ROOT/piececount_baseline_${SLURM_JOB_ID}" \
    model.n_generations=3

echo ""
echo "### Placement rate vs piece count ###"
python scripts/analyze_piececount_sweep.py \
    --results-dir "$LOG_ROOT/piececount_baseline_${SLURM_JOB_ID}/results" \
    --label "galli_pot sweep [baseline]" || true

echo ""
echo "=== Finished at $(date) ==="
