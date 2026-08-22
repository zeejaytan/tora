"""Is the balance filter selecting sherds, or selecting SLICES?

Found by rendering the smoke build rather than by reasoning: the first panels
show colour running in horizontal bands around a bottle. Bands are rings, and a
pot does not break into rings.

THE WORRY, stated so it can be refuted. Instances are chosen by the inverse
Simpson index, which rewards a break whose pieces are all about the same size.
Slicing a vessel into equal rings scores near-perfectly on that -- better than a
real break, which sheds a few small sherds. So the filter that was added to
reject "one remnant plus chips" may be selecting stratified cuts instead, and it
would do it silently because balance is exactly what it was asked to maximise.

If true it matters more than wear does. A model trained on rings learns that
fragments stack, and the Juglet's sherds do not stack.

HOW IT IS MEASURED, so a viewpoint cannot decide it. Every vessel has an axis of
revolution -- its first principal axis. For each fragment:

  angular span   how far it reaches AROUND that axis, in degrees. A ring covers
                 close to 360. A sherd covers a wedge.
  axial span     how far it reaches ALONG the axis, as a fraction of the
                 object's height. A ring is a thin band; a sherd is not.

A fragment is called a RING if it wraps more than 300 degrees. The number that
decides this is the fraction of fragments that are rings, and it is compared
between the breaks the filter PICKS and the breaks it passes over -- if picking
by balance is what pulls in the rings, the two will differ.

Rendered as well as measured, larger and with the pieces separated, because
"looks like bands" is what raised this and the picture has to be able to
disagree with the number.

Usage:
  python scripts/check_break_realism.py --src dataset/breaking_bad_vol.hdf5 \
      --out artifacts/break_realism.png
"""

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))

COLOURS = ["#1f4e79", "#c1440e", "#4a7c59", "#7d5ba6", "#b8860b",
           "#2f6f7e", "#8b3a62", "#556b2f", "#a0522d", "#4682b4",
           "#8b0000", "#2e8b57", "#6a5acd", "#cd853f", "#708090"]

CATS = ["Bottle", "Vase", "Mug", "Bowl", "Cup", "Teapot", "Plate", "WineBottle",
        "BeerBottle", "Teacup", "PillBottle", "WineGlass"]

RING_DEG = 300.0


def effective_pieces(sizes):
    p = np.asarray(sizes, dtype=float)
    if p.sum() <= 0:
        return 0.0
    p = p / p.sum()
    return 1.0 / float((p ** 2).sum())


def axis_frame(allv):
    """The vessel's axis of revolution and two perpendicular directions."""
    P = allv - allv.mean(axis=0)
    U = np.linalg.svd(P.T @ P)[0]
    return U[:, 0], U[:, 1], U[:, 2]


def piece_spans(parts):
    """Angular reach around the axis, and axial reach along it, per fragment."""
    allv = np.concatenate(parts, axis=0)
    ctr = allv.mean(axis=0)
    ax, e1, e2 = axis_frame(allv)
    height = float(np.ptp((allv - ctr) @ ax)) + 1e-12
    out = []
    for p in parts:
        q = p - ctr
        th = np.arctan2(q @ e2, q @ e1)
        # Angular EXTENT, not max-minus-min: a wedge straddling +/-pi would
        # otherwise read as a full circle. Found as the largest gap between
        # consecutive angles, subtracted from the whole turn.
        s = np.sort(th)
        gaps = np.diff(np.concatenate([s, s[:1] + 2 * np.pi]))
        span = float(np.degrees(2 * np.pi - gaps.max()))
        out.append((span, float(np.ptp(q @ ax)) / height))
    return out


def instances(node, min_eff):
    rows = []
    for fr in sorted(node.keys()):
        grp = node[fr]
        keys = sorted(grp.keys(), key=lambda s: int(s) if s.isdigit() else s)
        if len(keys) < 3:
            continue
        sz = [grp[k]["vertices"].shape[0] for k in keys]
        rows.append((effective_pieces(sz), fr, keys))
    rows.sort(key=lambda r: -r[0])
    return [r for r in rows if r[0] >= min_eff], rows


