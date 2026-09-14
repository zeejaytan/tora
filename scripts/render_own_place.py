"""Draw one Juglet attempt with every sherd coloured by where it landed.

Ticket `.scratch/u10-juglet-ceiling/issues/01`. `own_place.py` says the untouched
model puts about 3 of the Juglet's 9 sherds in their own place, while the
evaluator's count, which lets look-alikes swap, says 5 to 6. That gap is a claim
about geometry, so it is looked at before it is reported (workspace AGENTS.md).

WHAT THE FIGURE HAS TO RESOLVE. Whether a sherd is in ITS place, in another
sherd's place, or nowhere. Shape alone cannot show that -- a pot made of the wrong
sherds can look right -- so every sherd carries its number: in the true pot at
its home, in the answer where it landed. A sherd seated in another's place names
whose place it took ("4>5"). Colour is the verdict: green own place, amber seated
in another sherd's place, red off. The true pot is drawn faintly behind every
answer, in the pot's own frame, never re-centred. The tolerance (7.1% of pot
size, 4.6 mm on the Juglet) is about 30 pixels at this size, so a sherd off by
it is visibly off.

Usage:
  python scripts/render_own_place.py --run artifacts/jugdraw/jugdraw_baseline_30130049 \
      --pot-mm 65 --out artifacts/u10/own_place_baseline_median.png
"""

import argparse
import sys
import textwrap
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from own_place import SEAT_PCT, median, score_draw  # noqa: E402
from readout import cloud_for, part_slices  # noqa: E402

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

VIEWS = [((0, 2), "side"), ((1, 2), "side, turned a quarter"), ((0, 1), "from above")]
VERDICT = {"own": "#2a9d4b", "swapped": "#e09f1f", "off": "#d1495b"}
FAINT = "#dcdcdc"


def pick(draws) -> int:
    """The middle attempt, ranked on own place, then swap-allowed, then how far off."""
    order = sorted(range(len(draws)),
                   key=lambda k: (draws[k].own, draws[k].swap, median(draws[k].off_pct)))
    return order[len(order) // 2]


def tag(d, s: int) -> str:
    return f"{s}>{d.placed_in[s]}" if d is not None and d.status[s] == "swapped" else str(s)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", type=Path, required=True)
    ap.add_argument("--pot", default=None)
    ap.add_argument("--draw", type=int, default=None, help="default: the middle attempt")
    ap.add_argument("--pot-mm", type=float, default=None)
    ap.add_argument("--out", default="artifacts/u10/own_place_median.png")
    a = ap.parse_args()

    with np.load(cloud_for(a.run, a.pot), allow_pickle=True) as d:
        gt, ppp, name = d["pts_gt"], d["points_per_part"], str(d["name"])
        pred, prop = d["generations_pred"], d["generations_proposed"]
    slices = part_slices(ppp)
    raw = [score_draw(gt, g, ppp) for g in pred]
    solid = [score_draw(gt, g, ppp) for g in prop]
    k = a.draw if a.draw is not None else pick(raw)

    rows = [
        (gt, None, "As it really is\n(the conservator's\nreassembly)"),
        (pred[k], raw[k], f"Raw output,\nattempt {k}\n(what the evaluator\nscores)"),
        (prop[k], solid[k], f"Solid sherds,\nattempt {k}\n(each true sherd\nrigidly placed)"),
    ]
    lo, hi = gt.min(0), gt.max(0)
    pad = 0.08 * (hi - lo).max()
    cmap = plt.get_cmap("tab10")

    fig, axes = plt.subplots(len(rows), len(VIEWS), figsize=(11, 12), squeeze=False)
    for r, (pts, dr, label) in enumerate(rows):
        for c, ((i, j), vname) in enumerate(VIEWS):
            ax = axes[r][c]
            if dr is not None:
                ax.scatter(gt[:, i], gt[:, j], s=0.6, color=FAINT, linewidths=0,
                           rasterized=True)
            for s, (p0, p1) in enumerate(slices):
                col = cmap(s % 10) if dr is None else VERDICT[dr.status[s]]
                ax.scatter(pts[p0:p1, i], pts[p0:p1, j], s=0.9, color=col,
                           linewidths=0, rasterized=True)
            for s, (p0, p1) in enumerate(slices):
                ax.text(pts[p0:p1, i].mean(), pts[p0:p1, j].mean(), tag(dr, s),
                        fontsize=7, ha="center", va="center", weight="bold",
                        bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none",
                                  alpha=0.75))
            ax.set_xlim(lo[i] - pad, hi[i] + pad)
            ax.set_ylim(lo[j] - pad, hi[j] + pad)
            ax.set_aspect("equal")
            ax.set_xticks([])
            ax.set_yticks([])
            if r == 0:
                ax.set_title(vname, fontsize=9)
            if c == 0:
                ax.set_ylabel(label, fontsize=8)

    mmtxt = (f", about {SEAT_PCT * a.pot_mm / 100:.1f} mm on this {a.pot_mm:g} mm pot"
             if a.pot_mm else "")
    anchor = raw[k].anchor
    cap = "\n".join(textwrap.fill(t, 120) for t in [
        f"{name.split('/')[-1]}: attempt {k} of {len(raw)}, the middle one ranked on "
        "sherds in their own place.",
        "Green: in its own place. Amber: seated, but in another sherd's place "
        "('4>5' = sherd 4 sits where sherd 5 belongs). Red: not seated anywhere. "
        "Faint grey: the true pot.",
        f"Raw output: {raw[k].own} of {raw[k].n} in their own place, {raw[k].swap} by "
        f"the evaluator's count. Solid sherds: {solid[k].own} and {solid[k].swap}. "
        f"Sherd {anchor} is the anchor, pinned at home; it is one of the green.",
        f"Seated = within {SEAT_PCT:.1f}% of pot size of home{mmtxt}.",
    ])
    fig.suptitle(cap, fontsize=8.5)
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.out, dpi=170)
    print("wrote", a.out)
    for lab, dr in (("raw", raw[k]), ("solid", solid[k])):
        print(f"  {lab}: own {dr.own}, swap {dr.swap}, status {dr.status}, "
              f"placed_in {dr.placed_in}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
