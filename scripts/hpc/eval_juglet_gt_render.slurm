#!/bin/bash
#SBATCH --job-name=tora-jugletgt
#SBATCH --partition=gpu-a100
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_jugletgt_%j.log

set -euo pipefail

# Re-run the Juglet against the conservator's ground truth, this time SAVING the
# geometry, because the numbers from job 29308186 contradict each other and
# neither can be reported until the reassembly has been looked at.
#
# What the contradiction is. wear_v2 scored part_accuracy 0.80 -- nominally
# eight fragments in ten placed correctly -- while recall_at_10deg was 0.000 and
# the mean rotation error was 52.9 degrees. Not one fragment of nine is within
# ten degrees of its correct orientation, yet most are counted as correctly
# placed. One of those two statements is wrong about the same geometry.
#
# part_accuracy passes a fragment on chamfer distance, and chamfer distance is
# small for a sherd that sits roughly in the right region however it is turned.
# That is the failure this project has already been burned by once on this exact
# pot: an absolute threshold that faked an entire finding. See
# validate-metrics-before-concluding in docs/lessons.md.
#
# So: save the posed clouds, export the sherds as meshes, and look. For a
# reassembly the eye is the instrument that cannot be fooled by a threshold.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

DATA_ROOT=/data/gpfs/projects/punim2657/TORA/dataset
LOG_ROOT=/data/gpfs/projects/punim2657/TORA/eval_runs
OUT=/data/gpfs/projects/punim2657/TORA/juglet_gt_meshes
mkdir -p "$OUT"

BASE=/data/gpfs/projects/punim2657/TORA/checkpoints/tora_base.ckpt
WEAR_V1=$(ls -t /data/gpfs/projects/punim2657/TORA/output/wear_finetune_v1*/last.ckpt 2>/dev/null | head -1 || true)
WEAR_V2=$(ls -t /data/gpfs/projects/punim2657/TORA/output/wear_finetune_v2_29308186/last.ckpt 2>/dev/null | head -1 || true)

for TAG in "baseline:$BASE" "wear_v2:$WEAR_V2"; do
    NAME="${TAG%%:*}"; CKPT="${TAG#*:}"
    if [ -z "$CKPT" ] || [ ! -f "$CKPT" ]; then
        echo "skipping $NAME -- no checkpoint at '$CKPT'"
        continue
    fi
    RUN="$LOG_ROOT/jugletgt_render_${NAME}_${SLURM_JOB_ID}"

    echo ""
    echo "########## THE JUGLET vs real ground truth [$NAME] ##########"
    python sample.py \
        ckpt_path="$CKPT" \
        data_root="$DATA_ROOT" \
        data=zeroshot/juglet_gt \
        log_dir="$RUN" \
        model.n_generations=5 \
        "+visualizer._target_=tora.visualizer.FlowVisualizationCallback" \
        "+visualizer.renderer=mitsuba" \
        "+visualizer.image_size=512" \
        "+visualizer.max_samples_per_batch=1" \
        "+visualizer.center_points=true" \
        "+visualizer.save_trajectory=false" \
        "+visualizer.save_procrustes_assembly=true" \
        "+visualizer.save_assembly_npz=true" || true

    NPZ=$(ls "$RUN"/clouds/*.npz 2>/dev/null | head -1 || true)
    if [ -n "$NPZ" ]; then
        echo "exporting sherd meshes from $NPZ"
        python scripts/export_proposed_meshes.py \
            --npz "$NPZ" \
            --src "$DATA_ROOT/juglet_gt.hdf5" --dataset juglet_gt \
            --out "$OUT/$NAME" || true
    else
        echo "no clouds written for $NAME -- cannot export meshes"
    fi
done

echo ""
echo "=== Finished at $(date) ==="
echo "Judge this by looking at it. part_accuracy on this pot has lied before,"
echo "and it currently disagrees with the rotation error by a wide margin."
