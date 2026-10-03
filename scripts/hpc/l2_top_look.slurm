#!/bin/bash
#SBATCH --job-name=u17-l2-top
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=32G
#SBATCH --time=00:30:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/rank_u17/u17_l2_top_%j.log
set -euo pipefail
# U17 ticket 02: debug look at the Layers 1+2 top places (labels + picture).
module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo
R=/data/gpfs/projects/punim2657/TORA/rank_u17
J=$R/juglet_32107634
O=$R/l2top_${SLURM_JOB_ID}; mkdir -p "$O"
python scripts/l2_top_look.py --bundles "$J/bundles" --l2 "$R/l2_32147567/juglet_l2.json" \
    --ranks "$J/ranks.json" --key "$J/key/idmap.json" --out "$O/top5.png" --n 20 --k 5
