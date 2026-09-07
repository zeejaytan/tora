#!/bin/bash
#SBATCH --job-name=tora-wear-table-corrected
#SBATCH --partition=gpu-a100-short
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=03:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_wear_table_corrected_%j.log

set -euo pipefail

# TICKET .scratch/eval-readout/issues/05 PHASE 2 -- RESCORE THE WEAR TABLE
#
# WHY THIS EXISTS. Job 30187601 found that every number in WEAR_TEST_RESULTS.md
# section 4 was measured with a ruler this project has since retired. Job
# 29308186 ran 2026-08-17. Commit 0d6a85f, which changed part_accuracy from a
# size-dependent absolute chamfer threshold to the unit-box frame, landed
# 2026-09-02. The field kept its name, so nothing complained. The 2026-09-05
# "correction" re-pooled the same result files for the free anchor without ever
# re-scoring them.
#
# The two rulers are far apart and worst on small objects, which is exactly what
# 0d6a85f was made to fix: coxae (scales 0.3316) scores 0.950 on the old ruler
# and 0.050 on the corrected one, on the same ten draws.
#
# Job 30187601 rescored the BASELINE only (its arms A and C). So the LEVELS are
# corrected but the COMPARISON -- does wear training actually help? -- has never
# been run on the fixed ruler. Every ranking in section 4 is currently
# unestablished, and wear v3 success criteria are written against 0.843/0.645,
# two numbers that no longer mean what the table says they mean.
#
# WHAT IS BEING VARIED: NOTHING. This is 29308186 re-run on today's code. Same
# three checkpoints, same three test sets, same data configs, resolved from
# 29308186 own saved hydra overrides rather than from memory. The only
# differences are deliberate and are stated here:
#   1. today's evaluator (the point of the job)
#   2. 10 draws instead of 3 and 5. Section 4 fresh and Juglet rows rest on
#      3 and 5 draws, and two of the six pots have only two loose sherds, so a
#      single flip moves the six-pot mean by 17 points. That is how 0.843 was
#      quoted to three digits off three draws.
#   3. clouds saved, images not. save_assembly_npz gives render_assembly_grid.py
#      everything it needs; the mitsuba pass was most of the previous job 16
#      minutes and can be run afterwards on whichever rows the table makes
#      decision-relevant.
#
# STATED IN ADVANCE SO IT CAN FAIL. Prediction: the LEVELS all fall (the
# corrected ruler is stricter, and the baseline already fell 0.843 -> 0.597),
# but the RANKING survives -- wear_v2 still ahead of baseline on the worn sweep,
# by more than the draw-to-draw scatter. If instead the ranking collapses or
# reverses, then wear training was never shown to help and the wear programme
# rests on a retired metric. That is the outcome that would refute the current
# framing, and it must be reported.
#
# A SECOND PREDICTION THAT IS CHEAPER TO CHECK AND EASIER TO BE WRONG ABOUT:
# the Juglet rows will not move in ranking either. Section 4 already says wear
# training does not fix the Juglet; if the corrected ruler makes wear_v1/v2 look
# BETTER than baseline there, that is new information about the one object the
# whole project is about.
#
# NOT SCORED HERE: the Juglet has no valid archaeological ground truth. Its rows
# are against the conservator hand assembly and must be quoted that way.
#
# Usage:
#   sbatch scripts/hpc/eval_wear_table_corrected.slurm
#   DRAWS=20 sbatch scripts/hpc/eval_wear_table_corrected.slurm

echo "=== corrected wear table started at $(date) on $(hostname) ==="
nvidia-smi | head -15 || true

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
ENV_PREFIX=$TORA_ROOT/envs/tora
DATA_ROOT=$TORA_ROOT/dataset
LOG_ROOT=$TORA_ROOT/eval_runs

# Resolved from 29308186 own .hydra/overrides.yaml, not from the finetune
# script -- that script picks BEST by mtime and would not necessarily resolve
# to the same file today.
BASELINE=$TORA_ROOT/checkpoints/bbad_everyday_cka.ckpt
WEAR_V1=$TORA_ROOT/output/wear_finetune_28231335/last.ckpt
WEAR_V2=$TORA_ROOT/output/wear_finetune_v2_29308186/last.ckpt

DRAWS=${DRAWS:-10}
MODELS=${MODELS:-"baseline wear_v1 wear_v2"}
SETS=${SETS:-"fresh sweep jugletgt"}

module purge
module load Anaconda3/2024.02-1
module load CUDA/12.4.1
module load cuDNN/9.6.0.74-CUDA-12.4.1
eval "$(conda shell.bash hook)"
conda activate "$ENV_PREFIX"
export TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0"
export HF_HOME=$TORA_ROOT/.hf-cache
export WANDB_MODE=offline
cd "$TORA_ROOT/repo"

for f in "$BASELINE" "$WEAR_V1" "$WEAR_V2" \
         "$DATA_ROOT/erosion_sweep.hdf5" "$DATA_ROOT/real_heldout_norm.hdf5" \
         "$DATA_ROOT/juglet_gt.hdf5"; do
    [ -e "$f" ] || { echo "missing: $f"; exit 1; }
done

echo ""
echo '########## gate 1: the checkout must POSTDATE the scoring fix ##########'
# This is the gate for the exact mistake this job exists to repair. It costs one
# second. Scoring nine runs on a pre-0d6a85f checkout would silently reproduce
# the retired table and look like a confirmation.
if git merge-base --is-ancestor 0d6a85f HEAD; then
    echo "PASS: 0d6a85f (unit-box part accuracy) is an ancestor of $(git rev-parse --short HEAD)"
