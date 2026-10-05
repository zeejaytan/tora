#!/bin/bash
#SBATCH --job-name=u17-l2-report
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/rank_u17/u17_l2_report_%j.log
set -euo pipefail
# U17 ticket 02: Layer 2 joined to labels on the Juglet, per preregistration-l2.md.
module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-1}"  # Spartan's profile sets 1; one python process here
cd /data/gpfs/projects/punim2657/TORA/repo
R=/data/gpfs/projects/punim2657/TORA/rank_u17
J=$R/juglet_32107634
O=$R/l2report_${SLURM_JOB_ID}; mkdir -p "$O"
python scripts/l2_report.py --bundles "$J/bundles" --l2 "$R/l2_32147567/juglet_l2.json" \
    --ranks "$J/ranks.json" --key "$J/key/idmap.json" --report "$J/report.json" \
    --hdf5 /data/gpfs/projects/punim2657/TORA/dataset/juglet_gt.hdf5 --object juglet_gt/Juglet-000 --pot-mm 65 \
    --prereg .scratch/attempt-ranker/preregistration-l2.md --out "$O/l2_report.json"
