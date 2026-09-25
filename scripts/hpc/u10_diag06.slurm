#!/bin/bash
#SBATCH --job-name=u10-diag06
#SBATCH --partition=gpu-a100-short
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/logs/u10_diag06_%j.log

# U10 ticket 06 follow-up, after arm A (alignment off) held the practice score:
#   1. does arm A's adapter also avoid the forgetting arm C found? (everyday subset)
#   2. the lead's debugging render: untouched / ticket 04 ceiling / arm A on practice vessels
set -uo pipefail
TORA_ROOT=/data/gpfs/projects/punim2657/TORA
trap 'rc=$?; echo "$(date -u +%FT%TZ) job ${SLURM_JOB_ID:-nojob} step u10_diag06 exit $rc" >> "$TORA_ROOT/logs/job_status.log"' EXIT
S=$TORA_ROOT/repo/scripts/hpc/u10_session.sh
export ADAPTER=$TORA_ROOT/output/u10_noalign_ceiling_31280929_144409/last.ckpt

SKIP_UNTOUCHED=1 bash "$S" forget ceiling || rc1=$?
bash "$S" render ceiling || rc2=$?
echo "forget exit ${rc1:-0}, render exit ${rc2:-0}"
[ -z "${rc1:-}${rc2:-}" ]
