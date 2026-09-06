"""The Juglet's proposed assembly beside a freshly broken pot that scores the same.

Ticket .scratch/juglet-cause/issues/02, the one criterion that could not be met
from disk: no `*_fresh_*` or scale-ladder run had ever saved point clouds, only
`results/`. The fragment-drop job's `whole` arm saves them, so this closes it
without buying any GPU time of its own.

WHY IT MATTERS. Ticket 02 concluded that the Juglet's 66 degree turn sits INSIDE
the range fresh pots occupy at comparable fragment counts (48.7 to 81.8 deg), so
wear has no residual left to explain. That conclusion rests entirely on a number.
Two assemblies can share a number and look nothing alike -- one pot loosely
seated all over, another with half its sherds correct and half flung across the
vessel -- and only the picture can tell those apart. If the Juglet's failure
looks like a fresh pot's failure, the shared score means what ticket 02 says it
means. If it looks different in kind, the score was a coincidence.

Every panel is drawn in its own object's reference frame with nothing
re-centred, and each sherd gets its own colour, because the silhouette of these
pots still reads as a pot at 89 degrees of average turn (ticket 01).

Usage:
  python scripts/render_juglet_vs_fresh.py \
      --juglet artifacts/jugdraw/jugdraw_baseline_30130049 \
      --fresh artifacts/dropwhole/drop_whole_<jobid> \
      --pots plate narrow_bottle1 \
      --out artifacts/juglet_vs_fresh.png
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np

from readout import cloud_for, median_draw

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

VIEWS = [((0, 2), "side"), ((0, 1), "top")]


def kabsch_deg(a, b):
    """Turn, in degrees, between two copies of the same sherd."""
    ac, bc = a - a.mean(0), b - b.mean(0)
    u, _, vt = np.linalg.svd(ac.T @ bc)
    d = np.sign(np.linalg.det(u @ vt))
    r = u @ np.diag([1.0, 1.0, d]) @ vt
    return float(np.degrees(np.arccos(np.clip((np.trace(r) - 1.0) / 2.0, -1.0, 1.0))))


def load(run, pot=None):
    """The saved clouds for one pot, or for the run's only object.

    readout.cloud_for matches the name stored INSIDE each npz. The filenames are
    sample indices (`ceramics_sample00001.npz`), so matching a pot name against
    them silently finds nothing -- or, worse, the wrong pot.
    """
    return np.load(cloud_for(Path(run), pot))


def panel(ax, gt, prop, ids, view, lo, hi, pad, reference):
    i, j = view
    cmap = plt.get_cmap("tab20")
    pts = gt if reference else prop
    for k, pid in enumerate(sorted(set(ids.tolist()))):
        m = ids == pid
        ax.scatter(pts[m, i], pts[m, j], s=0.7, color=cmap(k % 20),
                   linewidths=0, rasterized=True)
    ax.set_xlim(lo[i] - pad, hi[i] + pad)
    ax.set_ylim(lo[j] - pad, hi[j] + pad)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--juglet", required=True)
    ap.add_argument("--fresh", required=True)
    ap.add_argument("--pots", nargs="+", required=True)
    ap.add_argument("--out", default="artifacts/juglet_vs_fresh.png")
    a = ap.parse_args()

    cases = [("Juglet (worn, 9 sherds)", a.juglet, None)]
    cases += [(p, a.fresh, p) for p in a.pots]

    nrow = len(VIEWS) * 2                      # reference row + proposed row
    fig, axes = plt.subplots(nrow, len(cases),
                             figsize=(len(cases) * 2.6, nrow * 2.6),
                             squeeze=False)

    for c, (label, run, pot) in enumerate(cases):
        d = load(run, pot)
        k, med = median_draw(Path(run), pot)
        gt, ids = d["pts_gt"], d["part_ids"]
        prop = d["generations_proposed"][k]
        lo, hi = gt.min(0), gt.max(0)
        pad = 0.06 * (hi - lo).max()
        parts = sorted(set(ids.tolist()))

        # Per-sherd turn, recomputed from the geometry so the caption and the
        # picture cannot disagree. Sherd 0 is the given anchor and is excluded.
        turns = [kabsch_deg(gt[ids == p], prop[ids == p]) for p in parts[1:]]

        for vi, (view, vname) in enumerate(VIEWS):
            for ri, ref in enumerate([True, False]):
                ax = axes[vi * 2 + ri][c]
                panel(ax, gt, prop, ids, view, lo, hi, pad, ref)
                if ref:
                    ax.set_title("%s %s\nas it really is, %d sherds"
                                 % (label, vname, len(parts)), fontsize=7)
                else:
                    ax.set_title("model's answer, median draw\nturn %.0f deg; "
                                 "worst sherd %.0f deg"
                                 % (med, max(turns) if turns else 0.0),
                                 fontsize=7)

    fig.suptitle(
        "Does a shared score mean a shared KIND of failure?\n"
        "The Juglet beside freshly broken pots that score about the same. One "
        "colour per sherd; nothing re-centred.\n"
        "Rows alternate: how the pot really is, then what the model proposed.",
        fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(a.out, dpi=130)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
