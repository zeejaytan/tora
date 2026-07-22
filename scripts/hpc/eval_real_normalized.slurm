#!/bin/bash
#SBATCH --job-name=tora-eval-norm
#SBATCH --partition=gpu-a100-short
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_eval_norm_%j.log

set -euo pipefail

echo "=== CORRECTED eval on scale-normalized real data, started $(date) on $(hostname) ==="
echo "Rationale: real HDF5s were in raw scan units (max|v| 21-297) while synthetic is"
echo "unit-scale (max|v|=0.5). Evaluator rescales by 'scales' then thresholds part_acc"
echo "at an ABSOLUTE CD<0.01, making real part_acc/recall structurally anchor-only."
echo "These runs use the rescaled copies so the metrics are finally meaningful."

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
REPO_DIR=$TORA_ROOT/repo
ENV_PREFIX=$TORA_ROOT/envs/tora
DATA_ROOT=$TORA_ROOT/dataset
LOG_ROOT=$TORA_ROOT/eval_runs

BASE_CKPT=$TORA_ROOT/checkpoints/bbad_everyday_cka.ckpt
ROBUST_CKPT=$TORA_ROOT/output/real_finetune_robust_27793083/epoch-59.ckpt

module purge
module load Anaconda3/2024.02-1
module load CUDA/12.4.1
module load cuDNN/9.6.0.74-CUDA-12.4.1
eval "$(conda shell.bash hook)"
conda activate "$ENV_PREFIX"
export TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0"
export HF_HOME=$TORA_ROOT/.hf-cache

cd "$REPO_DIR"

for TAG in "baseline:$BASE_CKPT" "robust:$ROBUST_CKPT"; do
    NAME="${TAG%%:*}"
    CKPT="${TAG#*:}"

    echo ""
    echo "### [$NAME] real held-out MULTI-PIECE, scale-normalized ###"
    python sample.py \
        ckpt_path="$CKPT" \
        data_root="$DATA_ROOT" \
        data=zeroshot/real_heldout_norm \
        log_dir="$LOG_ROOT/heldout_norm_${NAME}_${SLURM_JOB_ID}" \
        model.n_generations=3
done

echo ""
echo "### Per-object breakdown (normalized): piece count vs part_accuracy / rot_err ###"
python - <<PY
import json, glob, os
root = os.environ.get("LOG_ROOT", "$LOG_ROOT")
jid = "$SLURM_JOB_ID"
for name in ["baseline", "robust"]:
    d = f"{root}/heldout_norm_{name}_{jid}/results"
    print(f"\n=== {name} (scale-normalized) ===")
    for fp in sorted(glob.glob(d + "/*.json")):
        try:
            r = json.load(open(fp))
        except Exception:
            continue
        n = r.get("name", os.path.basename(fp))
        pa, re_ = r.get("part_accuracy"), r.get("rotation_error")
        if pa is not None:
            print(f"  {n}: part_acc={pa} rot_err={re_}")
PY

echo ""
echo "=== Finished at $(date) ==="
