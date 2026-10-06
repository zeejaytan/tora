#!/bin/bash
#SBATCH --job-name=u17-overlap5
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=128G
#SBATCH --time=06:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/rank_u17/u17_overlap5_%j.log
set -euo pipefail
# U17 Revision 5: overlap area away from joins. Cut-off on GARF's calibration pots; tested
# on fresh TORA draws (FRESH="<job id> [<job id> ...]" of u10_juglet_arm.slurm with
# SET=fractura ARM=untouched, seeds 101-110 between them); seen pots re-ranked as checks.
# Plan: .scratch/attempt-ranker/preregistration-overlap5.md.
FRESH="${FRESH:?FRESH=<job id(s) of the fresh TORA draws>}"
module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo
T=/data/gpfs/projects/punim2657/TORA
R=$T/rank_u17
D=$T/dataset
B=$R/l2_32147567; CALR=$R/calib_32274553; TESTR=$R/test_32317912; TORAR=$R/tora_32330575
GL=$R/fractura_labels_32111374.json; TL=$R/tora_fractura_labels.json
O=$R/overlap5_${SLURM_JOB_ID}; mkdir -p "$O"
CAL=(blue_pot narrow_bottle2 narrow_bottle4 pink_bowl plate)
L1=(--profile outer --cover-pct 2 --io-gate off --near-pct 12 --unjudged fail)
PRE=.scratch/attempt-ranker/preregistration-overlap5.md

echo "### fresh TORA draws (job $FRESH): label, then pick the pots that qualify"
FR=()
for j in $FRESH; do FR+=("$T"/eval_runs/u10_fractura_untouched_s1[0-9][0-9]_"$j"); done
for d in "${FR[@]}"; do [[ -d "$d/clouds" ]] || { echo "missing: $d/clouds"; exit 1; }; done
echo "runs: ${#FR[@]} (expect 10)"; [[ ${#FR[@]} -eq 10 ]]
python scripts/label_attempts.py --runs "${FR[@]}" --out "$O/fresh_labels.json"
mapfile -t POTS < <(python - "$O/fresh_labels.json" <<'PY'
import json, sys
from collections import defaultdict
by = defaultdict(list)
for r in json.load(open(sys.argv[1])):
    by[r["pot"].split("/")[-1]].append(r["oriented"] == r["n"])
for p, g in sorted(by.items()):
    if 0 < sum(g) <= 0.10 * len(g):
        print(p)
PY
)
echo "qualifying fresh pots: ${POTS[*]:-none}"

for p in "${POTS[@]}"; do
    echo "### fresh $p"
    mapfile -t RUNS < <(python - "$p" "${FR[@]/%//clouds/*.npz}" <<'PY'
import glob, sys, numpy as np
pot = sys.argv[1]
for g in sys.argv[2:]:
    for f in glob.glob(g):
        if str(np.load(f, allow_pickle=True)["name"]).endswith("/" + pot):
            print(f)
PY
)
    echo "runs: ${#RUNS[@]} (expect 10)"; [[ ${#RUNS[@]} -eq 10 ]]
    python scripts/rank_convert.py --runs "${RUNS[@]}" --hdf5 "$D/fractura_fresh.hdf5" \
        --object "fractura_fresh/$p" --pot-mm 100 --out "$O/fresh/$p/bundles" \
        --key "$O/fresh/$p/key" --check 10
    python scripts/l2_measure.py --bundles "$O/fresh/$p/bundles" --out "$O/fresh/${p}_l2.json"
    python scripts/rank_attempts.py --bundles "$O/fresh/$p/bundles" --out "$O/fresh/$p/ranks.json" \
        --pot-mm 100 --bin-pct 10.77 --profile-pct 0.873 "${L1[@]}"
    python scripts/overlap_measure.py --bundles "$O/fresh/$p/bundles" --out "$O/ov/fresh/${p}_overlap.json"
done

echo "### overlap on GARF (calibration and test pots) and TORA's earlier attempts"
for p in "${CAL[@]}" narrow_bottle3 galli_pot; do
    python scripts/overlap_measure.py --bundles "$B/$p/bundles" --out "$O/ov/garf/${p}_overlap.json"
done
for p in narrow_bottle3 plate; do
    python scripts/overlap_measure.py --bundles "$TORAR/$p/bundles" --out "$O/ov/tora/${p}_overlap.json"
done
FRESHSET=()
[[ ${#POTS[@]} -gt 0 ]] && FRESHSET=(--pots fresh "$O/fresh" "$O/fresh_labels.json" "$O/ov/fresh" "${POTS[@]}")
python scripts/u17_overlap.py --prereg "$PRE" --field area --profile-pct 0.873 --out "$O/report.json" \
    --calib-pots "$CALR" "$GL" "$O/ov/garf" "${CAL[@]}" \
    --pots garf-test "$TESTR" "$GL" "$O/ov/garf" narrow_bottle3 galli_pot \
    --pots tora-seen "$TORAR" "$TL" "$O/ov/tora" narrow_bottle3 plate "${FRESHSET[@]}"
python scripts/overlap_look.py --bundles "$B/plate/bundles" --report "$O/report.json" \
    --pot garf-calibration/plate --out "$O/garf_plate.png"
python scripts/overlap_look.py --bundles "$TORAR/plate/bundles" --report "$O/report.json" \
    --pot tora-seen/plate --out "$O/tora_plate.png"
for p in "${POTS[@]}"; do
    python scripts/overlap_look.py --bundles "$O/fresh/$p/bundles" --report "$O/report.json" \
        --pot "fresh/$p" --out "$O/fresh_$p.png"
done
