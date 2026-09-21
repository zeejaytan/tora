#!/bin/bash
#SBATCH --job-name=tora-u10set
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_u10set_%j.log

set -uo pipefail

# U10 ticket 02 (tora .scratch/u10-juglet-ceiling/issues/02): the training files and
# their audit, in one CPU job.
#
#   1. corpus.json is rebuilt from CSC job 30888410's per-vessel jsons by CSC's own
#      assemble_u10_corpus.py -- deterministic, so its sha256 must match the copy the
#      conservator was shown (printed below; compared on the laptop).
#   2. write_u10_trainset.py -> TORA/dataset/u10_ceiling.hdf5, u10_generic.hdf5.
#   3. audit_u10_trainset.py reads only those two files (and the Juglet's).
#   4. test_u10_audit.py: the audit fails every deliberately broken copy, by name.
#   5. check_u10_loader.py: TORA's loader, training settings, drops nothing.
#   6. render_u10_trainset.py: the pictures the audit's numbers need.
#
# Steps 3-6 all run even if one fails, so a failure arrives with its pictures; the job
# exits non-zero if any did.

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora

ROOT=/data/gpfs/projects/punim2657/TORA
CSC=/data/gpfs/projects/punim2657/CSC
SRC=$CSC/work/u10_corpus_30888410
WORK=$ROOT/work/u10_trainset_${SLURM_JOB_ID}
DATA=$ROOT/dataset
JUGLET=$DATA/juglet_gt.hdf5
mkdir -p "$WORK"

git -C "$CSC/repo" pull --ff-only || { echo "CSC checkout did not fast-forward: stop"; exit 2; }
git -C "$CSC/repo" log --oneline -1
cd "$ROOT/repo" && git log --oneline -1

python "$CSC/repo/scripts/assemble_u10_corpus.py" "$SRC" \
    "$CSC/repo/.scratch/u10-juglet-ceiling/recipes.json" "$WORK" \
    --no-output generic_train_15 || exit 3
sha256sum "$WORK/corpus.json"

python scripts/write_u10_trainset.py --corpus "$WORK/corpus.json" \
    --recipes "$CSC/repo/.scratch/u10-juglet-ceiling/recipes.json" \
    --sherds "$SRC" --out "$DATA" || exit 4
ls -lh "$DATA"/u10_*.hdf5
cp "$DATA/u10_trainset.manifest.json" "$WORK/"

FILES="$DATA/u10_ceiling.hdf5 $DATA/u10_generic.hdf5"
bad=0
echo "=== audit"
python scripts/audit_u10_trainset.py --juglet "$JUGLET" --out "$WORK/audit_report.json" \
    --workers 16 $FILES || bad=1
echo "=== fixtures"
python scripts/test_u10_audit.py --juglet "$JUGLET" $FILES || bad=1
echo "=== loader"
python scripts/check_u10_loader.py --juglet "$JUGLET" --out "$WORK/u10_look_loader.png" \
    $FILES || bad=1
echo "=== renders"
python scripts/render_u10_trainset.py --report "$WORK/audit_report.json" --juglet "$JUGLET" \
    --outdir "$WORK" $FILES || bad=1

ls -lh "$WORK"
echo "WORK=$WORK"
exit $bad
