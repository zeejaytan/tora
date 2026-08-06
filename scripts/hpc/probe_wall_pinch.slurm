#!/bin/bash
#SBATCH --job-name=tora-wallpinch
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --time=03:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_wallpinch_%j.log

set -euo pipefail

# The cross-section failed (blank panels, wrong window). Render the measured
# quantity itself instead. See scripts/probe_wall_pinch.py.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

python scripts/probe_wall_pinch.py \
    --objects egg__egg1,egg__egg2,bones__limb2,ceramics__blue_pot,bones__limb6 \
    --out-dir /data/gpfs/projects/punim2657/TORA/wall_pinch
