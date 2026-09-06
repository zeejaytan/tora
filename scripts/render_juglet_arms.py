"""Draw the twenty-draw Juglet arms one SHERD at a time.

Ticket .scratch/juglet-cause/issues/06 asks for renders "at individual-sherd
placement, not whole-pot silhouette", because ticket 01 showed the outline of
this pot still reads as a pot at 89 degrees of average turn. A silhouette
therefore cannot separate a good draw from a bad one, and a picture that
answers the wrong question is as misleading as a statistic that does
(docs/lessons.md).

So: one panel per non-anchor sherd per arm. Every panel is drawn in the SAME
frame -- the conservator's own assembly -- and is NOT re-centred or re-scaled,
so a displacement is a displacement and not an artefact of the view. The whole
reference pot is drawn behind in pale grey for context, that sherd's correct
position in dark grey, and where the model put it in colour.

Per-sherd rotation is recomputed here from the geometry itself (Kabsch between
the sherd's correct points and its proposed points), not read from the run's
own summary, so the picture and its caption cannot disagree.

Fragment 0 is the anchor: it is handed to the model already seated and is
identical in every arm, so it is drawn once for reference and not compared.

Usage:
  python scripts/render_juglet_arms.py --runs artifacts/jugdraw \
      --job 30130049 --out artifacts/juglet_arms_sherds.png
"""

import argparse
import json
from pathlib import Path

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ARMS = ["baseline", "adapter_on", "adapter_off"]
VIEWS = [((0, 2), "side"), ((0, 1), "top")]
COLOUR = {"baseline": "#1f4e79", "adapter_on": "#c1440e", "adapter_off": "#4a7c59"}


def kabsch_deg(a, b):
    """Turn, in degrees, between two copies of the same sherd."""
    ac = a - a.mean(0)
    bc = b - b.mean(0)
    u, _, vt = np.linalg.svd(ac.T @ bc)
    d = np.sign(np.linalg.det(u @ vt))
    r = u @ np.diag([1.0, 1.0, d]) @ vt
    return float(np.degrees(np.arccos(np.clip((np.trace(r) - 1.0) / 2.0, -1.0, 1.0))))


def median_draw(run):
    """Index of the draw whose whole-pot turn is the median of the run."""
    files = sorted((run / "results").glob("*_generation*.json"))
    rot = [(json.loads(f.read_text())["rotation_error"], i) for i, f in enumerate(files)]
    rot.sort()
    return rot[len(rot) // 2][1], [r for r, _ in rot]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="artifacts/jugdraw")
    ap.add_argument("--job", default="30130049")
    ap.add_argument("--out", default="artifacts/juglet_arms_sherds.png")
    a = ap.parse_args()

    runs = {arm: Path(a.runs) / f"jugdraw_{arm}_{a.job}" for arm in ARMS}
    data, draw, span = {}, {}, {}
    for arm, run in runs.items():
        npz = next((run / "clouds").glob("*.npz"))
        data[arm] = np.load(npz)
        draw[arm], span[arm] = median_draw(run)

    gt = data["baseline"]["pts_gt"]
    ids = data["baseline"]["part_ids"]
    parts = sorted(set(ids.tolist()))
    lo, hi = gt.min(0), gt.max(0)
    pad = 0.06 * (hi - lo).max()

    nrow = len(parts) - 1
    ncol = len(ARMS) * len(VIEWS)
    fig, axes = plt.subplots(nrow, ncol, figsize=(2.0 * ncol, 2.0 * nrow))

    for r, pid in enumerate(parts[1:]):
        m = ids == pid
        for c, ((i, j), vname) in enumerate(VIEWS):
            for k, arm in enumerate(ARMS):
                ax = axes[r][c * len(ARMS) + k]
                prop = data[arm]["generations_proposed"][draw[arm]]
                ax.scatter(gt[:, i], gt[:, j], s=0.3, c="#dddddd",
                           linewidths=0, rasterized=True)
                ax.scatter(gt[m, i], gt[m, j], s=0.9, c="#555555",
                           linewidths=0, rasterized=True)
                ax.scatter(prop[m, i], prop[m, j], s=0.9, c=COLOUR[arm],
                           linewidths=0, rasterized=True)
                gc, pc = gt[m].mean(0), prop[m].mean(0)
                ax.annotate("", xy=(pc[i], pc[j]), xytext=(gc[i], gc[j]),
                            arrowprops=dict(arrowstyle="->", color="black", lw=0.8))
                deg = kabsch_deg(gt[m], prop[m])
                off = 100.0 * np.linalg.norm(pc - gc) / (hi - lo).max()
                ax.set_title("%s %s\nsherd %d: %.0f deg, %.0f%% off"
                             % (arm, vname, pid, deg, off), fontsize=6)
                ax.set_xlim(lo[i] - pad, hi[i] + pad)
                ax.set_ylim(lo[j] - pad, hi[j] + pad)
                ax.set_aspect("equal")
                ax.set_xticks([])
                ax.set_yticks([])

    fig.suptitle(
        "Juglet, job %s: where each sherd was actually put, median draw of 20\n"
        "pale grey = the whole pot as the conservator assembled it   dark grey = "
        "this sherd's correct place   colour = where the model put it\n"
        "same frame in every panel, nothing re-centred; sherd 0 is the given "
        "anchor and is not shown" % a.job, fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.955))
    fig.savefig(a.out, dpi=130)
    print("wrote", a.out)
    for arm in ARMS:
        print("%-12s median draw %2d of %d, whole-pot turn %.1f deg"
              % (arm, draw[arm], len(span[arm]), span[arm][len(span[arm]) // 2]))


if __name__ == "__main__":
    main()
