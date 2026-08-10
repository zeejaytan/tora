"""How much of the pot is actually missing?

Once the conservator's hand reassembly exists, this stops being a guess. The
training distribution currently loses a median of 8.5% of an object when
anything is lost at all, and that figure was invented rather than measured — it
needs checking against the pot it was meant to represent.

Method, and why this one: a wheel-made vessel is close to a surface of
revolution, so every height around the pot should have material at every angle.
Standing the assembled sherds on their axis and asking, at each height, what
fraction of the circumference survives, gives a direct answer with a physical
meaning — "the pot is missing a band spanning N degrees over M% of its height"
— rather than a number that only exists inside a metric.

The surviving surface is measured, not the volume. For a vessel of roughly even
wall thickness the two agree closely, and surface can be measured from the
sherds alone while volume would need a model of the complete pot.

Three things this cannot do, stated because they bound the answer:

  * A handle is not a surface of revolution. It is detected and excluded from
    the body measurement, and reported separately, otherwise it reads as extra
    material at angles where the wall is thin.
  * Losses at the rim or base are indistinguishable from the vessel simply
    ending. Only gaps with surviving material ABOVE and BELOW are counted, so
    the result is a floor: a missing rim section would not be counted.
  * Axial symmetry is an assumption. It is checked by measuring how much the
    surviving radius varies at each height, and reported.

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

sys.path.insert(0, str(Path(__file__).resolve().parent))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", required=True)
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--object", default="")
    ap.add_argument("--n-height", type=int, default=40)
    ap.add_argument("--n-angle", type=int, default=72)   # 5-degree cells
    ap.add_argument("--samples", type=int, default=400000)
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

    per = max(2000, args.samples // len(meshes))
    pts = np.concatenate([trimesh.sample.sample_surface(m, per, seed=0)[0]
                          for m in meshes], axis=0)

    # stand the pot on its axis: the long principal direction of the body
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
    th = np.arctan2(y, x)

    # A handle sticks out well beyond the wall at its own height. Flag points
    # whose radius is far above the median for their height and set them aside.
    hb = np.clip(((z - z.min()) / (z.ptp() + 1e-12) * args.n_height).astype(int),
                 0, args.n_height - 1)
    med_r = np.array([np.median(r[hb == i]) if (hb == i).any() else 0.0
                      for i in range(args.n_height)])
    handle = r > 1.45 * med_r[hb]
    print(f"  set aside as handle/protrusion: {100 * handle.mean():.1f}% of surface")

    body = ~handle
    ab = np.clip(((th[body] + np.pi) / (2 * np.pi) * args.n_angle).astype(int),
                 0, args.n_angle - 1)
    occ = np.zeros((args.n_height, args.n_angle), bool)
    occ[hb[body], ab] = True

    # Only count a gap where material survives above AND below, so the vessel
    # simply ending at rim or base is not read as loss.
    rows = np.where(occ.any(axis=1))[0]
    if len(rows) < 3:
        print("  not enough of the pot to measure")
        return
    lo, hi = rows.min() + 1, rows.max() - 1

    circ = med_r * 2 * np.pi                      # circumference at each height
    tot = miss = 0.0
    per_row = []
    for i in range(lo, hi + 1):
        if not occ[i].any():
            continue
        w = circ[i] / args.n_angle                # arc length of one cell
        present = int(occ[i].sum())
        tot += args.n_angle * w
        miss += (args.n_angle - present) * w
        per_row.append((i, 100.0 * (args.n_angle - present) / args.n_angle))

    print(f"\n  surviving surface measured between {100 * lo / args.n_height:.0f}% "
          f"and {100 * hi / args.n_height:.0f}% of the pot's height")
    print(f"  MISSING: {100 * miss / max(tot, 1e-12):.1f}% of the vessel wall")

    worst = sorted(per_row, key=lambda t: -t[1])[:5]
    print("\n  where the gap is (height from base -> % of that ring missing):")
    for i, pct in worst:
        print(f"    {100 * i / args.n_height:>4.0f}% height   {pct:5.1f}% missing")

    var = np.array([np.std(r[(hb == i) & body]) / max(np.median(r[(hb == i) & body]), 1e-9)
                    for i in range(lo, hi + 1) if ((hb == i) & body).any()])
    print(f"\n  axial-symmetry check: radius varies by {100 * np.mean(var):.1f}% "
          f"around each ring")
    print("  (small = the assumption holds; large = treat the figure as rough)")
    print("\n  This is a FLOOR. Loss at the rim or base cannot be told apart from")
    print("  the vessel ending, so it is not counted.")


if __name__ == "__main__":
    main()
