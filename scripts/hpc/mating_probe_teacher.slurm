#!/bin/bash
#SBATCH --job-name=tora-c2b-teacher
#SBATCH --partition=gpu-a100-short
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_c2b_teacher_%j.log

set -euo pipefail

# C2b — WHICH CHANNEL SURVIVES WEAR?
#
# TORA reuses Rectified Point Flow's fracture encoder FROZEN and unmodified, so
# any wear-robustness TORA has over GARF cannot come from better break-surface
# perception. Its one distinctive channel is the alignment to a frozen Uni3D
# whole-object SHAPE teacher (the paper's actual contribution) — i.e. overall
# vessel form rather than break-surface micro-texture. GARF's own final report
# concluded that on worn sherds the mating information survives in exactly that
# macro-geometry channel, which GARF cannot read.
#
# Test: run the SAME mating probe, with the SAME labels, on both feature
# sources across the same three materials. Both are cut to a common dimension
# (PCA) so the comparison is like-for-like, and each run reports a
# shuffled-label control that must sit near 0.5.
#
# Expected if the macro-shape story is right: on the WORN Juglet the teacher
# (form) channel holds up better than the frozen encoder (break-surface)
# channel, whose contact signal already measured 0.92 -> 0.74 fresh -> worn.

echo "=== TORA C2b teacher-vs-encoder probe started at $(date) on $(hostname) ==="
nvidia-smi | head -15 || true

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

# encoder arm is re-run at the matched probe dimension so the two sources are
# compared under identical settings (not against the earlier 64-d numbers).
for SRC in encoder teacher; do
    for DS in pairs_synth real_heldout_norm juglet_norm; do
        echo ""
        echo "########## source=$SRC  material=$DS ##########"
        python mating_probe.py \
            ckpt_path="$CKPT" \
            data_root="$DATA_ROOT" \
            data=zeroshot/$DS \
            +probe_features=$SRC \
            +probe_dim=64 || echo "arm $SRC/$DS failed (continuing)"
    done
done

echo ""
echo "=== Finished at $(date) ==="
echo "Read in this order: (1) shuffled-label control near 0.5 on every arm,"
echo "(2) synthetic arm high => probe works, (3) then compare how far each"
echo "    channel falls from fresh real fracture to the worn Juglet."
