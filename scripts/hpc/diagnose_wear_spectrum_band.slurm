#!/bin/bash
#SBATCH --job-name=tora-wearspec-diag
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=200G
#SBATCH --time=04:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_wearspec_diag_%j.log

set -euo pipefail

# Job 30352180 returned exponents that do not look like break faces: fresh
# ceramic at 1.06-1.81 where real fracture is 0.4-0.8, two pots already at or
# above the WORN archaeological value before any wear, and the direction of
# change disagreeing between pots. Before any of that is read as a statement
# about our wear model, find out whether the ruler is measuring the break or
# the vessel wall it sits in.
#
# Four checks, any of which can contradict the others: wall thickness against
# the patch size, the exponent's dependence on band width, the share of each
# patch that has wrapped onto another surface, and the residual field itself
# rendered per point. The reasoning and the refutation conditions are in the
# script's docstring.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

D=/data/gpfs/projects/punim2657/TORA/dataset
OUT=/data/gpfs/projects/punim2657/TORA/eval_runs/wear_spectrum_diag_${SLURM_JOB_ID}

python scripts/diagnose_wear_spectrum_band.py \
    --erosion "$D/erosion_ceramics.hdf5" \
    --raw     "$D/fractura_real.hdf5" \
    --out-dir "$OUT" \
    --pots "${POTS:-blue_pot,pink_bowl,galli_pot,plate}" \
    --rungs "${RUNGS:-e000,e100}"

echo ""
echo "artifacts in $OUT"
echo "=== done $(date) ==="
