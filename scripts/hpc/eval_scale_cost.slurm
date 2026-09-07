#!/bin/bash
#SBATCH --job-name=tora-scale-cost
#SBATCH --partition=gpu-a100-short
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=03:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_scale_cost_%j.log

set -euo pipefail

# TICKET .scratch/eval-readout/issues/05 -- WHAT DOES THE OUT-OF-BAND SIZE COST?
#
# WHAT IS BEING DEFENDED. The wear verdict rests on one paired comparison in
# WEAR_TEST_RESULTS.md s4: the baseline model seats 0.843 of the loose sherds on
# fresh pots and 0.645 on the same pots worn. Job 30185814 measured the band the
# model was actually trained on -- 0.375 to 0.811, median 0.550 -- and found both
# of those rows were produced with the model told a size of 0.319 to 0.383. Two
# of the six pots sit below anything training ever showed. The gap is safe (the
# size is held to within 2% across the erosion ladder, so the handicap is applied
# equally to both sides) but the LEVEL is not, and wear v3's success criterion is
# written against these two numbers.
#
# THE PRIOR SAYS THIS WILL BE FLAT, AND THAT IS WORTH STATING BEFORE SPENDING THE
# GPU. Two ladders already varied this same input on real pots: 29891327 upward
# (flat 0.5 to 5, collapse only between 15 and 50) and 30130045 downward (rungs
# 0.04 to 0.5, flat and non-monotone, eight pots at ten draws, renders at the two
# ends indistinguishable). On that evidence the model barely notices the number.
#
# WHY THE JOB IS STILL WORTH RUNNING. Both ladders were read in ROTATION. Wear
# moves turn by about 3 degrees against a 27.7 degree between-pot floor -- that is
# the exact metric error the wear analysis made before it was caught, one level up.
# The wear finding lives in SEATING, and seating has never been read across a
# scale ladder. And both ladders used FRESH pots, so the interaction between
# out-of-band conditioning and WEAR is untested. That interaction is the only
# thing that could bend the s4 gap.
#
# ONE WORRY THAT DOES NOT APPLY. Seating cannot be distorted by the size input at
# all: part_accuracy is computed in the unit-box frame (tora/eval/evaluator.py:87,
# on pts_gt / unit_box_scale(pts_gt)), independent of `scales`. The 9-of-9
# saturation recorded at 0.0408 in juglet-cause ticket 03 was
# part_accuracy_absolute, the pre-0d6a85f scoring. So this job asks about the
# MODEL, not about the ruler.
#
# WHAT IS BEING VARIED. Exactly one number, and no data is rebuilt.
# data.normalize_object_scale restates the object at max|coord| = 0.5 AFTER
# centring on the point centroid and BEFORE the [-1, 1] normalization;
# data.scale_multiplier restates it again (tora/data/dataset.py:421-424). Rung m
# gives scales = 0.5 * m exactly, so 1.1 lands every object on 0.550, the measured
# median of the trained band. The coordinates the network sees are unchanged.
# The CPU gate below asserts that before any GPU time is spent, and the job stops
# if it fails.
#
# NOT scripts/normalize_real_hdf5.py. File-level normalisation is what produced
# juglet_norm's 0.041: it scaled by distance from the FILE's origin while the pot
# sat 0.48 away from it, shrinking the pot elevenfold. The runtime knob normalises
# about the object's own centroid, which is the right origin.
#
# FOUR ARMS, ONE JOB, ONE SETTINGS SET.
#   A  real_heldout_norm  as stored (0.319-0.383)   control, must reproduce 0.843
#   B  real_heldout_norm  at 0.550
#   C  erosion_sweep      as stored (0.319-0.321)   control, must reproduce 0.645
#   D  erosion_sweep      at 0.550
# A and C are not spare arms. If they miss s4 the settings do not match the table
# this job exists to defend, and B and D mean nothing.
#
# STATED IN ADVANCE SO IT CAN FAIL. Prediction: seating moves by less than the
# draw-to-draw scatter in all four arms, and the wear gap (A-C) matches (B-D)
# within that scatter. If instead the gap CLOSES when the size is corrected, part
# of the twenty points was an artefact of scoring a handicapped model -- that is
# the outcome that would refute the current framing and it must be reported.
#
# Usage:
#   sbatch scripts/hpc/eval_scale_cost.slurm
#   DRAWS=20 sbatch scripts/hpc/eval_scale_cost.slurm
#   ARMS="C D" sbatch scripts/hpc/eval_scale_cost.slurm      # worn pair only

echo "=== scale cost started at $(date) on $(hostname) ==="
nvidia-smi | head -15 || true

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
ENV_PREFIX=$TORA_ROOT/envs/tora
DATA_ROOT=$TORA_ROOT/dataset
LOG_ROOT=$TORA_ROOT/eval_runs
CKPT=$TORA_ROOT/checkpoints/bbad_everyday_cka.ckpt

# 10 draws, not s4's 3. Three is too few to see a seating difference against
# draw-to-draw scatter, and this job exists to measure a difference that the
# prior says is small.
DRAWS=${DRAWS:-10}
# Rung m gives scales = 0.5 * m. 1.1 -> 0.550, the measured median of the band.
RUNG=${RUNG:-1.1}
ARMS=${ARMS:-"A B C D"}

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

