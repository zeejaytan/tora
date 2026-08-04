"""Render before/after of a geometry operation, as a REQUIRED validation step.

Adopted as workspace practice 2026-08-01, at the conservator's suggestion, after
it proved itself: the recession bug (surfaces pushed toward their neighbour
instead of away, because 7-15% of scan normals are wound inward) survived THREE
rounds of numeric validation and fell over immediately once the join was drawn.

Numbers alone were not merely insufficient — they were actively misleading. The
wrongly-moved patches were the closest points, so they dominated every distance
statistic, which made a systematic defect read as erratic noise. I explained it
away twice before looking at it.

So: any operation that moves or removes geometry gets rendered as part of its
validation, not as a debugging step afterwards. A picture makes a wrong-direction
displacement obvious in seconds, where a summary statistic can hide it for days.

`render_pair_panel` draws one join edge-on, before and after, plus the
distribution of separation between the fragments — the measurement that cannot
be distorted by the choice of slice.
"""

import numpy as np
from scipy.spatial import cKDTree

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def contact_band(a, b, scale, tau_frac=0.02):
    d, _ = cKDTree(b if len(b) <= 80000 else b[::max(1, len(b) // 80000)]).query(
        a if len(a) <= 80000 else a[::max(1, len(a) // 80000)], workers=-1)
    src = a if len(a) <= 80000 else a[::max(1, len(a) // 80000)]
    return src[d < tau_frac * scale]


def separation(a, b, scale, cap_frac=0.05):
    sa = a if len(a) <= 60000 else a[::max(1, len(a) // 60000)]
    sb = b if len(b) <= 60000 else b[::max(1, len(b) // 60000)]
    d, _ = cKDTree(sb).query(sa, workers=-1)
    return d[d < cap_frac * scale] / scale


def render_pair_panel(variants, out_path, title=""):
    """Draw one join edge-on across several variants, plus separation histograms.

    Args:
        variants: [(label, [(verts, faces), (verts, faces)])] — the SAME two
            fragments under each condition, first entry treated as the original.
        out_path: PNG to write.
    """
    label0, pair0 = variants[0]
    a0, b0 = pair0[0][0], pair0[1][0]
    allv = np.concatenate([a0, b0])
    scale = float(np.linalg.norm(allv.max(0) - allv.min(0))) + 1e-9

    band = contact_band(a0, b0, scale)
    if len(band) < 50:
        return None
    c = band.mean(0)
    _, _, vt = np.linalg.svd(band - c, full_matrices=False)
    # vt[2] is the face normal: separation happens ALONG it, so it must be a
    # plotted axis. Slicing with it instead shows the face head-on, which hides
    # exactly the thing being checked.
    slab_normal, x_axis, y_axis = vt[0], vt[1], vt[2]
    ht = 0.02 * scale

    n = len(variants)
    fig, axes = plt.subplots(1, n + 1, figsize=(5.2 * (n + 1), 5.2))
    for ax, (label, pair) in zip(axes[:n], variants):
        for k, (v, _) in enumerate(pair):
            d = (v - c) @ slab_normal
            sl = v[np.abs(d) < ht]
            if not len(sl):
                continue
            x, y = (sl - c) @ x_axis, (sl - c) @ y_axis
            m = (np.abs(x) < 0.12 * scale) & (np.abs(y) < 0.06 * scale)
            ax.scatter(x[m], y[m], s=1.4, alpha=0.6,
                       c="tab:blue" if k == 0 else "tab:red")
        ax.set_title(label)
        ax.set_aspect("equal")
        ax.set_xlabel("along the join")
    axes[0].set_ylabel("across the join (separation direction)")

    ax = axes[n]
    bins = np.linspace(0, 0.02, 60)
    for label, pair in variants:
        ax.hist(separation(pair[0][0], pair[1][0], scale), bins=bins,
                alpha=0.5, label=label)
    ax.set_title("separation between fragments")
    ax.set_xlabel("distance (fraction of object size)")
    ax.legend(fontsize=8)

    fig.suptitle(title or out_path)
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)
    return out_path


def closest_pair(pieces):
    """The two fragments sharing the most contact — the clearest join to draw."""
    best, bi, bj = -1, 0, 1
    for i in range(len(pieces)):
        for j in range(i + 1, len(pieces)):
            a, b = pieces[i][0], pieces[j][0]
            allv = np.concatenate([a, b])
            scale = float(np.linalg.norm(allv.max(0) - allv.min(0))) + 1e-9
            sa = a if len(a) <= 40000 else a[::max(1, len(a) // 40000)]
            sb = b if len(b) <= 40000 else b[::max(1, len(b) // 40000)]
            d, _ = cKDTree(sb).query(sa, workers=-1)
            n = int((d < 0.01 * scale).sum())
            if n > best:
                best, bi, bj = n, i, j
    return bi, bj
