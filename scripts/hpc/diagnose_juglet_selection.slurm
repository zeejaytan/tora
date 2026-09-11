#!/bin/bash
#SBATCH --job-name=tora-jugsel
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_jugsel_%j.log

set -euo pipefail

# Why the Juglet's break-face selection is a scatter, and whether the
# tight-gap + opposite-partner rule fixes it. The synthetic gate runs first in
# the same log: the harness must reproduce the proven 99%+ recall on the
# geometry that rule was proven on before its reading of the Juglet counts,
# and the script exits non-zero without touching the Juglet if it does not.
# Second run (after 30419474): adds the overlap test -- whether each join dot
# lies inside the neighbouring closed sherd, by winding number, with its own
# push-in/push-out control. The winding sums are why the limit is an hour.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

D=/data/gpfs/projects/punim2657/TORA/dataset
O=/data/gpfs/projects/punim2657/TORA/eval_runs/sherd_scale
mkdir -p "$O"

python scripts/diagnose_juglet_selection.py --synthetic \
    --juglet   "$D/juglet_gt.hdf5" \
    --out-json "$O/juglet_selection.json" \
    --out-png  "$O/juglet_selection.png"

echo "=== done $(date) ==="
