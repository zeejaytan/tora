#!/bin/bash
#SBATCH --job-name=u17-overlap6
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=128G
#SBATCH --time=06:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/rank_u17/u17_overlap6_%j.log
set -euo pipefail
# U17 Revision 6: overlap judged by how far it reaches from the sherd's own break (a pressed
# join stays near the break; a sherd lying on another does not). Cut-off on GARF's
# calibration pots; seen pots re-ranked as checks; cost read on the fresh TORA attempts of
# job 32352965 (unseen genuine attempts on the pots TORA rebuilds). Every rejected genuine
# attempt is drawn. Plan: .scratch/attempt-ranker/preregistration-overlap6.md.
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
OV5=$R/overlap5_32352965; FL=$OV5/fresh_labels.json
O=$R/overlap6_${SLURM_JOB_ID}; mkdir -p "$O"
CAL=(blue_pot narrow_bottle2 narrow_bottle4 pink_bowl plate)
FRESHPOTS=(blue_pot narrow_bottle2 narrow_bottle4 pink_bowl)   # TORA right 45-100%: cost only
L1=(--profile outer --cover-pct 2 --io-gate off --near-pct 12 --unjudged fail)
PRE=.scratch/attempt-ranker/preregistration-overlap6.md
FR=("$T"/eval_runs/u10_fractura_untouched_s1[0-9][0-9]_3235296[34])
echo "fresh runs: ${#FR[@]} (expect 10)"; [[ ${#FR[@]} -eq 10 ]]

for p in "${FRESHPOTS[@]}"; do
    echo "### fresh $p (cost side only)"
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
python scripts/u17_overlap.py --prereg "$PRE" --field reach --profile-pct 0.873 --out "$O/report.json" \
    --calib-pots "$CALR" "$GL" "$O/ov/garf" "${CAL[@]}" \
    --pots garf-test "$TESTR" "$GL" "$O/ov/garf" narrow_bottle3 galli_pot \
    --pots tora-seen "$TORAR" "$TL" "$O/ov/tora" narrow_bottle3 plate \
    --pots fresh "$O/fresh" "$FL" "$O/ov/fresh" "${FRESHPOTS[@]}"

echo "### drawings: plates, then every pot's rejected genuine attempts (worst 3)"
python scripts/overlap_look.py --bundles "$B/plate/bundles" --report "$O/report.json" \
    --pot garf-calibration/plate --out "$O/garf_plate.png"
python scripts/overlap_look.py --bundles "$TORAR/plate/bundles" --report "$O/report.json" \
    --pot tora-seen/plate --out "$O/tora_plate.png"
draw_failed() {  # set pot bundles
    python scripts/overlap_look.py --bundles "$3" --report "$O/report.json" --pot "$1/$2" \
        --failed 3 --out "$O/rejected_${1}_$2.png" || echo "$1/$2: nothing rejected"
}
for p in "${CAL[@]}"; do draw_failed garf-calibration "$p" "$B/$p/bundles"; done
for p in narrow_bottle3 galli_pot; do draw_failed garf-test "$p" "$B/$p/bundles"; done
for p in narrow_bottle3 plate; do draw_failed tora-seen "$p" "$TORAR/$p/bundles"; done
for p in "${FRESHPOTS[@]}"; do draw_failed fresh "$p" "$O/fresh/$p/bundles"; done
echo "done -> $O"
