"""Does the pot still close when a sherd is missing?

Ticket .scratch/juglet-cause/issues/04, third acceptance criterion. The columns
in scripts/summarise_fragment_drop.py say how far each kept sherd turned. They
cannot say whether the result is still a vessel, and that is the question a
conservator actually asks of a reassembly.

Four columns per pot, in the SAME frame with nothing re-centred between them:

  reference (whole)    the pot as it really is, every sherd in its correct place
  model (whole)        what the model proposed with all sherds available
  reference (dropped)  the same pot MINUS the removed sherd, every remaining
                       sherd still in its correct place
  model (dropped)      what the model proposed with that sherd removed

THE THIRD COLUMN IS NOT DECORATION, and leaving it out made the first version of
this figure unreadable. With a sherd genuinely gone, a CORRECT answer also has a
hole in it. Without the third column there is no way to tell the hole the
missing sherd leaves from a hole the model opened by misplacing the sherds it
kept -- which is the entire question. Read column 4 against column 3, never
against column 1.

Colours are per column, not matched across the pair of arms: removing a fragment
renumbers the ones that remain, so sherd 2 in the dropped arm is not sherd 2 in
the whole arm. Within each arm the reference and the proposal do share colours,
which is the comparison that matters.

Two rows of views per pot. The first is the silhouette -- it answers "does it
close" and nothing else. The second colours each sherd separately, because a
silhouette of this kind of pot still reads as a pot at 89 degrees of average
turn (ticket 01), so the outline alone will happily pass a wrong answer.

Usage:
  python scripts/render_fragment_drop.py \
      --whole eval_runs/drop_whole_<jobid> \
      --dropped eval_runs/drop_rank2_<jobid> \
      --pots blue_pot galli_pot \
      --out artifacts/fragment_drop.png
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


def load(run, pot):
    """The saved clouds for one pot.

    Lookup and median-draw selection both live in readout.py: the clouds are
    named by sample index, not by pot, and the draw index has to be the run's own
    generation_idx rather than a position in a sorted file listing. Getting
    either wrong renders the wrong pot or the wrong attempt, convincingly.
    """
    return np.load(cloud_for(Path(run), pot))


def draw(ax, pts, ids, view, colour_by_part, lo, hi, pad):
    i, j = view
    if colour_by_part:
        cmap = plt.get_cmap("tab20")
        for k, pid in enumerate(sorted(set(ids.tolist()))):
            m = ids == pid
            ax.scatter(pts[m, i], pts[m, j], s=0.6, color=cmap(k % 20),
                       linewidths=0, rasterized=True)
    else:
        ax.scatter(pts[:, i], pts[:, j], s=0.5, c="#444444",
                   linewidths=0, rasterized=True)
    ax.set_xlim(lo[i] - pad, hi[i] + pad)
    ax.set_ylim(lo[j] - pad, hi[j] + pad)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--whole", required=True)
    ap.add_argument("--dropped", required=True)
    ap.add_argument("--pots", nargs="+", required=True)
    ap.add_argument("--out", default="artifacts/fragment_drop.png")
    a = ap.parse_args()

    nrow = len(a.pots) * len(VIEWS)
    fig, axes = plt.subplots(nrow, 4, figsize=(4 * 2.4, nrow * 2.4),
                             squeeze=False)

    for pi, pot in enumerate(a.pots):
        dw = load(a.whole, pot)
        dd = load(a.dropped, pot)
        kw, turn_w = median_draw(Path(a.whole), pot)
        kd, turn_d = median_draw(Path(a.dropped), pot)

        gt_w, ids_w = dw["pts_gt"], dw["part_ids"]
        gt_d, ids_d = dd["pts_gt"], dd["part_ids"]
        pr_w = dw["generations_proposed"][kw]
        pr_d = dd["generations_proposed"][kd]

        # The two runs normalise on different totals, so the dropped arm comes
        # back at a different size. Put it back on the reference's scale using
        # the fragments both runs have, or the pictures compare nothing.
        s = float(np.abs(gt_w).max() / max(np.abs(gt_d).max(), 1e-9))
        gt_d, pr_d = gt_d * s, pr_d * s

        lo, hi = gt_w.min(0), gt_w.max(0)
        pad = 0.06 * (hi - lo).max()

        for vi, (view, vname) in enumerate(VIEWS):
            r = pi * len(VIEWS) + vi
            colour = vi == 1
            n_w = len(set(ids_w.tolist()))
            n_d = len(set(ids_d.tolist()))
            for c, (pts, ids, title) in enumerate([
                (gt_w, ids_w, "as it really is, %d sherds" % n_w),
                (pr_w, ids_w, "model, all %d sherds, turned %.0f deg"
                 % (n_w, turn_w)),
                (gt_d, ids_d, "as it really is, %d sherds\n(one removed) -- "
                 "CORRECT answer with a hole" % n_d),
                (pr_d, ids_d, "model, %d sherds, turned %.0f deg\n"
                 "compare with the panel to its LEFT" % (n_d, turn_d)),
            ]):
                ax = axes[r][c]
                draw(ax, pts, ids, view, colour, lo, hi, pad)
                ax.set_title("%s %s\n%s" % (pot, vname, title), fontsize=7)

    fig.suptitle(
        "Whole pot against the same pot with one sherd removed\n"
        "same frame in every panel, nothing re-centred; the dropped arm is "
        "rescaled onto the reference so the two are comparable\n"
        "top row of each pair: silhouette -- does it close.  bottom row: one "
        "colour per sherd -- did the sherds it kept go to the right places\n"
        "COLUMN 4 IS READ AGAINST COLUMN 3, not column 1: with a sherd gone, "
        "the correct answer has a hole in it too",
        fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(a.out, dpi=130)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
