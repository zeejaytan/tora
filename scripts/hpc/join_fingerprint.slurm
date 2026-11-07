#!/bin/bash
# pr-workspace .scratch/uneven-wear/issues/01 (U20): the Juglet's join fingerprint, overlap
# excluded, with round 3's clean and worn4 copies of three pots beside it
# (scripts/measure_join_fingerprint.py). Writes $RUN_DIR/out only.
#
# Submit from the login node through new_run.sh:
#   git -C $T/repo fetch origin
#   git -C $T/repo show $SHA:scripts/hpc/join_fingerprint.slurm > $TMPDIR/jfp.slurm
#   $P/agent/pr-workspace/scripts/new_run.sh $T $T/repo $SHA join-fingerprint $TMPDIR/jfp.slurm
# CARDS overrides the three pots (space separated); a card not in round 3 stops the job.
#SBATCH --job-name=tora-join-fp
#SBATCH --partition=sapphire,cascade
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=04:00:00
set -euo pipefail
: "${RUN_DIR:?submit through new_run.sh}" "${SOURCE_COMMIT:?}" "${CANONICAL:?}"
export PYTHONDONTWRITEBYTECODE=1
P=/data/gpfs/projects/punim2657
PY=$P/TORA/envs/tora/bin/python
JUG=$P/TORA/dataset/juglet_gt.hdf5
R3=$P/CSC/runs/20261106-1423_46dfd26_wear-miss20/out
CARDS=${CARDS:-"p132_d02 p148_d00 p177_d05"}
source $P/agent/pr-workspace/scripts/run_from_commit.sh "$CANONICAL" "$SOURCE_COMMIT" "$RUN_DIR"
cd "$SRC"
echo "round 3 copies $R3; cards $CARDS" | tee -a "$RUN_DIR/source.txt"
md5sum "$JUG" "$R3"/csc_whole20miss_clean.hdf5 "$R3"/csc_whole20miss_worn4.hdf5 | tee -a "$RUN_DIR/source.txt"

echo "=== self-test (box pairs with known answers)"
$PY -u scripts/measure_join_fingerprint.py --selftest

echo "=== round-3 cards available"
$PY - "$R3" $CARDS <<'EOF'
import sys, h5py
d, want = sys.argv[1], sys.argv[2:]
with h5py.File(d + "/csc_whole20miss_worn4.hdf5", "r") as h:
    have = sorted(h["csc_whole20miss_worn4"])
print(" ".join(have))
miss = [c for c in want if c not in have]
if miss:
    sys.exit(f"not in round 3: {miss}")
EOF

ARGS=(--object "juglet=$JUG:juglet_gt::65" --drop-sherds "juglet:2,7")
for c in $CARDS; do
  for s in clean worn4; do
    ARGS+=(--object "${s}_$c=$R3/csc_whole20miss_$s.hdf5:csc_whole20miss_$s:$c")
  done
done
echo "=== fingerprint"
$PY -u scripts/measure_join_fingerprint.py --out "$RUN_DIR/out" "${ARGS[@]}"
ls -la "$RUN_DIR/out"
