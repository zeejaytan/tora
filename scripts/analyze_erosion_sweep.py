"""Report seating accuracy against simulated wear (C3 causal test).

Raw `part_accuracy` is not comparable across objects with different piece
counts (the clamped anchor gives it a floor of 1/k), so this reports the
anchor-corrected NON-ANCHOR seating rate:

    rate = (part_accuracy * k - 1) / (k - 1)

= the fraction of the k-1 loose fragments actually seated. 1.0 = every fragment
placed, 0.0 = none beyond the fixed anchor.

Reading:
  rate falls monotonically as wear rises  => WEAR CAUSES the failure.
  rate flat while wear demonstrably rises => wear is NOT sufficient; the Juglet
                                             deficit must be carried by
                                             something else.

The second reading is only meaningful if the achieved wear actually reached the
Juglet's level — check the calibration JSON. GARF's Exp 7 failed exactly here.

REWIRED 2026-09-05. Every number here now comes from scripts/readout.py, the one
place a run is read. WHAT MOVED: nothing in the seating table. The rate above
was already anchor-corrected and the corrected values agree exactly. WHAT IS
NEW: a turn column. This script read `rotation_error` out of every result file
and then never printed it, which is why the C3 verdict has always rested on the
seating rate alone — and seating passes a sherd on distance however it is
turned. The turn is the physical quantity wear should move, so it is printed
beside the rate now, corrected by n/(n-1) for the free anchor. Reconciliation:
docs/notes/READOUT_RECONCILIATION.md.

Usage:
  python scripts/analyze_erosion_sweep.py --results-dir <run>/results \
      [--calibration dataset/erosion_sweep.calibration.json]
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from readout import format_flags, read_run, weight  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results-dir", required=True)
    ap.add_argument("--calibration", default=None)
    args = ap.parse_args()

    calib = {}
    if args.calibration:
        try:
            calib = json.loads(open(args.calibration).read())
        except Exception:
            pass

    run_dir = Path(args.results_dir)
    if run_dir.name == "results":
        run_dir = run_dir.parent
    records = read_run(run_dir)
    if not records:
        raise SystemExit(f"no per-draw json under {run_dir}/results")

    per = defaultdict(list)
    for rec in records:
        tag = rec.object_name.split("/")[-1]
        m = re.match(r"(.+)_e(\d+)$", tag)
        if not m:
            continue
        obj, strength = m.group(1), int(m.group(2)) / 100.0
        rate = ((rec.seated - rec.floor) / rec.placed
                if rec.placed else float("nan"))
        per[(obj, strength)].append((rate, rec.turn_deg))

    objects = sorted({o for o, _ in per})
    strengths = sorted({s for _, s in per})

    print("\n=== C3: seating accuracy vs simulated wear ===")
    header = "  object        " + "".join(f"  wear {s:<5.2f}" for s in strengths)
    print(header)
    print("  " + "-" * (len(header) - 2))
    for obj in objects:
        row = f"  {obj:<14s}"
        for s in strengths:
            v = per.get((obj, s))
            row += f"  {np.mean([r for r, _ in v]):<10.3f}" if v else "  {:<10s}".format("-")
        print(row)

    print("\n  MEAN seating rate across objects, and the turn beside it:")
    means = []
    for s in strengths:
        vals = [np.mean([r for r, _ in per[(o, s)]]) for o in objects if (o, s) in per]
        turns = [np.mean([t for _, t in per[(o, s)]]) for o in objects if (o, s) in per]
        means.append(np.mean(vals) if vals else float("nan"))
        rel = ""
        if calib:
            rs = [c["relief_p90_mean"] for c in calib.values()
                  if abs(c["strength"] - s) < 1e-6]
            if rs:
                rel = f"   [achieved relief_p90 {np.mean(rs):.4f}]"
        turn = np.mean(turns) if turns else float("nan")
        print(f"    wear {s:.2f}:  seating {means[-1]:.3f}   "
              f"turn {turn:5.1f}d{rel}")

    if len(means) >= 2 and not np.isnan(means[0]) and not np.isnan(means[-1]):
        drop = means[0] - means[-1]
        print(f"\n  wear {strengths[0]:.2f} -> {strengths[-1]:.2f}: "
              f"seating {means[0]:.3f} -> {means[-1]:.3f}  (drop {drop:+.3f})")
        xs, ys = [], []
        for s in strengths:
            for o in objects:
                if (o, s) in per:
                    xs.append(s)
                    ys.append(np.mean([r for r, _ in per[(o, s)]]))
        try:
            from scipy.stats import spearmanr
            rho, p = spearmanr(xs, ys)
            print(f"  Spearman(wear, seating): rho={rho:.3f} p={p:.4f}")
        except Exception:
            pass
        if drop > 0.15:
            print("  => seating FALLS with wear: supports wear as the CAUSE.")
        else:
            print("  => seating roughly FLAT: wear alone does NOT reproduce the failure")
            print("     (only interpretable if achieved relief reached the Juglet's level).")
        print("     Read the turn column before accepting either verdict: seating")
        print("     passes a sherd on distance however it is turned.")

    for line in format_flags(records):
        print(f"  !! {line}")
    print(f"\n  Weight: {weight(records)}.")
    print()
    print("  A wear trend is an index to a picture. Draw the ends of the sweep")
    print("  before quoting it:")
    print(f"    python scripts/render_assembly_grid.py \\")
    print(f'        --runs "{run_dir.name}={run_dir.as_posix()}/clouds" \\')
    print(f"        --out artifacts/{run_dir.name}.png")
    print()


if __name__ == "__main__":
    main()