for f in "$DATA_ROOT/erosion_sweep.hdf5" "$DATA_ROOT/real_heldout_norm.hdf5" "$CKPT"; do
    [ -e "$f" ] || { echo "missing: $f"; exit 1; }
done

echo ""
echo '########## gate: the knob must move scales and nothing else ##########'
# Costs seconds on CPU and decides whether the GPU time means anything. If
# normalising also perturbed the coordinates or the normals, a change in score
# would not isolate the conditioning input and nothing downstream would mean
# anything. Both datasets, because the sweep is the one the claim rests on.
python scripts/check_scale_conditioning.py \
    --data "$DATA_ROOT/real_heldout_norm.hdf5" --dataset-name real_heldout_norm
python scripts/check_scale_conditioning.py \
    --data "$DATA_ROOT/erosion_sweep.hdf5" --dataset-name erosion_sweep

echo ""
echo "checkpoint: $CKPT"
echo "draws:      $DRAWS"
echo "rung:       $RUNG  -> scales = $(python -c "print(0.5 * $RUNG)")"
echo "arms:       $ARMS"

run_arm () {
    NAME=$1; DATACFG=$2; shift 2
    echo ""
    echo "########## $NAME ##########"
    DIR="$LOG_ROOT/scalecost_${NAME}_${SLURM_JOB_ID}"
    python sample.py ckpt_path="$CKPT" data_root="$DATA_ROOT" \
        data="$DATACFG" data.batch_size=4 data.num_workers=4 \
        lora.enabled=false \
        model.n_generations="$DRAWS" \
        "$@" \
        log_dir="$DIR" \
        "+visualizer._target_=tora.visualizer.FlowVisualizationCallback" \
        "+visualizer.renderer=mitsuba" \
        "+visualizer.image_size=512" \
        "+visualizer.max_samples_per_batch=8" \
        "+visualizer.center_points=true" \
        "+visualizer.save_trajectory=false" \
        "+visualizer.save_procrustes_assembly=true" \
        "+visualizer.save_assembly_npz=true" || true
}

# A / C -- exactly as the data ships. These reproduce WEAR_TEST_RESULTS s4.
case " $ARMS " in *" A "*)
    run_arm A_fresh_stored zeroshot/real_heldout_norm ;;
esac
case " $ARMS " in *" C "*)
    run_arm C_worn_stored zeroshot/erosion_sweep ;;
esac

# B / D -- the same pots, the same pieces, the same correct answer, restated so
# the model is told 0.550. Only `scales` differs from A / C.
case " $ARMS " in *" B "*)
    run_arm B_fresh_norm zeroshot/real_heldout_norm \
        +data.normalize_object_scale=true "+data.scale_multiplier=${RUNG}" ;;
esac
case " $ARMS " in *" D "*)
    run_arm D_worn_norm zeroshot/erosion_sweep \
        +data.normalize_object_scale=true "+data.scale_multiplier=${RUNG}" ;;
esac

echo ""
echo "### the four arms, in seating, paired by object ###"
python scripts/summarise_scale_cost.py \
    --arm "A=fresh as-stored:$LOG_ROOT/scalecost_A_fresh_stored_${SLURM_JOB_ID}" \
    --arm "B=fresh at-0.550:$LOG_ROOT/scalecost_B_fresh_norm_${SLURM_JOB_ID}" \
    --arm "C=worn as-stored:$LOG_ROOT/scalecost_C_worn_stored_${SLURM_JOB_ID}" \
    --arm "D=worn at-0.550:$LOG_ROOT/scalecost_D_worn_norm_${SLURM_JOB_ID}" \
    --pair AB --pair CD --gap A-C --gap B-D || true

echo ""
echo "### the worn ladder, wear level by wear level, as-stored (arm C) ###"
python scripts/analyze_erosion_sweep.py \
    --results-dir "$LOG_ROOT/scalecost_C_worn_stored_${SLURM_JOB_ID}/results" \
    --calibration "$DATA_ROOT/erosion_sweep.calibration.json" || true

echo ""
echo "### the worn ladder, wear level by wear level, at 0.550 (arm D) ###"
# If the wear finding is real at full strength, this ladder still falls with
# erosion. If it flattens once the size is corrected, the erosion effect was
# partly the handicap -- that is the refuting outcome and it shows up here first.
python scripts/analyze_erosion_sweep.py \
    --results-dir "$LOG_ROOT/scalecost_D_worn_norm_${SLURM_JOB_ID}/results" \
    --calibration "$DATA_ROOT/erosion_sweep.calibration.json" || true

echo ""
echo "### renders -- LOOK at C against D on the same pot before quoting any of this ###"
# head closes the pipe early; without the guard SIGPIPE trips pipefail and the
# whole job is reported FAILED after it has already succeeded.
{ find "$LOG_ROOT" -path "*scalecost_*_${SLURM_JOB_ID}*" -name "*.png" | sort | head -40; } || true

echo ""
echo "=== Finished at $(date) ==="
