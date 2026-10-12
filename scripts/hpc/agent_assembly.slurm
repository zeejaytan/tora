#!/bin/bash
#SBATCH --job-name=tora-agentasm
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=00:30:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/agent_assembly/logs/agentasm_%j.log

# AssemblyWorld test (.scratch/agent-assembly). Two modes, CPU only, minutes:
#   sbatch scripts/hpc/agent_assembly.slurm prep  v1            -> tasks_v1/ (public + secret)
#   sbatch scripts/hpc/agent_assembly.slurm score v1 runs_pilot -> scores_v1_runs_pilot/
# The secret/ folder holds the answer key and never leaves Spartan.
set -euo pipefail
MODE=$1; V=$2
W=/data/gpfs/projects/punim2657/TORA/agent_assembly
mkdir -p $W/logs
module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

if [ "$MODE" = prep ]; then
  python scripts/agent_assembly/prep_tasks.py --h5 ../dataset/juglet_gt.hdf5 \
      --out $W/tasks_$V --pairs 4 --pot-mm 65 --faces 30000
  tar -czf $W/tasks_${V}_public.tar.gz -C $W/tasks_$V public
  ls -la $W/tasks_${V}_public.tar.gz
elif [ "$MODE" = score ]; then
  RUNS=$3
  python scripts/agent_assembly/score_tasks.py --secret $W/tasks_$V/secret \
      --runs $W/$RUNS --out $W/scores_${V}_$RUNS
else
  echo "mode must be prep or score"; exit 2
fi
