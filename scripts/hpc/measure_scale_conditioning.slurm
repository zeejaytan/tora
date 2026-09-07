#!/bin/bash
#SBATCH --job-name=tora-scaleband
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_scaleband_%j.log

set -euo pipefail

# TICKET .scratch/eval-readout/issues/04 — WHAT IS `scales`, AND IS OUR WARNING REAL?
#
# The wear verdict rests on one table (WEAR_TEST_RESULTS.md §4: baseline seats
# 0.843 fresh, 0.645 worn), and both rows carry a warning we wrote and never
# tested: "scored at a stored object size of 0.319-0.383, at or below the trained
# floor of 0.375".
#
# That floor is arithmetic, not observation: 0.5 x 0.75, where 0.5 is the MESH
# convention (Breaking Bad stores max|v| = 0.5). But `scales` is not the mesh's
# max|v| -- dataset.py:427 takes it from the SAMPLED 5000-point cloud after
# centring on the point centroid and swapping the up axis. Sampled points do not
# reach the extreme vertex. So the observed value and the band it is judged
# against may simply be measured on different things.
#
# ALREADY ELIMINATED, by reading the code: augmentation is not running at
# evaluation. datamodule.py passes random_scale_range only to the train dataset
# (line 152); val, validate and test/predict all omit it.
#
# THIS JOB MEASURES the base value instead of deriving it -- on the corpus the
# baseline checkpoint was trained on, and on the two evaluation sets whose rows
# carry the warning, so all three sit on one axis. CPU only; no model is loaded.

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
ENV_PREFIX=$TORA_ROOT/envs/tora
DATA_ROOT=$TORA_ROOT/dataset
OUT=$TORA_ROOT/eval_runs/scale_band_${SLURM_JOB_ID}
mkdir -p "$OUT"

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate "$ENV_PREFIX"
cd "$TORA_ROOT/repo"

echo "=== Started at $(date) ==="

echo ""
echo "### 1. The training corpus: Breaking Bad everyday, TRAIN split ###"
echo "### (bbad_everyday_cka.ckpt is the baseline in the wear table)   ###"
python scripts/measure_scale_conditioning.py \
    --data "$DATA_ROOT/everyday.hdf5" --dataset-name everyday \
    --up-axis z --split train --min-parts 2 --max-parts 64 \
    --sample 400 --out-json "$OUT/everyday_train.json"

echo ""
echo "### 2. The same corpus, VAL split — the split every eval uses ###"
python scripts/measure_scale_conditioning.py \
    --data "$DATA_ROOT/everyday.hdf5" --dataset-name everyday \
    --up-axis z --split val --min-parts 2 --max-parts 64 \
    --sample 200 --out-json "$OUT/everyday_val.json"

echo ""
echo "### 3. real_heldout_norm — the 'fresh held-out' rows of §4 ###"
python scripts/measure_scale_conditioning.py \
    --data "$DATA_ROOT/real_heldout_norm.hdf5" --dataset-name real_heldout_norm \
    --split val --min-parts 2 --max-parts 20 \
    --sample 0 --out-json "$OUT/real_heldout_norm.json"

echo ""
echo "### 4. erosion_sweep — the 'worn sweep' rows of §4 ###"
python scripts/measure_scale_conditioning.py \
    --data "$DATA_ROOT/erosion_sweep.hdf5" --dataset-name erosion_sweep \
    --split val --min-parts 2 --max-parts 20 \
    --sample 0 --out-json "$OUT/erosion_sweep.json"

echo ""
echo "### 5. juglet_norm — the object the whole map is about ###"
python scripts/measure_scale_conditioning.py \
    --data "$DATA_ROOT/juglet_norm.hdf5" --dataset-name juglet_norm \
    --split val --min-parts 2 --max-parts 20 \
    --sample 0 --out-json "$OUT/juglet_norm.json" || true

echo ""
echo "Artifacts in $OUT"
echo "=== Finished at $(date) ==="
