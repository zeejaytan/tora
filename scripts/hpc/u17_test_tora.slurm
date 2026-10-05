#!/bin/bash
#SBATCH --job-name=u17-tora
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=128G
#SBATCH --time=04:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/rank_u17/u17_tora_%j.log
set -euo pipefail
# U17 ticket 06: the ranker, unchanged, on TORA's Fractura attempts (28 u10_fractura_* runs,
# 20 attempts each per pot). Cut-offs fixed from GARF's calibration (calib_32274553); read-outs
# and success rule in .scratch/attempt-ranker/preregistration-tora.md.
module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
# OMP_NUM_THREADS stays 1 (Spartan's profile): the long steps run one worker process per CPU.
cd /data/gpfs/projects/punim2657/TORA/repo
T=/data/gpfs/projects/punim2657/TORA
R=$T/rank_u17
D=$T/dataset
LABELS=$R/tora_fractura_labels.json
CAL=$R/calib_32274553/calib.json
O=$R/tora_${SLURM_JOB_ID}; mkdir -p "$O"
POTS=(narrow_bottle3 plate)
PROFILE=0.873
UNFIX=2.31
L1=(--profile outer --cover-pct 2 --io-gate off --near-pct 12 --unjudged fail)
for p in "${POTS[@]}"; do
    echo "### $p"
    # the clouds file holding this pot, in each of the 28 runs (picked by the name stored inside)
    mapfile -t RUNS < <(python - "$p" "$T"/eval_runs/u10_fractura_*/clouds/*.npz <<'PY'
import sys, numpy as np
pot, files = sys.argv[1], sys.argv[2:]
for f in files:
    if str(np.load(f, allow_pickle=True)["name"]).endswith("/" + pot):
        print(f)
PY
)
    echo "runs: ${#RUNS[@]} (expect 28)"; [[ ${#RUNS[@]} -eq 28 ]]
    python scripts/rank_convert.py --runs "${RUNS[@]}" --hdf5 "$D/fractura_fresh.hdf5" \
        --object "fractura_fresh/$p" --pot-mm 100 --out "$O/$p/bundles" --key "$O/$p/key" --check 10
    python scripts/l2_measure.py --bundles "$O/$p/bundles" --out "$O/${p}_l2.json"
    python scripts/rank_attempts.py --bundles "$O/$p/bundles" --out "$O/$p/ranks.json" \
        --pot-mm 100 --bin-pct 10.77 --profile-pct "$PROFILE" "${L1[@]}"
done
python scripts/u17_test.py --method tora --root "$O" --labels "$LABELS" --calib "$CAL" \
    --profile-pct "$PROFILE" --unfixable-pct "$UNFIX" --pots "${POTS[@]}" --pot-mm 100 \
    --prereg .scratch/attempt-ranker/preregistration-tora.md --out "$O/test.json"
for p in "${POTS[@]}"; do
    python scripts/l2_top_look.py --bundles "$O/$p/bundles" --l2 "$O/${p}_l2.json" \
        --ranks "$O/$p/ranks.json" --key "$O/$p/key/idmap.json" --out "$O/${p}_top5.png" \
        --n 20 --k 5
    python scripts/l1_look.py --root "$O" --bundles "$O/$p/bundles" --labels "$LABELS" \
        --pot "$p" --pot-mm 100 --bin-pct 10.77 --profile outer --cover-pct 2 --near-pct 12 \
        --fail-pct "$PROFILE" --out "$O/$p.png"
done
