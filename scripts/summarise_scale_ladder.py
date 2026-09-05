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

REWIRED 2026-09-05. This script already applied the n/(n-1) correction, and it
was the only one of the five that did. It now gets the same number from
scripts/readout.py instead of computing it here, so there is one place to fix
if the anchor count ever stops being one. WHAT MOVED: nothing. The eight rungs
by eight pots plus the pooled column -- 72 cells -- regenerate identically, the
largest difference being 0.048 deg, which is the rounding of the one-decimal
figures already published. That control is what licenses the module elsewhere:
docs/notes/READOUT_RECONCILIATION.md. The flags, weight and render lines below
the table are new; the table itself is byte-for-byte what it was.

Usage:
  python scripts/summarise_scale_ladder.py --runs <run_dir> [<run_dir> ...]
"""

import argparse
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from readout import TRAINED_SCALE_BAND, format_flags, read_run, weight  # noqa: E402

# Breaking Bad stores max|v| = 0.5; training multiplies by random_scale_range
# (0.75, 1.25). Outside this the model is extrapolating on an input it has
# never seen, in an encoding whose top frequency is 2^9. The band is the
# module's, so the ladder and the health flags cannot disagree about it.
TRAIN_LO, TRAIN_HI = TRAINED_SCALE_BAND


def median(xs):
    s = sorted(xs)
    n = len(s)
    if not n:
        return float("nan")
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True)
    a = ap.parse_args()

    rungs, all_records = [], []
    for r in a.runs:
        d = Path(r)
        if not (d / "results").is_dir():
            print(f"(skipping {d.name}: no results/)")
            continue
        records = read_run(d)
        if not records:
            print(f"(skipping {d.name}: no results/)")
            continue
        all_records += records
        by_pot = defaultdict(list)
        for x in records:
            by_pot[x.object_name].append(x)
        scale = median([x.model_scale for x in records if x.model_scale])
        rungs.append((scale, d.name, by_pot))

    if not rungs:
        raise SystemExit("no runs with results")
    rungs.sort(key=lambda t: t[0])

    pots = sorted({p for _, _, bp in rungs for p in bp})
    # names arrive as "<dataset>/<object>"; the dataset half is the same on
    # every column and eats the whole header width if it is left on.
    short = {p: p.split("/")[-1] for p in pots}

    print("\nOne knob, eight pots. Only `scales` differs between these rows;")
    print("the point coordinates the network sees are identical (asserted by")
    print("scripts/check_scale_conditioning.py).\n")
    print("Rotation error on the fragments the model had to place (the anchor")
    print("is excluded), in degrees. Lower is better; 90 deg is a right angle.\n")

    cw = max(9, max(len(v) for v in short.values()))
    head = (f"{'scale fed in':>12s}  {'band':>5s}  "
            + "  ".join(f"{short[p]:>{cw}s}" for p in pots))
    print(head + f"  {'ALL POTS':>{cw}s}")
    print("-" * (len(head) + 2 + cw))

    for scale, name, by_pot in rungs:
        band = "yes" if TRAIN_LO <= scale <= TRAIN_HI else "no"
        cells, pooled = [], []
        for p in pots:
            draws = by_pot.get(p)
            if not draws:
                cells.append(f"{'-':>{cw}s}")
                continue
            vals = [x.turn_deg for x in draws]
            pooled += vals
            cells.append(f"{median(vals):{cw - 1}.1f}d")
        print(f"{scale:12.3f}  {band:>5s}  " + "  ".join(cells) +
              f"  {median(pooled):{cw - 1}.1f}d")

    print()
    for scale, name, _ in rungs:
        print(f"  {scale:10.3f}  {name}")

    best = min(rungs, key=lambda t: median(
        [x.turn_deg for bp in [t[2]] for ds in bp.values() for x in ds]))
    worst = max(rungs, key=lambda t: median(
        [x.turn_deg for bp in [t[2]] for ds in bp.values() for x in ds]))
    print(f"\nBest rung: scale {best[0]:.3f}.  Worst rung: scale {worst[0]:.3f}.")
    print("If those two are far apart and the trend is monotone, the storage")
    print("units were doing the damage. If every rung is within a few degrees")
    print("of the others, they were not, and this line of enquiry is closed.\n")

    for line in format_flags(all_records):
        print(f"!! {line}")
    print(f"Weight: {weight(all_records)}.")

    print("\nA degree figure is an index to a picture, not a substitute for")
    print("one. Draw the two ends of the ladder and look at whether the pots")
    print("differ the way the numbers say they do:\n")
    for label, rung in (("best", best), ("worst", worst)):
        print(f"  # {label} rung, scale {rung[0]:.3f}")
        print(f"  python scripts/render_assembly_grid.py \\")
        print(f'      --runs "{rung[1]}=eval_runs/{rung[1]}/clouds" \\')
        print(f"      --out artifacts/{rung[1]}.png")
    print()


if __name__ == "__main__":
    main()
