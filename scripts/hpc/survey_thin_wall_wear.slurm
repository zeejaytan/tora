#!/bin/bash
#SBATCH --job-name=tora-wallsurvey
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=96G
#SBATCH --time=04:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_wallsurvey_%j.log

set -euo pipefail

# Find every object the wear model crumples instead of wearing.
# See scripts/survey_thin_wall_wear.py for what prompted this.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

python scripts/survey_thin_wall_wear.py \
    --out-json /data/gpfs/projects/punim2657/TORA/thin_wall_survey.json
