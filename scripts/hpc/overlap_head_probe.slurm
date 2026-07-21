#!/bin/bash
#SBATCH --job-name=tora-overlap-probe
#SBATCH --partition=gpu-a100-short
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:30:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_overlap_probe_%j.log

set -euo pipefail

echo "=== TORA overlap-head introspection probe started at $(date) on $(hostname) ==="
nvidia-smi | head -15 || true

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
REPO_DIR=$TORA_ROOT/repo
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

cd "$REPO_DIR"

echo ""
echo "### Synthetic in-domain reference: Breaking Bad thin-walled (subsampled 200) ###"
python overlap_head_probe.py \
    ckpt_path="$CKPT" \
    data_root="$DATA_ROOT" \
    data=main/bbad_thinwalled \
    data.limit_val_samples=200 \
    data.batch_size=8 \
    data.num_workers=4

# Fractura zero-shot subsets: two synthetic-fracture (bone_syn_pig, bone_syn_rib)
# vs three real-fracture (ceramics, egg, bones) -- the matched-category contrast
# from TORA_GOOD_VS_BAD_ANALYSIS.md.
SUBSETS=(bone_syn_pig bone_syn_rib ceramics egg bones)
for SUBSET in "${SUBSETS[@]}"; do
    echo ""
    echo "### Fractura subset: ${SUBSET} ###"
    python overlap_head_probe.py \
        ckpt_path="$CKPT" \
        data_root="$DATA_ROOT" \
        data=zeroshot/fractura/${SUBSET} \
        data.batch_size=8 \
        data.num_workers=4
done

echo ""
echo "### Juglet (real, worn, archaeological) ###"
python overlap_head_probe.py \
    ckpt_path="$CKPT" \
    data_root="$DATA_ROOT" \
    data=zeroshot/juglet_deploy_local02 \
    data.batch_size=1 \
    data.num_workers=4

echo ""
echo "=== All overlap-head probes finished at $(date) ==="
