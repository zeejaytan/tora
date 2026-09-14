"""The true pot, the model's raw output, and its rigid assembly, side by side.

Ticket .scratch/juglet-cause/issues/12. The raw output lets every point move on its
own, so it can form a convincing vessel out of bent sherds; the rigid assembly is
the same attempt with each sherd forced back to its real shape. The numbers from
`measure_nonrigid_cheating.py` say how far apart the two are. This shows it,
because a number alone has misled this project before.

Four columns per row: the true pot (sherd numbers written at their centres), the
raw output, the rigid assembly -- one colour per sherd, consistent across the row
-- and the raw output coloured by how far each point was bent. Every panel in a
row shares the TRUE object's box: nothing is re-centred or re-scaled, so a sherd
that moved is seen to move. Drawing conventions follow render_juglet_vs_fresh.py
(orthographic side and top views, one colour per sherd, nothing re-centred).

Scale check: each panel is ~2.9 in at 150 dpi, about 3.8 px per 1% of pot size,
so a bend of a few % of pot size is several pixels. Points sit ~1.8% of pot size
apart; a bend below that cannot be seen and is not claimed.

Usage:
  python scripts/render_shape_before_rigid.py \
      --case "Juglet baseline"=artifacts/jugdraw/jugdraw_baseline_30130049/clouds/juglet_gt_sample00000.npz:median \
      --case "Juglet baseline"=...:worst \
      --case "blue_pot (control)"=artifacts/nb3/whole/ceramics_sample00001.npz:median \
      --out artifacts/shape12/shape_before_rigid.png
"""

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from measure_nonrigid_cheating import (  # noqa: E402
    load_object, measure_draw, mirror_flags, rank_draws,
)
from readout import unit_box_scale  # noqa: E402

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

VIEWS = [((0, 2), "side"), ((0, 1), "top")]
BEND_MAX = 10.0          # colour scale top, % of pot size


def parse_case(s: str):
    label, rest = s.split("=", 1)
    path, _, which = rest.rpartition(":")
    if not path or not (which in ("median", "worst") or which.isdigit()):
        path, which = rest, "median"
    return label, path, which


def sherd_panel(ax, pts, ids, parts, view, lo, hi, pad, label_ids=False):
    i, j = view
    cmap = plt.get_cmap("tab10")
    for k, pid in enumerate(parts):
        m = ids == pid
        ax.scatter(pts[m, i], pts[m, j], s=0.8, color=cmap(k % 10),
                   linewidths=0, rasterized=True)
        if label_ids:
            c = pts[m].mean(0)
            ax.text(c[i], c[j], str(pid), fontsize=7, ha="center", va="center",
                    color="black", weight="bold",
                    bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.7))
    frame(ax, view, lo, hi, pad)


def frame(ax, view, lo, hi, pad):
    i, j = view
    ax.set_xlim(lo[i] - pad, hi[i] + pad)
    ax.set_ylim(lo[j] - pad, hi[j] + pad)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--case", action="append", required=True,
                    help='LABEL=path.npz[:median|worst|<draw>]')
    ap.add_argument("--out", default="artifacts/shape12/shape_before_rigid.png")
    a = ap.parse_args()

    cases = [parse_case(s) for s in a.case]
    nrow = len(cases) * len(VIEWS)
    fig, axes = plt.subplots(nrow, 4, figsize=(4 * 2.9, nrow * 2.9), squeeze=False,
                             layout="constrained")
    sc = None

    for ci, (label, path, which) in enumerate(cases):
        obj = load_object(path)
        gt, ids = obj["gt"], obj["ids"]
        per = [measure_draw(gt, obj["pred"][k], obj["prop"][k], ids)
               for k in range(len(obj["pred"]))]
        med, worst = rank_draws(per)
        _, flags = mirror_flags(per)
        k = med if which == "median" else worst if which == "worst" else int(which)
        tag = {med: "median draw", worst: "worst draw"}.get(k, "draw")
        p = per[k]
        pred, prop = obj["pred"][k], obj["prop"][k]
        parts = p["parts"]
        lo, hi = gt.min(0), gt.max(0)
        pad = 0.06 * unit_box_scale(gt)
        unit = unit_box_scale(gt)
        n_free = len(parts) - 1

        for vi, (view, vname) in enumerate(VIEWS):
            row = axes[ci * len(VIEWS) + vi]
            sherd_panel(row[0], gt, ids, parts, view, lo, hi, pad, label_ids=True)
            sherd_panel(row[1], pred, ids, parts, view, lo, hi, pad)
            sherd_panel(row[2], prop, ids, parts, view, lo, hi, pad)
            i, j = view
            sc = row[3].scatter(pred[:, i], pred[:, j], s=0.8, c=p["bend_point"],
                                cmap="magma_r", vmin=0, vmax=BEND_MAX,
                                linewidths=0, rasterized=True)
            # Name every free sherd where the raw output put it; M = it came out as the
            # mirror image of the real sherd (not bent: no solid turn can match it).
            for s, kind in flags[k].items():
                c = pred[ids == s].mean(0)
                row[3].text(c[i], c[j], f"{s}M" if kind == "mirror" else
                            f"{s}?" if kind == "deformed" else str(s),
                            fontsize=7, ha="center", va="center", weight="bold",
                            color="tab:blue" if kind == "mirror" else "black",
                            bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none",
                                      alpha=0.7))
            frame(row[3], view, lo, hi, pad)
            if vi == 0:
                row[0].set_title(f"{label}, {tag} {k} ({vname})\nas it really is; "
                                 f"sherd {p['anchor']} is pinned", fontsize=7)
                row[1].set_title(f"raw output ({vname})\noutline {p['raw_outline']:.1f}%, "
                                 f"own place {p['raw_own_mean']:.1f}%, "
                                 f"{p['raw_seated']}/{n_free} seated", fontsize=7)
                row[2].set_title(f"rigid assembly ({vname})\noutline "
                                 f"{p['rigid_outline']:.1f}%, own place "
                                 f"{p['rigid_own_mean']:.1f}%, {p['rigid_seated']}/{n_free} "
                                 f"seated", fontsize=7)
                row[3].set_title(f"raw, by bending ({vname}); M = mirror\n"
                                 f"mean {p['bend_mean']:.1f}%, worst sherd "
                                 f"{p['bend_worst']:.1f}% of pot size", fontsize=7)
            else:
                for c, t in enumerate(("as it really is", "raw output", "rigid assembly",
                                       "raw, by bending")):
                    row[c].set_title(f"{t} ({vname})", fontsize=7)
        print(f"{label}: draw {k} ({tag}); pot size {unit:.4f} model units")

    cb = fig.colorbar(sc, ax=axes, location="bottom", shrink=0.4, aspect=40)
    cb.set_label("how far the raw point sits from its sherd's rigid placement "
                 f"(% of pot size; capped at {BEND_MAX:.0f})", fontsize=7)
    fig.suptitle(
        "Does the model have the pot's shape before its sherds are made rigid?\n"
        "One colour per sherd, consistent across each row; every panel in a row "
        "uses the true pot's box, nothing re-centred.\n"
        "Numbers are free sherds only, % of pot size: outline = distance to the true "
        "surface ignoring which sherd; own place = each sherd to its own home.\n"
        "Last column: sherd numbers at their raw position; blue 'M' = the sherd came out "
        "as its own mirror image (no solid turn matches it).",
        fontsize=9)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.out, dpi=150, bbox_inches="tight")
    print("wrote", a.out)


if __name__ == "__main__":
    main()
