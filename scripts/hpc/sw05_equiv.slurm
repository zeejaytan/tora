#!/bin/bash
#SBATCH --job-name=tora-sw05equiv
#SBATCH --partition=sapphire,cascade
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=180G
#SBATCH --time=04:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/logs/sw05equiv_%j.log

# tora .scratch/use-sherd-worn/issues/01: does importing the wear code from sherd-worn v0.1.0
# change what TORA builds? Fetch the branch on the login node first, then submit from a copy:
#   git -C $ROOT/repo fetch origin master 01-tora-uses-the-package
#   git -C $ROOT/repo show origin/01-tora-uses-the-package:scripts/hpc/sw05_equiv.slurm > /tmp/sw05.sbatch
#   sbatch /tmp/sw05.sbatch
# Also runs under scripts/new_run.sh, which exports RUN_DIR and SOURCE_COMMIT.
#
#   worn, rough at dose 200, v3 smoke: master against the branch; any array that differs fails.
#   fine-scan on 3 objects, before the rescale: scripts/compare_fine_scan_arms.py.
#
# Each arm runs from a git-archive copy, never from the checkout, and the package goes into
# $RUN_DIR/pydeps rather than the shared env, whose install is the conservator's decision.
# PARTS picks parts for a rerun (PARTS="worn"). If a part differs, rerun it with
# SWITCHED=<the master commit it printed>: master against master tells non-determinism from
# a code change. A passing part's built files are deleted here; a failing part's are kept.
set -uo pipefail
ROOT=/data/gpfs/projects/punim2657/TORA
REPO=$ROOT/repo
BRANCH=01-tora-uses-the-package
PARTS=${PARTS:-"fine-scan v3 worn rough"}
CPUS=${SLURM_CPUS_PER_TASK:-32}
die() { echo "sw05: $*" >&2; exit 2; }

module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate $ROOT/envs/tora
PY=$ROOT/envs/tora/bin/python
export PYTHONNOUSERSITE=1

SWITCHED=$(git -C "$REPO" rev-parse --verify --quiet "${SOURCE_COMMIT:-${SWITCHED:-origin/$BRANCH}}^{commit}") \
    || die "branch not in $REPO; git -C $REPO fetch origin master $BRANCH on the login node first"
MASTER=$(git -C "$REPO" merge-base origin/master "origin/$BRANCH") || die "no merge base"
if [ -z "${RUN_DIR:-}" ]; then
    RUN_DIR=$ROOT/runs/$(date +%Y%m%d-%H%M)_${SWITCHED:0:7}_sw05equiv
    mkdir -p "$RUN_DIR/logs" "$RUN_DIR/out" || die "cannot make $RUN_DIR"
    scontrol write batch_script "${SLURM_JOB_ID:-0}" "$RUN_DIR/submit.sbatch" >/dev/null 2>&1
    printf '{"run_id": "%s", "tag": "sw05equiv", "job": "%s", "switched": "%s", "master": "%s", "parts": "%s", "host": "%s"}\n' \
        "$(basename "$RUN_DIR")" "${SLURM_JOB_ID:-}" "$SWITCHED" "$MASTER" "$PARTS" "$(hostname)" > "$RUN_DIR/run.json"
    printf '%s\t%s\t%s\tsw05equiv\t\t\n' "$(basename "$RUN_DIR")" "${SLURM_JOB_ID:-}" "${SWITCHED:0:7}" >> "$ROOT/runs/index.tsv"
fi
OUT=$RUN_DIR/out
TIMES=$OUT/times.tsv
echo "run $RUN_DIR"
echo "master $MASTER"
echo "switched $SWITCHED"
trap 'rc=$?; echo "$(date -u +%FT%TZ) job ${SLURM_JOB_ID:-nojob} step sw05equiv exit $rc" >> "$ROOT/logs/job_status.log"' EXIT

# tools: the compare scripts, from the branch, because a master-against-master rerun has none
for pair in "master $MASTER" "switched $SWITCHED" "tools $(git -C "$REPO" rev-parse "origin/$BRANCH")"; do
    set -- $pair
    mkdir -p "$RUN_DIR/code_$1" || die "cannot make code_$1"
    git -C "$REPO" archive "$2" scripts | tar -x -C "$RUN_DIR/code_$1" || die "archive of $2 failed"
done
"$PY" -m pip install --quiet --no-deps --no-build-isolation --target "$RUN_DIR/pydeps" \
    "git+https://github.com/zeejaytan/sherd-worn.git@v0.1.0" || die "package install failed; is GitHub reachable from $(hostname)?"
