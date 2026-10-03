#!/bin/bash
#SBATCH --job-name=u17-l1-look
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=32G
#SBATCH --time=00:30:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/rank_u17/u17_l1_look_%j.log
set -euo pipefail
# U17 calibration debug: why Layer 1 fails correct attempts on plate and narrow_bottle4.
module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo
R=/data/gpfs/projects/punim2657/TORA/rank_u17
C=$R/calib_32157454
O=$R/l1look_${SLURM_JOB_ID}; mkdir -p "$O"
for p in plate narrow_bottle4 pink_bowl; do
    python scripts/l1_look.py --root "$C" --bundles "$R/l2_32147567/$p/bundles" \
        --labels "$R/fractura_labels_32111374.json" --pot "$p" --pot-mm 100 --bin-pct 10.77 \
        --out "$O/$p.png"
done
