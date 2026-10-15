#!/bin/bash
#SBATCH --job-name=icaane-figs
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/figs_icaane/icaane_figs_%j.log

set -euo pipefail

# Draft figures 2-5 of the ICAANE 2027 paper (phd-thesis papers/icaane2027): greyscale
# shaded renders with scale bars, from the juglet bundles of ranker job 32107634 and the
# top-five meshes of attempt-ranker ticket 07. CPU only; reads, never writes, the inputs.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

U=/data/gpfs/projects/punim2657/TORA/rank_u17
O=/data/gpfs/projects/punim2657/TORA/figs_icaane/${SLURM_JOB_ID}
mkdir -p "$O"
python scripts/icaane_figures.py --bundles "$U/juglet_32107634" --top5 "$U/jug_top5" \
    --bbad /data/gpfs/projects/punim2657/TORA/dataset/breaking_bad_vol.hdf5 --out "$O"
ls -la "$O"
