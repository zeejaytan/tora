#!/bin/bash
#SBATCH --job-name=tora-erosion
#SBATCH --partition=gpu-a100-short
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=04:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_erosion_%j.log

set -euo pipefail

# C3 — DOES WEAR CAUSE THE FAILURE?
#
# Everything so far is correlational: the worn Juglet scores worse than fresh
# Fractura pots. This intervenes instead. Take real pots TORA reassembles well
# and progressively abrade their BREAK SURFACES ONLY, holding the pieces, the
# poses and the ground truth fixed. If seating accuracy falls as wear rises,
# wear is the cause rather than a correlate.
#
# Uses GARF's validated mollifier unmodified: vertex-only edit (faces and GT
# pose preserved, so scoring stays valid) at a fixed physical radius (so mesh
# density cannot confound it).
#
# Achieved surface roughness is recorded at every wear level. A flat result is
# only interpretable if the simulated wear actually reached the Juglet's real
# roughness -- GARF's Exp 7 plateaued below it and could not be interpreted.

echo "=== C3 erosion sweep started at $(date) on $(hostname) ==="
nvidia-smi | head -15 || true

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

echo ""
echo "### Build wear sweep (break surfaces only; poses preserved) ###"
python scripts/build_erosion_sweep.py \
    --src "$DATA_ROOT/real_heldout_norm.hdf5" \
    --src-dataset real_heldout_norm \
    --strengths 0,0.25,0.5,0.75,1.0 \
    --out-hdf5 "$DATA_ROOT/erosion_sweep.hdf5" \
    --out-calibration "$DATA_ROOT/erosion_sweep.calibration.json"

echo ""
echo "### Evaluate every wear level ###"
python sample.py \
    ckpt_path="$CKPT" \
    data_root="$DATA_ROOT" \
    data=zeroshot/erosion_sweep \
    data.batch_size=4 \
    data.num_workers=4 \
    log_dir="$LOG_ROOT/erosion_sweep_${SLURM_JOB_ID}" \
    model.n_generations=3

echo ""
echo "### Seating accuracy vs wear ###"
python scripts/analyze_erosion_sweep.py \
    --results-dir "$LOG_ROOT/erosion_sweep_${SLURM_JOB_ID}/results" \
    --calibration "$DATA_ROOT/erosion_sweep.calibration.json" || true

echo ""
echo "=== Finished at $(date) ==="
