#!/bin/bash
#SBATCH --job-name=tora-bbadset
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=180G
#SBATCH --time=12:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_bbadset_%j.log

set -euo pipefail

# The vessel-VARIETY training set. The conservator's diagnosis, after a week
# spent on wear: "the dataset provides more variety as to the shapes that get
# trained. We can make the relevant object fragment worn, but we don't have the
# shape/object in training right now. That's the gap."
#
# 8 ceramic vessels in the fine-tuning source against 371 vessel shapes already
# fractured on disk (docs/notes/GATE_B_DECISION.md), filtered by effective piece
# count so the breaks are reassembly problems rather than one remnant plus chips.
#
# Wear is recession only, at 0.05% and 0.10%, on the measurement in
# test_recession_curve.py (job 29475692): those doses open the joins 22-42%
# while the curve moves at most 4%. 0.20% is excluded -- it cost one object 6.6%.
#
# MAX_OBJ=<n> for a smoke test; unset or 0 builds the whole corpus.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

MAX_OBJ="${MAX_OBJ:-0}"
INST="${INST:-3}"
OUT="${OUT:-/data/gpfs/projects/punim2657/TORA/dataset/bbad_vessels.hdf5}"

python scripts/build_bbad_vessel_trainset.py \
    --src /data/gpfs/projects/punim2657/TORA/dataset/breaking_bad_vol.hdf5 \
    --out-hdf5 "$OUT" \
    --instances-per-object "$INST" \
    --max-objects "$MAX_OBJ"

ls -lh "$OUT"
echo ""
echo "=== Finished at $(date) ==="
