#!/bin/bash
#SBATCH --job-name=u17-overlap
#SBATCH --partition=sapphire
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=128G
#SBATCH --time=04:00:00
#SBATCH --output=/data/gpfs/projects/punim2657/TORA/rank_u17/u17_overlap_%j.log
set -euo pipefail
# U17 Revision 4: overlap measured on existing bundles (no conversion, no answer key), the
# cut-off set on GARF's calibration pots, every seen pot re-ranked. Rule and read-outs in
# .scratch/attempt-ranker/preregistration-overlap.md.
module purge
module load Anaconda3/2024.02-1
eval "$(conda shell.bash hook)"
conda activate /data/gpfs/projects/punim2657/TORA/envs/tora
cd /data/gpfs/projects/punim2657/TORA/repo
T=/data/gpfs/projects/punim2657/TORA
R=$T/rank_u17
B=$R/l2_32147567          # GARF bundles (calibration and test pots)
CALR=$R/calib_32274553    # Revision 3 calibration: ranks, l2 and key per pot
TESTR=$R/test_32317912    # GARF held-out test
TORAR=$R/tora_32330575    # TORA rerun after the converter fix
GL=$R/fractura_labels_32111374.json
TL=$R/tora_fractura_labels.json
O=$R/overlap_${SLURM_JOB_ID}; mkdir -p "$O"
CAL=(blue_pot narrow_bottle2 narrow_bottle4 pink_bowl plate)

echo "### GARF clouds against the scans (converter tolerance: scale 5%, shift 0.5% of pot)"
python - "$T/dataset/fractura_fresh.hdf5" "$B" "${CAL[@]}" narrow_bottle3 galli_pot <<'PY'
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, "scripts")
import rank_convert as rc
from readout import part_slices
h5, B, pots = sys.argv[1], Path(sys.argv[2]), sys.argv[3:]
for p in pots:
    run = next(iter(json.loads((B / p / "key" / "idmap.json").read_text()).values()))["run"]
    d = np.load(run, allow_pickle=True)
    scans = rc.load_scans(h5, f"fractura_fresh/{p}")
    k, o = rc.run_frame(d["pts_gt"].astype(float), list(part_slices(d["points_per_part"])), scans, run)
    print(f"{p}: scale {k:.4f}, shift {np.round(o, 4).tolist()} ({run})")
PY

echo "### TORA: shift by area-weighted centres (now) vs vertex means (used for tora_32330575)"
python - "$T/dataset/fractura_fresh.hdf5" "$TORAR" narrow_bottle3 plate <<'PY'
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, "scripts")
import rank_convert as rc
from readout import part_slices, unit_box_scale
h5, TR, pots = sys.argv[1], Path(sys.argv[2]), sys.argv[3:]
for p in pots:
    runs = sorted({m["run"] for m in json.loads((TR / p / "key" / "idmap.json").read_text()).values()})
    scans = rc.load_scans(h5, f"fractura_fresh/{p}")
    size = unit_box_scale(np.concatenate([v for v, _ in scans]))
    worst = 0.0
    for run in runs:
        d = np.load(run, allow_pickle=True)
        gt, sl = d["pts_gt"].astype(float), list(part_slices(d["points_per_part"]))
        k, o = rc.run_frame(gt, sl, scans, run)
        cg = np.array([gt[s:e].mean(0) for s, e in sl]) / k
        o_old = (cg - np.array([v.mean(0) for v, _ in scans])).mean(0)
        worst = max(worst, 100 * np.linalg.norm(o - o_old) / size)
    print(f"{p}: {len(runs)} runs; shift now vs then differs by at most {worst:.3f}% of pot")
PY

for p in "${CAL[@]}" narrow_bottle3 galli_pot; do
    python scripts/overlap_measure.py --bundles "$B/$p/bundles" --out "$O/garf/${p}_overlap.json"
done
for p in narrow_bottle3 plate; do
    python scripts/overlap_measure.py --bundles "$TORAR/$p/bundles" --out "$O/tora/${p}_overlap.json"
done
python scripts/u17_overlap.py --prereg .scratch/attempt-ranker/preregistration-overlap.md \
    --profile-pct 0.873 --out "$O/report.json" \
    --calib-pots "$CALR" "$GL" "$O/garf" "${CAL[@]}" \
    --pots garf-test "$TESTR" "$GL" "$O/garf" narrow_bottle3 galli_pot \
    --pots tora "$TORAR" "$TL" "$O/tora" narrow_bottle3 plate
python scripts/overlap_look.py --bundles "$TORAR/plate/bundles" --report "$O/report.json" \
    --pot tora/plate --out "$O/tora_plate.png"
python scripts/overlap_look.py --bundles "$TORAR/narrow_bottle3/bundles" --report "$O/report.json" \
    --pot tora/narrow_bottle3 --out "$O/tora_narrow_bottle3.png"
python scripts/overlap_look.py --bundles "$B/plate/bundles" --report "$O/report.json" \
    --pot garf-calibration/plate --out "$O/garf_plate.png"
