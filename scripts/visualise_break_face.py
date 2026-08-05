"""Show what wear actually does to a break face, as a height map.

The cross-section view (visual_check.py) confirms the geometry stays intact, but
it cannot show the wear itself: a displacement of ~0.002 of object size is
sub-pixel at whole-fragment zoom. So it answers "is this broken?" and not "what
does the wear look like?".

This answers the second question. The break face is isolated, flattened onto its
own plane, and drawn as a topographic map — height above the mean plane, on a
colour scale shared across all conditions so they are directly comparable.

Read it the way you would read a raking-light photograph of a sherd edge:
  strong mottling  = sharp, fresh fracture relief
  smoother field   = abraded surface, the high points taken off
  dark pits        = chips, where material is gone

Usage:
  python scripts/visualise_break_face.py --object limb3 --out face.png
"""

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wear_ops import _band_mask, apply_wear, wear_conditions  # noqa: E402

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def break_face_heightmap(pieces, idx, frame=None, res=260):
    """Height of the break face above its own mean plane, as an image."""
    v, f = pieces[idx]
    _, feather = _band_mask(pieces, idx, v)
    band = v[feather > 0.5]
    if len(band) < 200:
        return None, None

    if frame is None:
        c = band.mean(0)
        _, _, vt = np.linalg.svd(band - c, full_matrices=False)
        frame = (c, vt[0], vt[1], vt[2])      # centre, two in-plane axes, normal
    c, e1, e2, n = frame

    d = band - c
    x, y, h = d @ e1, d @ e2, d @ n

    # grid the scattered heights into an image
    lo_x, hi_x = np.percentile(x, [1, 99])
    lo_y, hi_y = np.percentile(y, [1, 99])
    ix = np.clip(((x - lo_x) / (hi_x - lo_x + 1e-12) * (res - 1)).astype(int), 0, res - 1)
    iy = np.clip(((y - lo_y) / (hi_y - lo_y + 1e-12) * (res - 1)).astype(int), 0, res - 1)

    acc = np.full((res, res), np.nan)
    cnt = np.zeros((res, res))
    sums = np.zeros((res, res))
    np.add.at(sums, (iy, ix), h)
    np.add.at(cnt, (iy, ix), 1)
    ok = cnt > 0
    acc[ok] = sums[ok] / cnt[ok]
    return acc, frame


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", default="/data/gpfs/projects/punim2657/TORA/dataset/real_heldout_norm.hdf5")
    ap.add_argument("--dataset", default="real_heldout_norm")
    ap.add_argument("--object", default="limb3")
    ap.add_argument("--fragment", type=int, default=-1,
                    help="which fragment; -1 picks the one with the largest break face")
    ap.add_argument("--out", default="face.png")
    args = ap.parse_args()

    with h5py.File(args.src, "r") as h:
        grp = h[args.dataset][args.object]
        g = grp["pieces"] if "pieces" in grp else grp
        keys = sorted(g.keys(), key=lambda s: int(s) if s.isdigit() else s)
        pieces = [(np.asarray(g[k]["vertices"][:], dtype=np.float64),
                   np.asarray(g[k]["faces"][:], dtype=np.int64)) for k in keys]

    idx = args.fragment
    if idx < 0:
        best, idx = -1, 0
        for i in range(len(pieces)):
            _, fe = _band_mask(pieces, i, pieces[i][0])
            n = int((fe > 0.5).sum())
            if n > best:
                best, idx = n, i
    print(f"{args.object}: fragment {idx}", flush=True)

    conds = [("original", None)] + [(n, kw) for n, kw in wear_conditions()
                                    if n != "fresh"]

    maps, frame = [], None
    for name, kw in conds:
        ps = pieces if kw is None else apply_wear(pieces, **kw)
        hm, frame = break_face_heightmap(ps, idx, frame=frame)
        if hm is None:
            print(f"  {name}: break face too small to map")
            continue
        rel = float(np.nanstd(hm))
        maps.append((name, hm, rel))
        print(f"  {name:<15s} surface variation {rel:.5f}", flush=True)

    if not maps:
        return

    finite = np.concatenate([m[~np.isnan(m)] for _, m, _ in maps])
    lim = float(np.percentile(np.abs(finite), 97))

    n = len(maps)
    fig, axes = plt.subplots(1, n, figsize=(3.6 * n, 4.2))
    if n == 1:
        axes = [axes]
    for ax, (name, hm, rel) in zip(axes, maps):
        im = ax.imshow(hm, cmap="terrain", vmin=-lim, vmax=lim, origin="lower",
                       interpolation="nearest")
        ax.set_title(f"{name}\nsurface variation {rel:.4f}", fontsize=10)
        ax.set_xticks([]); ax.set_yticks([])
    fig.colorbar(im, ax=axes, fraction=0.02, label="height above mean plane")
    fig.suptitle(f"{args.object}, fragment {idx}: the break face under each wear "
                 f"condition\n(like raking light on a sherd edge — mottling is "
                 f"fracture relief, smooth is abraded, dark pits are chips)")
    fig.savefig(args.out, dpi=140, bbox_inches="tight")
    print(f"  wrote {args.out}", flush=True)


if __name__ == "__main__":
    main()
