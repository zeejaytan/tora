"""Measure the Juglet's own fragments with the instrument used on bbad_vessels.

The conservator's correction, which this exists to check rather than accept:
Piece01 of the Juglet is a complete rim, one fragment wrapping the full 360
degrees. If that is so, a fragment that closes into a hoop is not a defect in
the training corpus -- it is a normal way for a vessel to come apart, and four
rounds of work spent trying to filter it out were aimed at the wrong target.

The Juglet is the real object, hand-fractured and hand-scanned. It outranks any
argument about what a break "should" look like, including mine.

Same instrument as check_band_coverage.py / show_ring_problem.py: wrap read off
1-degree occupancy around the object's axis of revolution, and each fragment
drawn ALONE from directly above against the whole object's footprint. Nothing
about the measurement is changed for this comparison -- the point is that both
sets go through the identical ruler.

THE GEOMETRY MUST BE ASSEMBLED. The first run of this pointed at the raw
Dataset/Juglet OBJs and reported Piece01 at exactly 360 degrees -- the answer
expected. The render showed why it was worthless: those OBJs hold the pieces
LAID OUT APART, centres running from z = -1 to z = -14.6, each piece barely 0.5
across. The axis of revolution was fitted to a scatter of separated blobs, so
every wrap was measured around a line that has nothing to do with the pot.

It agreed with the conclusion, which is exactly when a broken ruler survives.
Read from the assembled ground truth instead, and keep rendering the pieces
against the whole vessel so a scattered layout cannot pass again.

Usage:
  python scripts/measure_juglet_wrap.py \
      --hdf5 dataset/juglet_gt.hdf5 --key juglet_gt/Juglet-000 \
      --out artifacts/juglet_wrap.png
"""

import argparse
from pathlib import Path

import h5py
import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def load_obj_vertices(path):
    v = []
    with open(path, "r", errors="ignore") as fh:
        for line in fh:
            if line.startswith("v "):
                p = line.split()
                v.append((float(p[1]), float(p[2]), float(p[3])))
    return np.asarray(v, dtype=np.float64)


def axis_frame(allv):
    P = allv - allv.mean(axis=0)
    U = np.linalg.svd(P.T @ P)[0]
    return U[:, 0], U[:, 1], U[:, 2]


def wrap_degrees(theta):
    occ = np.zeros(360, dtype=bool)
    occ[np.clip(((np.degrees(theta) + 180.0) % 360.0).astype(int), 0, 359)] = True
    if occ.all():
        return 360.0
    if not occ.any():
        return 0.0
    start = int(np.argmax(occ))
    r = np.roll(occ, -start)
    longest = run = 0
    for v in r:
        run = 0 if v else run + 1
        longest = max(longest, run)
    return float(360 - longest)


