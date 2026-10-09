#!/bin/bash
#SBATCH --job-name=u17-test
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --time=04:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/rank_u17/u17_test_%j.log
set -euo pipefail
# U17 test: the ranker on the held-out Fractura pots with the Revision 3 cut-offs fixed
# (calib_32274553), read-outs and success rule in .scratch/attempt-ranker/preregistration-test.md.
module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
# OMP_NUM_THREADS stays 1 (Spartan's profile): the long steps run one worker process per CPU.
cd /data/gpfs/projects/punim2657/TORA/repo
R=/data/gpfs/projects/punim2657/TORA/rank_u17
B=$R/l2_32147567
CAL=$R/calib_32274553/calib.json
LABELS=$R/fractura_labels_32111374.json
O=$R/test_${SLURM_JOB_ID}; mkdir -p "$O"
POTS=(narrow_bottle3 galli_pot)
PROFILE=0.873   # Layer 1 profile cut-off, % of pot (Revision 3 calibration)
UNFIX=2.31      # Layer 2 unfixable flag, % of pot
L1=(--profile outer --cover-pct 2 --io-gate off --near-pct 12 --unjudged fail)
for p in "${POTS[@]}"; do
    echo "### $p"
    mkdir -p "$O/$p"
    ln -sfn "$B/$p/key" "$O/$p/key"
    ln -sf "$B/${p}_l2.json" "$O/${p}_l2.json"
    python scripts/rank_attempts.py --bundles "$B/$p/bundles" --out "$O/$p/ranks.json" \
        --pot-mm 100 --bin-pct 10.77 --profile-pct "$PROFILE" "${L1[@]}"
done
python scripts/u17_test.py --root "$O" --labels "$LABELS" --calib "$CAL" \
    --profile-pct "$PROFILE" --unfixable-pct "$UNFIX" --pots "${POTS[@]}" --pot-mm 100 \
    --prereg .scratch/attempt-ranker/preregistration-test.md --out "$O/test.json"
# render rule: the top 5 under Layers 1+2 per pot, and the median genuine attempt's profile
for p in "${POTS[@]}"; do
    python scripts/l2_top_look.py --bundles "$B/$p/bundles" --l2 "$O/${p}_l2.json" \
        --ranks "$O/$p/ranks.json" --key "$O/$p/key/idmap.json" --out "$O/${p}_top5.png" \
        --n 20 --k 5
    python scripts/l1_look.py --root "$O" --bundles "$B/$p/bundles" --labels "$LABELS" \
        --pot "$p" --pot-mm 100 --bin-pct 10.77 --profile outer --cover-pct 2 --near-pct 12 \
        --out "$O/$p.png"
done
