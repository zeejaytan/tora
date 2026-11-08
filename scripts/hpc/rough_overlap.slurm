#!/bin/bash
# pr-workspace .scratch/uneven-wear/issues/10 (U20): how far the rough (jitter) training copies
# put sherds inside each other, against the clean and worn 4x copies of the same U10 objects
# (scripts/measure_join_fingerprint.py, ticket 01's ruler). Writes $RUN_DIR/out only.
#
# Submit from the login node through new_run.sh:
#   git -C $T/repo fetch origin
#   git -C $T/repo show $SHA:scripts/hpc/rough_overlap.slurm > $TMPDIR/ro.slurm
#   $P/agent/pr-workspace/scripts/new_run.sh $T $T/repo $SHA rough-overlap $TMPDIR/ro.slurm
# N (default 3) objects, the first ones present in all three files. U10 vessels have no
# real size: LONGEST_MM is nominal (100), so read inside shares and % of diagonal, not mm.
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_%x_%j.log
#SBATCH --job-name=tora-rough-overlap
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
D=$P/TORA/dataset
CLEAN=$D/u10_generic.hdf5
ROUGH=$D/u10_noise_d100.hdf5
WORN=$D/u10_worn_d400.hdf5
N=${N:-3}
source $P/agent/pr-workspace/scripts/run_from_commit.sh "$CANONICAL" "$SOURCE_COMMIT" "$RUN_DIR"
cd "$SRC"
md5sum "$CLEAN" "$ROUGH" "$WORN" | tee -a "$RUN_DIR/source.txt"
# The copies are named <source group>__<clean tag>__<level> (write_u10_worn.py), so a clean
# tag T in u10_generic is u10_generic__T__d100 in the rough file and u10_generic__T__d400 in worn.
PICK=$($PY - "$CLEAN" "$ROUGH" "$WORN" "$N" <<'EOF'
import sys, h5py
(clean, rough, worn), n = sys.argv[1:4], int(sys.argv[4])
def tags(f):
    with h5py.File(f, "r") as h:
        g = [k for k in h if k != "data_split"][0]
        return g, {t for t in h[g] if "pieces" in h[g][t]}
gc, tc = tags(clean); gr, tr = tags(rough); gw, tw = tags(worn)
print(f"{len(tc)} clean, {len(tr)} rough, {len(tw)} worn; e.g. {sorted(tr)[:2]}", file=sys.stderr)
out = []
for t in sorted(tc):
    r = sorted(x for x in tr if x.startswith(f"{gc}__{t}__"))
    w = sorted(x for x in tw if x.startswith(f"{gc}__{t}__"))
    if r and w:
        out.append(f"{gc},{t},{gr},{r[0]},{gw},{w[0]}")
    if len(out) == n:
        break
print(f"{len(out)} picked", file=sys.stderr)
if not out:
    sys.exit("no clean object has both a rough and a worn copy")
print(" ".join(out))
EOF
)
echo "picked: $PICK" | tee -a "$RUN_DIR/source.txt"
ARGS=()
for p in $PICK; do
  IFS=, read -r gc t gr tr gw tw <<< "$p"
  ARGS+=(--object "clean_$t=$CLEAN:$gc:$t:100" --object "rough_$t=$ROUGH:$gr:$tr:100" --object "worn4_$t=$WORN:$gw:$tw:100")
done
$PY -u scripts/measure_join_fingerprint.py --out "$RUN_DIR/out" "${ARGS[@]}"
ls -la "$RUN_DIR/out"
