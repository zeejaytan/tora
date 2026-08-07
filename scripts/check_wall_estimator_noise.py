"""How much of the wall-thickness change is real, and how much is the ruler?

The all-object run produced a table with an impossible entry. Wear removes
material; it cannot make a wall THICKER. Yet:

    bones__vert7   3.54% -> 7.37%   +42.9%
    bones__limb4   1.82% -> 2.59%   +42.1%
    bones__vert5   5.37% -> 7.45%   +38.8%

Thirteen of twenty-seven objects came out thicker after wear. Either the wear
model is doing something even stranger than crushing shells, or the estimator
has a noise floor wide enough to swallow most of the table.

Until that is known, none of those 27 verdicts can be used -- including the
ones that agree with the story I already believe. A metric that produces
physically impossible values is not partially trustworthy.

The estimator samples the surface at random and, for each sample, finds the
nearest sample whose normal faces the opposite way. Two independent sources of
scatter: which points get sampled, and whether a genuine across-the-wall partner
is among the 64 neighbours searched.

This measures that scatter directly. Same mesh, untouched, many seeds. The
spread across seeds IS the noise floor, and any wear-induced change smaller than
it means nothing.

Usage:
  python scripts/check_wall_estimator_noise.py --seeds 12
"""

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from probe_wall_pinch import wall_thickness_frac  # noqa: E402
from wear_ops import _band_mask  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", default="/data/gpfs/projects/punim2657/TORA/dataset/real_finetune.hdf5")
    ap.add_argument("--dataset", default="real_finetune")
    ap.add_argument("--objects",
                    default="egg__egg1,bones__vert7,bones__limb4,ceramics__blue_pot,"
                            "ceramics__narrow_bottle3,bones__limb6")
    ap.add_argument("--seeds", type=int, default=12)
    ap.add_argument("--n-pts", type=int, default=6000)
    args = ap.parse_args()

    print("Noise floor of the wall-thickness estimator.")
    print(f"  Same UNTOUCHED mesh, {args.seeds} different random samplings.")
    print("  Any wear-induced change smaller than this spread means nothing.")
    print()
    print(f"  {'object':<26s} {'median':>8s} {'min':>8s} {'max':>8s} "
          f"{'spread':>9s} {'sd':>7s}")

    worst = 0.0
    with h5py.File(args.src, "r") as h:
        ds = h[args.dataset]
        for obj in [o.strip() for o in args.objects.split(",") if o.strip()]:
            if obj not in ds:
                print(f"  {obj}: not present")
                continue
            grp = ds[obj]
            g = grp["pieces"] if "pieces" in grp else grp
            keys = sorted(g.keys(), key=lambda s: int(s) if s.isdigit() else s)
            pieces = [(np.asarray(g[k]["vertices"][:], dtype=np.float64),
                       np.asarray(g[k]["faces"][:], dtype=np.int64)) for k in keys]

            idx = int(np.argmax([len(v) for v, _ in pieces]))
            vf, ff = pieces[idx]
            band, _ = _band_mask(pieces, idx, vf)
            restrict = vf[band] if band.any() else None

            vals = np.array([
                wall_thickness_frac(vf, ff, restrict=restrict,
                                    n_pts=args.n_pts, seed=s)
                for s in range(args.seeds)])
            vals = vals[np.isfinite(vals)]
            if len(vals) < 3:
                print(f"  {obj}: estimator failed on most seeds")
                continue

            med = float(np.median(vals))
            lo, hi = float(vals.min()), float(vals.max())
            spread = 100.0 * (hi - lo) / med if med > 0 else float("nan")
            sd = 100.0 * float(vals.std()) / med if med > 0 else float("nan")
            worst = max(worst, spread)
            print(f"  {obj:<26s} {med * 100:>7.2f}% {lo * 100:>7.2f}% "
                  f"{hi * 100:>7.2f}% {spread:>8.1f}% {sd:>6.1f}%", flush=True)

    print()
    print(f"  worst spread on an untouched mesh: {worst:.1f}%")
    print()
    print("  Compare against the changes reported for wear:")
    print("    egg1 -37%, egg2 -33%, egg3 -28%, narrow_bottle2 -55%,")
    print("    narrow_bottle3 -57%   <- the crushing claim rests on these")
    print("    vert7 +43%, limb4 +42%, vert5 +39%   <- physically impossible")
    print()
    print("  If the noise floor is comparable to the impossible values, then the")
    print("  thinning results survive only where they clear it by a wide margin,")
    print("  and the per-object table cannot be used to decide which variants to")
    print("  keep. A better instrument would be needed for that.")


if __name__ == "__main__":
    main()
