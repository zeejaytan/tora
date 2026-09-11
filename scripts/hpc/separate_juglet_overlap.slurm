#!/bin/bash
#SBATCH --job-name=tora-jugsep
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=05:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_jugsep_%j.log

set -euo pipefail

# Move the Juglet's reference sherds apart where the hand reassembly set them
# into each other (jobs 30420351 / 30420961: a third of the join dots inside
# the neighbour). The reference file is only read; the separated copies go to
# eval_runs/, and are written only if the box selftest, both targets and gates
# G1 (re-run moves nothing) and G2 (a pushed sherd comes back) all pass. Then
# the break-face selection is read again on each copy, in the original's mm.
# The winding sums are why it asks for 8 CPUs and five hours.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1

D=/data/gpfs/projects/punim2657/TORA/dataset
O=/data/gpfs/projects/punim2657/TORA/eval_runs/sherd_scale
mkdir -p "$O"

python scripts/selftest_separate_juglet.py

python scripts/separate_juglet_overlap.py \
    --juglet  "$D/juglet_gt.hdf5" \
    --out-dir "$O" \
    --workers "$SLURM_CPUS_PER_TASK"

for s in strict tolerant; do
    echo ""
    echo "=== break-face selection on the $s copy ==="
    python scripts/diagnose_juglet_selection.py \
        --juglet     "$O/juglet_gt_separated_$s.hdf5" \
        --scale-from "$D/juglet_gt.hdf5" \
        --out-json   "$O/juglet_selection_sep_$s.json" \
        --out-png    "$O/juglet_selection_sep_$s.png"
done

echo "=== done $(date) ==="