else
    echo "FAIL: this checkout PREDATES 0d6a85f. Every number would be on the retired ruler."
    exit 1
fi

echo ""
echo "baseline: $BASELINE"
echo "wear_v1:  $WEAR_V1"
echo "wear_v2:  $WEAR_V2"
echo "draws:    $DRAWS"
echo "models:   $MODELS"
echo "sets:     $SETS"

run_one () {
    SET=$1; MDL=$2; CKPT=$3; DATACFG=$4; BS=$5
    echo ""
    echo "########## $SET / $MDL ##########"
    DIR="$LOG_ROOT/wearft2_${SET}_${MDL}_${SLURM_JOB_ID}"
    python sample.py ckpt_path="$CKPT" data_root="$DATA_ROOT" \
        data="$DATACFG" data.batch_size="$BS" data.num_workers=4 \
        lora.enabled=false \
        model.n_generations="$DRAWS" \
        log_dir="$DIR" \
        "+visualizer._target_=tora.visualizer.FlowVisualizationCallback" \
        "+visualizer.renderer=none" \
        "+visualizer.center_points=true" \
        "+visualizer.save_trajectory=false" \
        "+visualizer.save_procrustes_assembly=true" \
        "+visualizer.save_assembly_npz=true" || true
}

ckpt_for () {
    case "$1" in
        baseline) echo "$BASELINE" ;;
        wear_v1)  echo "$WEAR_V1" ;;
        wear_v2)  echo "$WEAR_V2" ;;
        *) echo "unknown model: $1" >&2; exit 1 ;;
    esac
}

MARKER_CHECKED=""
for MDL in $MODELS; do
    C=$(ckpt_for "$MDL")
    for S in $SETS; do
        case "$S" in
            fresh)    run_one fresh    "$MDL" "$C" zeroshot/real_heldout_norm 4 ;;
            sweep)    run_one sweep    "$MDL" "$C" zeroshot/erosion_sweep     4 ;;
            jugletgt) run_one jugletgt "$MDL" "$C" zeroshot/juglet_gt         1 ;;
        esac

        # gate 2, after the very first run only: the results THIS job writes
        # must carry the post-fix marker. Gate 1 checks the source; this checks
        # the output, which is what readout.py actually keys on. If it is
        # missing, the evaluator in use is not the one we think it is and
        # nothing downstream would mean anything.
        if [ -z "$MARKER_CHECKED" ]; then
            MARKER_CHECKED=1
            echo ""
            echo '########## gate 2: the results must carry the post-fix marker ##########'
            python scripts/check_post_fix_marker.py \
                "$LOG_ROOT/wearft2_${S}_${MDL}_${SLURM_JOB_ID}"
        fi
    done
done

echo ""
echo "###################################################################"
echo "### the wear table, rescored -- per object, all three models     ###"
echo "###################################################################"
python scripts/audit_placement_metrics.py --runs "$LOG_ROOT" --job "$SLURM_JOB_ID" || true

echo ""
echo "### does wear training help? paired, in seating, on the FRESH set ###"
python scripts/summarise_scale_cost.py \
    --arm "A=baseline fresh:$LOG_ROOT/wearft2_fresh_baseline_${SLURM_JOB_ID}" \
    --arm "B=wear_v1 fresh:$LOG_ROOT/wearft2_fresh_wear_v1_${SLURM_JOB_ID}" \
    --arm "C=wear_v2 fresh:$LOG_ROOT/wearft2_fresh_wear_v2_${SLURM_JOB_ID}" \
    --pair AB --pair AC || true

echo ""
echo "### does wear training help? paired, in seating, on the WORN sweep ###"
python scripts/summarise_scale_cost.py \
    --arm "A=baseline worn:$LOG_ROOT/wearft2_sweep_baseline_${SLURM_JOB_ID}" \
    --arm "B=wear_v1 worn:$LOG_ROOT/wearft2_sweep_wear_v1_${SLURM_JOB_ID}" \
    --arm "C=wear_v2 worn:$LOG_ROOT/wearft2_sweep_wear_v2_${SLURM_JOB_ID}" \
    --pair AB --pair AC || true

for MDL in $MODELS; do
    echo ""
    echo "### the erosion ladder on the corrected ruler -- $MDL ###"
    python scripts/analyze_erosion_sweep.py \
        --results-dir "$LOG_ROOT/wearft2_sweep_${MDL}_${SLURM_JOB_ID}/results" \
        --calibration "$DATA_ROOT/erosion_sweep.calibration.json" || true
done

echo ""
echo "### clouds saved for the mandatory render (no images were made) ###"
echo "Render before quoting any row, e.g.:"
echo "  python scripts/render_assembly_grid.py \\"
echo "    --runs baseline=$LOG_ROOT/wearft2_sweep_baseline_${SLURM_JOB_ID}/clouds \\"
echo "           wear_v2=$LOG_ROOT/wearft2_sweep_wear_v2_${SLURM_JOB_ID}/clouds \\"
echo "    --match e100 --out artifacts/wear_table_e100.png"
{ find "$LOG_ROOT" -path "*wearft2_*_${SLURM_JOB_ID}*" -name "*.npz" | sort | head -12; } || true

echo ""
echo "=== Finished at $(date) ==="
