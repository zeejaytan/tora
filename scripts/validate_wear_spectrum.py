"""Does our wear blunt the teeth and preserve the curve? Pass or fail.

The conservator's statement of what wear does, made after reassembling a real
worn pot by hand (2026-08-10):

    besides the teeth that lock into each other for a fresh break, there is also
    the CURVE of the fractured surface. Wear blunts the teeth and preserves the
    curve.

That is a testable claim about geometry, and this is the test. It is the only
comparison in this area that is trustworthy, because everything is measured on
ONE object before and after. The obvious version -- compare our simulated wear
against the real worn Juglet -- was run first and had to be discarded: the
Juglet's mesh spacing is 0.535% of object size against blue_pot's 0.141%, so the
two finest probes sat below the Juglet's own vertex spacing and the comparison
was reading mesh resolution, not wear. Same confound as the earlier mesh-density
finding. Within one mesh there is nothing to confound.

WHAT IT MEASURES. The break face is smoothed at a series of radii, and the
deviation removed at each radius is the amount of structure living at that
scale. Small radii = teeth, large radii = curve. A single roughness number
cannot distinguish them, which is how the previous wear model passed validation
for months while eroding the curve.

THE CRITERION, and it is deliberately strict:

  teeth   fine-scale structure (0.4%, 0.8%) must FALL as wear increases,
          monotonically. Not merely end lower.
  curve   coarse-scale structure (3.2%, 6.4%) must stay within tolerance of
          fresh. The previous model lost 14% here and that is the failure this
          exists to catch.
  gap     the joins must OPEN. Wear removes material, so fragments that used to
          meet must stop meeting. A model that smooths without opening the join
          is not modelling loss.

CHIPS ARE MEASURED SEPARATELY, with --no-chips, and this matters. A chip of
radius r is a feature of size r, so chips at the sizes the conservator validated
as common (0.22-0.45% of object) necessarily add structure in the teeth band.
That is not a bug and it is not something to tune away -- a chipped sherd really
does carry small scars. But it means abrasion and chipping must be judged apart,
or the chips mask whether the abrasion term itself is correct.

Usage:
  python scripts/validate_wear_spectrum.py \
      --src dataset/real_heldout_norm.hdf5 --dataset real_heldout_norm \
      --object ceramics__blue_pot
  python scripts/validate_wear_spectrum.py ... --no-chips     # abrasion alone
  python scripts/validate_wear_spectrum.py ... --mode legacy  # the old model
"""

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wear_ops import _local_mean, apply_wear  # noqa: E402

RADII = [0.004, 0.008, 0.016, 0.032, 0.064]
TEETH = [0, 1]          # indices into RADII treated as the interlock scale
CURVE = [3, 4]          # ... and as the curve

# Severity rides on the CUTOFF as much as on the dose: heavier wear blunts
# larger asperities, rather than cutting the same small ones deeper. That is
# this module's framing of wear as loss moving up the scales, and it is also
# what keeps the operation bounded -- at strength 1.0 the face lands on its own
# envelope and stops, instead of carving past it.
LEVELS = [
    ("light",    dict(smoothing=0.5, smoothing_passes=2, blunt_cut=0.003,
                      recession=0.0006, chip_count=2, chip_size=0.0022)),
    ("moderate", dict(smoothing=0.8, smoothing_passes=2, blunt_cut=0.004,
                      recession=0.0012, chip_count=3, chip_size=0.0045)),
    ("heavy",    dict(smoothing=1.0, smoothing_passes=3, blunt_cut=0.005,
                      recession=0.0020, chip_count=4, chip_size=0.0090)),
]


def load(path, dsname, want=""):
    with h5py.File(path, "r") as h:
        ds = h[dsname]
        obj = want or sorted(ds.keys())[0]
        grp = ds[obj]
        g = grp["pieces"] if "pieces" in grp else grp
        keys = sorted(g.keys(), key=lambda s: int(s) if s.isdigit() else s)
        return obj, [(np.asarray(g[k]["vertices"][:], dtype=np.float64),
                      np.asarray(g[k]["faces"][:], dtype=np.int64)) for k in keys]


def scale_spectrum(pts, size):
    """Structure remaining at each scale, as a percentage of object size.

    The smoothed surface comes from `wear_ops._local_mean`, which bounds how
    many points a ball may hold. That matters here as much as in the wear model
    itself: at the 6.4% radius on a densely scanned pot an unbounded query
    materialises tens of millions of indices, and the earlier per-point Python
    loop did not finish in two minutes on a 24k-vertex toy.
    """
    out = []
    for rf in RADII:
        sm = _local_mean(pts, pts.copy(), rf * size)
        moved = np.linalg.norm(pts - sm, axis=1)
        out.append(float(moved.mean()) / size * 100 if len(moved) >= 50
                   else float("nan"))
    return out


