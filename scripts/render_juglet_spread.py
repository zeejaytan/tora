"""Draw the Juglet reference and the best and worst baseline draws side by side.

Ticket .scratch/juglet-cause/issues/01-run-to-run-spread.md asks whether the
run-to-run difference on this pot is a real difference between methods or the
scatter of a stochastic sampler. The arithmetic says scatter: twenty baseline
draws of the SAME model on the SAME pot span 35.4 to 88.9 degrees. This draws
the two ends of that span so the spread can be seen rather than believed, and
draws the ground truth once so the reference itself is confirmed by eye to be
an assembled vessel -- the check that no score can make for us.

Everything is drawn from the saved point clouds, orthographic, each panel
centred and scaled on its own so the comparison is of shape and not of size.
One colour per fragment, consistent across panels, so a sherd can be followed.

Usage:
  python scripts/render_juglet_spread.py --runs artifacts/juglet_runs \
      --out artifacts/juglet_spread.png
"""

import argparse
import glob
import os

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

COLOURS = ["#1f4e79", "#c1440e", "#4a7c59", "#7d5ba6", "#b8860b",
           "#2f6f7e", "#8b3a62", "#556b2f", "#a0522d"]


def panel(ax, pts, ids, title, axes):
    """One orthographic view. axes picks which two coordinates to plot."""
    p = pts - pts.mean(0)
    p = p / np.abs(p).max()
    i, j = axes
    for k, pid in enumerate(sorted(set(ids.tolist()))):
        m = ids == pid
        ax.scatter(p[m, i], p[m, j], s=0.6, c=COLOURS[k % len(COLOURS)],
                   linewidths=0, rasterized=True)
    ax.set_aspect("equal")
    ax.set_xlim(-1.05, 1.05)
    ax.set_ylim(-1.05, 1.05)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(title, fontsize=8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="artifacts/juglet_runs")
    ap.add_argument("--out", default="artifacts/juglet_spread.png")
    a = ap.parse_args()

    # Every baseline draw, on the corrected (non-anchor) turn.
    draws = []
    for d in sorted(glob.glob(os.path.join(a.runs, "*baseline*"))):
        npz = glob.glob(os.path.join(d, "clouds", "*.npz"))
        if not npz:
            continue
        for f in sorted(glob.glob(os.path.join(d, "results", "*.json"))):
            import json
            x = json.load(open(f))
            n = x["num_parts"]
            draws.append((x["rotation_error"] * n / (n - 1),
                          npz[0], x["generation_idx"], os.path.basename(d)))
    draws.sort()
    best, worst = draws[0], draws[-1]

    z = np.load(best[1])
    ids = z["part_ids"]

    fig, axs = plt.subplots(2, 3, figsize=(9.5, 6.6))
    for row, (ax_pair, vname) in enumerate((((0, 2), "side"), ((0, 1), "from above"))):
        panel(axs[row][0], z["pts_gt"], ids,
              "conservator's assembly (%s)" % vname, ax_pair)
        for col, (deg, f, gi, run) in ((1, best), (2, worst)):
            zz = np.load(f)
            panel(axs[row][col], zz["generations_pred"][gi], ids,
                  "%s draw, %.0f° (%s)" % (
                      "best" if col == 1 else "worst", deg, vname), ax_pair)

    fig.suptitle(
        "Same model, same pot: twenty baseline draws span %.1f° to %.1f°"
        % (draws[0][0], draws[-1][0]), fontsize=10)
    fig.text(0.5, 0.015,
             "best: %s draw %d   |   worst: %s draw %d   |   turn is the "
             "non-anchor mean over the eight free fragments"
             % (best[3], best[2], worst[3], worst[2]),
             ha="center", fontsize=7, color="#444")
    fig.tight_layout(rect=(0, 0.03, 1, 0.96))
    fig.savefig(a.out, dpi=170)
    print("wrote", a.out)

    # The silhouette survives at both ends of the spread, so the picture above
    # cannot separate 35 degrees from 89. Draw the measured quantity itself:
    # every draw, unbinned, grouped by the run it came from.
    import json
    runs = {}
    for d in sorted(glob.glob(os.path.join(a.runs, "*baseline*"))):
        v = []
        for f in sorted(glob.glob(os.path.join(d, "results", "*.json"))):
            x = json.load(open(f))
            v.append(x["rotation_error"] * x["num_parts"] / (x["num_parts"] - 1))
        if v:
            runs[os.path.basename(d)] = v

    fig2, ax = plt.subplots(figsize=(8.2, 3.4))
    for y, (name, v) in enumerate(runs.items()):
        ax.scatter(v, [y] * len(v), s=42, c="#1f4e79", zorder=3)
        med = float(np.median(v))
        ax.scatter([med], [y], s=150, marker="|", c="#c1440e", zorder=4)
        ax.text(92, y, "median %.1f" % med, va="center", fontsize=7, color="#c1440e")
    allv = [x for v in runs.values() for x in v]
    ax.axvspan(float(np.percentile(allv, 10)), float(np.percentile(allv, 90)),
               color="#1f4e79", alpha=0.07, zorder=0)
    ax.set_yticks(range(len(runs)))
    ax.set_yticklabels(list(runs), fontsize=7)
    ax.set_xlabel("how far the eight free fragments are turned from correct "
                  "(degrees, non-anchor mean)", fontsize=8)
    ax.set_xlim(25, 110)
    ax.set_title("Four runs of the same untrained-on-wear model, five draws each",
                 fontsize=9)
    fig2.tight_layout()
    out2 = a.out.replace(".png", "_draws.png")
    fig2.savefig(out2, dpi=170)
    print("wrote", out2)
    print("best  %.1f deg  %s draw %d" % (best[0], best[3], best[2]))
    print("worst %.1f deg  %s draw %d" % (worst[0], worst[3], worst[2]))


if __name__ == "__main__":
    main()
