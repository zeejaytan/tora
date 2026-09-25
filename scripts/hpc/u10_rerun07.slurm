#!/bin/bash
#SBATCH --job-name=u10-rerun07
#SBATCH --partition=gpu-a100-short
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/logs/u10_rerun07_%j.log

# U10 ticket 07: stage 1 again with the alignment term off (ticket 06's fix).
#   1. train the generic adapter with repa_stop=0, head frozen (u10_session.sh noalign)
#   2. Juglet and Fractura, 20 draws, for generic and ceiling, each adapter's last pass.
# The ceiling adapter is ticket 06 arm A; the untouched arm stands from ticket 05.
set -uo pipefail
TORA_ROOT=/data/gpfs/projects/punim2657/TORA
trap 'rc=$?; echo "$(date -u +%FT%TZ) job ${SLURM_JOB_ID:-nojob} step u10_rerun07 exit $rc" >> "$TORA_ROOT/logs/job_status.log"' EXIT
H=$TORA_ROOT/repo/scripts/hpc
CEIL=$TORA_ROOT/output/u10_noalign_ceiling_31280929_144409/last.ckpt

bash "$H/u10_session.sh" noalign generic || { echo "generic training failed"; exit 1; }
GEN_DIR=$(ls -d "$TORA_ROOT/output/u10_noalign_generic_${SLURM_JOB_ID}_"* | tail -1)
GEN=$GEN_DIR/last.ckpt
[ -f "$GEN" ] || { echo "no generic last.ckpt in $GEN_DIR"; exit 1; }
echo "generic adapter: $GEN"

fail=0
for SET in juglet fractura; do
    SET=$SET ARM=generic ADAPTER=$GEN LABEL=noalign bash "$H/u10_juglet_arm.slurm" || fail=1
    SET=$SET ARM=ceiling ADAPTER=$CEIL LABEL=noalign bash "$H/u10_juglet_arm.slurm" || fail=1
done
echo "rerun07 done, any arm failed: $fail"
exit $fail
