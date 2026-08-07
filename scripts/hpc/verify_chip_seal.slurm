#!/bin/bash
#SBATCH --job-name=tora-chipseal
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --time=04:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_chipseal_%j.log

set -euo pipefail

# Acceptance test for the chip-scar fix.
#
# Chips used to delete faces and leave the wound open, so every sherd came out
# perforated at every wear level although the scans arrived sealed. They are now
# capped with a shallow inward dish -- material still gone, sherd still solid.
#
# Three things have to hold, and the third is the one that would otherwise be
# missed:
#
#   1. Every sherd sealed at every wear level. Directly comparable with the
#      earlier table, same objects, same script.
#   2. Chipping no longer inflates roughness. Sharp hole rims were being read as
#      break-surface texture -- that is what made the plate look like it was
#      getting rougher (+6.6% with chips, -5.6% without). With scars sealed, the
#      two should now agree.
#   3. The scar must not undo the wear. Capping adds faces back, and a cap
#      placed outward instead of inward would restore material that wear just
#      removed. Face counts and roughness are reported so that shows up.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

echo ""
echo "### 1/2  are the sherds sealed now? ###"
echo "(compare with job 28876346: every level was 0 sealed)"
python scripts/check_mesh_integrity.py \
    --objects ceramics__plate,ceramics__blue_pot,egg__egg1,bones__limb3,ceramics__narrow_bottle3

echo ""
echo "### 2/2  do chips still inflate roughness? ###"
echo "(before the fix: plate +6.6% with chips vs -5.6% without)"
python scripts/test_roughness_without_chips.py
