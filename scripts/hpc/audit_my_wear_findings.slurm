#!/bin/bash
#SBATCH --job-name=tora-audit
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --time=03:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_audit_%j.log

set -euo pipefail

# The conservator inspected the plate, eggshell and bone at every wear level and
# found them all fine apart from the chip holes. My measurements claim the plate
# loses 29% of its wall and the eggshell 37%, and that wear runs backwards on
# thin shells.
#
# Both cannot be true. Between a conservator's eye on the actual meshes and two
# statistics I wrote yesterday, the statistics get audited.
#
#   1. validate_wall_estimator -- slabs of KNOWN thickness. If the estimator
#      reports thinning on a wall we control, it is responding to edge rounding
#      and every wall number I have reported is void.
#
#   2. test_roughness_without_chips -- the "wear runs backwards" result with
#      chipping switched off. A chip hole has a rim, and a rim is exactly what a
#      roughness measure detects. On an eggshell those rims are a large part of
#      the surface.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

echo ""
echo "### 1/2  is the wall estimator measuring edge rounding? ###"
python scripts/validate_wall_estimator.py

echo ""
echo "### 2/2  does roughness still run backwards without chips? ###"
python scripts/test_roughness_without_chips.py
