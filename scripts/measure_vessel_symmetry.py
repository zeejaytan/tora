"""Is the Juglet a shape the model has never seen? Measure axial symmetry.

The conservator's hypothesis, 2026-08-18: the Juglet is not a surface of
revolution -- it has ONE handle -- and that asymmetry may be what is holding the
model back, because everything it trains on may be symmetric.

Worth testing rather than assuming, and cheap. A wheel-made vessel without
attachments is a surface of revolution: rotate it about its axis and it maps
onto itself. A handle breaks that. So the measurement is direct -- spin the
object about its own principal axis and ask how far the surface moves.

  symmetry error   after rotating by an angle, how far each point sits from the
                   nearest point of the unrotated object, as a percentage of
                   object size, averaged over many angles. Near zero means a
                   surface of revolution. Large means something sticks out.

  handle mass      the fraction of surface that lies well outside the median
                   radius at its height -- an attachment rather than the wall.

If the training objects are all near zero and the Juglet is not, the conservator
is right and the model has never been shown the kind of object it is being asked
to solve. If several training objects are also asymmetric, the hypothesis does
not hold and the difficulty lies elsewhere.

Usage:
  python scripts/measure_vessel_symmetry.py \
      --sets train=dataset/real_finetune.hdf5:real_finetune \
             juglet=dataset/juglet_gt.hdf5:juglet_gt
"""

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))

ANGLES = [30, 60, 90, 120, 150, 180]


def load_objects(spec):
    parts = spec.split(":")
    path, dsname = parts[0], parts[1]
    out = {}
    with h5py.File(path, "r") as h:
        ds = h[dsname]
        for obj in sorted(ds.keys()):
            grp = ds[obj]
            g = grp["pieces"] if "pieces" in grp else grp
            keys = sorted(g.keys(), key=lambda s: int(s) if s.isdigit() else s)
            v = [np.asarray(g[k]["vertices"][:], dtype=np.float64) for k in keys]
            if v:
                out[obj] = np.concatenate(v, axis=0)
    return out


def axis_of(pts):
    """The vessel's own axis, from the spread of its surface."""
    c = pts.mean(axis=0)
    P = pts - c
    u = np.linalg.svd(P.T @ P)[0]
    return c, u[:, 0]


def rotate_about(pts, centre, axis, deg):
    a = np.deg2rad(deg)
    k = axis / (np.linalg.norm(axis) + 1e-12)
    P = pts - centre
    return (centre + P * np.cos(a) + np.cross(k, P) * np.sin(a)
            + np.outer(P @ k, k) * (1 - np.cos(a)))


def measure(pts, max_pts=40000, seed=0):
    rng = np.random.default_rng(seed)
    q = pts if len(pts) <= max_pts else pts[rng.choice(len(pts), max_pts, False)]
    size = float(np.linalg.norm(q.max(0) - q.min(0)))
    c, ax = axis_of(q)
    tree = cKDTree(q)

    errs = []
    for d in ANGLES:
        r = rotate_about(q, c, ax, d)
        dist, _ = tree.query(r, workers=-1)
        errs.append(float(dist.mean()) / size * 100)

    # how much surface sits outside the wall at its own height
    P = q - c
    z = P @ ax
    e1 = np.cross(ax, [0.0, 0.0, 1.0])
    if np.linalg.norm(e1) < 1e-6:
        e1 = np.cross(ax, [0.0, 1.0, 0.0])
    e1 = e1 / np.linalg.norm(e1)
    e2 = np.cross(ax, e1)
    rad = np.hypot(P @ e1, P @ e2)
    nb = 24
    bins = np.clip(((z - z.min()) / (np.ptp(z) + 1e-12) * nb).astype(int), 0, nb - 1)
    med = np.array([np.median(rad[bins == i]) if (bins == i).any() else 0.0
                    for i in range(nb)])
    outside = float((rad > 1.45 * med[bins]).mean()) * 100
    return float(np.mean(errs)), float(np.max(errs)), outside


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sets", nargs="+", required=True)
    args = ap.parse_args()

    print("Spin each object about its own axis and see how far the surface moves.")
    print("A surface of revolution barely moves. A handle makes it move a lot.\n")
    print("  {:<12s} {:<28s} {:>12s} {:>12s} {:>14s}".format(
        "set", "object", "mean move", "worst move", "outside wall"))
    print("  " + "-" * 82)

    rows = []
    for spec in args.sets:
        label, rest = spec.split("=", 1)
        for obj, pts in load_objects(rest).items():
            m, w, o = measure(pts)
            rows.append((label, obj, m, w, o))
            print("  {:<12s} {:<28s} {:>11.2f}% {:>11.2f}% {:>13.1f}%".format(
                label, obj[:27], m, w, o))

    print("\n  mean move  = average distance the surface travels when spun,")
    print("               as a percentage of object size. Near zero means the")
    print("               object is a surface of revolution.")
    print("  outside wall = share of surface sitting well outside the median")
    print("               radius at its own height -- a handle or spout.")

    for label in dict.fromkeys(r[0] for r in rows):
        v = [r for r in rows if r[0] == label]
        print("\n  {}: {} objects, mean move {:.2f}%, outside wall {:.1f}%".format(
            label, len(v), np.mean([x[2] for x in v]),
            np.mean([x[4] for x in v])))


if __name__ == "__main__":
    main()
