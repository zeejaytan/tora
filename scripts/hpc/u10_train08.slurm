#!/bin/bash
#SBATCH --job-name=u10-t08
#SBATCH --partition=gpu-a100-short
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/logs/u10_train08_%j.log

# U10 ticket 08 (tora .scratch/u10-juglet-ceiling/issues/08): one arm, end to end.
#   ARM=pooled sbatch scripts/hpc/u10_train08.slurm    # fresh, 20 passes, also scores untouched
#   ARM=worn   sbatch scripts/hpc/u10_train08.slurm    # 10 passes over two copies = same steps
#   ARM=noise  sbatch scripts/hpc/u10_train08.slurm
#   SEED=7 ARM=noise ...   # replication from another random start; outputs tagged t08s7
#   1. train: ticket 07's recipe (u10_session.sh noalign: alignment off, head frozen)
#   2. freshval: last.ckpt on u10_pooled's val set, the one yardstick for every arm
#   3. Juglet and the eight unworn Fractura pots, 20 draws (u10_juglet_arm.slurm)
#   4. the erosion ladder (zeroshot/erosion_ceramics), 20 draws, clouds saved; scored on
#      the laptop per pot and level, never pooled
# Worn/noise need dataset/u10_{worn,noise}.hdf5 linked from their build job's work dir,
# which happens only after the lead has rendered a built join.
set -uo pipefail
TORA_ROOT=/data/gpfs/projects/punim2657/TORA
trap 'rc=$?; echo "$(date -u +%FT%TZ) job ${SLURM_JOB_ID:-nojob} step u10_train08 ${ARM:-?} exit $rc" >> "$TORA_ROOT/logs/job_status.log"' EXIT
: "${ARM:?ARM=pooled|worn|noise}"
case "$ARM" in pooled) EP=20 ;; worn|noise) EP=10 ;; *) echo "ARM must be pooled, worn or noise"; exit 2 ;; esac
H=$TORA_ROOT/repo/scripts/hpc
# Seed 42 is the first run's (train.yaml default); any other seed gets its own tag so
# the first runs' eval folders are never overwritten.
SEED=${SEED:-42}; export SEED
T=t08; [ "$SEED" = 42 ] || T=t08s$SEED
echo "seed $SEED, tag $T"
DATA_ROOT=$TORA_ROOT/dataset

bash "$H/u10_session.sh" noalign "$ARM" "$EP" || { echo "$ARM training failed"; exit 1; }
DIR=$(ls -d "$TORA_ROOT/output/u10_noalign_${ARM}_${SLURM_JOB_ID}_"* | tail -1)
AD=$DIR/last.ckpt
[ -f "$AD" ] || { echo "no last.ckpt in $DIR"; exit 1; }
echo "adapter: $AD"

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate "$TORA_ROOT/envs/tora"
python -c "import torch,sys; c=torch.load(sys.argv[1], map_location='cpu', weights_only=False); print('global_step', c['global_step'], 'epoch', c['epoch'])" "$AD"

fail=0
ADAPTER=$AD bash "$H/u10_session.sh" freshval "$ARM" || fail=1
[ "$ARM" = pooled ] && { bash "$H/u10_session.sh" freshval pooled || fail=1; }  # untouched
for SET in juglet fractura; do
    SET=$SET ARM=$ARM ADAPTER=$AD LABEL=$T bash "$H/u10_juglet_arm.slurm" || fail=1
done

module purge
module load Anaconda3/2024.02-1 CUDA/12.4.1 cuDNN/9.6.0.74-CUDA-12.4.1
eval "$(conda shell.bash hook)"
conda activate "$TORA_ROOT/envs/tora"
export HF_HOME=$TORA_ROOT/.hf-cache WANDB_MODE=offline
cd "$TORA_ROOT/repo"
python sample.py ckpt_path="$AD" data_root="$DATA_ROOT" \
    data=zeroshot/erosion_ceramics data.batch_size=4 data.num_workers=4 \
    lora.enabled=true lora.r=128 lora.alpha=256 lora.dropout=0.1 lora.last_n_blocks=6 \
    lora.train_head=false lora.active=true \
    model.n_generations=20 \
    log_dir="$TORA_ROOT/eval_runs/u10_ladder_${ARM}_${T}_${SLURM_JOB_ID}" \
    "+visualizer._target_=tora.visualizer.FlowVisualizationCallback" \
    "+visualizer.renderer=none" \
    "+visualizer.center_points=true" \
    "+visualizer.save_trajectory=false" \
    "+visualizer.save_procrustes_assembly=true" \
    "+visualizer.save_assembly_npz=true" || fail=1
echo "$T $ARM done, any step failed: $fail"
exit $fail
