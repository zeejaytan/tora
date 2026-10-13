#!/bin/bash
#SBATCH --job-name=tora-agentasm
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=01:30:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/agent_assembly/logs/agentasm_%j.log

# AssemblyWorld test (.scratch/agent-assembly). Three modes, CPU only, minutes:
#   sbatch scripts/hpc/agent_assembly.slurm prep  v1            -> tasks_v1/ (public + secret)
#   sbatch scripts/hpc/agent_assembly.slurm score v1 runs_pilot -> scores_v1_runs_pilot/
#   sbatch scripts/hpc/agent_assembly.slurm garf  v1            -> tasks_v1/{public,secret}/garf_*
#        (ticket 05: GARF rough 1x / worn 4x Juglet attempts, jobs 31835635-36, as starting
#        scenes; also scores each untouched, i.e. GARF's own attempt, as scores_v1_runs_garf_base)
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
elif [ "$MODE" = garf ]; then
  python scripts/agent_assembly/prep_from_garf.py --h5 ../dataset/juglet_gt.hdf5 \
      --runs '/data/gpfs/projects/punim2657/GARF/logs/rwlora/rwlora_eval_*juglet_gt_3183563[56]/version_0' \
      --out $W/tasks_$V --pot-mm 65 --faces 30000
  python - "$W/tasks_$V/secret" "$W/runs_garf_base" <<'PY'
import json, sys, numpy as np
from pathlib import Path
sec, out = Path(sys.argv[1]), Path(sys.argv[2])
for f in sorted(sec.glob("garf_*.json")):
    s = json.loads(f.read_text())
    (out / s["task"]).mkdir(parents=True, exist_ok=True)
    (out / s["task"] / "final.json").write_text(json.dumps(
        {"task": s["task"], "T": {p: np.eye(4).tolist() for p in s["parts"]}}))
PY
  python scripts/agent_assembly/score_tasks.py --secret $W/tasks_$V/secret \
      --runs $W/runs_garf_base --out $W/scores_${V}_runs_garf_base
  tar -czf $W/tasks_${V}_garf_public.tar.gz -C $W/tasks_$V/public $(cd $W/tasks_$V/public && ls -d garf_*)
  ls -la $W/tasks_${V}_garf_public.tar.gz
else
  echo "mode must be prep, score or garf"; exit 2
fi
