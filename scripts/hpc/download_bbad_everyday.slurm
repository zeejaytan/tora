#!/bin/bash
#SBATCH --job-name=tora-dl-bbad
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_download_%j.log

set -euo pipefail

echo "=== TORA download started at $(date) on $(hostname) ==="

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
DATASET_DIR=$TORA_ROOT/dataset
CKPT_DIR=$TORA_ROOT/checkpoints
ENV_PREFIX=$TORA_ROOT/envs/tora

mkdir -p "$DATASET_DIR" "$CKPT_DIR"

# --- 1) BBad-Everyday HDF5 (27 GB) from RPF's GCS ---
RPF_URL="https://storage.googleapis.com/flow-asm/breaking_bad_vol.hdf5"
RPF_FILE="$DATASET_DIR/breaking_bad_vol.hdf5"

echo "--- Downloading BBad-Everyday HDF5 (resume-enabled) ---"
# -c resumes partial downloads; safe to re-run
wget -c --progress=dot:giga -O "$RPF_FILE" "$RPF_URL"

echo "Downloaded size:"
du -h "$RPF_FILE"

# --- 2) Activate conda env for huggingface_hub + h5py inspection ---
module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate "$ENV_PREFIX"

# --- 3) TORA pretrained checkpoint (CKA variant on bbad_everyday) ---
echo "--- Downloading TORA bbad_everyday CKA checkpoint from Hugging Face ---"
python - <<PY
from huggingface_hub import hf_hub_download
import shutil, os
path = hf_hub_download(
    repo_id="NahyukLEE/tora",
    filename="bbad_everyday_cka.ckpt",
    local_dir="$CKPT_DIR",
)
print("Checkpoint at:", path)
print("Size:", os.path.getsize(path) / 1e6, "MB")
PY

# --- 4) Inspect HDF5 to determine correct dataset_name for TORA config ---
echo "--- Inspecting HDF5 structure ---"
python - <<'PY'
import h5py, os, sys
path = "/data/gpfs/projects/punim2657/TORA/dataset/breaking_bad_vol.hdf5"
with h5py.File(path, "r", libver="latest", swmr=True) as f:
    print("Top-level keys:", list(f.keys()))
    if "data_split" in f:
        print("data_split keys:", list(f["data_split"].keys()))
        for k in f["data_split"].keys():
            splits = list(f["data_split"][k].keys())
            counts = {s: len(f["data_split"][k][s]) for s in splits}
            print(f"  {k}: splits={splits} counts={counts}")
PY

# --- 5) Symlink to the name TORA's config expects ---
# config/data/main/bbad_everyday.yaml sets  dataset_names: ["everyday"]
# datamodule.py derives dataset_name from filename before the first dot.
# So the file must be named "everyday.hdf5" AND have internal key data_split/everyday/...
echo "--- Creating symlink everyday.hdf5 -> breaking_bad_vol.hdf5 ---"
ln -sf breaking_bad_vol.hdf5 "$DATASET_DIR/everyday.hdf5"
ls -l "$DATASET_DIR/"

echo ""
echo "=== Download finished at $(date) ==="
echo "Next: if inspection above shows data_split/everyday/..., you're ready."
echo "      If it shows data_split/breaking_bad_vol/..., update"
echo "      config/data/main/bbad_everyday.yaml dataset_names to [\"breaking_bad_vol\"]"
echo "      and remove the symlink."