PYTHONPATH=$RUN_DIR/pydeps "$PY" -c "
import sherd_worn
assert sherd_worn.__version__ == '0.1.0', sherd_worn.__version__
print('package', sherd_worn.__version__, sherd_worn.__file__)" || die "wrong package"

# run <arm> <args>: the master arm cannot see the package, the switched arm must import it
run() {
    local arm=$1; shift
    if [ "$arm" = master ]; then env -u PYTHONPATH "$PY" "$@"; else PYTHONPATH=$RUN_DIR/pydeps "$PY" "$@"; fi
}
check_imports() {
    local arm=$1 want=$2 got
    got=$(cd "$RUN_DIR/code_$arm/scripts" && run "$arm" -c "import wear_ops; print(wear_ops._proud_height.__module__)") || die "$arm does not import"
    echo "arm $arm: _proud_height from $got"
    [ "$got" = "$want" ] || die "arm $arm uses $got, not $want"
}
check_imports master wear_ops
if [ "$SWITCHED" != "$MASTER" ]; then check_imports switched sherd_worn.wear; fi

timed() {   # timed <part> <arm> <command...>; the wall time goes in times.tsv
    local part=$1 arm=$2 t0=$SECONDS rc; shift 2
    "$@"; rc=$?
    printf '%s\t%s\t%s\t%s\n' "$part" "$arm" "$((SECONDS - t0))" "$rc" >> "$TIMES"
    return $rc
}
build_u10() {   # build_u10 <mode> <part> <arm>
    run "$3" "$RUN_DIR/code_$3/scripts/write_u10_worn.py" --src "$ROOT/dataset" \
        --csc "$ROOT/../CSC/work/u10_corpus_30888410" --mode "$1" --scale-pct 200 \
        --out "$OUT/$2_$3" --workers "$CPUS"
}
build_v3() {    # build_v3 <arm>
    mkdir -p "$OUT/v3_$1"
    run "$1" "$RUN_DIR/code_$1/scripts/build_bbad_vessel_trainset.py" \
        --src "$ROOT/dataset/breaking_bad_vol.hdf5" --out-hdf5 "$OUT/v3_$1/smoke.hdf5" \
        --instances-per-object 3 --max-objects 6 --screen-csv "$ROOT/artifacts/corpus_screen.csv"
}
compare() {     # compare <part> <file> <manifest>
    local part=$1 file=$2 manifest=$3
    run switched "$RUN_DIR/code_tools/scripts/compare_hdf5_arrays.py" \
        "$OUT/${part}_master/$file" "$OUT/${part}_switched/$file" \
        --manifest-a "$OUT/${part}_master/$manifest" --manifest-b "$OUT/${part}_switched/$manifest" \
        --out "$OUT/compare_$part.json"
}
part_u10() {    # part_u10 <part> <mode> <file stem>
    local part=$1 mode=$2 stem=$3
    timed "$part" master build_u10 "$mode" "$part" master || return 1
    timed "$part" switched build_u10 "$mode" "$part" switched || return 1
    compare "$part" "$stem.hdf5" "$stem.manifest.json" || return 1
    rm -rf -- "${OUT:?}/${part}_master" "${OUT:?}/${part}_switched"
}
part_v3() {
    timed v3 master build_v3 master || return 1
    timed v3 switched build_v3 switched || return 1
    compare v3 smoke.hdf5 smoke.hdf5.manifest.json || return 1
    rm -rf -- "${OUT:?}/v3_master" "${OUT:?}/v3_switched"
}
part_fine() {
    # Capped so a slow fine-scan cannot take the other parts' time. Each finished object has its own file.
    timed fine-scan all timeout 110m env PYTHONPATH="$RUN_DIR/pydeps" "$PY" "$RUN_DIR/code_tools/scripts/compare_fine_scan_arms.py" \
        --master-scripts "$RUN_DIR/code_master/scripts" --src "$ROOT/dataset/real_finetune.hdf5" \
        --objects bones__limb2 bones__limb4 ceramics__blue_pot --out "$OUT/fine_scan"
}

bad=0
for part in $PARTS; do
    echo "=== $part $(date -u +%FT%TZ)"
    case "$part" in
        worn) part_u10 worn worn u10_worn_d200 ;;
        rough) part_u10 rough noise u10_noise_d200 ;;
        v3) part_v3 ;;
        fine-scan) part_fine ;;
        *) die "unknown part $part" ;;
    esac
    rc=$?
    echo "PART $part exit $rc"
    [ "$rc" = 0 ] || bad=1
done
echo "=== times (part, arm, seconds, exit)"
cat "$TIMES"
echo "SW05_EQUIV bad=$bad run=$RUN_DIR"
exit $bad
