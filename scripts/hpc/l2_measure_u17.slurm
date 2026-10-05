#!/bin/bash
#SBATCH --job-name=u17-l2-gap
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=96G
#SBATCH --time=03:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/rank_u17/u17_l2_gap_%j.log

set -euo pipefail

# U17 ticket 02 groundwork: how tightly GARF's attempts sit at their breaks, in % of pot
# size, on the Juglet and all 8 Fractura pots. Attempt side reads bundles only
# (l2_measure.py); the true-assembly floor comes from the key side (l2_truth.py).

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
# OMP_NUM_THREADS stays 1 (Spartan's profile): the long steps run one worker process per CPU.
cd /data/gpfs/projects/punim2657/TORA/repo

D=/data/gpfs/projects/punim2657/TORA/dataset
L=/data/gpfs/projects/punim2657/GARF/logs/rwlora
O=/data/gpfs/projects/punim2657/TORA/rank_u17/l2_${SLURM_JOB_ID}
mkdir -p "$O"

echo "### Juglet (existing bundles, job 32107634)"
python scripts/l2_measure.py --bundles /data/gpfs/projects/punim2657/TORA/rank_u17/juglet_32107634/bundles \
    --pot-mm 65 --out "$O/juglet_l2.json"
python scripts/l2_truth.py --hdf5 "$D/juglet_gt.hdf5" --object juglet_gt/Juglet-000 --out "$O/juglet_truth.json"

POTS=(blue_pot galli_pot narrow_bottle1 narrow_bottle2 narrow_bottle3 narrow_bottle4 pink_bowl plate)
OBJS=()
for i in "${!POTS[@]}"; do
    p=${POTS[$i]}; OBJS+=("fractura_fresh/$p")
    RUNS=()
    while read -r d; do RUNS+=("$L/${d/juglet_gt/fractura_fresh}/version_0/clouds/$i.npz"); done \
        < .scratch/attempt-ranker/juglet_runs.txt
    echo "### $p (clouds/$i.npz, ${#RUNS[@]} runs)"
    # nominal pot size 100 mm: Fractura has no real size; l2 works in % of pot either way
    python scripts/rank_convert.py --runs "${RUNS[@]}" --hdf5 "$D/fractura_fresh.hdf5" \
        --object "fractura_fresh/$p" --pot-mm 100 --out "$O/$p/bundles" --key "$O/$p/key" --check 10
    python scripts/l2_measure.py --bundles "$O/$p/bundles" --out "$O/${p}_l2.json"
done
python scripts/l2_truth.py --hdf5 "$D/fractura_fresh.hdf5" --object "${OBJS[@]}" --out "$O/fractura_truth.json"
echo "done -> $O"
