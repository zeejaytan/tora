#!/bin/bash
#SBATCH --job-name=tora-install
#SBATCH --partition=gpu-a100-short
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=03:30:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_install_%j.log

set -euo pipefail

echo "=== TORA install started at $(date) on $(hostname) ==="
nvidia-smi || true

# --- Modules: match TORA's required stack (CUDA 12.4, cuDNN 12.4) ---
module purge
module load Anaconda3/2024.02-1
module load CUDA/12.4.1
module load cuDNN/9.6.0.74-CUDA-12.4.1
module load GCC/13.3.0        # nvcc host compiler for pointnet2_ops / KNN_CUDA

eval "$(conda shell.bash hook)"

# Tell nvcc which arches to target (A100=8.0, H100=9.0, L40S=8.9)
export TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0"
export CUDA_HOME="${CUDA_HOME:-$EBROOTCUDA}"
echo "CUDA_HOME=$CUDA_HOME"
nvcc --version

# --- Paths ---
TORA_ROOT=/data/gpfs/projects/punim2657/TORA
ENV_PREFIX=$TORA_ROOT/envs/tora
REPO_DIR=$TORA_ROOT/repo

mkdir -p "$TORA_ROOT"

# --- Create conda env (Python 3.10) on project filesystem ---
if [ ! -d "$ENV_PREFIX" ]; then
    echo "Creating conda env at $ENV_PREFIX"
    conda create -p "$ENV_PREFIX" python=3.10 -y
fi
conda activate "$ENV_PREFIX"
python --version
which pip

# Keep pip caches off $HOME quota
export PIP_CACHE_DIR=$TORA_ROOT/.pip-cache
export TMPDIR=$TORA_ROOT/.tmp
mkdir -p "$PIP_CACHE_DIR" "$TMPDIR"

# --- Clone repo (with submodules) ---
if [ ! -d "$REPO_DIR/.git" ]; then
    echo "Cloning TORA into $REPO_DIR"
    git clone --recursive https://github.com/NahyukLEE/tora.git "$REPO_DIR"
else
    echo "Repo already present; pulling latest"
    git -C "$REPO_DIR" pull --recurse-submodules
fi

cd "$REPO_DIR"

# --- Run upstream install.sh ---
# The repo's install.sh builds pointnet2_ops and KNN_CUDA from source,
# which is why this job needs a GPU node + nvcc + GCC loaded.
bash install.sh

# --- Sanity check ---
python - <<'PY'
import torch, pytorch3d, flash_attn
print("torch       :", torch.__version__, "cuda?", torch.cuda.is_available())
print("torch.cuda  :", torch.version.cuda)
print("pytorch3d   :", pytorch3d.__version__)
print("flash_attn  :", flash_attn.__version__)
import pointnet2_ops, knn_cuda  # noqa: F401
print("pointnet2_ops + knn_cuda import OK")
PY

echo "=== TORA install finished at $(date) ==="
