#!/bin/bash
#SBATCH --job-name=tora-wearspec
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=160G
#SBATCH --time=03:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_wearspec_%j.log

set -euo pipefail

# Put our simulated worn break faces beside REAL eroded archaeological fracture,
# on the one statistic that can be compared without a before-state: how fast
# break-face texture grows with patch radius, curvature removed by a fitted
# quadric. Gate A measured 1.71 on 20 RePAIR frescoes over 0.4-6.4 mm, and 1.73
# refitted over 0.4-1.6 mm alone; fresh fracture is 0.4-0.8.
#
# VERSION 2. Job 30352180 ran version 1 and its numbers are void: it selected the
# break face by distance to another sherd alone, which on a 4.5 mm pot wall takes
# the vessel surface too, and it read Gate A's radii up to 6.4 mm, whose 12.8 mm
# patch is 2.9x that wall. Fresh ceramic came back at 1.06-1.81 where real
# fracture is 0.4-0.8. Three things changed: the break face is found by mating
# direction, the radii stop at 1.6 mm, and every radius carries an off-face and
# patch-shape gate. Full reasoning in the script's own docstring.
#
# The instrument is calibrated against known answers before it is trusted:
#   python scripts/selftest_wear_spectrum_mating.py     # flat break -> 0.00000
#   python scripts/selftest_wear_spectrum_exponent.py   # Hurst 0.5 -> 0.585
# Both run in under a minute on a laptop and are the reason this version is worth
# queue time. Run them if the code is touched.
#
# CPU, no GPU, no model. The cost is geometric: a nearest-neighbour query of
# every vertex of every sherd against every other sherd, then a least-squares
# quadric per probe point per radius, over 40 pot-and-rung combinations. That is
# an hour of CPU, which is why it is a batch job and not an ssh one-liner.
#
# Reasoning, predictions recorded before the run, and the two deliberate
# departures from Gate A's method are in the script's own docstring.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

D=/data/gpfs/projects/punim2657/TORA/dataset
OUT=/data/gpfs/projects/punim2657/TORA/eval_runs/wear_spectrum_${SLURM_JOB_ID}

# the corrected measurement
python scripts/wear_fracture_spectrum.py \
    --erosion "$D/erosion_ceramics.hdf5" \
    --raw     "$D/fractura_real.hdf5" \
    --face-mode mating \
    --out-dir "$OUT"

# and job 30352180's contaminated selection on the same objects in the same run,
# so the correction is shown rather than asserted. Same radii, so the ONLY
# difference is which points are called the break face.
python scripts/wear_fracture_spectrum.py \
    --erosion "$D/erosion_ceramics.hdf5" \
    --raw     "$D/fractura_real.hdf5" \
    --face-mode band \
    --out-dir "$OUT/band_control"

echo ""
echo "artifacts in $OUT"
echo "=== done $(date) ==="
