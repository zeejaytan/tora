"""Look at Breaking Bad's vessel objects before treating them as pottery.

Gate B asked how to fracture Geometric Breaks' 1,125 vessels. Checking what we
already hold first turned up 375 vessel-shaped objects in `breaking_bad_vol.hdf5`
-- bottles, vases, mugs, bowls, cups, teapots, plates -- each with about a
hundred fracture instances, already fractured with fracture modes by the people
who wrote it.

That is only useful if they are actually pot-like. ShapeNet's bottle class holds
plastic water bottles and spray cans, and a thousand irrelevant shapes is worse
than eight relevant ones. So this draws a sample, assembled, one colour per
piece, before anything is built on them.

WHAT TO JUDGE, as a conservator would:

  Is it a VESSEL a potter would recognise -- a wheel-made or hand-built form
  with a wall, a base and a rim? A plastic bottle with a moulded screw thread is
  not, whatever the class label says.

  Do the FRACTURES look like breakage? Fracture modes produces the object's
  preferred break patterns, so sherds should look like sherds -- irregular,
  spanning the wall -- rather than slices.

Multi-piece instances are preferred for the sample, since two-piece breaks are
the majority and the least informative about how a pot comes apart.

Usage:
  python scripts/render_bbad_vessels.py --src dataset/breaking_bad_vol.hdf5 \
      --out artifacts/bbad_vessels.png
"""

import argparse

import h5py
import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

COLOURS = ["#1f4e79", "#c1440e", "#4a7c59", "#7d5ba6", "#b8860b",
           "#2f6f7e", "#8b3a62", "#556b2f", "#a0522d", "#4682b4",
           "#8b0000", "#2e8b57", "#6a5acd", "#cd853f"]

CATS = ["Bottle", "Vase", "Mug", "Bowl", "Cup", "Teapot", "Plate", "WineBottle",
        "BeerBottle", "Teacup", "PillBottle", "WineGlass"]


def pieces_of(grp):
    out = []
    for k in sorted(grp.keys(), key=lambda s: int(s) if s.isdigit() else s):
        node = grp[k]
        v = node["vertices"][:] if "vertices" in node else node[:]
        out.append(np.asarray(v, dtype=np.float64))
    return out


def pick(node, want_min=4):
    """A fracture instance with several pieces, since two-piece is the norm."""
    best, best_n = None, -1
    for fr in sorted(node.keys()):
        n = len(node[fr].keys())
        if n >= want_min:
            return fr, n
        if n > best_n:
            best, best_n = fr, n
    return best, best_n


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", required=True)
    ap.add_argument("--dataset", default="everyday")
    ap.add_argument("--per-cat", type=int, default=2)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    h = h5py.File(args.src, "r")
    ev = h[args.dataset]

    items = []
    for c in CATS:
        if c not in ev:
            continue
        objs = sorted(ev[c].keys())
        step = max(1, len(objs) // max(1, args.per_cat))
        for o in objs[::step][:args.per_cat]:
            fr, n = pick(ev[c][o])
            if fr is None:
                continue
            items.append((c, o, fr, n, pieces_of(ev[c][o][fr])))
    print(f"{len(items)} objects sampled")

    ncol = 6
    nrow = int(np.ceil(len(items) / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(2.5 * ncol, 2.7 * nrow))
    axes = np.atleast_2d(axes).ravel()
    for ax in axes:
        ax.axis("off")

    for a, (c, o, fr, n, parts) in zip(axes, items):
        allv = np.concatenate(parts, axis=0)
        ctr = allv.mean(axis=0)
        s = float(np.abs(allv - ctr).max()) + 1e-12
        for k, p in enumerate(parts):
            q = (p - ctr) / s
            if len(q) > 4000:
                q = q[::max(1, len(q) // 4000)]
            a.scatter(q[:, 0], q[:, 1], s=0.8, alpha=0.6, linewidths=0,
                      color=COLOURS[k % len(COLOURS)])
        a.set_aspect("equal")
        a.set_xlim(-1.15, 1.15)
        a.set_ylim(-1.15, 1.15)
        a.axis("on")
        a.set_xticks([]); a.set_yticks([])
        a.set_title(f"{c}  ({n} pieces)", fontsize=8.5)

    fig.suptitle(
        "Breaking Bad vessel objects we already hold, assembled, one colour per "
        "piece\n"
        "Judge as a conservator: are these vessels a potter would recognise, and "
        "do the breaks look like breakage?", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(args.out, dpi=140)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
