#!/bin/bash
#SBATCH --job-name=tora-levers
#SBATCH --partition=gpu-a100-short
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=03:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_levers_%j.log

set -euo pipefail

# S1 — do the FREE inference knobs recover seating on worn pots?
#
# Test bed is the C3 erosion sweep: real pots with VALID ground truth whose
# break surfaces have been progressively abraded, where seating is known to
# fall 0.875 (fresh) -> 0.524 (fully worn). Any fix must move that curve.
# The Juglet cannot be used for this -- it has no correct answer to score.
#
# Knobs: ODE sampler (euler/rk2/rk4), integration steps, generations.
# Expectation is LOW -- GARF's Exp 5 found inference knobs barely moved its
# accuracy -- but these cost nothing and rule out the cheap explanation before
# any retraining is attempted.

echo "=== inference-lever sweep started at $(date) on $(hostname) ==="

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
ENV_PREFIX=$TORA_ROOT/envs/tora
DATA_ROOT=$TORA_ROOT/dataset
LOG_ROOT=$TORA_ROOT/eval_runs
CKPT=$TORA_ROOT/checkpoints/bbad_everyday_cka.ckpt

module purge
module load Anaconda3/2024.02-1
module load CUDA/12.4.1
module load cuDNN/9.6.0.74-CUDA-12.4.1
eval "$(conda shell.bash hook)"
conda activate "$ENV_PREFIX"
export TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0"
export HF_HOME=$TORA_ROOT/.hf-cache
cd "$TORA_ROOT/repo"

run () {  # name sampler steps gens
    echo ""
    echo "########## $1  (sampler=$2 steps=$3 gens=$4) ##########"
    python sample.py \
        ckpt_path="$CKPT" \
        data_root="$DATA_ROOT" \
        data=zeroshot/erosion_sweep \
        data.batch_size=4 \
        data.num_workers=4 \
        model.inference_sampler=$2 \
        model.inference_sampling_steps=$3 \
        model.n_generations=$4 \
        log_dir="$LOG_ROOT/levers_$1_${SLURM_JOB_ID}"
    python scripts/analyze_erosion_sweep.py \
        --results-dir "$LOG_ROOT/levers_$1_${SLURM_JOB_ID}/results" \
        --calibration "$DATA_ROOT/erosion_sweep.calibration.json" || true
}

run baseline   euler 50  3     # reproduces the C3 curve
run steps200   euler 200 3     # 4x integration resolution
run rk4        rk4   50  3     # higher-order sampler
run gens10     euler 50  10    # more attempts, best-of-N

echo ""
echo "=== Finished at $(date) ==="
echo "Compare the 'MEAN seating rate' block across arms, especially at wear 0.75-1.00."
