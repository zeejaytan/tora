"""Look at the objects either side of the solid-lump cut, at the cut.

`filter_lumps_from_splits.py` removed 714 of 1882 training examples on one
scalar, `fill_fraction < 0.65`. That number was validated across its whole
range by `render_fill_ladder.py`, but a ladder spanning 0.04 to 0.99 says
nothing about the one place this cut can actually be wrong: THE BOUNDARY.
Drawing a random sample of survivors would show obvious vases and prove
nothing -- the easy middle is not where a threshold fails.

So this renders the WORST SURVIVORS against the NARROWEST MISSES: the highest-
fill examples still in `train`, and the lowest-fill examples just dropped.

The first version showed only those two rows, and they looked alike -- which
read as a broken threshold until the distribution was plotted. It is not: fill
is BIMODAL, kept median 0.215 against dropped median 0.994, with almost nothing
between. Two boundary rows drawn out of an empty gap must look alike; that is
what an empty gap is. So the histogram is now part of the figure and a row of
TYPICAL kept objects sits above the boundary rows, because a picture of the
rarest 4% presented on its own answers a question nobody asked -- the same trap
as the four wear views in `docs/lessons.md`.

Sections use the median of three orthogonal cuts with every scanline's measured
interior shaded -- the same routine and the same honesty constraint as the
ladder figure, whose outline-only first version confirmed both ends and left
the middle unreadable (`docs/lessons.md`).

Usage:
  python scripts/check_lump_cut.py --src dataset/bbad_vessels_v3.hdf5 \
      --dataset bbad_vessels --out artifacts/lump_cut_boundary.png
"""

import argparse
import json
from pathlib import Path

import h5py
import numpy as np
import trimesh

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                   # noqa: E402

from measure_gap_as_network_sees import load_meshes               # noqa: E402
from screen_vessel_corpus import fill_fraction                    # noqa: E402
from render_fill_ladder import draw                               # noqa: E402


