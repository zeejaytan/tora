#!/bin/bash
#SBATCH --job-name=u17-relabel
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=96G
#SBATCH --time=04:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/rank_u17/u17_relabel_%j.log
set -euo pipefail
# U17 ticket 10: re-label every attempt with the turn limit (own_place.TURN_LIMIT_DEG),
# the same attempts as the old label files, then re-read what depended on the labels:
# the calibration cut-off, the GARF and TORA tests, and the Juglet's genuine/near count.
# Plan: .scratch/attempt-ranker/issues/10-key-turn-limit.md.
module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
# OMP_NUM_THREADS stays 1 (Spartan's profile): label_attempts runs one worker per CPU.
cd /data/gpfs/projects/punim2657/TORA/repo
T=/data/gpfs/projects/punim2657/TORA
R=$T/rank_u17
L=/data/gpfs/projects/punim2657/GARF/logs/rwlora
GL=$R/fractura_labels_32111374.json; TL=$R/tora_fractura_labels.json
O=$R/relabel_${SLURM_JOB_ID}; mkdir -p "$O"
runs_of() {  # label file, base dir -> the run directories it labelled
    python - "$1" "$2" <<'PY'
import json, sys
for r in sorted({r["run"] for r in json.load(open(sys.argv[1]))}):
    print(f"{sys.argv[2]}/{r}")
PY
}
mapfile -t GR < <(runs_of "$GL" "$L"); mapfile -t TR < <(runs_of "$TL" "$T/eval_runs")
JR=(); while read -r d; do JR+=("$L/$d"); done < .scratch/attempt-ranker/juglet_runs.txt
echo "runs: GARF Fractura ${#GR[@]} (expect 70), TORA Fractura ${#TR[@]} (expect 28), Juglet ${#JR[@]} (expect 70)"
for d in "${GR[@]}" "${TR[@]}" "${JR[@]}"; do [[ -d $d ]] || { echo "missing $d"; exit 1; }; done

python scripts/label_attempts.py --runs "${GR[@]}" --out "$O/garf_fractura_labels.json"
python scripts/label_attempts.py --runs "${TR[@]}" --out "$O/tora_fractura_labels.json"
python scripts/label_attempts.py --runs "${JR[@]}" --out "$O/juglet_labels.json"
echo "### what the turn limit changes"
python scripts/u17_relabel_diff.py --new "$O/garf_fractura_labels.json" --old "$GL" --name "GARF Fractura"
python scripts/u17_relabel_diff.py --new "$O/tora_fractura_labels.json" --old "$TL" --name "TORA Fractura"
python scripts/u17_relabel_diff.py --new "$O/juglet_labels.json" --name "GARF Juglet"

echo "### calibration cut-off with the new labels (Revision 3 rule, ranks of calib_32274553)"
python scripts/u17_calibrate.py --root "$R/calib_32274553" --labels "$O/garf_fractura_labels.json" \
    --pots blue_pot narrow_bottle2 narrow_bottle4 pink_bowl plate --pot-mm 100 \
    --rule .scratch/attempt-ranker/calibration-fractura.md --out "$O/calib.json" \
    --io-gate off --unjudged fail
echo "### tests re-read with the new labels (cut-offs unchanged: 0.873, 2.31)"
mkdir -p "$O/test_garf" "$O/test_tora"
for p in narrow_bottle3 galli_pot; do
    ln -sfn "$R/test_32317912/$p" "$O/test_garf/$p"; ln -sf "$R/test_32317912/${p}_l2.json" "$O/test_garf/${p}_l2.json"
done
for p in narrow_bottle3 plate; do
    ln -sfn "$R/tora_32330575/$p" "$O/test_tora/$p"; ln -sf "$R/tora_32330575/${p}_l2.json" "$O/test_tora/${p}_l2.json"
done
python scripts/u17_test.py --root "$O/test_garf" --labels "$O/garf_fractura_labels.json" \
    --calib "$R/calib_32274553/calib.json" --profile-pct 0.873 --unfixable-pct 2.31 \
    --pots narrow_bottle3 galli_pot --pot-mm 100 \
    --prereg .scratch/attempt-ranker/preregistration-test.md --out "$O/test_garf.json"
python scripts/u17_test.py --method tora --root "$O/test_tora" --labels "$O/tora_fractura_labels.json" \
    --calib "$R/calib_32274553/calib.json" --profile-pct 0.873 --unfixable-pct 2.31 \
    --pots narrow_bottle3 plate --pot-mm 100 \
    --prereg .scratch/attempt-ranker/preregistration-tora.md --out "$O/test_tora.json"
echo "relabel and test re-reads done -> $O"
echo "### ticket 11: inside-out gate with a size guard (labels with the turn limit)"
B=$R/l2_32147567; TORAR=$R/tora_32330575
python scripts/u17_io_guard.py --prereg .scratch/attempt-ranker/preregistration-io-guard.md \
    --profile-pct 0.873 --calib garf-calibration --out "$O/io_guard.json" \
    --set garf-calibration "$R/calib_32274553" "$B" "$O/garf_fractura_labels.json" \
        blue_pot narrow_bottle2 narrow_bottle4 pink_bowl plate \
    --set garf-test "$O/test_garf" "$B" "$O/garf_fractura_labels.json" narrow_bottle3 galli_pot \
    --set tora-seen "$O/test_tora" "$TORAR" "$O/tora_fractura_labels.json" narrow_bottle3 plate
echo "done (io guard) -> $O/io_guard.json"
