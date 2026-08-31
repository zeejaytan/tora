#!/bin/bash
#SBATCH --job-name=tora-sections
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=00:40:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_sections_%j.log

set -euo pipefail

# Cut the training vessels open and look, because a number contradicts a note.
#
# GATE_B_DECISION.md says the corpus is hollow -- a wall found in 72 of 72
# objects, median 0.95-3.10% of object. The validated ray caster reads three of
# the eight training objects at 10-15%. The five thin ones agree with the note
# almost exactly, so this is the signature of a reach limit in the older probe
# rather than disagreement: _wall_estimate can see about 2% of object and
# returns 0.0 past that, and 0.0 is dropped rather than counted.
#
# That is an argument, and it happens to favour my own measurement, so it does
# not settle anything. The section does.

cd /data/gpfs/projects/punim2657/TORA

module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate ./envs/tora

export PYTHONPATH=repo:repo/scripts

python repo/scripts/render_object_sections.py \
  --out artifacts/object_sections.png

echo "done"