def measure(pieces, band_frac=0.02, max_pts=40000, seed=0):
    """Break-face spectrum and mean join gap, averaged over touching pairs."""
    allv = np.concatenate([v for v, _ in pieces], axis=0)
    size = float(np.linalg.norm(allv.max(0) - allv.min(0)))
    rng = np.random.default_rng(seed)
    tau = band_frac * size

    spectra, gaps = [], []
    for i, (vi, _) in enumerate(pieces):
        for j, (vj, _) in enumerate(pieces):
            if j <= i:
                continue
            a = vi if len(vi) <= max_pts else vi[rng.choice(len(vi), max_pts, False)]
            b = vj if len(vj) <= max_pts else vj[rng.choice(len(vj), max_pts, False)]
            d, _ = cKDTree(b).query(a, workers=-1)
            band = a[d < tau]
            if len(band) < 300:
                continue
            spectra.append(scale_spectrum(band, size))
            gaps.append(float(d[d < tau].mean()) / size * 100)
    if not spectra:
        return None, None, 0
    return (np.nanmean(np.array(spectra), axis=0), float(np.mean(gaps)),
            len(spectra))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", required=True)
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--object", default="")
    ap.add_argument("--mode", default="blunt", choices=["blunt", "legacy"])
    ap.add_argument("--blunt-cut", type=float, default=0.0)  # 0 = per-level
    ap.add_argument("--scan-spacing", type=float, default=0.0,
                    help="blur to a scanner's resolution first, as a fraction "
                         "of object size (0.00535 = the Juglet's own spacing)")
    ap.add_argument("--no-chips", action="store_true",
                    help="abrasion only, so chip scars cannot mask whether the "
                         "abrasion term itself is correct")
    ap.add_argument("--curve-tol", type=float, default=4.0,
                    help="percent of fresh the curve may drift before failing")
    args = ap.parse_args()

    obj, pieces = load(args.src, args.dataset, args.object)
    print(f"{obj}: {len(pieces)} fragments, mode={args.mode}"
          + (", chips off" if args.no_chips else "")
          + (f", scan blur {100 * args.scan_spacing:.3f}%"
             if args.scan_spacing else ""))
    print("Structure on the break face at each scale (% of object size).")
    print("Teeth on the left, curve on the right.\n")
    print(f"  {'level':<10s} " + "  ".join(f"{100 * r:5.1f}%" for r in RADII)
          + "     gap   pairs")
    print("  " + "-" * 62)

    kw0 = dict(mode=args.mode, scan_spacing=args.scan_spacing)
    fresh = (apply_wear(pieces, smoothing=0.0, recession=0.0, chip_count=0,
                        chip_size=0.0, **kw0)
             if args.scan_spacing else pieces)
    s0, g0, n0 = measure(fresh)
    if s0 is None:
        print("  no touching pairs -- cannot measure this object")
        return
    print(f"  {'fresh':<10s} " + "  ".join(f"{v:6.3f}" for v in s0)
          + f"   {g0:5.3f}%   {n0}")

    rows = []
    for name, kw in LEVELS:
        kw = dict(kw)
        if args.blunt_cut > 0:
            kw["blunt_cut"] = args.blunt_cut       # override the whole sweep
        if args.no_chips:
            kw["chip_count"], kw["chip_size"] = 0, 0.0
        s, g, n = measure(apply_wear(pieces, seed=0, **kw, **kw0))
        rows.append((name, s, g))
        print(f"  {name:<10s} " + "  ".join(f"{v:6.3f}" for v in s)
              + f"   {g:5.3f}%   {n}")

    # ---- the verdict -----------------------------------------------------
    print("\n  Verdict, against what the conservator says wear does:")
    ok = True

    for k in TEETH:
        seq = [s0[k]] + [r[1][k] for r in rows]
        mono = all(b <= a * 1.001 for a, b in zip(seq, seq[1:]))
        drop = 100 * (1 - seq[-1] / max(seq[0], 1e-12))
        ok &= mono
        print(f"    teeth at {100 * RADII[k]:.1f}%: "
              f"{'BLUNTED' if mono else 'NOT BLUNTED'} "
              f"({seq[0]:.3f} -> {seq[-1]:.3f}, {drop:+.1f}%)"
              + ("" if mono else "   ** rises somewhere in the sweep **"))

    for k in CURVE:
        drift = 100 * (rows[-1][1][k] / max(s0[k], 1e-12) - 1)
        good = abs(drift) <= args.curve_tol
        ok &= good
        print(f"    curve at {100 * RADII[k]:.1f}%: "
              f"{'PRESERVED' if good else 'DAMAGED'} "
              f"({s0[k]:.3f} -> {rows[-1][1][k]:.3f}, {drift:+.1f}%)"
              + ("" if good else f"   ** beyond {args.curve_tol:.0f}% tolerance **"))

    gseq = [g0] + [r[2] for r in rows]
    gmono = all(b >= a * 0.999 for a, b in zip(gseq, gseq[1:]))
    ok &= gmono
    print(f"    join gap: {'OPENS' if gmono else 'DOES NOT OPEN'} "
          f"({g0:.3f}% -> {gseq[-1]:.3f}%)")

    print(f"\n  {'PASS' if ok else 'FAIL'} -- "
          + ("teeth blunted, curve preserved, joins opened."
             if ok else "this wear model does not behave like wear."))
    print("  One object. Run it on several before treating a pass as general;")
    print("  the failure it is built to catch was visible on every object, but")
    print("  a pass on one proves only that one.")
    if not args.no_chips:
        print("  Chips are included here, and a chip of radius r IS a feature of")
        print("  size r -- rerun with --no-chips to judge the abrasion term alone.")


if __name__ == "__main__":
    main()
