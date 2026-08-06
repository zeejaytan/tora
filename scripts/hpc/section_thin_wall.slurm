#!/bin/bash
#SBATCH --job-name=tora-wallsection
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=96G
#SBATCH --time=02:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_wallsection_%j.log

set -euo pipefail

# Draw the wall in cross-section, fresh vs worn, before trusting the crumpling
# story any further. See scripts/section_thin_wall.py.
#
# Two eggs (worst affected), one mid-range case, and a thick-walled control. If
# the control buckles too, the drawing is wrong, not the wear model.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

python scripts/section_thin_wall.py \
    --objects egg__egg1,egg__egg2,bones__limb2,ceramics__blue_pot \
    --out-dir /data/gpfs/projects/punim2657/TORA/wall_sections
