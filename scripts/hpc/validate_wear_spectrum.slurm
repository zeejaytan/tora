#!/bin/bash
#SBATCH --job-name=tora-wearspec
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=160G
#SBATCH --time=06:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_wearspec_%j.log

set -euo pipefail

# Does the rebuilt wear model do what the conservator says wear does -- blunt
# the teeth, preserve the curve, open the joins?
#
# The mechanism was proved on a synthetic break face with a curve and teeth I
# put there myself, so I knew the answer before measuring. That proves the
# operation works; it says nothing about pottery. This runs it on real scans.
#
# OBJECTS SPAN THE THICKNESS SPECTRUM deliberately. The conservator's point,
# and the thing that caught the last wear bug: an eggshell sherd and a solid
# bone put the material asymmetry at completely different scales, and a wear
# model tuned on one can run backwards on the other. blue_pot and plate are
# thin-walled ceramic; coxae and vert9 are solid bone with no wall at all.
#
# Chips are measured separately. A chip of radius r IS a feature of size r, so
# chips at the sizes the conservator called common necessarily add structure in
# the teeth band -- that is a real property of a chipped sherd, not a bug, but
# it would mask whether the abrasion term itself is correct.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

DATA=/data/gpfs/projects/punim2657/TORA/dataset/real_heldout_norm.hdf5
OUT=/data/gpfs/projects/punim2657/TORA/wear_blunt_v3
mkdir -p "$OUT"

echo "=== Started $(date) ==="
python -c "import trimesh, scipy, numpy; print('trimesh', trimesh.__version__)"

for OBJ in blue_pot plate coxae vert9; do
    echo ""
    echo "##################################################################"
    echo "##  $OBJ  -- abrasion alone (chips off), NEW one-sided blunting  ##"
    echo "##################################################################"
    python scripts/validate_wear_spectrum.py \
        --src "$DATA" --dataset real_heldout_norm --object "$OBJ" \
        --mode blunt --no-chips || true

    # The old model has now been measured twice on all four objects with
    # consistent results (curve down 8-28%, teeth up 33-57%). Keeping it on one
    # object as a control rather than paying for it on all four.
    if [ "$OBJ" = "blue_pot" ]; then
        echo ""
        echo "----- $OBJ -- the OLD model, as a control -----"
        python scripts/validate_wear_spectrum.py \
            --src "$DATA" --dataset real_heldout_norm --object "$OBJ" \
            --mode legacy --no-chips || true
    fi

    echo ""
    echo "----- $OBJ -- new model WITH chips (the dataset setting) -----"
    python scripts/validate_wear_spectrum.py \
        --src "$DATA" --dataset real_heldout_norm --object "$OBJ" \
        --mode blunt || true

    echo ""
    echo "----- $OBJ -- look at it (mandatory, and at the right scale) -----"
    python scripts/render_blunting.py \
        --src "$DATA" --dataset real_heldout_norm --object "$OBJ" \
        --out "$OUT/blunt_${OBJ}.png" || true
done

echo ""
echo "=== Finished $(date) ==="
echo "Renders in $OUT -- fetch with scripts/remote/fetch_artifacts.sh"
echo ""
echo "READ THE VERDICT LINES, not the averages. The failure this exists to"
echo "catch (the old model eroding 14% of the curve) passed every single-number"
echo "roughness check for months."
