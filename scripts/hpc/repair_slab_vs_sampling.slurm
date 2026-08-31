#!/bin/bash
#SBATCH --job-name=tora-repairslab
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_repairslab_%j.log

set -euo pipefail

# Is RePAIR's fracture inside what TORA can read?
#
# The proposal is a `lora_repair` adapter that teaches "how two worn fractured
# pieces join". Before spending a GPU on it, ask whether the join survives the
# encoder's own sampling. TORA takes 5000 points per object, area-weighted, so
# its cell is sqrt(2*area/5000). A fresco fragment is a thin plaque and its
# fracture is a ribbon around the perimeter. Under one cell through the slab,
# one point straddles the whole thickness, the ribbon gets no row of its own,
# and anything the adapter learns is learned from the plaque's OUTLINE.
#
# Same instrument and same threshold as the vessel corpus (job 29764781, median
# 0.78 cells). Gate A already established the other half of this: RePAIR's
# fracture surfaces carry no fracture-like roughness at any scale those scans
# resolve, texture rising as R^1.7 where a fresh fracture is self-affine at
# R^0.4-0.8 (docs/notes/GATE_A_RESULT.md, job 29404479).

cd /data/gpfs/projects/punim2657/TORA

module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate ./envs/tora

export PYTHONPATH=repo:repo/scripts

python repo/scripts/measure_repair_slab_vs_sampling.py \
  --dir /data/gpfs/projects/punim2657/TORA/repair/OPEN_DISCOVERY/pieces \
  --limit 0 \
  --out artifacts/repair_slab_vs_sampling.csv \
  --render artifacts/repair_slab_vs_sampling.png

echo ""
echo "=== Finished at $(date) ==="