def load(grp, keys):
    return [np.asarray(grp[k]["vertices"][:], dtype=np.float64) for k in keys]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", required=True)
    ap.add_argument("--dataset", default="everyday")
    ap.add_argument("--objects-per-cat", type=int, default=6)
    ap.add_argument("--min-effective", type=float, default=4.0)
    ap.add_argument("--picked", type=int, default=3,
                    help="how many top-balanced instances the builder takes")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    h = h5py.File(args.src, "r")
    ev = h[args.dataset]

    per_cat = {}
    panels = []
    for c in CATS:
        if c not in ev:
            continue
        objs = sorted(ev[c].keys())
        step = max(1, len(objs) // args.objects_per_cat)
        pick_ring, pass_ring, pick_n, pass_n, effs = [], [], 0, 0, []
        for o in objs[::step][:args.objects_per_cat]:
            ok, allrows = instances(ev[c][o], args.min_effective)
            if not ok:
                continue
            taken = ok[:args.picked]
            skipped = [r for r in allrows if r not in taken]
            for group, ringbuf, cnt in ((taken, pick_ring, "pick"),
                                        (skipped[:args.picked], pass_ring, "pass")):
                for e, fr, keys in group:
                    sp = piece_spans(load(ev[c][o][fr], keys))
                    ringbuf.extend([1.0 if s >= RING_DEG else 0.0 for s, _ in sp])
                    if cnt == "pick":
                        pick_n += 1
                        effs.append(e)
                    else:
                        pass_n += 1
            if len(panels) < 12 and taken:
                e, fr, keys = taken[0]
                panels.append((c, o, e, load(ev[c][o][fr], keys)))
        if pick_ring:
            per_cat[c] = (100 * float(np.mean(pick_ring)), pick_n,
                          100 * float(np.mean(pass_ring)) if pass_ring else float("nan"),
                          pass_n, float(np.mean(effs)) if effs else float("nan"))

    print(f"A fragment counts as a RING if it wraps more than {RING_DEG:.0f} "
          f"degrees around the vessel's axis.")
    print()
    print(f"  {'category':<14s} {'ring % (picked)':>16s} {'inst':>6s} "
          f"{'ring % (passed over)':>21s} {'inst':>6s} {'mean eff':>9s}")
    print("  " + "-" * 78)
    for c in sorted(per_cat, key=lambda k: -per_cat[k][0]):
        a, an, b, bn, e = per_cat[c]
        print(f"  {c:<14s} {a:>15.1f}% {an:>6d} {b:>20.1f}% {bn:>6d} {e:>9.1f}")
    if per_cat:
        A = float(np.mean([v[0] for v in per_cat.values()]))
        B = float(np.mean([v[2] for v in per_cat.values() if v[2] == v[2]]))
        print("  " + "-" * 78)
        print(f"  {'ALL':<14s} {A:>15.1f}% {'':>6s} {B:>20.1f}%")
        print()
        if A > B + 5:
            print("  THE FILTER IS PULLING IN RINGS. Balance is selecting "
                  "stratified cuts.")
        elif A > 25:
            print("  Rings are common in the corpus generally, not caused by "
                  "the filter.")
        else:
            print("  Rings are rare either way. The banding in the sample "
                  "render was something else.")

    if args.out:
        ncol = 4
        nrow = int(np.ceil(len(panels) / ncol))
        fig, axes = plt.subplots(nrow, ncol, figsize=(4.6 * ncol, 4.9 * nrow))
        axes = np.atleast_2d(axes).ravel()
        for a in axes:
            a.axis("off")
        for a, (c, o, e, parts) in zip(axes, panels):
            allv = np.concatenate(parts, axis=0)
            ctr = allv.mean(axis=0)
            s = float(np.abs(allv - ctr).max()) + 1e-12
            ax, e1, _ = axis_frame(allv)
            for k, p in enumerate(parts):
                q = (p - ctr) / s
                if len(q) > 6000:
                    q = q[::max(1, len(q) // 6000)]
                a.scatter(q @ e1, q @ ax, s=1.6, alpha=0.75, linewidths=0,
                          color=COLOURS[k % len(COLOURS)])
            a.set_aspect("equal")
            a.set_xlim(-1.15, 1.15); a.set_ylim(-1.15, 1.15)
            a.axis("on"); a.set_xticks([]); a.set_yticks([])
            sp = piece_spans(parts)
            rings = sum(1 for x, _ in sp if x >= RING_DEG)
            a.set_title(f"{c}/{o[:8]}  eff {e:.1f}\n{len(parts)} pieces, "
                        f"{rings} wrap >{RING_DEG:.0f}deg", fontsize=9)
        fig.suptitle(
            "The breaks the balance filter PICKS, side-on, one colour per "
            "fragment\n"
            "Horizontal bands of colour would mean rings. Sherds should read as "
            "irregular patches spanning the wall.", fontsize=12)
        fig.tight_layout(rect=(0, 0, 1, 0.94))
        fig.savefig(args.out, dpi=130)
        print(f"\n  wrote {args.out}")


if __name__ == "__main__":
    main()
