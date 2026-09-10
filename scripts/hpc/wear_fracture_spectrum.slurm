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
# quadric. Gate A measured 1.71 on 20 RePAIR frescoes; fresh fracture is 0.4-0.8.
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

python scripts/wear_fracture_spectrum.py \
    --erosion "$D/erosion_ceramics.hdf5" \
    --raw     "$D/fractura_real.hdf5" \
    --out-dir "$OUT"

echo ""
echo "artifacts in $OUT"
echo "=== done $(date) ==="
