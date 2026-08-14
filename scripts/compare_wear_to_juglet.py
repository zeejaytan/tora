"""Does our simulated wear look like the real thing? Judged against the Juglet.

The point of the wear model is to generate training data, so the question that
decides whether it is fit for use is not whether it obeys a physical rule -- it
does, that is established -- but whether a sherd we wear resembles a sherd the
ground wore. The Juglet is the only real worn pot here with a valid assembly,
the conservator's own hand reassembly, so it is the only thing to check against.

WHY THIS WAS NOT DONE EARLIER, and what changed. The first attempt compared the
Juglet directly against blue_pot and had to be thrown away: the Juglet's break
faces are sampled at 0.535% of object size against blue_pot's 0.141%, four
times coarser, so the fine probes were reading mesh resolution rather than
geometry. Two fixes make it answerable:

  1. The point clouds are thinned to a COMMON spacing before measuring, and
     only radii at least twice that spacing are reported. Both objects are then
     measured by the same ruler.

  2. A dimensionless ratio is reported alongside the raw figures: fine relief
     divided by coarse relief. Absolute roughness differs between pots for
     reasons that have nothing to do with wear -- fabric, forming, firing --
     but the BALANCE between fine texture and the overall shape of the face is
     what wear changes, and it can be compared across objects. Wear should
     lower it: teeth go, curve stays.

Relief is the normal deviation from the local mean, never the full distance --
the sideways component is two to three times larger at fine scales on these
meshes and no wear can remove it.

WHAT WOULD COUNT AS A PASS. The real worn Juglet should sit at a LOWER
fine-to-coarse ratio than a fresh break, and one of our wear levels should land
near it. If our heaviest wear cannot reach the Juglet's ratio, the model is too
gentle for this material and the dataset would not contain the case we care
about. If fresh already sits at the Juglet's ratio, the Juglet is not
distinguishable from a fresh break by this measure and the comparison says
nothing either way.

Usage:
  python scripts/compare_wear_to_juglet.py \
      --gt dataset/juglet_gt.hdf5:juglet_gt \
      --sim dataset/real_heldout_norm.hdf5:real_heldout_norm:blue_pot
"""

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wear_ops import _local_mean, apply_wear  # noqa: E402

# radii as fractions of object size. The fine end is set by what the Juglet's
# own sampling can carry, not by what we would like to measure.
RADII = [0.012, 0.016, 0.024, 0.032, 0.048, 0.064, 0.096]
FINE, COARSE = 0.016, 0.064

LEVELS = [
    ("light",    dict(smoothing=0.5, smoothing_passes=2, blunt_cut=0.003,
                      recession=0.0, chip_count=2, chip_size=0.0022)),
    ("moderate", dict(smoothing=0.8, smoothing_passes=2, blunt_cut=0.004,
                      recession=0.0, chip_count=3, chip_size=0.0045)),
    ("heavy",    dict(smoothing=1.0, smoothing_passes=3, blunt_cut=0.005,
                      recession=0.0, chip_count=4, chip_size=0.0090)),
    ("very heavy", dict(smoothing=1.0, smoothing_passes=3, blunt_cut=0.008,
                        recession=0.0, chip_count=5, chip_size=0.0180)),
]


def load(spec):
    parts = spec.split(":")
    path, dsname = parts[0], parts[1]
    want = parts[2] if len(parts) > 2 else ""
    with h5py.File(path, "r") as h:
        ds = h[dsname]
        obj = want or sorted(ds.keys())[0]
        grp = ds[obj]
        g = grp["pieces"] if "pieces" in grp else grp
        keys = sorted(g.keys(), key=lambda s: int(s) if s.isdigit() else s)
        return obj, [(np.asarray(g[k]["vertices"][:], dtype=np.float64),
                      np.asarray(g[k]["faces"][:], dtype=np.int64)) for k in keys]


def spacing_of(pts):
    d, _ = cKDTree(pts).query(pts, k=2, workers=-1)
    return float(np.median(d[:, 1]))


def thin_to(pts, target, rng):
    """Randomly thin a cloud until its median spacing is about `target`.

    Spacing on a surface goes as 1/sqrt(N), so the count needed is exact enough
    to hit the target in one step. Thinning is the honest direction: the finer
    cloud can be made to look like the coarser one, never the reverse.
    """
    cur = spacing_of(pts)
    if cur >= target * 0.98 or len(pts) < 500:
        return pts, cur
    n = max(400, int(len(pts) * (cur / target) ** 2))
    if n >= len(pts):
        return pts, cur
    keep = rng.choice(len(pts), n, replace=False)
    return pts[keep], spacing_of(pts[keep])


def normals(pts, k=24):
    _, nb = cKDTree(pts).query(pts, k=min(k, len(pts)), workers=-1)
    P = pts[nb] - pts[:, None, :]
    return np.linalg.eigh(np.einsum("nki,nkj->nij", P, P))[1][:, :, 0]


def faces_of(pieces, size, band_frac=0.02, max_pts=250000, seed=0):
    """Break-face point clouds, one per touching pair."""
    rng = np.random.default_rng(seed)
    out = []
    for i, (vi, _) in enumerate(pieces):
        for j, (vj, _) in enumerate(pieces):
            if j <= i:
                continue
            a = vi if len(vi) <= max_pts else vi[rng.choice(len(vi), max_pts, False)]
            b = vj if len(vj) <= max_pts else vj[rng.choice(len(vj), max_pts, False)]
            d, _ = cKDTree(b).query(a, workers=-1)
            band = a[d < band_frac * size]
            if len(band) >= 400:
                out.append(band)
    return out