def sub(q, n):
    return q if len(q) <= n else q[::max(1, len(q) // n)]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", default="", help="folder of Piece*.obj")
    ap.add_argument("--hdf5", default="", help="assembled source, preferred")
    ap.add_argument("--key", default="juglet_gt/Juglet-000")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    if args.hdf5:
        h = h5py.File(args.hdf5, "r")
        pg = h[args.key]["pieces"]
        keys = sorted(pg.keys(), key=lambda s: int(s) if s.isdigit() else s)
        parts = [np.asarray(pg[k]["vertices"][:], dtype=np.float64)
                 for k in keys]
        names = [f"Piece{int(k) + 1:02d}" for k in keys]
        print(f"{len(parts)} fragments from {args.hdf5}:{args.key}\n")
    else:
        files = sorted(Path(args.dir).glob("Piece*.obj"))
        parts = [load_obj_vertices(f) for f in files]
        names = [f.stem for f in files]
        print(f"{len(parts)} fragments from {args.dir}\n")

    # Assembled or laid out? The first run measured a scattered layout and
    # reported a confident 360. A fragment of a vessel spans a real share of
    # it; a laid-out piece sits in its own small box far from the others.
    exts = np.array([np.ptp(p, axis=0).max() for p in parts])
    whole = float(np.ptp(np.concatenate(parts, axis=0), axis=0).max())
    frac = float(exts.max() / (whole + 1e-12))
    print(f"  largest fragment spans {100 * frac:.0f}% of the object's extent")
    if frac < 0.25:
        print("  *** NOT ASSEMBLED -- every piece is small against the whole,")
        print("  *** so these are laid out apart. Wrap around a fitted axis")
        print("  *** would be meaningless. Point --hdf5 at the assembled GT.\n")

    allv = np.concatenate(parts, axis=0)
    ctr = allv.mean(axis=0)
    ax, e1, e2 = axis_frame(allv)
    Q = allv - ctr
    height = float(np.ptp(Q @ ax))
    max_r = float(np.hypot(Q @ e1, Q @ e2).max())
    print(f"  slenderness (height / widest diameter): {height / (2 * max_r):.2f}")
    print(f"  vertices: {len(allv)}\n")

    print(f"  {'fragment':<12s} {'verts':>8s} {'share %':>8s} {'wrap':>7s}  "
          f"what it is")
    print("  " + "-" * 60)
    rows = []
    for nm, p in zip(names, parts):
        q = p - ctr
        u, v, z = q @ e1, q @ e2, q @ ax
        w = wrap_degrees(np.arctan2(v, u))
        share = 100.0 * len(p) / len(allv)
        # where it sits along the axis: 0 = base, 1 = rim
        lo = (float(z.min()) - float(Q[:, 0].min() if False else (Q @ ax).min()))
        span = float(np.ptp(Q @ ax)) + 1e-12
        mid = (float(z.mean()) - float((Q @ ax).min())) / span
        kind = ("CLOSED HOOP" if w >= 340 else
                "nearly closed" if w >= 260 else "arc")
        rows.append((nm, w, share, mid, kind))
        print(f"  {nm:<12s} {len(p):>8d} {share:>7.1f}% {w:>6.0f}d  {kind}"
              f"   (height {mid:.2f} of the way up)")

    closed = [r for r in rows if r[1] >= 340]
    print(f"\n  {len(closed)} of {len(rows)} fragments close completely "
          f"({100 * len(closed) / len(rows):.0f}%)")
    print(f"  bbad_vessels, same ruler: 13.9% of fragments close past 340d")

    if not args.out:
        return

    n = len(parts)
    fig, axes = plt.subplots(2, n, figsize=(2.55 * n, 6.4))
    foot = sub(np.c_[Q @ e1, Q @ e2], 12000)
    side = sub(np.c_[Q @ e1, Q @ ax], 12000)
    s = float(np.abs(Q).max()) + 1e-12
    for k, (nm, p) in enumerate(zip(names, parts)):
        q = sub(p - ctr, 8000)
        col = plt.cm.tab10(k % 10)
        a = axes[0, k]
        a.scatter(side[:, 0] / s, side[:, 1] / s, s=0.6, alpha=0.12,
                  linewidths=0, color="#9aa5ad")
        a.scatter((q @ e1) / s, (q @ ax) / s, s=1.8, alpha=0.85,
                  linewidths=0, color=col)
        a.set_title(f"{nm}\nside on", fontsize=9)
        a = axes[1, k]
        a.scatter(foot[:, 0] / s, foot[:, 1] / s, s=0.6, alpha=0.12,
                  linewidths=0, color="#9aa5ad")
        a.scatter((q @ e1) / s, (q @ e2) / s, s=1.8, alpha=0.85,
                  linewidths=0, color=col)
        w = rows[k][1]
        a.set_title(f"from above\n{w:.0f}deg  {rows[k][4]}", fontsize=9,
                    color="#b8342a" if w >= 340 else "#2f6f7e")
    for a in axes.ravel():
        a.set_aspect("equal")
        a.set_xlim(-1.1, 1.1); a.set_ylim(-1.1, 1.1)
        a.set_xticks([]); a.set_yticks([])

    fig.suptitle(
        "The Juglet's own nine fragments, each alone, against the whole "
        "vessel in grey.\n"
        "This is the real object -- hand fractured, hand scanned. Whatever it "
        "does is by definition a real way for a pot to break.", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    fig.savefig(args.out, dpi=130)
    print(f"\n  wrote {args.out}")


if __name__ == "__main__":
    main()
