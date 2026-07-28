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

Usage:
  python scripts/analyze_erosion_sweep.py --results-dir <run>/results \
      [--calibration dataset/erosion_sweep.calibration.json]
"""

import argparse
import glob
import json
import re
from collections import defaultdict

import numpy as np


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

    per = defaultdict(list)
    for fp in sorted(glob.glob(f"{args.results_dir}/*.json")):
        with open(fp) as f:
            d = json.load(f)
        tag = d["name"].split("/")[-1]
        m = re.match(r"(.+)_e(\d+)$", tag)
        if not m:
            continue
        obj, strength = m.group(1), int(m.group(2)) / 100.0
        k = int(d["num_parts"])
        rate = (d["part_accuracy"] * k - 1.0) / (k - 1.0) if k > 1 else float("nan")
        per[(obj, strength)].append((rate, d["rotation_error"]))

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

    print("\n  MEAN seating rate across objects:")
    means = []
    for s in strengths:
        vals = [np.mean([r for r, _ in per[(o, s)]]) for o in objects if (o, s) in per]
        means.append(np.mean(vals) if vals else float("nan"))
        rel = ""
        if calib:
            rs = [c["relief_p90_mean"] for c in calib.values()
                  if abs(c["strength"] - s) < 1e-6]
            if rs:
                rel = f"   [achieved relief_p90 {np.mean(rs):.4f}]"
        print(f"    wear {s:.2f}:  seating {means[-1]:.3f}{rel}")

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


if __name__ == "__main__":
    main()
