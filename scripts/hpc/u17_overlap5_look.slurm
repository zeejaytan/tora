#!/bin/bash
#SBATCH --job-name=u17-ov5-look
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/rank_u17/u17_overlap5_look_%j.log
set -euo pipefail
# Draw the genuine attempts Revision 5's overlap gate rejected (pre-registration rule:
# every rejected genuine is drawn before anything is reported). OV=<job id of u17_overlap5>.
OV="${OV:?OV=<job id of the u17_overlap5 run>}"
module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo
R=/data/gpfs/projects/punim2657/TORA/rank_u17
B=$R/l2_32147567; TORAR=$R/tora_32330575
O=$R/overlap5_$OV
for p in galli_pot narrow_bottle3; do
    python scripts/overlap_look.py --bundles "$B/$p/bundles" --report "$O/report.json" \
        --pot "garf-test/$p" --failed 3 --out "$O/rejected_garf_$p.png"
done
python scripts/overlap_look.py --bundles "$B/narrow_bottle4/bundles" --report "$O/report.json" \
    --pot garf-calibration/narrow_bottle4 --failed 3 --out "$O/rejected_garf_narrow_bottle4.png"
python - "$O/report.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
for k, v in r["pots"].items():
    if v["genuine_failed_overlap"]:
        print(k, v["genuine_failed_overlap"], "rejected genuine; drawn (worst first):",
              sorted(v["genuine_failed_why"], key=lambda w: -w["inside"])[:3])
PY
