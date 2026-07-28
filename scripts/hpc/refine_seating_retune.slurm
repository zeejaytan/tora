#!/bin/bash
#SBATCH --job-name=tora-refine-retune
#SBATCH --partition=cascade
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_refine_retune_%j.log

set -euo pipefail

# S2b — retune the settling step against the MEASURED error scale.
#
# The first attempt (job 28229957) used a reach of 0.06 and changed nothing.
# Diagnosis: at full wear the typical fragment sits 0.35 from where it belongs
# (90th pct 1.2), while the seating tolerance is ~0.14 -- so the refiner could
# only reach 12% of fragments. It was mis-scaled by roughly 5x.
#
# This sweeps the reach across the real error scale. Two possible outcomes,
# both worth knowing:
#   * seating improves  -> the failure IS recoverable settling, just at the
#                          right scale, and this is a cheap fix requiring no
#                          retraining;
#   * still nothing     -> the fragments are not "nearly right", they are in
#                          the WRONG PLACE, and no post-hoc geometry can fix
#                          it. The fix must then improve the prediction itself
#                          (S3), not tidy it afterwards.

echo "=== S2b refinement retune started at $(date) ==="

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
ENV_PREFIX=$TORA_ROOT/envs/tora
CLOUDS=$TORA_ROOT/eval_runs/refine_src_28229957/clouds

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate "$ENV_PREFIX"
cd "$TORA_ROOT/repo"

for MC in 0.06 0.15 0.30 0.50; do
    echo ""
    echo "########## reach = $MC ##########"
    python scripts/refine_seating.py \
        --clouds-dir "$CLOUDS" \
        --iters 80 --max-corr $MC --reg 0.10 \
        2>&1 | tail -6
done

echo ""
echo "=== Finished at $(date) ==="
