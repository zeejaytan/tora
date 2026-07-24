#!/bin/bash
#SBATCH --job-name=tora-pairwise-norm
#SBATCH --partition=gpu-a100-short
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_pairwise_norm_%j.log

set -euo pipefail

# Test C1-precursor / H1-vs-H2: re-run the pairwise mating oracle on
# SCALE-NORMALIZED real pairs so part_accuracy is a valid mate/non-mate signal
# (the pre-normalization 0.5-pinned value was the absolute-threshold metric bug;
# rotation_error was already scale-invariant, so its 1.03x stands unchanged).
# Synthetic pairs are unit-normalized by construction (positive control).

echo "=== TORA normalized pairwise oracle started at $(date) on $(hostname) ==="
nvidia-smi | head -15 || true

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
REPO_DIR=$TORA_ROOT/repo
ENV_PREFIX=$TORA_ROOT/envs/tora
DATA_ROOT=$TORA_ROOT/dataset
CKPT=$TORA_ROOT/checkpoints/bbad_everyday_cka.ckpt
LOG_ROOT=$TORA_ROOT/eval_runs

module purge
module load Anaconda3/2024.02-1
module load CUDA/12.4.1
module load cuDNN/9.6.0.74-CUDA-12.4.1
eval "$(conda shell.bash hook)"
conda activate "$ENV_PREFIX"
export TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0"
export HF_HOME=$TORA_ROOT/.hf-cache
mkdir -p "$LOG_ROOT"
cd "$REPO_DIR"

echo ""
echo "### Pairwise oracle: SYNTHETIC pairs (unit-normalized control) ###"
python sample.py \
    ckpt_path="$CKPT" \
    data_root="$DATA_ROOT" \
    data=zeroshot/pairs_synth \
    data.batch_size=8 \
    data.num_workers=4 \
    log_dir="$LOG_ROOT/pairs_synth_norm_${SLURM_JOB_ID}" \
    model.n_generations=3

echo ""
echo "### Pairwise oracle: REAL pairs, SCALE-NORMALIZED ###"
python sample.py \
    ckpt_path="$CKPT" \
    data_root="$DATA_ROOT" \
    data=zeroshot/pairs_real_norm \
    data.batch_size=8 \
    data.num_workers=4 \
    log_dir="$LOG_ROOT/pairs_real_norm_${SLURM_JOB_ID}" \
    model.n_generations=3

echo ""
echo "### Join with adjacency labels (valid part_acc + rot_err separation) ###"
python scripts/analyze_pairwise_oracle.py \
    --results-dir "$LOG_ROOT/pairs_synth_norm_${SLURM_JOB_ID}/results" \
    --adjacency "$TORA_ROOT/logs_pairs_synth_adjacency.json" \
    --label "synthetic (norm control)" || true
python scripts/analyze_pairwise_oracle.py \
    --results-dir "$LOG_ROOT/pairs_real_norm_${SLURM_JOB_ID}/results" \
    --adjacency "$TORA_ROOT/logs_pairs_real_adjacency.json" \
    --label "real (scale-normalized)" || true

echo ""
echo "=== Finished at $(date) ==="
