#!/bin/bash
#SBATCH --job-name=tora-wear-ft2
#SBATCH --partition=gpu-a100
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=10:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_wear_ft2_%j.log

set -euo pipefail

# S3 v2 — retrain on the FINISHED wear model.
#
# The first attempt (job 28231335) worked: +0.235 seating on worn material,
# p=0.0078, on genuinely held-out objects. But it was trained on a wear model we
# have since found to be wrong in ways that mattered — it pushed surfaces toward
# their neighbours instead of away (inverted mesh normals), folded geometry over
# on itself, and swept a single "wear level" dial that conflated two independent
# things.
#
# The rebuilt training set separates them, following the conservator's reading:
#
#   MATERIAL LOSS is real but modest on actual sherds (0.2-2.7% of volume), and
#   is kept at that level. Over-damaging the training data would teach the model
#   to expect destruction that is rare.
#
#   SMOOTHNESS — the rounding-off of the break face — is what removes the
#   information about how sherds lock together. That is why GARF, which reads
#   only the fracture surface, fails on worn material, and why TORA, which also
#   reads whole-object form, holds up better. This axis is spanned as widely as
#   the simulation permits.
#
# Recipe unchanged from v1 and still deliberately conservative (synthetic replay,
# low LR), because both fine-tunes here before v1 ended up WORSE than the
# checkpoint they started from.
#
# Success = seating improves at the worn end WITHOUT wrecking fresh objects,
# and ideally beats v1 — if it does not, the wear-model fixes did not matter for
# training, which is itself worth knowing.

echo "=== S3 v2 wear-augmented fine-tune started at $(date) on $(hostname) ==="
nvidia-smi | head -15 || true

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
ENV_PREFIX=$TORA_ROOT/envs/tora
DATA_ROOT=$TORA_ROOT/dataset
LOG_ROOT=$TORA_ROOT/eval_runs
OUT_ROOT=$TORA_ROOT/output/wear_finetune_v2_${SLURM_JOB_ID}
CKPT=$TORA_ROOT/checkpoints/bbad_everyday_cka.ckpt
WEAR_V1=$TORA_ROOT/output/wear_finetune_28231335/last.ckpt

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

echo ""
echo "### 1/3  build worn training data with the validated wear model ###"
if [ ! -f "$DATA_ROOT/wear_trainset_v2.hdf5" ]; then
    python scripts/build_wear_trainset_v2.py \
        --src "$DATA_ROOT/real_finetune.hdf5" \
        --src-dataset real_finetune \
        --dataset-name wear_trainset_v2 \
        --out-hdf5 "$DATA_ROOT/wear_trainset_v2.hdf5"
else
    echo "wear_trainset_v2.hdf5 already present, reusing"
fi

echo ""
echo "### 2/3  fine-tune with synthetic replay ###"
python train.py \
    data=main/wear_finetune_v2 \
    data_root="$DATA_ROOT" \
    model.encoder_ckpt="$CKPT" \
    model.flow_model_ckpt="$CKPT" \
    model.optimizer.lr=2e-5 \
    trainer.max_epochs=40 \
    log_dir="$OUT_ROOT" || { echo "training failed"; exit 1; }

BEST=$(find "$OUT_ROOT" -name "*.ckpt" -printf "%T@ %p\n" 2>/dev/null | sort -rn | head -1 | cut -d" " -f2)
echo "using checkpoint: $BEST"

echo ""
echo "### 3/3  evaluate: worn sweep AND fresh material, against v1 ###"
# Three models side by side so the comparison is honest: the untouched baseline,
# the first wear fine-tune, and this one.
for TAG in "baseline:$CKPT" "wear_v1:$WEAR_V1" "wear_v2:$BEST"; do
    NAME="${TAG%%:*}"; C="${TAG#*:}"
    if [ -z "$C" ] || [ ! -f "$C" ]; then
        echo "skipping $NAME -- no checkpoint at '$C'"
        continue
    fi

    echo ""
    echo "########## $NAME : WORN sweep (the gain we want) ##########"
    python sample.py ckpt_path="$C" data_root="$DATA_ROOT" \
        data=zeroshot/erosion_sweep data.batch_size=4 \
        log_dir="$LOG_ROOT/wearft2_sweep_${NAME}_${SLURM_JOB_ID}" \
        model.n_generations=3
    python scripts/analyze_erosion_sweep.py \
        --results-dir "$LOG_ROOT/wearft2_sweep_${NAME}_${SLURM_JOB_ID}/results" \
        --calibration "$DATA_ROOT/erosion_sweep.calibration.json" || true

    echo ""
    echo "########## $NAME : FRESH objects (the do-no-harm check) ##########"
    python sample.py ckpt_path="$C" data_root="$DATA_ROOT" \
        data=zeroshot/real_heldout_norm data.batch_size=4 \
        log_dir="$LOG_ROOT/wearft2_fresh_${NAME}_${SLURM_JOB_ID}" \
        model.n_generations=3 || true
done

echo ""
echo "=== Finished at $(date) ==="
echo "Read it as a trade, not a score: the worn sweep is what we are buying,"
echo "the fresh run is what we might be paying with. v1 bought +0.235 seating"
echo "on worn material for about -0.115 on fresh."