def spectrum(bands, size, target_spacing, rng):
    """Mean normal relief at each radius, on clouds thinned to a common spacing."""
    acc, sp = [], []
    for band in bands:
        pts, s = thin_to(band, target_spacing, rng)
        if len(pts) < 300:
            continue
        sp.append(s)
        nrm = normals(pts)
        row = []
        for rf in RADII:
            d = pts - _local_mean(pts, pts.copy(), rf * size)
            row.append(float(np.abs((d * nrm).sum(axis=1)).mean()) / size * 100)
        acc.append(row)
    if not acc:
        return None, float("nan")
    return np.mean(np.array(acc), axis=0), float(np.mean(sp)) / size * 100


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gt", required=True, help="the REAL worn pot")
    ap.add_argument("--sim", required=True, help="a fresh pot to wear")
    args = ap.parse_args()
    rng = np.random.default_rng(0)

    name_gt, gt = load(args.gt)
    allv = np.concatenate([v for v, _ in gt], axis=0)
    size_gt = float(np.linalg.norm(allv.max(0) - allv.min(0)))
    bands_gt = faces_of(gt, size_gt)

    name_s, sim = load(args.sim)
    allv = np.concatenate([v for v, _ in sim], axis=0)
    size_s = float(np.linalg.norm(allv.max(0) - allv.min(0)))

    # the common ruler: whichever object is sampled more coarsely sets it
    sp_gt = np.median([spacing_of(b) for b in bands_gt]) / size_gt
    bands_s0 = faces_of(sim, size_s)
    sp_s = np.median([spacing_of(b) for b in bands_s0]) / size_s
    target = max(sp_gt, sp_s)
    print(f"REAL worn pot: {name_gt}, {len(bands_gt)} break faces, "
          f"spacing {100 * sp_gt:.3f}% of object")
    print(f"simulated on:  {name_s}, {len(bands_s0)} break faces, "
          f"spacing {100 * sp_s:.3f}% of object")
    print(f"both thinned to {100 * target:.3f}% -> only radii above "
          f"{2 * 100 * target:.2f}% are readable\n")

    rows = []
    s, sp = spectrum(bands_gt, size_gt, target * size_gt, rng)
    rows.append((f"REAL worn ({name_gt})", s, sp))
    s, sp = spectrum(bands_s0, size_s, target * size_s, rng)
    rows.append((f"fresh ({name_s})", s, sp))
    for lname, kw in LEVELS:
        worn = apply_wear(sim, seed=0, **kw)
        s, sp = spectrum(faces_of(worn, size_s), size_s, target * size_s, rng)
        rows.append((f"  our {lname}", s, sp))

    print(f"  {'set':<24s} " + "".join(f"{100 * r:>8.1f}%" for r in RADII)
          + f"{'fine/coarse':>13s}")
    print("  " + "-" * (24 + 9 * len(RADII) + 13))
    fi, ci = RADII.index(FINE), RADII.index(COARSE)
    ratios = {}
    for name, s, sp in rows:
        if s is None:
            print(f"  {name:<24s}  no measurable break faces")
            continue
        r = s[fi] / max(s[ci], 1e-12)
        ratios[name.strip()] = r
        print(f"  {name:<24s} " + "".join(f"{v:>9.3f}" for v in s)
              + f"{r:>12.3f}")

    print(f"\n  fine/coarse = relief at {100 * FINE:.1f}% divided by relief at "
          f"{100 * COARSE:.1f}%.")
    print("  Wear should LOWER it: the teeth go, the curve stays. It is")
    print("  dimensionless, so it survives the two pots being different pots.")

    real = ratios.get(f"REAL worn ({name_gt})")
    fresh = ratios.get(f"fresh ({name_s})")
    if real is None or fresh is None:
        return
    print(f"\n  VERDICT")
    if real >= fresh:
        print(f"  The real worn pot ({real:.3f}) is NOT below a fresh break "
              f"({fresh:.3f}).")
        print("  This measure cannot tell them apart, so it cannot judge the")
        print("  simulation either. Nothing here supports or refutes the model.")
        return
    print(f"  Real worn {real:.3f} vs fresh {fresh:.3f} -- the real pot does sit")
    print(f"  lower, so the measure sees wear.")
    best, bestd = None, np.inf
    for lname, _ in LEVELS:
        v = ratios.get(f"our {lname}")
        if v is None:
            continue
        if abs(v - real) < bestd:
            best, bestd = lname, abs(v - real)
    span = [ratios.get(f"our {l}") for l, _ in LEVELS]
    span = [v for v in span if v is not None]
    print(f"  Closest of our levels: {best} "
          f"({ratios.get('our ' + best):.3f} against {real:.3f}).")
    if span and min(span) > real:
        print("  ** Our heaviest wear does not reach the real pot. The model is")
        print("     too gentle for this material and a dataset built from it")
        print("     would not contain the case the Juglet represents. **")
    else:
        print("  Our range brackets the real pot, so a dataset built across")
        print("  these levels contains material like it.")
    print("\n  One pot, one conservator's reassembly. It is the only real worn")
    print("  object here with a valid answer key, and it is still one object.")


if __name__ == "__main__":
    main()
