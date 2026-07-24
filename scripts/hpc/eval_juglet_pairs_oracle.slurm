#!/bin/bash
#SBATCH --job-name=tora-juglet-pairs
#SBATCH --partition=gpu-a100-short
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_juglet_pairs_%j.log

set -euo pipefail

# B1 — Juglet pairwise mating oracle. Does TORA place true-mate Juglet pairs
# into a consistent/correct relative pose better than non-mates? Scored against
# PF++ pseudo-GT (form-level, NOT contact-accurate — see builder caveat).
# Direct analogue of GARF Exp 6, on the exact same object, for cross-comparison
# to GARF's 0.070/0.073 = no-separation Juglet result.

echo "=== TORA Juglet pairwise oracle started at $(date) on $(hostname) ==="
nvidia-smi | head -15 || true

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
REPO_DIR=$TORA_ROOT/repo
ENV_PREFIX=$TORA_ROOT/envs/tora
DATA_ROOT=$TORA_ROOT/dataset
LOG_ROOT=$TORA_ROOT/eval_runs
BASE_CKPT=$TORA_ROOT/checkpoints/bbad_everyday_cka.ckpt
ROBUST_CKPT=$TORA_ROOT/output/real_finetune_robust_27793083/epoch-59.ckpt

# PF++ pseudo-GT sources
PFPP_DIR=/data/gpfs/projects/punim2657/Puzzlefusion/output/denoiser/everyday_epoch2000_bs64/inference/juglet_deploy/0
PC_NPZ=/data/gpfs/projects/punim2657/Puzzlefusion/data/pc_data/juglet_deploy/val/00000.npz
PFPP_ADJ=/data/gpfs/projects/punim2657/GARF/logs/diagnostics/juglet_adjacency/adjacency.json

module purge
module load Anaconda3/2024.02-1
module load CUDA/12.4.1
module load cuDNN/9.6.0.74-CUDA-12.4.1
eval "$(conda shell.bash hook)"
conda activate "$ENV_PREFIX"
export TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0"
export HF_HOME=$TORA_ROOT/.hf-cache
cd "$REPO_DIR"

echo ""
echo "### Build Juglet pairs HDF5 with PF++ pseudo-GT poses ###"
python scripts/build_juglet_pairs_pseudogt.py \
    --pfpp-dir "$PFPP_DIR" \
    --pc-npz "$PC_NPZ" \
    --adjacency "$PFPP_ADJ" \
    --out-hdf5 "$DATA_ROOT/juglet_pairs.hdf5" \
    --out-adjacency "$DATA_ROOT/juglet_pairs_adjacency.json"

for TAG in "baseline:$BASE_CKPT" "robust:$ROBUST_CKPT"; do
    NAME="${TAG%%:*}"; CKPT="${TAG#*:}"
    echo ""
    echo "### Juglet pairwise oracle [$NAME] ###"
    python sample.py \
        ckpt_path="$CKPT" \
        data_root="$DATA_ROOT" \
        data=zeroshot/juglet_pairs \
        data.batch_size=8 \
        data.num_workers=4 \
        log_dir="$LOG_ROOT/juglet_pairs_${NAME}_${SLURM_JOB_ID}" \
        model.n_generations=5
    echo ""
    echo "### Join with PF++ adjacency [$NAME] ###"
    python scripts/analyze_pairwise_oracle.py \
        --results-dir "$LOG_ROOT/juglet_pairs_${NAME}_${SLURM_JOB_ID}/results" \
        --adjacency "$DATA_ROOT/juglet_pairs_adjacency.json" \
        --label "Juglet pairs [$NAME] (PF++ pseudo-GT, form-level)" || true
done

echo ""
echo "=== Finished at $(date) ==="
echo "REMINDER: PF++ pseudo-GT is form-level, not contact-accurate. A pass means"
echo "TORA reproduces PF++'s coarse layout, not that it truly mates the sherds."
