#!/bin/bash
#SBATCH --job-name=tora-chipsize
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=160G
#SBATCH --time=05:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_chipsize_%j.log

set -euo pipefail

# A chip-SIZE series for visual judgement of how much material a chip should
# take. The standard chip removes 0.002% of a sherd on real scans -- effectively
# cosmetic -- and whether that is too timid is a conservator's call, not one the
# numbers can settle.
#
# blue_pot first: it is the reference object, already inspected and approved, so
# the comparison is against something with a known verdict. The plate second, as
# ordinary pottery with a thinner wall.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

OUT=/data/gpfs/projects/punim2657/TORA/wear_chip_sizes

for OBJ in ceramics__blue_pot ceramics__plate; do
    echo ""
    echo "########## $OBJ ##########"
    python scripts/export_chip_sizes.py --object "$OBJ" --out "$OUT/$OBJ"
done

echo ""
du -sh "$OUT"/*
