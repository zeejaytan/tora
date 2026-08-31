#!/bin/bash
#SBATCH --job-name=tora-bbadset3
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=180G
#SBATCH --time=24:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_bbadset3_%j.log

set -euo pipefail

# REBUILD of the vessel training set. Why it is being rebuilt, in one line: the
# joins in the old one are not joins. 44% of the fragments' vertices are exactly
# coincident, so the fresh third of that corpus is a lookup table, and the
# adapter trained on it dropped worn pottery from 79% to 62% of fragments
# correctly placed (job 29623885).
#
# WHAT CHANGED, all three on measurement:
#
#   dose        0.10% -> 0.30% of object. The old figure came from `joint_gap`,
#               a 10th percentile over all 5000 sampled points, which saturates
#               at the sampling floor and reads 0.277 on a build whose vertices
#               are EXACTLY coincident. On the contact band (job 29765789) the
#               real worn pot sits at p10/p50/p90 = 0.182/0.615/1.692 % of
#               object; 0.30% recession puts the Vase at 0.181/0.588/1.771.
#               All three percentiles, not just the middle one.
#
#   chipping    restored, at the RESTRAINED validated settings (2-3 chips at
#               0.22-0.25% of object; job 28742114 showed 6 chips at 0.40% make
#               "heavy wear" read ROUGHER than an untouched sherd, because
#               ragged chip boundaries are themselves relief). Recession alone
#               moves the join distribution to the right place but leaves it
#               tall and narrow where the real one is a broad hump.
#
#   `fresh`     no longer trainable. It is the defect. Built and kept as split
#               "control" so it can still be measured against.
#
# AND A GATE, not a paragraph: any worn example that still has a coincident
# vertex is DROPPED with its name printed. Three prose rules did not stop the
# last data-build error; a check does.
#
# The corpus screen (job 29765705) rides along in the manifest rather than
# deciding here: 37% of this corpus is a solid lump, not a vessel, and 97% of
# objects sit on the diagonal where "TORA resolves the break face" and "not a
# vessel" are the same objects. Both arms are written -- train/val over
# everything, train_screened/val_screened over the 207 that are a hollow vessel
# whose break TORA can actually see -- so that choice is made once, visibly, at
# training time.
#
# WRITES A NEW FILE. bbad_vessels.hdf5 is left alone: it is what the screen and
# the fill ladder were measured on, and overwriting it would erase the baseline
# this rebuild has to be compared against.
#
# MAX_OBJ=6 for the smoke pass. Run that FIRST and read the gate line.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

ROOT=/data/gpfs/projects/punim2657/TORA
MAX_OBJ="${MAX_OBJ:-0}"
INST="${INST:-3}"
TAG="${TAG:-v3}"
OUT="${OUT:-$ROOT/dataset/bbad_vessels_${TAG}.hdf5}"

mkdir -p "$ROOT/artifacts"

python scripts/build_bbad_vessel_trainset.py \
    --src "$ROOT/dataset/breaking_bad_vol.hdf5" \
    --out-hdf5 "$OUT" \
    --instances-per-object "$INST" \
    --max-objects "$MAX_OBJ" \
    --screen-csv "$ROOT/artifacts/corpus_screen.csv"

ls -lh "$OUT"

# LOOK AT IT. A build summary reports what the script meant to write; it cannot
# see a folded surface, a chip scar left open, or a collapsed normalisation.
# All three have happened here.
python scripts/render_trainset_sample.py \
    --src "$OUT" --dataset bbad_vessels \
    --out "$ROOT/artifacts/bbad_vessels_${TAG}_sample.png"

# BEFORE AND AFTER, on the quantity that was wrong. The join distribution is
# the whole reason for the rebuild, so it is measured on the new file and on
# the old one with the same instrument, in one run, rather than compared across
# two logs written weeks apart.
python scripts/measure_join_uniformity.py \
    --root "$ROOT" --src "$OUT" --dataset bbad_vessels

echo ""
echo "=== Finished at $(date) ==="
