#!/bin/bash
#SBATCH --job-name=tora-eval-heldout-mp
#SBATCH --partition=gpu-a100-short
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=00:40:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_eval_heldout_mp_%j.log

set -euo pipefail

echo "=== Real held-out MULTI-PIECE eval: baseline vs robust fine-tune, started $(date) on $(hostname) ==="

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
REPO_DIR=$TORA_ROOT/repo
ENV_PREFIX=$TORA_ROOT/envs/tora
DATA_ROOT=$TORA_ROOT/dataset
export LOG_ROOT=$TORA_ROOT/eval_runs

module purge
module load Anaconda3/2024.02-1
module load CUDA/12.4.1
module load cuDNN/9.6.0.74-CUDA-12.4.1
eval "$(conda shell.bash hook)"
conda activate "$ENV_PREFIX"
export TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0"
export HF_HOME=$TORA_ROOT/.hf-cache

cd "$REPO_DIR"

# baseline = shipped synthetic-only checkpoint; robust = replay fine-tune best
for TAG in "baseline:$TORA_ROOT/checkpoints/bbad_everyday_cka.ckpt" \
           "robust_best:$TORA_ROOT/output/real_finetune_robust_27793083/epoch-59.ckpt"; do
    NAME="${TAG%%:*}"
    CKPT="${TAG##*:}"

    echo ""
    echo "### [$NAME] real held-out multi-piece (3,3,3,5,6,10 pieces) ###"
    python sample.py \
        ckpt_path="$CKPT" \
        data_root="$DATA_ROOT" \
        data=zeroshot/real_heldout \
        data.batch_size=4 \
        data.num_workers=4 \
        log_dir="$LOG_ROOT/real_heldout_${NAME}_${SLURM_JOB_ID}" \
        model.n_generations=3
done

echo ""
echo "### Per-object breakdown (piece count vs part_accuracy / rot_err) ###"
python - <<'PY'
import json, os, glob
root = os.environ["LOG_ROOT"]
jid = os.environ["SLURM_JOB_ID"]
for name in ("baseline", "robust_best"):
    d = f"{root}/real_heldout_{name}_{jid}/results"
    print(f"\n=== {name} ===")
    fs = sorted(glob.glob(f"{d}/*.json"))
    if not fs:
        print("  (no per-sample result JSONs found; check table in main log)")
        continue
    for fp in fs:
        try:
            r = json.load(open(fp))
        except Exception as e:
            print("  skip", os.path.basename(fp), e); continue
        nm = r.get("name", os.path.basename(fp))
        pa = r.get("part_accuracy", r.get("best_of_n", {}).get("part_accuracy"))
        re_ = r.get("rotation_error", r.get("best_of_n", {}).get("rotation_error"))
        print(f"  {nm}: part_acc={pa} rot_err={re_}")
PY

echo ""
echo "=== Finished at $(date) ==="
