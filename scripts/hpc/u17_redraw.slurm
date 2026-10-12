#!/bin/bash
#SBATCH --job-name=u17-redraw
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/rank_u17/u17_redraw_%j.log
set -euo pipefail
# U17 ticket 03: Juglet Layer 2 re-measured under new point draws (seeds 11-13) plus a
# same-seed control (3), compared per .scratch/attempt-ranker/preregistration-redraw.md.
# Also exports TORA narrow_bottle3's top 5 as posed meshes for the blind look (ticket 09):
# no labels are read for that part.
module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
# OMP_NUM_THREADS stays 1 (Spartan's profile): l2_measure runs one worker process per CPU.
cd /data/gpfs/projects/punim2657/TORA/repo
R=/data/gpfs/projects/punim2657/TORA/rank_u17
J=$R/juglet_32107634
O=$R/redraw_${SLURM_JOB_ID}; mkdir -p "$O"
for s in 3 11 12 13; do
    echo "### Layer 2, seed $s"
    python scripts/l2_measure.py --bundles "$J/bundles" --pot-mm 65 --seed "$s" --out "$O/seed$s.json"
done
python scripts/u17_redraw.py --ranks "$R/jug_v2_32274553/ranks.json" --l2 "$R/l2_32147567/juglet_l2.json" \
    --redraws "$O"/seed3.json "$O"/seed11.json "$O"/seed12.json "$O"/seed13.json \
    --key "$J/key/idmap.json" --report "$J/report.json" --pot-mm 65 \
    --prereg .scratch/attempt-ranker/preregistration-redraw.md --out "$O/redraw.json"
echo "### Juglet top 5 (jug_top5): which sherds the existing inside-out rule flags (juglet-cause 14)"
python - "$R/jug_v2_32274553/ranks.json" "$R/jug_top5/top.json" <<'PY'
import json, sys
rk = {r["id"]: r for r in json.load(open(sys.argv[1]))["attempts"]}
for t in json.load(open(sys.argv[2]))["attempts"]:
    print(f"pick {t['rank']}: {t['id']} inside_out={rk[t['id']]['inside_out']}")
PY
echo "### TORA narrow_bottle3 top 5 (blind export)"
T=$R/tora_32330575
python scripts/u17_top5_export.py --bundles "$T/narrow_bottle3/bundles" --l2 "$T/narrow_bottle3_l2.json" \
    --ranks "$T/narrow_bottle3/ranks.json" --out "$R/nb3_tora_top5" --k 5
echo "done -> $O, $R/nb3_tora_top5"
