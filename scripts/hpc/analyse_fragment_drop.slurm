#!/bin/bash
#SBATCH --job-name=tora-drop-analyse
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=00:40:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_drop_analyse_%j.log

set -euo pipefail

# READ AN ALREADY-FINISHED FRAGMENT-DROP JOB. No GPU, no model, no sampling.
#
# This exists because the analysis is not free. `readout.chamfer` compares every
# point against every point -- it has to, because that is exactly what the
# evaluator thresholds and a cheaper approximation would be a different ruler
# from the one that produced the numbers being compared. Over seven arms, eight
# pots and ten draws each that is enough work to be thrown off a login node,
# which is where it belongs in a batch script rather than in an ssh one-liner.
#
# It also renders, because the summary is not readable without the pictures: the
# turn column and the render disagreed on this data and the render was right.
#
# Usage:
#   JOBID=30167044 sbatch scripts/hpc/analyse_fragment_drop.slurm
#   JOBID=30167044 POTS="blue_pot plate pink_bowl" RANKS="2 3" sbatch ...

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
ENV_PREFIX=$TORA_ROOT/envs/tora
L=$TORA_ROOT/eval_runs
JOBID=${JOBID:?set JOBID to the fragment-drop job being read}
RANKS=${RANKS:-"2 3 4 5 6"}
POTS=${POTS:-"blue_pot plate pink_bowl"}
JUGLET=${JUGLET:-$L/jugdraw_baseline_30130049}
FRESH_POTS=${FRESH_POTS:-"plate narrow_bottle1 galli_pot"}

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate "$ENV_PREFIX"
cd "$TORA_ROOT/repo"

OUT=$L/drop_whole_${JOBID}
[ -d "$OUT" ] || { echo "no such run: $OUT"; exit 1; }

DROPPED=()
for K in $RANKS; do
    D="$L/drop_rank${K}_${JOBID}"
    [ -d "$D/results" ] && DROPPED+=("$D")
done

echo "=== reading job $JOBID at $(date) on $(hostname) ==="
echo ""
echo "### did the sherds we KEPT still go to the right place ###"
python scripts/summarise_fragment_drop.py \
    --whole "$L/drop_whole_${JOBID}" \
    --reseed "$L/drop_reseed_${JOBID}" \
    --dropped "${DROPPED[@]}"

echo ""
echo "### does the vessel still close ###"
for K in $RANKS; do
    D="$L/drop_rank${K}_${JOBID}"
    [ -d "$D/clouds" ] || continue
    python scripts/render_fragment_drop.py \
        --whole "$L/drop_whole_${JOBID}" --dropped "$D" \
        --pots $POTS --out "$D/fragment_drop_rank${K}.png" || true
done

echo ""
echo "### the Juglet beside fresh pots that score the same (ticket 02) ###"
if [ -d "$JUGLET/clouds" ]; then
    python scripts/render_juglet_vs_fresh.py \
        --juglet "$JUGLET" --fresh "$L/drop_whole_${JOBID}" \
        --pots $FRESH_POTS \
        --out "$L/drop_whole_${JOBID}/juglet_vs_fresh.png" || true
fi

echo ""
find "$L" -path "*_${JOBID}*" -name "*.png" | sort
echo ""
echo "=== Finished at $(date) ==="
