#!/bin/bash
#SBATCH --job-name=tora-roughness-probe
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_roughness_probe_%j.log

set -euo pipefail

echo "=== TORA fracture-surface roughness probe (mesh-only, no GPU) started at $(date) on $(hostname) ==="

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
REPO_DIR=$TORA_ROOT/repo
ENV_PREFIX=$TORA_ROOT/envs/tora
DATA_ROOT=$TORA_ROOT/dataset

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate "$ENV_PREFIX"

cd "$REPO_DIR"

echo ""
echo "### SYNTHETIC fracture: bone_syn_pig (pig, bone_synthetic.hdf5) ###"
python scripts/fracture_surface_roughness.py \
    --hdf5 "$DATA_ROOT/bone_synthetic.hdf5" --dataset-name pig \
    --min-parts 2 --max-parts 12

echo ""
echo "### SYNTHETIC fracture: bone_syn_rib (rib, bone_synthetic.hdf5) ###"
python scripts/fracture_surface_roughness.py \
    --hdf5 "$DATA_ROOT/bone_synthetic.hdf5" --dataset-name rib \
    --min-parts 2 --max-parts 12

echo ""
echo "### REAL fracture: bones (fractura_real.hdf5) ###"
python scripts/fracture_surface_roughness.py \
    --hdf5 "$DATA_ROOT/fractura_real.hdf5" --dataset-name bones \
    --min-parts 2 --max-parts 12

echo ""
echo "### REAL fracture: ceramics (fractura_real.hdf5) ###"
python scripts/fracture_surface_roughness.py \
    --hdf5 "$DATA_ROOT/fractura_real.hdf5" --dataset-name ceramics \
    --min-parts 2 --max-parts 12

echo ""
echo "### REAL fracture: egg (fractura_real.hdf5) ###"
python scripts/fracture_surface_roughness.py \
    --hdf5 "$DATA_ROOT/fractura_real.hdf5" --dataset-name egg \
    --min-parts 2 --max-parts 12

echo ""
echo "=== All roughness probes finished at $(date) ==="
