"""Draw what the two anchor modes hand the model, on the Juglet's own geometry.

Ticket .scratch/juglet-cause/issues/02-is-nine-fragments-enough.md set out to
compare the Juglet against fresh pots of similar fragment count. It cannot be
done from the runs on disk, because the two sides were not asked the same
question: `config/data/zeroshot/juglet_gt.yaml` sets `anchor_free: true` and
every other dataset config in the project sets it false. Four configs out of
thirty-six are anchor-free, and all four are the Juglet.

The difference is in what the model is given before it starts:

  anchor-FIXED (every fresh pot, every Breaking Bad set, every Fractura subset)
    The largest fragment is handed over already sitting in its correct place in
    the finished vessel -- position and orientation both -- and is pinned there
    for the whole reconstruction (tora/data/dataset.py:395, tora/modeling/tora.py:338).
    The model builds the pot around a fragment that is already correctly seated.

  anchor-FREE (the Juglet, and only the Juglet)
    No fragment is placed. Every one is centred on its own centroid and the
    non-anchor ones are randomly turned (tora/data/dataset.py:383).

This draws both, from the Juglet's saved cloud, so the difference in the task
can be seen rather than inferred. No GPU: the anchor-fixed panel is constructed
from the stored ground truth exactly as dataset.py constructs it, by putting the
largest fragment back at its ground-truth pose and leaving the rest as they are.

Usage:
  python scripts/render_anchor_mode.py \
      --npz artifacts/juglet_runs/lorav_juglet_baseline_29623885/clouds/juglet_gt_sample00000.npz \
      --out artifacts/anchor_mode.png
"""

import argparse

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

COLOURS = ["#1f4e79", "#c1440e", "#4a7c59", "#7d5ba6", "#b8860b",
           "#2f6f7e", "#8b3a62", "#556b2f", "#a0522d"]


def panel(ax, pts, ids, anchor_id, title, axes, note=None):
    i, j = axes
    lim = np.abs(pts).max() * 1.05
    for k, pid in enumerate(sorted(set(ids.tolist()))):
        m = ids == pid
        is_anchor = pid == anchor_id
        ax.scatter(pts[m, i], pts[m, j], s=1.4 if is_anchor else 0.5,
                   c="#c1440e" if is_anchor else COLOURS[k % len(COLOURS)],
                   linewidths=0, rasterized=True, zorder=3 if is_anchor else 2)
    ax.set_aspect("equal")
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(title, fontsize=9)
    if note:
        ax.text(0.5, -0.03, note, transform=ax.transAxes, ha="center",
                va="top", fontsize=7.5, color="#444")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--npz", required=True)
    ap.add_argument("--out", default="artifacts/anchor_mode.png")
    a = ap.parse_args()

    z = np.load(a.npz)
    ids = z["part_ids"]
    gt = z["pts_gt"].astype(float)
    inp = z["pts_input"].astype(float)

    # dataset.py:325 -- the anchor is the fragment with the most points.
    parts = sorted(set(ids.tolist()))
    anchor = max(parts, key=lambda p: int((ids == p).sum()))

    # anchor-FIXED: the anchor sits at its ground-truth pose; the rest are as
    # the anchor-free input already has them (centred and randomly turned).
    fixed = inp.copy()
    fixed[ids == anchor] = gt[ids == anchor]

    fig, axs = plt.subplots(1, 3, figsize=(11.5, 5.0))
    panel(axs[0], gt, ids, anchor, "the finished vessel", (0, 2),
          "what a correct answer looks like")
    panel(axs[1], fixed, ids, anchor,
          "anchor-FIXED: every other pot in this project", (0, 2),
          "the largest fragment (red) is given, already\n"
          "correctly placed, and held there throughout")
    panel(axs[2], inp, ids, anchor,
          "anchor-FREE: the Juglet, and only the Juglet", (0, 2),
          "nothing is placed. all nine fragments start\n"
          "stacked at the origin, turned at random")

    fig.suptitle("The Juglet has never been asked the same question as the pots "
                 "it is compared against", fontsize=11)
    fig.tight_layout(rect=(0, 0.14, 1, 0.93))
    fig.savefig(a.out, dpi=170)
    print("wrote", a.out)
    print("anchor fragment: part %d, %d of %d points"
          % (anchor, int((ids == anchor).sum()), len(ids)))


if __name__ == "__main__":
    main()
