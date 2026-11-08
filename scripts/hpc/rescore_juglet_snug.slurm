#!/bin/bash
# pr-workspace .scratch/uneven-wear/issues/11 (U20): re-score GARF's saved Juglet attempts
# (rough-worn-dose arms) against juglet_gt and juglet_gt_snug on one ruler
# (scripts/rescore_on_new_reference.py). Writes $RUN_DIR/out only.
#
# Submit from the login node through new_run.sh:
#   git -C $T/repo fetch origin
#   git -C $T/repo show $SHA:scripts/hpc/rescore_juglet_snug.slurm > $TMPDIR/rjs.slurm
#   $P/agent/pr-workspace/scripts/new_run.sh $T $T/repo $SHA rescore-juglet-snug $TMPDIR/rjs.slurm
# RUNS overrides the glob of GARF eval run dirs.
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/tora_%x_%j.log
#SBATCH --job-name=tora-rescore-snug
#SBATCH --partition=sapphire,cascade
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=06:00:00
set -euo pipefail
: "${RUN_DIR:?submit through new_run.sh}" "${SOURCE_COMMIT:?}" "${CANONICAL:?}"
export PYTHONDONTWRITEBYTECODE=1
P=/data/gpfs/projects/punim2657
PY=$P/TORA/envs/tora/bin/python
OLD=$P/TORA/dataset/juglet_gt.hdf5
NEW=$P/TORA/runs/20261109-0008_57cd34b_reseat-juglet2/out/juglet_gt_snug.hdf5
source $P/agent/pr-workspace/scripts/run_from_commit.sh "$CANONICAL" "$SOURCE_COMMIT" "$RUN_DIR"
cd "$SRC"
md5sum "$OLD" "$NEW" | tee -a "$RUN_DIR/source.txt"
if [ -z "${RUNS:-}" ]; then
  RUNS=$(ls -d $P/GARF/logs/rwlora/rwlora_eval_*juglet*/version_0 2>/dev/null || true)
fi
[ -n "$RUNS" ] || { echo "no GARF Juglet eval runs found"; ls $P/GARF/logs/rwlora | head -50; exit 1; }
echo "$RUNS" | tee "$RUN_DIR/out/runs.txt"
echo "$RUNS" | wc -l
$PY -u scripts/rescore_on_new_reference.py --old "$OLD" --new "$NEW" --group juglet_gt \
    --pot-mm 65 --json "$RUN_DIR/out/rescore.json" $RUNS
echo "=== by arm (solid sherds; right way round = full reassembly count)"
$PY - "$RUN_DIR/out/rescore.json" <<'EOF'
import json, re, sys
from collections import defaultdict
d = json.load(open(sys.argv[1]))
agg = defaultdict(lambda: defaultdict(int))
for key, row in d.items():
    m = re.search(r"rwlora_eval_(.+?)_ds(\d+)", key)
    arm = (m[1] if m else key.split("::")[0]) + (f" ds{m[2]}" if m else "")
    s = row["solid"]
    n = len(s["own"])
    a = agg[arm]
    a["attempts"] += n
    for k in ("own", "oriented", "own_snug", "oriented_snug"):
        a[k] += sum(s[k])
    a["full"] += sum(x == 9 for x in s["oriented"])
    a["full_snug"] += sum(x == 9 for x in s["oriented_snug"])
    a[">=7"] += sum(x >= 7 for x in s["oriented"])
    a[">=7_snug"] += sum(x >= 7 for x in s["oriented_snug"])
    a["changed"] += len(s["changed"])
print(f"{'arm':28s} {'att':>5s} {'own/att':>15s} {'rwr/att':>15s} {'full':>7s} {'>=7':>9s} {'changed':>7s}")
for arm, a in sorted(agg.items()):
    n = a["attempts"]
    print(f"{arm:28s} {n:5d} {a['own']/n:6.2f}->{a['own_snug']/n:6.2f}  {a['oriented']/n:6.2f}->{a['oriented_snug']/n:6.2f}"
          f"  {a['full']:2d}->{a['full_snug']:2d}  {a['>=7']:3d}->{a['>=7_snug']:3d}  {a['changed']:7d}")
EOF
ls -la "$RUN_DIR/out"
