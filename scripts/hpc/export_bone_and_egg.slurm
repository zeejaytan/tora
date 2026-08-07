#!/bin/bash
#SBATCH --job-name=tora-boneegg
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --time=03:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_boneegg_%j.log

set -euo pipefail

# Export one SOLID object and one SHELL object as sherd meshes, for inspection
# by hand across the wear series -- the same treatment blue_pot got.
#
# These are the two ends of the conservator's thickness spectrum, and the wear
# model is measured to behave differently at each:
#
#   bones__limb3   solid. Break face loses relief as intended (-36.9%). This is
#                  the end the model was built for and should look right.
#   egg__egg1      shell, wall 1.50%. Loses 37% of its wall thickness at the
#                  break. Should look WRONG, and the export exists so that can
#                  be judged by eye rather than taken on the numbers.
#
# Exported from the CURRENT wear model, faults and all. That is deliberate: this
# is the before, against which the rewrite will be compared.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

SRC=/data/gpfs/projects/punim2657/TORA/dataset/real_finetune.hdf5
OUT=/data/gpfs/projects/punim2657/TORA/wear_sherds_spectrum

for OBJ in bones__limb3 egg__egg1; do
    echo ""
    echo "########## $OBJ ##########"
    python scripts/export_wear_sherds.py \
        --src "$SRC" --dataset real_finetune \
        --object "$OBJ" \
        --min-pieces 2 --max-pieces 12 \
        --out "$OUT/$OBJ"
done

# The generated README reports a fracture-texture number. On a shell that number
# is not trustworthy, and saying so next to the files is the difference between
# a useful export and a misleading one.
cat > "$OUT/egg__egg1/READ_THIS_FIRST.txt" <<'NOTE'
egg__egg1 — a SHELL, and the wear model is known to be WRONG on it
==================================================================

This export is deliberately of the BROKEN behaviour. It is the "before" for a
fix, not a candidate for use.

WHAT THE MEASUREMENTS SAY
  The wall at the break is 1.50% of the object's width. Under wear it drops to
  0.94% — the shell loses 37% of its thickness right where it broke.
  For comparison, blue_pot's wall is 6.07% and does not change (+1.5%).

  Every object with a wall thinner than the smoothing patch (5% of object
  width) is affected; every object with a thicker wall is not. The separation
  is complete, with nothing in between.

WHAT TO LOOK FOR — the break edge, viewed EDGE ON
  Correct wear would round the sharp line where the break meets the inner and
  outer surfaces, leaving the wall its full thickness.

  What this model does instead is squeeze the wall thinner at the break,
  leaving a feathered, tapering lip. That feather is geometrically sharper
  than what it replaced, which is why the measured texture goes the WRONG WAY
  on this object: it reads ROUGHER after wear, not smoother.

IGNORE the "MEASURED FRACTURE TEXTURE" numbers in README.txt for this object.
  That measurement compares surface directions within a patch 3% of the object
  wide. This shell is thinner than that, so the patch spans the inner and outer
  wall at once and reports wall thinness rather than break-surface texture. It
  sits near its ceiling (~1.2 out of 2.0) and barely moves at any wear level.

  The number is not measuring what its label says. On solid objects such as
  bones__limb3 it is fine.
NOTE

cat > "$OUT/bones__limb3/READ_THIS_FIRST.txt" <<'NOTE'
bones__limb3 — a SOLID object, the end of the spectrum the model was built for
==============================================================================

Solid throughout: the fracture is a genuine surface with interlocking relief,
not a thin ribbon. There is no wall to crush.

WHAT THE MEASUREMENTS SAY
  Break-surface texture falls from 0.0752 to 0.0475 under heavy wear, a 37%
  reduction. That is the intended behaviour: the face becomes blunt and, under
  severe wear, tends toward flat.

WHAT TO LOOK FOR — light the break face at a low angle
  The interlocking relief of the break should progressively soften and lose its
  fine detail while the overall shape of the fracture stays put. Under severe
  wear it should approach a flattened face.

  It should NOT look melted or smoothed all over. Only the break is worn; the
  original outer bone surface stays as it was.

  Small chips at the sharp, exposed corners are expected and intended.

NOTE ON THE WALL FIGURES ELSEWHERE
  Wall-thickness numbers reported for bones in earlier tables are meaningless.
  That measurement looks for the nearest surface facing the opposite way, which
  on a hollow vessel is the far side of the wall — but a solid bone has no wall,
  so it finds whatever feature happens to be closest. It produced impossible
  results on bones, including walls that appeared to get THICKER under wear.
  Judge solid objects by break-surface texture, not by wall.
NOTE

echo ""
echo "=== exports at $OUT ==="
find "$OUT" -name "*.ply" | wc -l
du -sh "$OUT"
