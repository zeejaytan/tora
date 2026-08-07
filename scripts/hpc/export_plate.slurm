#!/bin/bash
#SBATCH --job-name=tora-plate
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --time=03:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_plate_%j.log

set -euo pipefail

# Export ceramics__plate for inspection.
#
# The most decision-relevant of the three exports, because it is the MIDDLE of
# the spectrum and it is ordinary archaeological pottery rather than eggshell.
#
#   wall 3.54% of object width, against a 5% smoothing patch
#   wall drops to 2.53% under wear -- a 29% loss
#
# Eggshell at 1.5% is an extreme case and easy to dismiss as exotic. A plate is
# not. If the crushing is visible here, the fault reaches ordinary ceramics, and
# the Juglet sits in this part of the range too.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

SRC=/data/gpfs/projects/punim2657/TORA/dataset/real_finetune.hdf5
OUT=/data/gpfs/projects/punim2657/TORA/wear_sherds_spectrum

python scripts/export_wear_sherds.py \
    --src "$SRC" --dataset real_finetune \
    --object ceramics__plate \
    --min-pieces 2 --max-pieces 12 \
    --out "$OUT/ceramics__plate"

cat > "$OUT/ceramics__plate/READ_THIS_FIRST.txt" <<'NOTE'
ceramics__plate — ordinary pottery, and the wear model is wrong on it too
=========================================================================

This is the export that matters most, because a plate is not an exotic case.

WHERE IT SITS
  Wall at the break:  3.54% of the object's width
  Smoothing patch:    5.00%    <- wider than the wall
  Wall after wear:    2.53%    -- a 29% loss

  For comparison, blue_pot (which you judged good) has a 6.07% wall, thicker
  than the patch, and does not change at all: +1.5%.

  Every object measured with a wall thinner than the patch is affected; every
  object with a thicker wall is not. Nothing falls in between:

      eggs            1.4-1.6%   -28% to -37%
      narrow bottles  2.8-3.4%   -19% to -57%
      plate           3.5%       -29%
      ---------------------------------- 5% smoothing patch
      galli_pot       5.8%        +3%
      pink_bowl       6.1%        -8%  (within measurement noise)
      blue_pot        6.1%        +2%

WHAT TO LOOK FOR — the broken edge, viewed EDGE ON, raking light
  Compare against blue_pot, which you have already inspected and approved.

  Correct: the sharp line where the break meets the upper and lower faces
  softens and rounds, and the sherd keeps its full thickness right up to the
  break.

  What to suspect here: the sherd tapering as it approaches the break, ending
  in a thinned, feathered lip rather than a rounded edge of full thickness. A
  plate wall pinched from 3.5% down to 2.5% should be visible as the edge
  looking thinner than the body of the sherd.

  If it does NOT look wrong to you, say so. The measurement would then be
  detecting something real but too small to matter for reassembly, which is a
  different decision from the one the numbers currently imply.

WHY THIS ONE DECIDES THINGS
  Eggshell is easy to set aside as a special case. A plate is normal
  archaeological material, and the Juglet -- the object this whole effort exists
  to reassemble -- is thin-walled and sits in this part of the range.
NOTE

echo ""
echo "=== export at $OUT/ceramics__plate ==="
find "$OUT/ceramics__plate" -name "*.ply" | wc -l
du -sh "$OUT/ceramics__plate"
