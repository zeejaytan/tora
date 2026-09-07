"""Look at the seam before believing the seam number.

Reads what `scripts/check_seam_swap.py` measured and draws it. Rows 1-2 are the
true bottle and the best swapped bottle that exists -- the one where both flaps
have been freed to shuffle until the joins close as far as they ever will, so
the swap is being judged at its best rather than at its first guess.

The third column and the bottom panel are THE MEASURED QUANTITY ITSELF: every
break-surface vertex drawn at its own position with its own gap, and then the
same numbers as unbinned cumulative curves. A summary statistic can hide a seam
that presses shut in one place while gaping in another, and on this bottle that
is exactly what the swap does -- so the distribution has to be shown, not a
median. The scan's own vertex spacing is marked, because a gap below it is not a
gap, it is the sampling interval (that is what made the 5000-point eval clouds
useless for this question).

Usage:
  python scripts/render_seam_swap.py --mesh artifacts/nb3seam/nb3_mesh_vertices.npz \
      --seam artifacts/nb3seam/nb3_seam.npz \
      --out artifacts/nb3seam/narrow_bottle3_seam_swap.png
"""

import argparse
import textwrap

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

GREY = "#c9c9c9"
FLAPCOL = ["#d1495b", "#2e6f95"]
OTHER = ["#c9c9c9", "#edae49"]
STEP = 12          # whole-pot views only; the seam panels draw every vertex


def arrangement(V, z, name):
    return {k: V[k] @ z[f"pose_{name}_{k}_R"].T + z[f"pose_{name}_{k}_t"]
            for k in V}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mesh", required=True)
    ap.add_argument("--seam", required=True)
    ap.add_argument("--spacing", type=float, default=0.22,
                    help="the scan's own vertex spacing, %% of object size")
    ap.add_argument("--caption", default="")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    m = np.load(a.mesh)
    V = {int(k[1:]): m[k].astype(np.float64) for k in m.files}
    z = np.load(a.seam)
    A, B = (int(x) for x in z["flaps"])
    seam = {k: z[f"seam{k}"] for k in V}
    col = {k: OTHER[i % len(OTHER)]
           for i, k in enumerate(k for k in sorted(V) if k not in (A, B))}
    col[A], col[B] = FLAPCOL

    ARR = {"true": arrangement(V, z, "true"),
           "swapped": arrangement(V, z, "swapped")}
    G = {n: {k: z[f"{n}_settled_{k}"] for k in (A, B)} for n in ARR}

    allp = np.concatenate(list(ARR["true"].values()))
    lo, hi = allp.min(0), allp.max(0)
    pad = 0.05 * (hi - lo).max()
    vmax = float(np.percentile(np.concatenate(list(G["swapped"].values())), 90))

    fig = plt.figure(figsize=(13.5, 12))
    gs = fig.add_gridspec(3, 3, height_ratios=[1, 1, 0.75],
                          width_ratios=[1, 1, 1.15])
    labels = {
        "true": "The bottle as it really is",
        "swapped": "The two flaps swapped, then\nallowed to shuffle until the\n"
                   "joins close as far as\nthey ever will",
    }
    for r, name in enumerate(["true", "swapped"]):
        arr = ARR[name]
        for c, (i, j) in enumerate([(0, 2), (0, 1)]):
            ax = fig.add_subplot(gs[r, c])
            for k in sorted(arr):
                p = arr[k][::STEP]
                ax.scatter(p[:, i], p[:, j], s=0.5, color=col[k], linewidths=0,
                           rasterized=True)
            ax.set_xlim(lo[i] - pad, hi[i] + pad)
            ax.set_ylim(lo[j] - pad, hi[j] + pad)
            ax.set_aspect("equal")
            ax.set_xticks([])
            ax.set_yticks([])
            if r == 0:
                ax.set_title(["side", "from above"][c], fontsize=9)
            if c == 0:
                ax.set_ylabel(labels[name], fontsize=9)
        ax = fig.add_subplot(gs[r, 2])
        for k in (A, B):
            p = arr[k][seam[k]]
            sc = ax.scatter(p[:, 0], p[:, 2], s=0.7, c=G[name][k],
                            cmap="inferno_r", vmin=0, vmax=vmax, linewidths=0,
                            rasterized=True)
        ax.set_xlim(lo[0] - pad, hi[0] + pad)
        ax.set_ylim(lo[2] - pad, hi[2] + pad)
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title("every break-surface point,\ncoloured by its own gap",
                     fontsize=9)
        fig.colorbar(sc, ax=ax, fraction=0.045, label="gap, % of object size")

    ax = fig.add_subplot(gs[2, :])
    for name, style in [("true", "-"), ("swapped", "--")]:
        for k in (A, B):
            d = np.sort(G[name][k])
            ax.plot(d, np.linspace(0, 100, len(d)), style, color=col[k], lw=1.8,
                    label=f"{name}, flap {k}")
    ax.axvline(a.spacing, color="k", lw=0.8, ls=":")
    ax.set_xlim(0, 6)
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8, loc="lower right")
    ax.set_xlabel("gap between a break-surface point and the nearest other "
                  f"fragment, % of the object's own size   "
                  f"(dotted line = {a.spacing}%, the scan's own resolution)")
    ax.set_ylabel("% of break-surface points")
    ax.set_title("Every point, no binning. Solid = true, dashed = the best "
                 "swapped arrangement that exists.", fontsize=9)

    if a.caption:
        fig.suptitle(textwrap.fill(a.caption, 120), fontsize=9.5)
    fig.tight_layout(rect=(0, 0, 1, 0.955 if a.caption else 1))
    fig.savefig(a.out, dpi=175)
    print("wrote", a.out)
    for name in ARR:
        for k in (A, B):
            g = G[name][k]
            print(f"  {name:>8} flap {k}: median gap {np.median(g):.2f}%, "
                  f"p90 {np.percentile(g, 90):.2f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
