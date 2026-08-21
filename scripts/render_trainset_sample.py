"""Look at a built training set before training on it.

A training set is geometry, and the rule in this workspace is that geometry gets
rendered before any claim is made about it. The build script's summary can only
report what it intended to write; it cannot notice that the recession folded a
surface, that fragment loss removed the anchor, or that the shared normalisation
collapsed an object. Every one of those has happened here.

WHAT TO JUDGE, as a conservator would:

  Is it still a VESSEL. The pieces are drawn in their ground-truth positions, so
  a panel should read as a pot with cracks through it, not as a scatter.

  Are the PIECES sherd-like -- irregular, spanning the wall -- rather than
  slices or chips. The effective piece count in the title says how balanced the
  break is; near the Juglet's nine is what we want.

  Where a piece is MISSING, is the hole plausible. The set deliberately drops
  fragments, because a real assemblage is incomplete and a model that has only
  seen complete puzzles will seat every fragment against something.

Works on any dataset written by the builders here: `<name>/<tag>/pieces/<i>/
vertices`.

Usage:
  python scripts/render_trainset_sample.py \
      --src dataset/bbad_vessels.hdf5 --dataset bbad_vessels \
      --out artifacts/bbad_vessels_sample.png
"""

import argparse
import json
from pathlib import Path

import h5py
import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

COLOURS = ["#1f4e79", "#c1440e", "#4a7c59", "#7d5ba6", "#b8860b",
           "#2f6f7e", "#8b3a62", "#556b2f", "#a0522d", "#4682b4",
           "#8b0000", "#2e8b57", "#6a5acd", "#cd853f", "#708090"]


def pieces_of(grp):
    g = grp["pieces"] if "pieces" in grp else grp
    keys = sorted(g.keys(), key=lambda s: int(s) if s.isdigit() else s)
    return [np.asarray(g[k]["vertices"][:], dtype=np.float64) for k in keys]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", required=True)
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n", type=int, default=18)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    man = {}
    mp = Path(str(args.src) + ".manifest.json")
    if mp.exists():
        man = json.loads(mp.read_text())

    with h5py.File(args.src, "r") as h:
        ds = h[args.dataset]
        tags = sorted(ds.keys())
        rng = np.random.default_rng(args.seed)

        # Spread the sample across SHAPES rather than taking the first N tags,
        # which would be three wear levels of the same six objects and would
        # say nothing about the variety the set exists to provide.
        by_obj = {}
        for t in tags:
            key = man.get(t, {}).get("object", t.split("__")[0])
            by_obj.setdefault(key, []).append(t)
        objs = sorted(by_obj)
        pick = [by_obj[o][int(rng.integers(len(by_obj[o])))]
                for o in (objs if len(objs) <= args.n
                          else [objs[i] for i in
                                np.linspace(0, len(objs) - 1, args.n).astype(int)])]

        ncol = 6
        nrow = int(np.ceil(len(pick) / ncol))
        fig, axes = plt.subplots(nrow, ncol, figsize=(2.6 * ncol, 2.9 * nrow))
        axes = np.atleast_2d(axes).ravel()
        for ax in axes:
            ax.axis("off")

        for a, t in zip(axes, pick):
            parts = pieces_of(ds[t])
            allv = np.concatenate(parts, axis=0)
            ctr = allv.mean(axis=0)
            s = float(np.abs(allv - ctr).max()) + 1e-12
            # SIDE-ON. Plotting x against y looks straight down the axis of
            # revolution on these objects, so every vessel comes out a circle
            # and nothing about its form can be judged -- a real mistake made
            # on this corpus once already.
            P = allv - ctr
            long = np.linalg.svd(P.T @ P)[0][:, 0]
            e1 = np.cross(long, [0.0, 0.0, 1.0])
            if np.linalg.norm(e1) < 1e-6:
                e1 = np.cross(long, [0.0, 1.0, 0.0])
            e1 = e1 / np.linalg.norm(e1)
            for k, p in enumerate(parts):
                q = (p - ctr) / s
                if len(q) > 3500:
                    q = q[::max(1, len(q) // 3500)]
                a.scatter(q @ e1, q @ long, s=0.7, alpha=0.65, linewidths=0,
                          color=COLOURS[k % len(COLOURS)])
            a.set_aspect("equal")
            a.set_xlim(-1.15, 1.15)
            a.set_ylim(-1.15, 1.15)
            a.axis("on")
            a.set_xticks([]); a.set_yticks([])
            m = man.get(t, {})
            head = f"{m.get('category', '')} {m.get('wear', '')}".strip() or t[:22]
            sub = (f"{len(parts)} pieces, eff {m.get('effective_pieces', 0):.1f}"
                   if m else f"{len(parts)} pieces")
            miss = m.get("missing", "")
            a.set_title(f"{head}\n{sub}\n{miss}", fontsize=7.0)

        fig.suptitle(
            f"{args.dataset}: assembled, one colour per fragment, one panel per "
            f"vessel shape\n"
            "Judge as a conservator: still a vessel, sherd-like pieces, "
            "plausible holes where fragments are absent.", fontsize=11)
        fig.tight_layout(rect=(0, 0, 1, 0.93))
        fig.savefig(args.out, dpi=140)
        print(f"wrote {args.out}  ({len(pick)} panels of {len(tags)} examples)")


if __name__ == "__main__":
    main()
