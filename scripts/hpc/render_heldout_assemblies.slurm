#!/bin/bash
#SBATCH --job-name=tora-heldoutviz
#SBATCH --partition=gpu-a100
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_heldoutviz_%j.log

set -euo pipefail

# The conservator asked for the Juglet treatment applied to the other objects.
# The retrain saved no geometry, so this re-runs the held-out set and the worn
# sweep with the posed clouds written out, then draws each object's proposal
# beside its correct assembly.
#
# The claim being tested is mine. I reported that a fragment turned thirty
# degrees "is not a reassembly", and whether that is true of pottery is a
# judgement to be made by looking, not by arithmetic. Three cases decide it:
#
#   blue_pot  scored 1.000 -- every fragment "correctly placed" -- at 19 degrees
#             average with none within ten.
#   limb3     baseline 10.2 degrees with a third of fragments within ten; wear
#             training pushes it to 30 and none. The precision loss, if real.
#   plate     the reverse -- baseline 49 degrees, wear_v2 18.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
DATA_ROOT=$TORA_ROOT/dataset
LOG_ROOT=$TORA_ROOT/eval_runs
OUT=$TORA_ROOT/heldout_viz
mkdir -p "$OUT"

BASE=$TORA_ROOT/checkpoints/bbad_everyday_cka.ckpt
WEAR_V2=$TORA_ROOT/output/wear_finetune_v2_29308186/last.ckpt

for SET in real_heldout_norm erosion_sweep; do
    for TAG in "baseline:$BASE" "wear_v2:$WEAR_V2"; do
        NAME="${TAG%%:*}"; CKPT="${TAG#*:}"
        if [ ! -f "$CKPT" ]; then
            echo "skipping $NAME -- no checkpoint at '$CKPT'"
            continue
        fi
        echo ""
        echo "########## $SET [$NAME] ##########"
        python sample.py \
            ckpt_path="$CKPT" \
            data_root="$DATA_ROOT" \
            data=zeroshot/$SET \
            data.batch_size=1 \
            log_dir="$LOG_ROOT/viz_${SET}_${NAME}_${SLURM_JOB_ID}" \
            model.n_generations=5 \
            "+visualizer._target_=tora.visualizer.FlowVisualizationCallback" \
            "+visualizer.renderer=mitsuba" \
            "+visualizer.image_size=384" \
            "+visualizer.max_samples_per_batch=1" \
            "+visualizer.center_points=true" \
            "+visualizer.save_trajectory=false" \
            "+visualizer.save_procrustes_assembly=true" \
            "+visualizer.save_assembly_npz=true" || true
    done

    echo ""
    echo "----- drawing $SET -----"
    python scripts/render_assembly_grid.py \
        --runs "baseline=$LOG_ROOT/viz_${SET}_baseline_${SLURM_JOB_ID}/clouds" \
               "wear_v2=$LOG_ROOT/viz_${SET}_wear_v2_${SLURM_JOB_ID}/clouds" \
        --out "$OUT/${SET}_assemblies.png" || true
done

ls -la "$OUT"
echo ""
echo "=== Finished at $(date) ==="
echo "Judge these by eye. part_accuracy calls most of them correct; the"
echo "rotation errors say 20-50 degrees. The pictures decide which is right."
