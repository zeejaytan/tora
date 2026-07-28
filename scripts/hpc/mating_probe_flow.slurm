#!/bin/bash
#SBATCH --job-name=tora-flow-probe
#SBATCH --partition=gpu-a100-short
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_flow_probe_%j.log

set -euo pipefail

# DID THE FORM STRUCTURE ACTUALLY TRANSFER?
#
# Earlier I measured the Uni3D TEACHER's features holding up under wear (0.88)
# and inferred that TORA therefore "has" form information it fails to use. That
# inference was unsound: the teacher is TRAINING-ONLY and discarded at
# inference, so its score shows what was AVAILABLE to transfer, not what TORA
# carries where placement is decided.
#
# The CKA loss aligns the FLOW MODEL's intermediate features at repa_layer
# (layer 3 of 6) to the teacher, using the teacher's view of the ASSEMBLED pot.
# Probing those flow features settles it:
#
#   flow ~= 0.88 (teacher-like) -> the structure DID transfer, and is present
#                                 but underused at placement time. The shortcut
#                                 hypothesis stands; retraining pressure (S3)
#                                 is the right fix.
#   flow ~= 0.71 (encoder-like) -> it did NOT transfer. Form is effectively
#                                 absent from the placement pathway, so no
#                                 training pressure can make TORA use it and an
#                                 explicit form-fed matching stage becomes
#                                 necessary rather than optional.
#
# Probed at several timesteps because the intermediate features depend on the
# noisy state; a conclusion that only holds at one t is not a conclusion.

echo "=== flow-feature probe started at $(date) on $(hostname) ==="

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
ENV_PREFIX=$TORA_ROOT/envs/tora
DATA_ROOT=$TORA_ROOT/dataset
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

for T in 0.1 0.3 0.6; do
    for DS in pairs_synth real_heldout_norm juglet_norm; do
        echo ""
        echo "########## flow features  t=$T  material=$DS ##########"
        python mating_probe.py \
            ckpt_path="$CKPT" \
            data_root="$DATA_ROOT" \
            data=zeroshot/$DS \
            +probe_features=flow \
            +probe_t=$T \
            +probe_dim=64 || echo "arm t=$T/$DS failed (continuing)"
    done
done

echo ""
echo "=== Finished at $(date) ==="
echo "Compare the worn-Juglet flow score against encoder 0.71 and teacher 0.88."
