"""How much of the pot is missing, and where?

Once the conservator's hand reassembly exists this stops being a guess. The
training distribution loses a median 8.5% of an object when anything is lost,
and that figure was invented rather than measured.

TWO FAULTS IN THE FIRST VERSION, both caught by the conservator reading the
output against the actual pot ("top? you mean the rim? there is only one gap in
the body near middle"):

  1. It did not know which end was which. The axis comes from an SVD, whose
     sign is arbitrary, so "95% of the height" was as likely to be the base as
     the rim. The report was confidently upside down. The base is now
     identified by whether material reaches the axis -- a base is closed, a rim
     is an opening -- and the labels follow from that.

  2. It fabricated gaps at the narrow ends. Occupancy was tested by binning
     into cells and calling an empty cell missing. Near the neck the
     circumference is small, so cells are tiny, and ordinary sampling sparsity
     leaves them empty. That produced "60% of the ring missing" at the very
     ends, which is a sampling artifact, not a hole. Occupancy is now tested by
     DISTANCE to the nearest real surface point, which does not care how
     densely a region happened to be sampled.

Method: a wheel-made vessel is close to a surface of revolution, so every
height should carry material at every angle. Standing the sherds on their axis
and asking what fraction of each ring survives gives an answer with physical
meaning -- a gap of N degrees at a stated height -- rather than a number that
only exists inside a metric.

Bounds on the answer, unchanged:
  * A handle is not a surface of revolution; it is detected and set aside.
  * Loss at the rim or base cannot be told from the vessel ending, so it is not
    counted and the figure is a floor.
  * Axial symmetry is assumed, and checked by reporting how much the surviving
    radius varies around each ring.

Usage:
  python scripts/measure_missing_fraction.py --src dataset/juglet_gt.hdf5 \
      --dataset juglet_gt
"""

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np
import trimesh
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", required=True)
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--object", default="")
    ap.add_argument("--n-height", type=int, default=32)
    ap.add_argument("--n-angle", type=int, default=48)
    ap.add_argument("--samples", type=int, default=600000)
    ap.add_argument("--tol-frac", type=float, default=0.035,
                    help="a ring position counts as PRESENT if real surface lies "
                         "within this fraction of the object size")
    args = ap.parse_args()

    with h5py.File(args.src, "r") as h:
        ds = h[args.dataset]
        obj = args.object or sorted(ds.keys())[0]
        grp = ds[obj]
        g = grp["pieces"] if "pieces" in grp else grp
        keys = sorted(g.keys(), key=lambda s: int(s) if s.isdigit() else s)
        meshes = [trimesh.Trimesh(
            vertices=np.asarray(g[k]["vertices"][:], dtype=np.float64),
            faces=np.asarray(g[k]["faces"][:], dtype=np.int64), process=False)
            for k in keys]
    print(f"{obj}: {len(meshes)} sherds, assembled")

    per = max(4000, args.samples // len(meshes))
    pts = np.concatenate([trimesh.sample.sample_surface(m, per, seed=0)[0]
                          for m in meshes], axis=0)
    size = float(np.linalg.norm(pts.max(0) - pts.min(0)))

    c = pts.mean(axis=0)
    P = pts - c
    axis = np.linalg.svd(P.T @ P)[0][:, 0]
    z = P @ axis
    e1 = np.cross(axis, [0.0, 0.0, 1.0])
    if np.linalg.norm(e1) < 1e-6:
        e1 = np.cross(axis, [0.0, 1.0, 0.0])
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(axis, e1)
    x, y = P @ e1, P @ e2
    r = np.hypot(x, y)

    # WHICH END IS THE BASE? A base is closed, so material reaches in toward the
    # axis; a rim is an opening, so the surface stays out at the wall. Compare
    # the smallest radius found in the outer tenth at each end.
    zl, zh = z.min(), z.max()
    span = zh - zl
    low = r[z < zl + 0.10 * span]
    high = r[z > zh - 0.10 * span]
    inner_low = float(np.percentile(low, 5)) if len(low) else np.inf
    inner_high = float(np.percentile(high, 5)) if len(high) else np.inf
    if inner_low > inner_high:            # the closed end is the base
        z = -z
        zl, zh = z.min(), z.max()
        inner_low, inner_high = inner_high, inner_low
    print(f"  base identified as the closed end (material reaches to "
          f"{inner_low / size * 100:.1f}% of object size from the axis; "
          f"the open end stops at {inner_high / size * 100:.1f}%)")

    hb = np.clip(((z - zl) / (span + 1e-12) * args.n_height).astype(int),
                 0, args.n_height - 1)
    med_r = np.array([np.median(r[hb == i]) if (hb == i).any() else 0.0
                      for i in range(args.n_height)])
    handle = r > 1.45 * med_r[hb]
    print(f"  set aside as handle/protrusion: {100 * handle.mean():.1f}% of surface")

    body = pts[~handle]
    tree = cKDTree(body)
    tol = args.tol_frac * size

    rows = np.where(np.array([(hb == i).sum() for i in range(args.n_height)]) > 0)[0]
    lo, hi = rows.min() + 1, rows.max() - 1

    tot = miss = 0.0
    per_row = []
    for i in range(lo, hi + 1):
        if med_r[i] <= 0:
            continue
        zc = zl + (i + 0.5) / args.n_height * span
        ang = (np.arange(args.n_angle) + 0.5) / args.n_angle * 2 * np.pi
        probe = (c + np.outer(np.full(args.n_angle, zc), axis)
                 + np.outer(med_r[i] * np.cos(ang), e1)
                 + np.outer(med_r[i] * np.sin(ang), e2))
        d, _ = tree.query(probe)
        present = int((d < tol).sum())
        w = med_r[i] * 2 * np.pi / args.n_angle
        tot += args.n_angle * w
        miss += (args.n_angle - present) * w
        per_row.append((i, 100.0 * (args.n_angle - present) / args.n_angle))

    print(f"\n  measured between {100 * lo / args.n_height:.0f}% and "
          f"{100 * hi / args.n_height:.0f}% of the height, base = 0%")
    print(f"  MISSING: {100 * miss / max(tot, 1e-12):.1f}% of the vessel wall")

    print("\n  gap by height (base = 0%, rim = 100%):")
    for i, pct in per_row:
        bar = "#" * int(round(pct / 4))
        if pct > 0.5:
            print(f"    {100 * i / args.n_height:>4.0f}%  {pct:5.1f}%  {bar}")

    var = [np.std(r[(hb == i) & ~handle]) / max(np.median(r[(hb == i) & ~handle]), 1e-9)
           for i in range(lo, hi + 1) if ((hb == i) & ~handle).any()]
    print(f"\n  axial-symmetry check: radius varies {100 * np.mean(var):.1f}% "
          f"around each ring (large = treat the figure as rough)")
    print("  Loss at the rim or base cannot be told from the vessel ending, so")
    print("  this is a FLOOR.")


if __name__ == "__main__":
    main()
