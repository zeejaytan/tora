"""Is a collapsed reassembly a PLACEMENT failure or an IDENTITY failure?

Written 2026-09-07 for juglet-cause ticket 07 (`narrow_bottle3`).

The distinction matters because it decides what to do next. If the model put
every sherd somewhere wrong, that is a placement failure and more or better
training is the lever. If the model built a perfectly good pot but exchanged two
sherds that look alike, that is an identity failure -- the geometry is right, the
labels are swapped -- and more training is not the lever at all. On the normal
archaeological material this project is about (plain body sherds with no rim and
no profile) interchangeable-looking pieces are the rule, not the exception, so
which of the two is happening is load-bearing well beyond one bottle.

THE TEST. For one draw, score every predicted sherd against every ground-truth
sherd, not just against its own. That gives a cost matrix; the Hungarian
algorithm then finds the best matching of predicted sherds to ground-truth
sherds. Two numbers come out:

  identity  -- the cost of the assignment the evaluator uses (sherd i is sherd i)
  best      -- the cost of the best assignment over all permutations

If `best` is much lower than `identity` AND the winning permutation is not the
identity, the pieces are in the right PLACES wearing the wrong NAMES. If `best`
is barely below `identity`, no relabelling rescues the assembly and the failure
is genuine mis-placement.

The per-sherd figure is the same one the renders caption -- symmetric chamfer
between the ground-truth sherd and the proposed sherd, both divided by the
longest side of the ground truth's bounding box, reported as
`100 * sqrt(chamfer / 2)`, i.e. **percent of pot size**. It is used here rather
than turn because a near-planar sherd can read 177 degrees while sitting a
millimetre from home; distance from home cannot be fooled that way
(`scripts/render_juglet_vs_fresh.py`).

The anchor is excluded from the reported worst-sherd figures (it is handed over
already seated) but is KEPT in the assignment problem, because a permutation that
moves the anchor is exactly the kind of relabelling we want to be able to see.

Usage:
    python scripts/check_identity_swap.py --clouds artifacts/nb3/whole
    python scripts/check_identity_swap.py --clouds artifacts/nb3/whole --pot narrow_bottle3
"""

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from readout import chamfer, unit_box_scale  # noqa: E402

try:
    from scipy.optimize import linear_sum_assignment
except ImportError:  # pragma: no cover
    linear_sum_assignment = None

# Points per sherd used to build the cost matrix. The full clouds run to 3000
# points a sherd and the matrix is quadratic in that; 300 is plenty to decide
# whether one blob is standing where another belongs, and the numbers actually
# REPORTED are recomputed on the full clouds for the winning assignment.
SUBSAMPLE = 300


def _sub(pts: np.ndarray, rng: np.random.Generator, n: int = SUBSAMPLE) -> np.ndarray:
    if len(pts) <= n:
        return pts
    return pts[rng.choice(len(pts), size=n, replace=False)]


def pct(c: float) -> float:
    """Chamfer in the unit-box frame -> percent of pot size."""
    return 100.0 * float(np.sqrt(max(c, 0.0) / 2.0))


def cost_matrix(gt, prop, ids, parts, unit, rng):
    """cost[i][j] = how far predicted sherd j sits from ground-truth sherd i."""
    g = [_sub(gt[ids == p] / unit, rng) for p in parts]
    q = [_sub(prop[ids == p] / unit, rng) for p in parts]
    n = len(parts)
    C = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            C[i, j] = chamfer(g[i], q[j])
    return C


def analyse_draw(gt, prop, ids, parts, anchor, unit, rng):
    C = cost_matrix(gt, prop, ids, parts, unit, rng)
    n = len(parts)
    ident = np.arange(n)
    if linear_sum_assignment is None:
        raise SystemExit("scipy is required for the assignment step")
    _, best = linear_sum_assignment(C)

    free = [k for k, p in enumerate(parts) if p != anchor]
    worst_ident = max((pct(C[k, ident[k]]) for k in free), default=0.0)
    worst_best = max((pct(C[k, best[k]]) for k in free), default=0.0)
    swapped = [(parts[k], parts[best[k]]) for k in range(n) if best[k] != k]
    return {
        "worst_identity": worst_ident,
        "worst_best": worst_best,
        "permutation": best,
        "swapped": swapped,
        "per_part_identity": {parts[k]: pct(C[k, k]) for k in range(n)},
        "per_part_best": {parts[k]: pct(C[k, best[k]]) for k in range(n)},
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--clouds", required=True, help="directory of saved *.npz clouds")
    ap.add_argument("--pot", default=None, help="only this object")
    ap.add_argument("--draws", type=int, default=None, help="cap the draws examined")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    rng = np.random.default_rng(a.seed)
    files = sorted(Path(a.clouds).glob("*.npz"))
    if not files:
        raise SystemExit(f"no clouds under {a.clouds}")

    print("Is the collapse a placement failure or an identity failure?")
    print("Worst free sherd, percent of pot size. `identity` is what the evaluator")
    print("scores; `relabelled` is the best that ANY renaming of the sherds could do.")
    print("If relabelling does not rescue it, the sherds are genuinely misplaced.\n")
    print(f"{'object':18s} {'sherds':>6s} {'identity':>9s} {'relabelled':>11s} "
          f"{'rescued?':>9s}  swaps the relabelling makes")
    print("-" * 92)

    rows = []
    for f in files:
        d = np.load(f, allow_pickle=True)
        name = str(d["name"]).split("/")[-1]
        if a.pot and a.pot not in name:
            continue
        gt = d["pts_gt"]
        ids = d["part_ids"]
        props = d["generations_proposed"]
        parts = sorted(set(ids.tolist()))
        anchor = max(parts, key=lambda p: int((ids == p).sum()))
        unit = unit_box_scale(gt)

        n_draws = len(props) if a.draws is None else min(a.draws, len(props))
        per = [analyse_draw(gt, props[k], ids, parts, anchor, unit, rng)
               for k in range(n_draws)]

        # The median draw by the evaluator's own reading, so the row is not the
        # best attempt. Ranking on `worst_identity` keeps that consistent.
        order = sorted(range(n_draws), key=lambda k: per[k]["worst_identity"])
        mid = order[n_draws // 2]
        r = per[mid]

        drop = r["worst_identity"] - r["worst_best"]
        rescued = "YES" if (r["swapped"] and drop > 0.25 * r["worst_identity"]
                            and r["worst_best"] < 5.0) else "no"
        swaps = ", ".join(f"{i}<-{j}" for i, j in r["swapped"]) or "none (identity wins)"
        print(f"{name:18s} {len(parts):6d} {r['worst_identity']:8.2f}% "
              f"{r['worst_best']:10.2f}% {rescued:>9s}  {swaps}")
        rows.append((name, mid, r, parts, anchor))

    print("\nPer-sherd detail on the median draw (percent of pot size from home):")
    for name, mid, r, parts, anchor in rows:
        print(f"\n  {name}  (draw {mid}, anchor is sherd {anchor})")
        for p in parts:
            tag = "  <- anchor" if p == anchor else ""
            print(f"     sherd {p}: as itself {r['per_part_identity'][p]:7.2f}%   "
                  f"best relabelling {r['per_part_best'][p]:7.2f}%{tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
