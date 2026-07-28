#!/bin/bash
#SBATCH --job-name=tora-wear-ft
#SBATCH --partition=gpu-a100
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=08:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_wear_ft_%j.log

set -euo pipefail

# S3 — teach TORA to seat WORN fragments.
#
# Until now this could not be attempted: the only genuinely worn object we have
# (the Juglet) has no correct answer, so there was nothing to learn from. The
# validated mollifier changes that -- it abrades real objects while PRESERVING
# their ground-truth poses, manufacturing worn training data that keeps its
# answer key.
#
# Recipe deliberately conservative, because BOTH earlier fine-tunes here ended
# up WORSE than the checkpoint they started from:
#   * synthetic replay mixed in (GARF Exp 11-15 recipe) to resist forgetting;
#   * low learning rate, few epochs;
#   * evaluated on BOTH worn and fresh material, so a gain on worn pots that is
#     paid for by wrecking fresh ones is reported as the trade it is.
#
# Success = seating recovers at the WORN end of the C3 curve WITHOUT losing the
# fresh-object performance the baseline already has.

echo "=== S3 wear-augmented fine-tune started at $(date) on $(hostname) ==="
nvidia-smi | head -15 || true

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
ENV_PREFIX=$TORA_ROOT/envs/tora
DATA_ROOT=$TORA_ROOT/dataset
LOG_ROOT=$TORA_ROOT/eval_runs
OUT_ROOT=$TORA_ROOT/output/wear_finetune_${SLURM_JOB_ID}
CKPT=$TORA_ROOT/checkpoints/bbad_everyday_cka.ckpt

module purge
module load Anaconda3/2024.02-1
module load CUDA/12.4.1
module load cuDNN/9.6.0.74-CUDA-12.4.1
eval "$(conda shell.bash hook)"
conda activate "$ENV_PREFIX"
export TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0"
export HF_HOME=$TORA_ROOT/.hf-cache
# wandb is the only logger config shipped, and the cluster has no outbound
# network for it -- run it offline, as the previous working fine-tunes did.
export WANDB_MODE=offline
cd "$TORA_ROOT/repo"

echo ""
echo "### 1/3  manufacture worn training data (ground truth preserved) ###"
if [ ! -f "$DATA_ROOT/wear_trainset.hdf5" ]; then
    python scripts/build_erosion_sweep.py \
        --src "$DATA_ROOT/real_finetune.hdf5" \
        --src-dataset real_finetune \
        --strengths 0,0.3,0.6,1.0 \
        --normalize --preserve-split --skip-relief \
        --dataset-name wear_trainset \
        --out-hdf5 "$DATA_ROOT/wear_trainset.hdf5"
else
    echo "wear_trainset.hdf5 already present, reusing"
fi

echo ""
echo "### 2/3  fine-tune with synthetic replay ###"
python train.py \
    data=main/wear_finetune \
    data_root="$DATA_ROOT" \
    model.encoder_ckpt="$CKPT" \
    model.flow_model_ckpt="$CKPT" \
    model.optimizer.lr=2e-5 \
    trainer.max_epochs=40 \
    log_dir="$OUT_ROOT" || { echo "training failed"; exit 1; }

BEST=$(find "$OUT_ROOT" -name "*.ckpt" -printf "%T@ %p\n" 2>/dev/null | sort -rn | head -1 | cut -d" " -f2)
echo "using checkpoint: $BEST"

echo ""
echo "### 3/3  evaluate on WORN material, and check fresh is not wrecked ###"
for TAG in "baseline:$CKPT" "wear_ft:$BEST"; do
    NAME="${TAG%%:*}"; C="${TAG#*:}"
    [ -z "$C" ] && continue
    echo ""
    echo "########## $NAME : worn sweep ##########"
    python sample.py ckpt_path="$C" data_root="$DATA_ROOT" \
        data=zeroshot/erosion_sweep data.batch_size=4 \
        log_dir="$LOG_ROOT/wearft_sweep_${NAME}_${SLURM_JOB_ID}" \
        model.n_generations=3
    python scripts/analyze_erosion_sweep.py \
        --results-dir "$LOG_ROOT/wearft_sweep_${NAME}_${SLURM_JOB_ID}/results" \
        --calibration "$DATA_ROOT/erosion_sweep.calibration.json" || true
done

echo ""
echo "=== Finished at $(date) ==="
echo "Read the wear 0.00 column as the do-no-harm check and wear 0.75-1.00 as the gain."
