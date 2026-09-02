"""Read the scale ladder: does the conditioning number alone move the answer?

The same eight pots, the same checkpoint, the same seed, the same coordinates.
The ONLY thing that changes between rungs is the number in `scales` -- what the
object's size would have been if the scan had been saved in different units.
`scales` is fed to the flow model at every denoising step and encoded
sinusoidally onto all 5000 points (tora/modeling/flow_model/embedding.py), so
it is a model input, not bookkeeping. Breaking Bad trains at ~0.5; the Fractura
ceramics are stored in millimetres and arrive at 45-120.

If rotation error tracks the rung, the Fractura failure is the storage units.
If it is flat, this hypothesis is dead and the failure is in the material.

Two things this prints that the per-draw json does not:

  NON-ANCHOR rotation. compute_transform_errors skips the anchor fragment but
  still divides by every part, so a 5-part pot's reported mean is diluted by one
  free zero. Multiplying back by n/(n-1) gives the error on the fragments the
  model actually had to place. Comparisons across pots with different fragment
  counts are only fair in that column.

  The rung's actual `scales`, read back out of the run rather than assumed from
  the multiplier -- if the knob did not take effect, that column says so.

Usage:
  python scripts/summarise_scale_ladder.py --runs <run_dir> [<run_dir> ...]
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path

# Breaking Bad stores max|v| = 0.5; training multiplies by random_scale_range
# (0.75, 1.25). Outside this the model is extrapolating on an input it has
# never seen, in an encoding whose top frequency is 2^9.
TRAIN_LO, TRAIN_HI = 0.375, 0.625


def median(xs):
    s = sorted(xs)
    n = len(s)
    if not n:
        return float("nan")
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def load(run_dir: Path):
    res = run_dir / "results"
    if not res.is_dir():
        return None
    draws = [json.loads(p.read_text()) for p in sorted(res.glob("*_generation*.json"))]
    return draws or None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True)
    a = ap.parse_args()

    rungs = []
    for r in a.runs:
        d = Path(r)
        draws = load(d)
        if draws is None:
            print(f"(skipping {d.name}: no results/)")
            continue
        by_pot = defaultdict(list)
        for x in draws:
            by_pot[x["name"]].append(x)
        scale = median([x["scales"] for x in draws if x.get("scales")])
        rungs.append((scale, d.name, by_pot))

    if not rungs:
        raise SystemExit("no runs with results")
    rungs.sort(key=lambda t: t[0])

    pots = sorted({p for _, _, bp in rungs for p in bp})
    pw = max(len(p) for p in pots)

    print("\nOne knob, eight pots. Only `scales` differs between these rows;")
    print("the point coordinates the network sees are identical (asserted by")
    print("scripts/check_scale_conditioning.py).\n")
    print("Rotation error on the fragments the model had to place (the anchor")
    print("is excluded), in degrees. Lower is better; 90 deg is a right angle.\n")

    head = f"{'scale fed in':>12s}  {'band':>5s}  " + "  ".join(f"{p[:9]:>9s}" for p in pots)
    print(head + f"  {'ALL POTS':>9s}")
    print("-" * len(head + "  " + " " * 9))

    for scale, name, by_pot in rungs:
        band = "yes" if TRAIN_LO <= scale <= TRAIN_HI else "no"
        cells, pooled = [], []
        for p in pots:
            draws = by_pot.get(p)
            if not draws:
                cells.append(f"{'-':>9s}")
                continue
            n = draws[0]["num_parts"]
            f = n / (n - 1) if n > 1 else 1.0
            vals = [x["rotation_error"] * f for x in draws]
            pooled += vals
            cells.append(f"{median(vals):8.1f}d")
        print(f"{scale:12.3f}  {band:>5s}  " + "  ".join(cells) +
              f"  {median(pooled):8.1f}d")

    print()
    for scale, name, _ in rungs:
        print(f"  {scale:10.3f}  {name}")

    best = min(rungs, key=lambda t: median(
        [x["rotation_error"] * (x["num_parts"] / max(x["num_parts"] - 1, 1))
         for bp in [t[2]] for ds in bp.values() for x in ds]))
    worst = max(rungs, key=lambda t: median(
        [x["rotation_error"] * (x["num_parts"] / max(x["num_parts"] - 1, 1))
         for bp in [t[2]] for ds in bp.values() for x in ds]))
    print(f"\nBest rung: scale {best[0]:.3f}.  Worst rung: scale {worst[0]:.3f}.")
    print("If those two are far apart and the trend is monotone, the storage")
    print("units were doing the damage. If every rung is within a few degrees")
    print("of the others, they were not, and this line of enquiry is closed.\n")


if __name__ == "__main__":
    main()
