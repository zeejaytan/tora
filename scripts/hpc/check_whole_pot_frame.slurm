#!/bin/bash
#SBATCH --job-name=tora-wholepot
#SBATCH --partition=sapphire,cascade
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=00:45:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/logs/check_whole_pot_frame_%j.log

# wear-beyond-juglet 20 (U3): the whole-pot frame on the real round-2 / round-3 sets. CPU only.
# Writes pictures to $OUT only (default TORA/logs/whole_pot_frame_<job>).
set -uo pipefail
TORA_ROOT=/data/gpfs/projects/punim2657/TORA
C=/data/gpfs/projects/punim2657/CSC/runs/20261104-1554_cd2549b_wear-copies20/out
M=/data/gpfs/projects/punim2657/CSC/runs/20261106-1423_46dfd26_wear-miss20/out
OUT="${OUT:-$TORA_ROOT/logs/whole_pot_frame_${SLURM_JOB_ID:-local}}"
module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate "$TORA_ROOT/envs/tora"
cd "$TORA_ROOT/repo"
echo "=== check_whole_pot_frame on $(hostname), repo $(git rev-parse --short HEAD) ==="
python -c "import trimesh, scipy; print('trimesh', trimesh.__version__, 'scipy', scipy.__version__)"
python scripts/test_presentation_seed.py; echo "exit $?"
python scripts/test_whole_pot_frame.py; echo "exit $?"
for S in worn4 clean; do
  python scripts/check_whole_pot_frame.py --whole $C/csc_whole20_$S.hdf5 --whole-name csc_whole20_$S \
      --miss $M/csc_whole20miss_$S.hdf5 --miss-name csc_whole20miss_$S --seed 3 \
      --cards p132_d00 p148_d00 p390_d03 --render p148_d00 --out "$OUT/$S"; echo "exit $?"
done
ls -la "$OUT"/*
