"""Draw the `narrow_bottle3` collapse: is it a mis-placement or a mix-up?

Ticket `.scratch/juglet-cause/issues/07`. `scripts/check_identity_swap.py` says
the model exchanges two sherds of this bottle rather than scattering them, and
says it in all ten draws. That is a claim about geometry, so it does not get
reported until it has been looked at (workspace `AGENTS.md`, "look at it before
trusting the numbers").

WHAT THE FIGURE HAS TO RESOLVE. The scale being tested is a two-sherd exchange,
not a general looseness, so the view has to make identity visible rather than
just shape. Every panel therefore colours the SAME sherds the same way, and the
two flaps under suspicion are drawn in strong colour against everything else in
grey. A swap then shows up as the strong colours trading places between the
reference row and the model's row -- something no amount of "the silhouette
still reads as a bottle" can hide.

The third row is the key one and it moves no geometry at all. It is the model's
own answer, exactly the points drawn in row 2, recoloured by which ground-truth
sherd each predicted piece actually landed on (the assignment
`check_identity_swap.py` computes). If rows 1 and 3 agree spatially while row 2
disagrees, then the pieces are in roughly the right places wearing the wrong
names, and the failure is a mix-up, not a collapse.

Usage:
  python scripts/render_identity_swap.py --clouds artifacts/nb3/whole \
      --out artifacts/nb3/narrow_bottle3_identity_swap.png
"""

import argparse
import textwrap
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_identity_swap import cost_matrix, pct  # noqa: E402
from readout import unit_box_scale  # noqa: E402
from scipy.optimize import linear_sum_assignment  # noqa: E402

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

VIEWS = [((0, 2), "side"), ((0, 1), "from above")]

# The two flaps of `narrow_bottle3` that the assignment says change places, and
# a colour each. Everything else in the pot is drawn grey so the eye is not
# asked to track four colours at once.
HILITE = {0: "#d1495b", 3: "#2e6f95"}
GREY = "#c9c9c9"


def load(clouds_dir: Path, pot: str):
    for f in sorted(Path(clouds_dir).glob("*.npz")):
        d = np.load(f, allow_pickle=True)
        if str(d["name"]).split("/")[-1] == pot:
            return d
    raise SystemExit(f"{pot} not found under {clouds_dir}")


def colours(ids, mapping, palette=None):
    """mapping: predicted-sherd-id -> the sherd id whose colour it should take.

    `palette` overrides the two-flap highlight. A pot that is SCATTERED has no
    pair to point at, so every sherd needs its own colour or the eye cannot
    follow where any of them went; `--hilite all` builds that palette.
    """
    pal = HILITE if palette is None else palette
    return np.array([pal.get(mapping.get(int(p), int(p)), GREY) for p in ids])


def draw(ax, pts, cols, view, lo, hi, pad):
    i, j = view
    # grey first so the two flaps are never buried under the rest of the pot
    back = cols == GREY
    ax.scatter(pts[back, i], pts[back, j], s=0.7, color=GREY, linewidths=0,
               rasterized=True)
    ax.scatter(pts[~back, i], pts[~back, j], s=0.9, c=cols[~back], linewidths=0,
               rasterized=True)
    ax.set_xlim(lo[i] - pad, hi[i] + pad)
    ax.set_ylim(lo[j] - pad, hi[j] + pad)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])


