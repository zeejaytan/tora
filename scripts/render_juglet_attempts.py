"""Draw the proposed Juglet reassemblies beside the conservator's own.

Written because the scores contradict each other. Against the real ground truth
wear_v2 reported part_accuracy 0.80 -- eight fragments in ten placed correctly --
while reporting a mean rotation error of 52.9 degrees and not one fragment of
nine within ten degrees of correct. part_accuracy passes a fragment on chamfer
distance, which stays small for a sherd sitting roughly in the right region
however it is turned, and that is the failure that faked an entire finding on
this exact pot once already.

For a reassembly the eye is the instrument a threshold cannot fool. This draws
each attempt next to the hand assembly, in two views, with each sherd in its own
colour so a piece can be followed between panels.

WHAT TO LOOK FOR, in the order that decides what to do next:

  Does it read as a POT? A closed, roughly axially symmetric body with a rim.
  If the pieces form a plausible vessel, the model has understood the object
  even where individual poses are wrong.

  Are sherds INTERPENETRATING? Two fragments occupying the same space is
  physically impossible and no metric averaging over points reports it clearly.

  Is the MISSING PIECE left open? The pot is incomplete. A reconstruction that
  leaves that gap is CORRECT and one that closes it is wrong -- the opposite of
  what a contact-rewarding metric will say.

Every panel is drawn from the geometry itself, orthographic, no perspective to
flatter a viewpoint. Each assembly is centred and scaled independently, so the
comparison is of SHAPE and not of size.

Usage:
  python scripts/render_juglet_attempts.py \
      --meshes /path/to/juglet_gt_meshes/wear_v2 \
      --gt dataset/juglet_gt.hdf5 --gt-dataset juglet_gt \
      --out artifacts/juglet_attempts.png
"""

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np
import trimesh

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

COLOURS = ["#1f4e79", "#c1440e", "#4a7c59", "#7d5ba6", "#b8860b",
           "#2f6f7e", "#8b3a62", "#556b2f", "#a0522d"]


def load_gt(path, dsname):
    with h5py.File(path, "r") as h:
        ds = h[dsname]
        obj = sorted(ds.keys())[0]
        grp = ds[obj]
        g = grp["pieces"] if "pieces" in grp else grp
        keys = sorted(g.keys(), key=lambda s: int(s) if s.isdigit() else s)
        return [np.asarray(g[k]["vertices"][:], dtype=np.float64) for k in keys]


def load_scene(path):
    s = trimesh.load(path, process=False)
    if isinstance(s, trimesh.Scene):
        out = []
        for name in sorted(s.geometry.keys()):
            g = s.geometry[name]
            v = np.asarray(g.vertices, dtype=np.float64)
            tf = s.graph.get(name)[0] if name in s.graph.nodes_geometry else None
            if tf is not None:
                v = trimesh.transform_points(v, tf)
            out.append(v)
        return out
    return [np.asarray(s.vertices, dtype=np.float64)]


def normalise(parts):
    allv = np.concatenate(parts, axis=0)
    c = allv.mean(axis=0)
    s = float(np.abs(allv - c).max()) + 1e-12
    return [(p - c) / s for p in parts]


def draw(ax, parts, axes_pair, title, max_pts=6000, seed=0):
    rng = np.random.default_rng(seed)
    i, j = axes_pair
    for k, p in enumerate(parts):
        q = p if len(p) <= max_pts else p[rng.choice(len(p), max_pts, False)]
        ax.scatter(q[:, i], q[:, j], s=0.4, alpha=0.5, linewidths=0,
                   color=COLOURS[k % len(COLOURS)])
    ax.set_aspect("equal")
    ax.set_xlim(-1.15, 1.15)
    ax.set_ylim(-1.15, 1.15)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(title, fontsize=9)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--meshes", required=True)
    ap.add_argument("--gt", required=True)
    ap.add_argument("--gt-dataset", default="juglet_gt")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    gt = normalise(load_gt(args.gt, args.gt_dataset))
    print(f"ground truth: {len(gt)} sherds")

    files = sorted(Path(args.meshes).glob("attempt*.glb"))
    sets = [("hand assembly\n(the answer)", gt)]
    for f in files:
        parts = normalise(load_scene(f))
        sets.append((f.stem, parts))
        print(f"{f.name}: {len(parts)} sherds")

    n = len(sets)
    fig, axes = plt.subplots(2, n, figsize=(2.5 * n, 5.6))
    axes = np.atleast_2d(axes)
    for c, (name, parts) in enumerate(sets):
        draw(axes[0, c], parts, (0, 1), name)
        draw(axes[1, c], parts, (0, 2), "")
    axes[0, 0].set_ylabel("front", fontsize=9)
    axes[1, 0].set_ylabel("from above", fontsize=9)

    fig.suptitle(
        "The Juglet: the conservator's hand assembly against the model's "
        "attempts\n"
        "each sherd in its own colour, orthographic, each assembly scaled "
        "independently so this compares SHAPE",
        fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.90))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=150)
    print(f"wrote {args.out}")

    # a measurement the viewpoint cannot distort: do sherds share space?
    print("\n  interpenetration -- fragments occupying the same space")
    from scipy.spatial import cKDTree
    for name, parts in sets:
        worst = 0.0
        for a in range(len(parts)):
            for b in range(len(parts)):
                if b <= a:
                    continue
                pa, pb = parts[a], parts[b]
                sa = pa if len(pa) <= 4000 else pa[::max(1, len(pa) // 4000)]
                d, _ = cKDTree(pb).query(sa, workers=-1)
                worst = max(worst, float((d < 0.02).mean()))
        print(f"    {name.splitlines()[0]:<24s} worst pair: "
              f"{100 * worst:.1f}% of one sherd within 2% of another")
    print("  The hand assembly sets the honest baseline -- real sherds touch,")
    print("  so this is never zero. Attempts far above it are interpenetrating.")


if __name__ == "__main__":
    main()
