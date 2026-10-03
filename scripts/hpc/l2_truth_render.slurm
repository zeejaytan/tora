#!/bin/bash
#SBATCH --job-name=u17-l2-look
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=00:30:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/rank_u17/u17_l2_look_%j.log
set -euo pipefail
# U17 ticket 02 debug look: why Fractura true joins read 1-2% of pot (Juglet 0.6%).
module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo
D=/data/gpfs/projects/punim2657/TORA/dataset
O=/data/gpfs/projects/punim2657/TORA/rank_u17/look_${SLURM_JOB_ID}; mkdir -p "$O"
python scripts/l2_truth_render.py --hdf5 "$D/fractura_fresh.hdf5" --object fractura_fresh/pink_bowl --out "$O/pink_bowl.png"
python scripts/l2_truth_render.py --hdf5 "$D/fractura_fresh.hdf5" --object fractura_fresh/galli_pot --out "$O/galli_pot.png"
python scripts/l2_truth_render.py --hdf5 "$D/juglet_gt.hdf5" --object juglet_gt/Juglet-000 --out "$O/juglet.png"