def family(clouds_dir: Path, pots, out: str) -> int:
    """Do the sibling bottles fail the same way? The ticket asks; this answers it.

    `narrow_bottle1/2/3/4` share the form -- elongated, thin-walled, roughly
    symmetric about the long axis -- but sit at wildly different scores. If the
    exchange were caused by the FORM, all four should show it. Each pot gets its
    true assembly above the model's answer, every sherd its own colour, so a
    correct assembly, an exchange and a scattering are told apart by eye.
    """
    rng = np.random.default_rng(0)
    fig, axes = plt.subplots(2, len(pots), figsize=(len(pots) * 2.7, 6.2),
                             squeeze=False)
    caps = []
    for c, pot in enumerate(pots):
        d = load(Path(clouds_dir), pot)
        gt, ids, props = d["pts_gt"], d["part_ids"], d["generations_proposed"]
        parts = sorted(set(ids.tolist()))
        unit = unit_box_scale(gt)
        anchor = max(parts, key=lambda p: int((ids == p).sum()))
        mats = [cost_matrix(gt, props[k], ids, parts, unit, rng)
                for k in range(len(props))]
        worst = [max(pct(C[i, i]) for i, p in enumerate(parts) if p != anchor)
                 for C in mats]
        k = sorted(range(len(props)), key=lambda t: worst[t])[len(props) // 2]
        C = mats[k]
        _, best = linear_sum_assignment(C)
        wb = max(pct(C[i, best[i]]) for i, p in enumerate(parts) if p != anchor)
        # how often the SAME assignment recurs: a real exchange repeats, a
        # scattering picks a different permutation every time
        perms = {}
        for t in range(len(props)):
            _, b = linear_sum_assignment(mats[t])
            perms[tuple(int(x) for x in b)] = perms.get(tuple(int(x) for x in b), 0) + 1
        top = max(perms.values())
        ident_wins = tuple(range(len(parts))) in perms

        lo, hi = gt.min(0), gt.max(0)
        pad = 0.06 * (hi - lo).max()
        cmap = plt.get_cmap("tab20")
        for r, pts in enumerate([gt, props[k]]):
            ax = axes[r][c]
            for m, pid in enumerate(parts):
                sel = ids == pid
                ax.scatter(pts[sel, 0], pts[sel, 2], s=0.7, color=cmap(m % 20),
                           linewidths=0, rasterized=True)
            ax.set_xlim(lo[0] - pad, hi[0] + pad)
            ax.set_ylim(lo[2] - pad, hi[2] + pad)
            ax.set_aspect("equal")
            ax.set_xticks([])
            ax.set_yticks([])
            if r == 0:
                ax.set_title(f"{pot}\n{len(parts)} sherds, as it really is", fontsize=7)
            else:
                ax.set_title(f"model's answer: worst sherd {worst[k]:.1f}%\n"
                             f"best renaming {wb:.1f}%, same renaming {top}/10",
                             fontsize=7)
        verdict = ("assembled correctly" if worst[k] < 5 else
                   "ONE EXCHANGE, every attempt" if top == len(props) and not ident_wins
                   else "scattered, no repeated pattern")
        caps.append(f"{pot}: {verdict}")

    fig.suptitle("\n".join(textwrap.fill(t, 100) for t in [
        "Four bottles of the same shape, four different outcomes -- so the shape "
        "alone is not what breaks narrow_bottle3.",
        "'worst sherd' is how far the worst loose piece sits from home, as a "
        "percent of the pot's own size; 2-3% is a correct assembly.",
        "'best renaming' is what that becomes if the pieces are allowed to swap "
        "names; 'same renaming N/10' is how many of the ten attempts agree on it.",
        "   ".join(caps),
    ]), fontsize=8.5)
    fig.tight_layout(rect=(0, 0, 1, 0.84))
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=190)
    print("wrote", out)
    for t in caps:
        print("  ", t)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--clouds", required=True)
    ap.add_argument("--pot", default="narrow_bottle3")
    ap.add_argument("--draw", type=int, default=None,
                    help="which of the 10 attempts; default = the median one")
    ap.add_argument("--family", nargs="+", default=None,
                    help="instead: draw these pots side by side, true vs answer")
    ap.add_argument("--hilite", default="0,3",
                    help="sherds to colour, rest grey; 'all' gives every sherd "
                         "its own colour (use when the pot is scattered, not swapped)")
    ap.add_argument("--caption", default=None,
                    help="override the first caption line")
    ap.add_argument("--out", default="artifacts/nb3/narrow_bottle3_identity_swap.png")
    a = ap.parse_args()

    if a.family:
        return family(Path(a.clouds), a.family, a.out)

    d = load(Path(a.clouds), a.pot)
    gt, ids, props = d["pts_gt"], d["part_ids"], d["generations_proposed"]
    parts = sorted(set(ids.tolist()))
    unit = unit_box_scale(gt)
    anchor = max(parts, key=lambda p: int((ids == p).sum()))
    rng = np.random.default_rng(0)

    # Rank the attempts the way the evaluator does and take the median, so this
    # is a typical answer rather than the best one the model managed.
    mats = [cost_matrix(gt, props[k], ids, parts, unit, rng) for k in range(len(props))]
    worst = [max(pct(C[i, i]) for i, p in enumerate(parts) if p != anchor) for C in mats]
    k = a.draw if a.draw is not None else sorted(range(len(props)), key=lambda t: worst[t])[len(props) // 2]

    C = mats[k]
    _, best = linear_sum_assignment(C)
    # predicted sherd j landed on ground-truth sherd `landed[j]`
    landed = {int(parts[int(best[i])]): int(parts[i]) for i in range(len(parts))}
    w_id = worst[k]
    w_best = max(pct(C[i, best[i]]) for i, p in enumerate(parts) if p != anchor)

    prop = props[k]
    lo, hi = gt.min(0), gt.max(0)
    pad = 0.06 * (hi - lo).max()

    if a.hilite == "all":
        cmap = plt.get_cmap("tab20")
        palette = {int(p): matplotlib.colors.to_hex(cmap(i % 20))
                   for i, p in enumerate(parts)}
    else:
        want = {int(x) for x in a.hilite.split(",") if x.strip() != ""}
        palette = {k: v for k, v in HILITE.items() if k in want}

    ident = {p: p for p in parts}
    rows = [
        (gt, ident, "The bottle\nas it really is"),
        (prop, ident, "The model's answer,\ncoloured by the name\nthe MODEL gave each piece"),
        (prop, landed, "The same answer, recoloured\nby the place each piece\nactually landed in"),
    ]

    fig, axes = plt.subplots(len(rows), len(VIEWS),
                             figsize=(len(VIEWS) * 2.9 + 1.2, len(rows) * 3.0),
                             squeeze=False)
    for r, (pts, mapping, label) in enumerate(rows):
        for c, (view, vname) in enumerate(VIEWS):
            ax = axes[r][c]
            draw(ax, pts, colours(ids, mapping, palette), view, lo, hi, pad)
            if r == 0:
                ax.set_title(vname, fontsize=9)
            if c == 0:
                ax.set_ylabel(label, fontsize=8)

    cap = "\n".join(textwrap.fill(line, 84) for line in [
        a.caption or f"{a.pot}: the two flaps change places -- and the bottle "
                     "still does not close.",
        ("One colour per sherd." if a.hilite == "all" else
         "Red is sherd 0, blue is sherd 3, grey is the rest.") +
        f" Attempt {k} of {len(props)}, the median one.",
        "Row 3 is row 2 recoloured, not re-placed: if the pieces were merely "
        "mis-named it would look like row 1.",
        f"Worst loose sherd as scored: {w_id:.1f}% of the pot's size from home. With "
        f"the names exchanged: {w_best:.1f}%. A correctly assembled pot here is 2-3%.",
    ])
    fig.suptitle(cap, fontsize=8.5)
    fig.tight_layout(rect=(0, 0, 1, 0.87))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.out, dpi=190)
    print("wrote", a.out)
    print(f"  attempt {k}; worst loose sherd {w_id:.2f}% as scored, "
          f"{w_best:.2f}% after the swap")
    print("  predicted sherd -> ground-truth sherd it landed on:", landed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
