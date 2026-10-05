#!/bin/bash
#SBATCH --job-name=u17-jug-v2
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/rank_u17/u17_jug_v2_%j.log
set -euo pipefail
# U17: Juglet rerun with the repaired Layer 1 (rule file Revision 2) and the cut-off the
# calibration set (CALIB, default calib_32160629 = Revision 2). Same bundles and Layer 2
# gaps as before. Revision 3: CALIB=calib_<id> L1X="--near-pct 12 --unjudged fail".
module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
# OMP_NUM_THREADS stays 1 (Spartan's profile): the long steps run one worker process per CPU.
cd /data/gpfs/projects/punim2657/TORA/repo
R=/data/gpfs/projects/punim2657/TORA/rank_u17
J=$R/juglet_32107634
O=$R/jug_v2_${SLURM_JOB_ID}; mkdir -p "$O"
CALIB=${CALIB:-calib_32160629}
read -ra L1X <<< "${L1X:-}"
PCT=$(python -c "import json;print(json.load(open('$R/$CALIB/calib.json'))['profile_pct'])")
echo "profile cut-off from calibration: $PCT% of pot"
python scripts/rank_attempts.py --bundles "$J/bundles" --out "$O/ranks.json" \
    --pot-mm 65 --profile-pct "$PCT" --profile outer --cover-pct 2 --io-gate off ${L1X[@]+"${L1X[@]}"}
python scripts/rank_report.py --ranks "$O/ranks.json" --key "$J/key/idmap.json" \
    --prereg .scratch/attempt-ranker/preregistration.md --out "$O/report.json" \
    --expect-genuine 2 --expect-near 19
python scripts/l2_report.py --bundles "$J/bundles" --l2 "$R/l2_32147567/juglet_l2.json" \
    --ranks "$O/ranks.json" --key "$J/key/idmap.json" --report "$J/report.json" \
    --hdf5 /data/gpfs/projects/punim2657/TORA/dataset/juglet_gt.hdf5 --object juglet_gt/Juglet-000 --pot-mm 65 \
    --prereg .scratch/attempt-ranker/preregistration-l2.md --out "$O/l2_report.json"
