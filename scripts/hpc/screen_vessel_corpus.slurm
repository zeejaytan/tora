#!/bin/bash
#SBATCH --job-name=tora-screen
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --time=04:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_screen_%j.log

set -euo pipefail

# Does the whole corpus have the two faults found on eight objects?
#
#   1. the wall is thinner than TORA's sampling cell, so the break face never
#      gets a row of points of its own (median 0.78 cells on the eight)
#   2. the "vessel" is a solid body, so its fracture is a broad face through a
#      lump rather than a ribbon through a shell (3 of the eight)
#
# GATE_B_DECISION.md records this corpus as hollow in 72 of 72 objects. That
# came from `wear_ops._wall_estimate`, which this repo had already flagged twice
# for the exact failure involved -- see validate_wall_estimator.py and
# check_wall_estimator_noise.py, neither of whose conclusions was written back
# into the gate note. Sections show three of the eight filled to the outline.
#
# Both instruments are checked against shapes with known answers before the run
# and the job stops if either fails: the ray caster against icosphere shells of
# known wall thickness, the fill fraction against a solid sphere (1.000) and
# shells at 0.0975 and 0.2775.

cd /data/gpfs/projects/punim2657/TORA

module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate ./envs/tora

export PYTHONPATH=repo:repo/scripts

echo "=== instrument check: wall thickness, shells of known thickness ==="
python repo/scripts/measure_wall_vs_sampling.py --selftest

echo ""
echo "=== instrument check: fill fraction, solid and shells ==="
python repo/scripts/screen_vessel_corpus.py --selftest

echo ""
echo "=== screening every vessel in the corpus, fresh level ==="
python repo/scripts/screen_vessel_corpus.py \
  --root . --limit 0 --level fresh \
  --out artifacts/corpus_screen.csv

echo ""
echo "done"
