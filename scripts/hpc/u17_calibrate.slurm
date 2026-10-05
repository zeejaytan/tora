#!/bin/bash
#SBATCH --job-name=u17-calib
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --time=06:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/rank_u17/u17_calib_%j.log
set -euo pipefail
# U17: Layer 1 on the 5 calibration Fractura pots (bundles from job 32147567), then cut-offs
# by the rule in .scratch/attempt-ranker/calibration-fractura.md. Test pots untouched.
module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
# OMP_NUM_THREADS stays 1 (Spartan's profile): the long steps run one worker process per CPU.
cd /data/gpfs/projects/punim2657/TORA/repo
R=/data/gpfs/projects/punim2657/TORA/rank_u17
B=$R/l2_32147567
O=$R/calib_${SLURM_JOB_ID}; mkdir -p "$O"
POTS=(blue_pot narrow_bottle2 narrow_bottle4 pink_bowl plate)
# Revision 2 of the rule file: outer-surface profile, inside-out reported only
L1=(--profile outer --cover-pct 2 --io-gate off)
for p in "${POTS[@]}"; do
    echo "### $p"
    mkdir -p "$O/$p"
    ln -sfn "$B/$p/key" "$O/$p/key"
    ln -sf "$B/${p}_l2.json" "$O/${p}_l2.json"
    # provisional pass cut-off (Juglet 7 mm on 65 mm); the calibration reads raw deviation
    python scripts/rank_attempts.py --bundles "$B/$p/bundles" --out "$O/$p/ranks.json" \
        --pot-mm 100 --bin-pct 10.77 --profile-pct 10.77 "${L1[@]}"
done
python scripts/u17_calibrate.py --root "$O" --labels "$R/fractura_labels_32111374.json" \
    --pots "${POTS[@]}" --pot-mm 100 --rule .scratch/attempt-ranker/calibration-fractura.md \
    --out "$O/calib.json" --io-gate off
# look at what the new measure compares (render rule), on the two pots that broke it
for p in plate narrow_bottle4; do
    python scripts/l1_look.py --root "$O" --bundles "$B/$p/bundles"         --labels "$R/fractura_labels_32111374.json" --pot "$p" --pot-mm 100 --bin-pct 10.77         --profile outer --cover-pct 2 --out "$O/$p.png"
done
