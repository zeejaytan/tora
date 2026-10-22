#!/bin/bash
#SBATCH --job-name=icaane-figs
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/figs_icaane/icaane_figs_%j.log

set -euo pipefail

# Draft figures 2-5 of the ICAANE 2027 paper (phd-thesis papers/icaane2027): greyscale
# shaded renders with scale bars, from the juglet bundles of ranker job 32107634 and the
# top-five meshes of attempt-ranker ticket 07. CPU only; reads, never writes, the inputs.
# ONLY picks figures: 3 4 5 2, r = Rabati contact sheet (to choose Fig 2's sherd),
# R = Fig 2 with the chosen Rabati sherd (set RABATI_MESH and RABATI_MM_PER_UNIT).

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

U=/data/gpfs/projects/punim2657/TORA/rank_u17
RB=/data/gpfs/projects/punim2657/Rabati2025
O=/data/gpfs/projects/punim2657/TORA/figs_icaane/${SLURM_JOB_ID}
mkdir -p "$O"
python scripts/icaane_figures.py --bundles "$U/juglet_32107634/bundles" \
    --key "$U/juglet_32107634/key/idmap.json" \
    --hdf5 /data/gpfs/projects/punim2657/TORA/dataset/juglet_gt.hdf5 --top5 "$U/jug_top5" \
    --bbad /data/gpfs/projects/punim2657/TORA/dataset/breaking_bad_vol.hdf5 --out "$O" \
    --only "${ONLY:-345r}" \
    --rabati-glob "$RB/03072025/N01/work_colmap_openmvs/**/sherd_*.ply" \
                  "$RB/17062025/A02/work_colmap_openmvs/**/sherd_*.ply" \
    ${RABATI_MESH:+--rabati-mesh "$RABATI_MESH" --rabati-mm-per-unit "${RABATI_MM_PER_UNIT:-1}"}
ls -la "$O"
