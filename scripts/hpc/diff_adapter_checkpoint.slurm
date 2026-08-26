#!/bin/bash
#SBATCH --job-name=tora-ckptdiff
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --time=00:20:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_ckptdiff_%j.log

set -euo pipefail

# Why job 29527496's control arm did not reproduce the baseline. Two 2.3 GB
# checkpoints get loaded and compared, which is why this is a job and not a
# login-node one-liner.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo

TORA_ROOT=/data/gpfs/projects/punim2657/TORA
BASE=$TORA_ROOT/checkpoints/bbad_everyday_cka.ckpt
TRAINED=$(find "$TORA_ROOT/output/lora_vessels_29527496" -name "*.ckpt" \
    -printf "%T@ %p\n" 2>/dev/null | sort -rn | head -1 | cut -d" " -f2)

echo "trained checkpoint: $TRAINED"
python scripts/diff_adapter_checkpoint.py --base "$BASE" --trained "$TRAINED"

echo ""
echo "=== Finished at $(date) ==="
