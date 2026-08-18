"""Draw every held-out object's reassembly beside its correct answer.

The conservator asked for the Juglet treatment applied to the rest, and it is
the right check: the claim under test is mine. I said a fragment turned thirty
degrees "is not a reassembly, it is a rough sorting", and whether that is true
is a judgement about pottery, not about arithmetic. It should be made by looking.

THE CASES THAT DECIDE IT, from the metric audit:

  blue_pot   scored 1.000 -- every fragment "correctly placed" -- while turned
             19 degrees on average with NONE within ten. If this looks
             reassembled, the threshold is kinder than I claimed and the fault
             is in my reading. If it looks wrong, the measure is broken.

  limb3      the baseline manages 10.2 degrees and a third of fragments within
             ten; wear training pushes it to 30 degrees and none. This is where
             the precision loss should be visible, if it is real.

  plate      the reverse: baseline 49 degrees, wear_v2 18. Where wear training
             should visibly help.

Drawn from the saved clouds directly -- `pts_gt` against
`generations_proposed`, which are the input parts rigidly posed by the predicted
transform, i.e. the actual proposal rather than the raw network output. Each
fragment keeps its own colour across every panel so a piece can be followed.

The FIRST attempt is shown for every object, never the best of five. Choosing
the best per object would flatter whichever model got lucky, and the audit
already reports best-of-n separately.

Usage:
  python scripts/render_assembly_grid.py \
      --runs baseline=/path/clouds wear_v2=/path/clouds --out grid.png
"""

import argparse
from pathlib import Path

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

COLOURS = ["#1f4e79", "#c1440e", "#4a7c59", "#7d5ba6", "#b8860b",
           "#2f6f7e", "#8b3a62", "#556b2f", "#a0522d", "#4682b4",
           "#8b0000", "#2e8b57"]


def parts_of(pts, part_ids):
    return [pts[part_ids == p] for p in sorted(np.unique(part_ids))]


def normalise(parts):
    allv = np.concatenate(parts, axis=0)
    c = allv.mean(axis=0)
    s = float(np.abs(allv - c).max()) + 1e-12
    return [(p - c) / s for p in parts]


def draw(ax, parts, ij, title, sub=""):
    i, j = ij
    for k, p in enumerate(parts):
        ax.scatter(p[:, i], p[:, j], s=1.2, alpha=0.55, linewidths=0,
                   color=COLOURS[k % len(COLOURS)])
    ax.set_aspect("equal")
    ax.set_xlim(-1.15, 1.15)
    ax.set_ylim(-1.15, 1.15)
    ax.set_xticks([])
    ax.set_yticks([])
    if title:
        ax.set_title(title, fontsize=8.5)
    if sub:
        ax.text(0.5, -0.06, sub, transform=ax.transAxes, ha="center",
                va="top", fontsize=7.5, color="0.3")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", nargs="+", required=True,
                    help="label=/path/to/clouds")
    ap.add_argument("--attempt", type=int, default=0)
    ap.add_argument("--match", default="",
                    help="only objects whose name contains this, so a 30-object "
                         "sweep can be split into figures that can actually be "
                         "read rather than one strip 22000 pixels tall")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    runs = {}
    for spec in args.runs:
        label, path = spec.split("=", 1)
        runs[label] = Path(path)

    # objects present in every run, so the comparison is like for like
    common = None
    index = {}
    for label, d in runs.items():
        here = {}
        for f in sorted(d.glob("*.npz")):
            z = np.load(f, allow_pickle=True)
            name = str(z["name"]) if "name" in z else f.stem
            here[name.split("/")[-1]] = f
        index[label] = here
        common = set(here) if common is None else (common & set(here))
    objs = sorted(o for o in (common or []) if args.match in o)
    print(f"{len(objs)} objects in every run: {', '.join(objs)}")
    if not objs:
        return

    labels = list(runs)
    ncol = 1 + len(labels)
    fig, axes = plt.subplots(2 * len(objs), ncol,
                             figsize=(3.0 * ncol, 2.9 * 2 * len(objs)))
    axes = np.atleast_2d(axes)

    for r, obj in enumerate(objs):
        f0 = index[labels[0]][obj]
        z0 = np.load(f0, allow_pickle=True)
        pid = z0["part_ids"]
        gt = normalise(parts_of(z0["pts_gt"], pid))
        for v, ij in enumerate([(0, 1), (0, 2)]):
            draw(axes[2 * r + v, 0], gt, ij,
                 f"{obj}\nCORRECT" if v == 0 else "",
                 "front" if v == 0 else "from above")
        for c, label in enumerate(labels):
            f = index[label][obj]
            z = np.load(f, allow_pickle=True)
            key = ("generations_proposed" if "generations_proposed" in z
                   else "generations_pred")
            gen = z[key][min(args.attempt, len(z[key]) - 1)]
            parts = normalise(parts_of(gen, z["part_ids"]))
            for v, ij in enumerate([(0, 1), (0, 2)]):
                draw(axes[2 * r + v, 1 + c], parts, ij,
                     label if v == 0 else "")

    fig.suptitle(
        "Every held-out object: the correct assembly against what the models "
        "propose\n"
        "first attempt shown for each, never the best of five; each fragment "
        "keeps its colour across panels",
        fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.975))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=130)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