def decode(arr):
    return [v.decode() if isinstance(v, bytes) else str(v) for v in arr]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--dataset", default="bbad_vessels")
    ap.add_argument("--out", default="artifacts/lump_cut_boundary.png")
    ap.add_argument("--max-fill", type=float, default=0.65)
    ap.add_argument("--n", type=int, default=5)
    a = ap.parse_args()

    man = json.loads(Path(str(a.src) + ".manifest.json").read_text())

    with h5py.File(a.src, "r") as h:
        sgrp = h["data_split"][a.dataset]
        if "train_all" not in sgrp:
            raise SystemExit("no train_all -- run filter_lumps_from_splits.py first")
        kept = set(decode(sgrp["train"][:]))
        allm = decode(sgrp["train_all"][:])
        dropped = [m for m in allm if m not in kept]

        # Measure fill here the same way the filter does. Reading it from the
        # manifest instead ranked the panels by the stale corpus_screen value
        # and put an object at the top of "worst kept" that the filter had
        # already remeasured at 0.520 -- a figure sorted by a number other than
        # the one that made the decision illustrates nothing.
        cache = {}

        def fill_of(m):
            tag = m.split("/", 1)[1]
            if tag not in cache:
                asm = trimesh.util.concatenate(load_meshes(h[a.dataset][tag]))
                v = fill_fraction(asm)
                cache[tag] = np.nan if v is None else float(v)
            return cache[tag]

        print(f"measuring fill on {len(allm)} examples ...", flush=True)
        for m in allm:
            fill_of(m)

        def shape_of(m):
            return "__".join(m.split("/", 1)[1].split("__")[:2])

        def pick(members, reverse):
            """One example per SHAPE.

            fill is a property of the shape, so the raw ordering returns the
            same pot twice under two wear levels and a five-panel row shows
            three objects. Deduplicating is the difference between five
            independent checks and three.
            """
            out, seen = [], set()
            for m in sorted(members, key=fill_of, reverse=reverse):
                if shape_of(m) in seen:
                    continue
                seen.add(shape_of(m))
                out.append(m)
                if len(out) == a.n:
                    break
            return out

        def pick_near(members, target):
            """n shapes whose fill sits closest to `target`."""
            out, seen = [], set()
            for m in sorted(members, key=lambda m_: abs(fill_of(m_) - target)):
                if shape_of(m) in seen:
                    continue
                seen.add(shape_of(m))
                out.append(m)
                if len(out) == a.n:
                    break
            return sorted(out, key=fill_of)

        # worst survivors: highest fill still in; narrowest misses: lowest out
        top_kept = pick(kept, True)
        low_drop = pick(dropped, False)

        typical = pick_near(kept, float(np.median([fill_of(m) for m in kept])))
        rows = [(typical, "TYPICAL KEPT", "#2a7"),
                (top_kept, "WORST KEPT", "#2a7"),
                (low_drop, "MILDEST DROPPED", "#b33")]

        fig = plt.figure(figsize=(3.4 * a.n, 3.1 * len(rows) + 3.0))
        gs = fig.add_gridspec(len(rows) + 1, a.n,
                              height_ratios=[1.15] + [1.0] * len(rows))

        # The measured quantity itself, every example, before any panel.
        hax = fig.add_subplot(gs[0, :])
        fk = [fill_of(m) for m in kept]
        fd = [fill_of(m) for m in dropped]
        bins = np.linspace(0, 1, 101)
        hax.hist(fk, bins=bins, color="#2a7", alpha=0.85,
                 label=f"kept, n={len(fk)} (median {np.median(fk):.3f})")
        hax.hist(fd, bins=bins, color="#b33", alpha=0.85,
                 label=f"dropped, n={len(fd)} (median {np.median(fd):.3f})")
        hax.axvline(a.max_fill, color="k", lw=1.6, ls="--",
                    label=f"the cut, fill = {a.max_fill}")
        hax.set_xlabel("section fill: the fraction of each scanline that is "
                       "solid, median of three orthogonal cuts")
        hax.set_ylabel("training examples")
        hax.legend(fontsize=9)
        hax.set_title("The cut falls in a gap the data barely occupies -- "
                      "which is why the two boundary rows below look alike",
                      fontsize=10)

        for r, (members, label, colour) in enumerate(rows):
            for col, full in enumerate(members):
                ax = fig.add_subplot(gs[r + 1, col])
                tag = full.split("/", 1)[1]
                rec = man[tag]
                meshes = load_meshes(h[a.dataset][tag])
                asm = trimesh.util.concatenate(meshes)
                cells = rec.get("cells_through_wall")
                old_f = rec.get("fill_fraction")
                title = (f"{label}  {tag.split('__')[0]} "
                         f"{tag.split('__')[1][:8]}\n"
                         f"fill {fill_of(full):.3f}"
                         + (f"   (csv said {float(old_f):.3f})"
                            if old_f is not None else "")
                         + (f"   cells {cells:.2f}" if cells is not None else ""))
                draw(ax, asm, title)
                for sp in ax.spines.values():
                    sp.set_edgecolor(colour)
                    sp.set_linewidth(2.0)

    fig.suptitle(
        f"Removing the solid lumps (fill < {a.max_fill}): the distribution, "
        f"then the objects on each side of the line.\n"
        f"Row 1 typical kept, row 2 the least hollow still kept, row 3 the "
        f"mildest dropped.  Pink = each scanline's measured interior.",
        fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.955])
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=130)
    print("wrote", out)

    print("\nkept, highest fill:")
    for m in top_kept:
        print(f"  {fill_of(m):.3f}  {m.split('/', 1)[1]}")
    print("dropped, lowest fill:")
    for m in low_drop:
        print(f"  {fill_of(m):.3f}  {m.split('/', 1)[1]}")


if __name__ == "__main__":
    main()
