"""Report placement quality vs piece count for the C1 sweep.

Raw `part_accuracy` is not comparable across piece counts: the anchor is clamped
to GT and always passes, so part_accuracy has a floor of 1/k. This converts it to
the **non-anchor placement rate**

    rate = (part_accuracy * k - 1) / (k - 1)

i.e. the fraction of the k-1 non-anchor pieces that were correctly seated
(0.0 = anchor only, 1.0 = every piece placed) — directly comparable at every k.

Reading (tests H2, "is the mating signal contextual?"):
  - rate low at k=2 and rising with k => CONTEXTUAL: TORA needs >2-piece context.
  - rate flat/high from k=2           => mating is genuinely pairwise.

Usage:
  python scripts/analyze_piececount_sweep.py --results-dir <run>/results
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
    ap.add_argument("--label", default="")
    args = ap.parse_args()

    per_obj = defaultdict(list)
    for fp in sorted(glob.glob(f"{args.results_dir}/*.json")):
        with open(fp) as f:
            d = json.load(f)
        per_obj[d["name"]].append(d)

    by_k = defaultdict(lambda: {"mean": [], "best": [], "rot": [], "n": 0})
    for name, gens in per_obj.items():
        m = re.search(r"_k(\d+)_", name)
        k = int(m.group(1)) if m else int(gens[0]["num_parts"])
        k = max(k, int(gens[0]["num_parts"]))

        def rate(pa):
            return (pa * k - 1.0) / (k - 1.0) if k > 1 else float("nan")

        rates = [rate(g["part_accuracy"]) for g in gens]
        by_k[k]["mean"].append(float(np.mean(rates)))
        by_k[k]["best"].append(float(np.max(rates)))
        by_k[k]["rot"].append(float(np.mean([g["rotation_error"] for g in gens])))
        by_k[k]["n"] += 1

    print(f"\n=== Piece-count sweep: {args.label or args.results_dir} ===")
    print("  k | subsets | non-anchor placement rate (mean / best-of-n) | rot_err")
    print("  --+---------+-----------------------------------------------+--------")
    ks = sorted(by_k)
    for k in ks:
        d = by_k[k]
        print(f"  {k:2d} |   {d['n']:3d}   |        {np.mean(d['mean']):.3f}  /  {np.mean(d['best']):.3f}"
              f"                  | {np.mean(d['rot']):6.2f}")

    if len(ks) >= 2:
        lo, hi = ks[0], ks[-1]
        a, b = np.mean(by_k[lo]["mean"]), np.mean(by_k[hi]["mean"])
        print(f"\n  k={lo} -> k={hi}: placement rate {a:.3f} -> {b:.3f}"
              f"  ({'RISES with context => H2 CONTEXTUAL' if b > a + 0.10 else 'flat/falls => mating is pairwise, H2 not supported'})")
        xs, ys = [], []
        for k in ks:
            xs += [k] * len(by_k[k]["mean"])
            ys += by_k[k]["mean"]
        if len(set(xs)) > 1:
            try:
                from scipy.stats import spearmanr
                rho, p = spearmanr(xs, ys)
                print(f"  Spearman(k, placement rate): rho={rho:.3f} p={p:.4f}")
            except Exception:
                pass


if __name__ == "__main__":
    main()
