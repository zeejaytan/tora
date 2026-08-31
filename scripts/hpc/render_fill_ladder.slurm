#!/bin/bash
#SBATCH --job-name=tora-fillladder
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=00:40:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_fillladder_%j.log

set -euo pipefail

# The corpus screen (job 29765705) says 37% of the training corpus is SOLID and
# that 97% of objects sit on one diagonal: resolvable break face => not a
# vessel. That is a strong claim resting on one scalar. Its arithmetic is
# selftested against a sphere and two shells; its LABELS on real fractured
# objects are not. This draws eight objects spanning fill 0.04 to 0.99 so the
# eye can check the bins before the verdict is reported.

cd /data/gpfs/projects/punim2657/TORA
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate ./envs/tora
export PYTHONPATH=repo:repo/scripts

python repo/scripts/render_fill_ladder.py \
  --root . --out artifacts/fill_ladder.png

echo ""
echo "=== Finished at $(date) ==="
