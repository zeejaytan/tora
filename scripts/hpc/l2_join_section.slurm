#!/bin/bash
#SBATCH --job-name=u17-l2-cut
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=32G
#SBATCH --time=00:30:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/rank_u17/u17_l2_cut_%j.log
set -euo pipefail
# U17 ticket 02 debug: do Fractura's true joins touch? cut across one join; true gap after nudge.
module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-1}"  # Spartan's profile sets 1; one python process here
cd /data/gpfs/projects/punim2657/TORA/repo
D=/data/gpfs/projects/punim2657/TORA/dataset
O=/data/gpfs/projects/punim2657/TORA/rank_u17/cut_${SLURM_JOB_ID}; mkdir -p "$O"
for p in pink_bowl narrow_bottle4 plate; do
  echo "### $p"; python scripts/l2_join_section.py --hdf5 "$D/fractura_fresh.hdf5" --object fractura_fresh/$p --out "$O/$p.png"
done
echo "### juglet"; python scripts/l2_join_section.py --hdf5 "$D/juglet_gt.hdf5" --object juglet_gt/Juglet-000 --out "$O/juglet.png"
