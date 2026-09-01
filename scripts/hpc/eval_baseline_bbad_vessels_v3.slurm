#!/bin/bash
#SBATCH --job-name=tora-base-vessels-v3
#SBATCH --partition=gpu-a100
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=02:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_base_vessels_v3_%j.log

set -euo pipefail

# The untouched model, scored on the vessel validation set it will be adapted
# against. Item 4 of docs/notes/LORA_VESSELS_29623885_RESULT.md, never done.
#
# WHY IT MATTERS MORE THAN IT SOUNDS. The last adapter run produced a number
# with nothing to sit against on this material: the three arms were compared on
# the erosion sweep, the fresh held-out set and the Juglet, none of which is the
# distribution the adapter was trained on. Without the base model's score on
# these same 117 vessels there is no way to tell "the adapter learned this data"
# from "this data is easy".
#
# It is also a cheap failure detector for the long run. If the new data config
# does not load, or the split rename did not land, this says so in twenty
# minutes instead of five hours.
#
# NOTE ON THE SPLIT. PointCloudDataModule.setup() uses split="val" for the
# test/predict stage (datamodule.py:181), so this scores the 117 VALIDATION
# vessels. That is deliberate and it is also the only honest option: the `test`
# split in this file is a verbatim copy of `val` (build_bbad_vessel_trainset.py
# :417) and is never read by the loader.

echo "=== baseline on bbad_vessels_v3 val, started $(date) on $(hostname) ==="
nvidia-smi | head -15 || true

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
export WANDB_MODE=offline
cd "$TORA_ROOT/repo"

for f in "$DATA_ROOT/bbad_vessels_v3.hdf5" "$CKPT"; do
    [ -f "$f" ] || { echo "missing: $f"; exit 1; }
done

python sample.py ckpt_path="$CKPT" data_root="$DATA_ROOT" \
    data=main/bbad_vessels_v3 data.batch_size=4 \
    lora.enabled=false \
    model.n_generations=3 \
    log_dir="$LOG_ROOT/base_vessels_v3_${SLURM_JOB_ID}"

echo ""
echo "=== Finished at $(date) ==="
echo "Read the AVERAGE, not the best-of-3: best-of-N reports the luckiest run"
echo "of N and is not what a conservator gets on a single attempt."
