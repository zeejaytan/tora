"""Report placement quality vs piece count for the C1 sweep.

Raw `part_accuracy` is not comparable across piece counts: the anchor is clamped
to GT and always passes, so part_accuracy has a floor of 1/k. This converts it to
the **non-anchor placement rate**

    rate = (seated - free) / (k - free)

i.e. the fraction of the non-anchor pieces that were correctly seated
(0.0 = anchor only, 1.0 = every piece placed) — directly comparable at every k.

Reading (tests H2, "is the mating signal contextual?"):
  - rate low at k=2 and rising with k => CONTEXTUAL: TORA needs >2-piece context.
  - rate flat/high from k=2           => mating is genuinely pairwise.

REWIRED 2026-09-05. Every number here now comes from scripts/readout.py, the one
place a run is read. WHAT MOVED: the rotation column, and only that one. The
placement rate was already anchor-corrected — this script was half-right, which
is the dangerous kind: it took the free piece out of the accuracy and left it in
the rotation error sitting beside it. `rotation_error` is summed over the
non-anchor pieces and divided by all of them, so the correction is n/(n-1), and
on a sweep that is a DIFFERENT factor in every row of the table this script
exists to compare: x2.000 at k=2, x1.500 at k=3, x1.125 at k=9. A rotation
column read down that table was reading the piece count, not the model. The
placement rate is unchanged.

Reconciliation and the control that licenses the module:
docs/notes/READOUT_RECONCILIATION.md.

Usage:
  python scripts/analyze_piececount_sweep.py --results-dir <run>/results
"""

import argparse
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
    ap.add_argument("--label", default="")
    args = ap.parse_args()

    run_dir = Path(args.results_dir)
    if run_dir.name == "results":
        run_dir = run_dir.parent

    # The subset size is in the object's own name; a k-piece subset must be
    # scored out of k, not out of the whole pot. Passing it to read_run is what
    # keeps the floor and the denominator following the subset instead of
    # silently staying at the full fragment count.
    probe = read_run(run_dir)
    if not probe:
        raise SystemExit(f"no per-draw json under {run_dir}/results")
    subset = {}
    for rec in probe:
        m = re.search(r"_k(\d+)_", rec.object_name)
        if m:
            subset[rec.object_name] = max(int(m.group(1)), rec.n_fragments)
    records = read_run(run_dir, subset=subset or None)

    per_obj = defaultdict(list)
    for rec in records:
        per_obj[rec.object_name].append(rec)

    by_k = defaultdict(lambda: {"mean": [], "best": [], "rot": [], "n": 0})
    for name, gens in per_obj.items():
        k = gens[0].n_fragments
        placed = gens[0].placed

        rates = [(g.seated - g.floor) / placed if placed else float("nan")
                 for g in gens]
        by_k[k]["mean"].append(float(np.mean(rates)))
        by_k[k]["best"].append(float(np.max(rates)))
        by_k[k]["rot"].append(float(np.mean([g.turn_deg for g in gens])))
        by_k[k]["n"] += 1

    print(f"\n=== Piece-count sweep: {args.label or args.results_dir} ===")
    print("  k | subsets | non-anchor placement rate (mean / best-of-n) | rot_err")
    print("  --+---------+-----------------------------------------------+--------")
    ks = sorted(by_k)
    for k in ks:
        d = by_k[k]
        print(f"  {k:2d} |   {d['n']:3d}   |        {np.mean(d['mean']):.3f}  /  {np.mean(d['best']):.3f}"
              f"                  | {np.mean(d['rot']):6.2f}")

    print("\n  rot_err is the turn on the pieces the model had to place, so it is")
    print("  comparable down the k column. Best-of-n is the luckiest draw, not")
    print("  the typical one -- read the mean when deciding anything.")

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

    for line in format_flags(records):
        print(f"  !! {line}")
    print(f"\n  Weight: {weight(records)}.")

    print("\n  A trend down this table is an index to a picture. Draw the ends of")
    print("  the sweep before quoting it:\n")
    print(f"  python scripts/render_assembly_grid.py \\")
    print(f'      --runs "{run_dir.name}={run_dir.as_posix()}/clouds" \\')
    print(f"      --out artifacts/{run_dir.name}.png")
    print()


if __name__ == "__main__":
    main()
