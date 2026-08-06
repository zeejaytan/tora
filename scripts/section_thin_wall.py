"""Cut across the wall and LOOK at what wear does to a thin shell.

The numbers said wear makes eggshell rougher instead of smoother, and offered a
mechanism: the smoothing patch (5% of object size) is three to four times wider
than the eggshell wall (1.2-1.6%), so instead of rounding the broken edge it
drags the inner and outer wall toward each other and crumples the shell.

That is a story built on a statistic, and today a statistic has already sent me
after the wrong cause once. This draws it.

Scale is the thing to get right, and it is where four earlier attempts in this
project failed — each picture was too coarse for the effect it was meant to show.
The quantity here is wall thickness, 1.2-1.6% of the object. So:

  * the cut is made ACROSS the wall, not along it. A slice taken along the
    fracture ribbon shows material apparently vanishing when it has only left
    the slice -- that exact mistake was made here before.
  * the view is windowed to a few wall thicknesses, not to the sherd. At sherd
    scale a wall this thin is a hairline and any change to it is invisible.
  * fresh and worn are drawn on the SAME axes, so the comparison is direct
    rather than a matter of remembering the previous picture.

Paired with a measurement no viewpoint can distort: wall thickness sampled along
the cut, before and after. If the shell is being pinched, the wall gets thinner
and the profile buckles. If wear is behaving, the wall holds its thickness and
only the broken edge rounds off.

A thick-walled control (blue_pot) is cut the same way. If the control also
buckles, the fault is in this drawing, not in the wear model.

Usage:
  python scripts/section_thin_wall.py --objects egg__egg1,ceramics__blue_pot \
      --out-dir /data/gpfs/projects/punim2657/TORA/wall_sections
"""

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import trimesh  # noqa: E402
from scipy.spatial import cKDTree  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wear_ops import _band_mask, apply_wear  # noqa: E402

N_SLICES = 3


def band_frame(pieces, idx):
    """A cutting frame anchored on the fracture band of piece `idx`.

    Returns (centre, along, across) where `along` runs down the length of the
    break edge. Cutting planes take `along` as their normal, so each section is
    perpendicular to the ribbon -- the cut that actually crosses the wall.
    """
    v = pieces[idx][0]
    hard, _ = _band_mask(pieces, idx, v)
    if hard.sum() < 50:
        return None, None, None, None
    band = v[hard]
    centre = band.mean(axis=0)
    # principal direction of the band = the direction the break edge runs
    u, s, vt = np.linalg.svd(band - centre, full_matrices=False)
    along = vt[0] / (np.linalg.norm(vt[0]) + 1e-12)
    across = vt[1] / (np.linalg.norm(vt[1]) + 1e-12)
    extent = float(np.abs((band - centre) @ along).max())
    return centre, along, across, extent


def section_points(v, f, origin, normal):
    """Points where the mesh crosses the plane, as an ordered-ish scatter."""
    try:
        m = trimesh.Trimesh(vertices=v, faces=f, process=False)
        sec = m.section(plane_origin=origin, plane_normal=normal)
    except Exception:
        return None
    if sec is None:
        return None
    try:
        return np.asarray(sec.vertices, dtype=np.float64)
    except Exception:
        return None


def wall_thickness_near(pts_3d, origin, radius):
    """Median across-wall spacing among section points near `origin`.

    On a shell the section is a thin closed loop: for every point on the outer
    face there is a partner on the inner face a wall-thickness away. Taking the
    nearest NON-adjacent partner approximates that gap without needing the loop
    to be ordered.
    """
    if pts_3d is None or len(pts_3d) < 8:
        return float("nan")
    d = np.linalg.norm(pts_3d - origin, axis=1)
    local = pts_3d[d < radius]
    if len(local) < 8:
        return float("nan")
    tree = cKDTree(local)
    dd, _ = tree.query(local, k=min(12, len(local)))
    # column 0 is self; adjacent samples along the loop are much closer than the
    # wall, so take a higher-order neighbour as the across-wall partner
    cand = dd[:, min(6, dd.shape[1] - 1)]
    cand = cand[np.isfinite(cand) & (cand > 0)]
    return float(np.median(cand)) if len(cand) else float("nan")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", default="/data/gpfs/projects/punim2657/TORA/dataset/real_finetune.hdf5")
    ap.add_argument("--dataset", default="real_finetune")
    ap.add_argument("--objects", default="egg__egg1,ceramics__blue_pot")
    ap.add_argument("--out-dir", default="/data/gpfs/projects/punim2657/TORA/wall_sections")
    ap.add_argument("--window-walls", type=float, default=6.0,
                    help="half-width of the view, in multiples of wall thickness")
    args = ap.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    print("Cross-sections ACROSS the wall, fresh vs worn.")
    print(f"  view windowed to +/-{args.window_walls:.0f} wall thicknesses")
    print("  a pinched wall means the smoothing patch is crossing the shell")
    print()

    with h5py.File(args.src, "r") as h:
        ds = h[args.dataset]
        for obj in [o.strip() for o in args.objects.split(",") if o.strip()]:
            if obj not in ds:
                print(f"  {obj}: not present")
                continue
            grp = ds[obj]
            g = grp["pieces"] if "pieces" in grp else grp
            keys = sorted(g.keys(), key=lambda s: int(s) if s.isdigit() else s)
            pieces = [(np.asarray(g[k]["vertices"][:], dtype=np.float64),
                       np.asarray(g[k]["faces"][:], dtype=np.int64)) for k in keys]

            worn = apply_wear(pieces, smoothing=1.0, smoothing_passes=3,
                              recession=0.0020, chip_count=4, chip_size=0.0022)

            # the sherd with the largest fracture band shows the most break edge
            idx = int(np.argmax([len(v) for v, _ in pieces]))
            centre, along, across, extent = band_frame(pieces, idx)
            if centre is None:
                print(f"  {obj}: no usable fracture band")
                continue

            vf, ff = pieces[idx]
            vw, fw = worn[idx]
            scale = float(np.linalg.norm(vf.max(0) - vf.min(0)))

            offs = np.linspace(-0.5 * extent, 0.5 * extent, N_SLICES)
            fig, axes = plt.subplots(1, N_SLICES, figsize=(5.2 * N_SLICES, 5.2))
            if N_SLICES == 1:
                axes = [axes]

            print(f"  {obj}  (sherd {idx}, object size {scale:.3f})")
            print(f"    {'slice':>7s} {'wall fresh':>11s} {'wall worn':>10s} {'change':>9s}")

            for si, (ax, off) in enumerate(zip(axes, offs)):
                o = centre + along * off
                pf = section_points(vf, ff, o, along)
                pw = section_points(vw, fw, o, along)

                tf = wall_thickness_near(pf, o, 0.05 * scale)
                tw = wall_thickness_near(pw, o, 0.05 * scale)
                chg = 100.0 * (tw - tf) / tf if np.isfinite(tf) and tf > 0 else float("nan")
                print(f"    {si:>7d} {tf / scale * 100:>10.2f}% "
                      f"{tw / scale * 100:>9.2f}% {chg:>8.1f}%", flush=True)

                # in-plane 2D axes for drawing
                e1 = across
                e2 = np.cross(along, across)
                e2 /= np.linalg.norm(e2) + 1e-12

                half = args.window_walls * (tf if np.isfinite(tf) and tf > 0
                                            else 0.015 * scale)
                for pts, colour, label, z in ((pf, "0.45", "fresh", 1),
                                              (pw, "#c1121f", "worn", 2)):
                    if pts is None or not len(pts):
                        continue
                    q = pts - o
                    x, y = q @ e1, q @ e2
                    keep = (np.abs(x) < half) & (np.abs(y) < half)
                    ax.scatter(x[keep], y[keep], s=3.5, c=colour, label=label,
                               zorder=z, linewidths=0)

                ax.set_xlim(-half, half)
                ax.set_ylim(-half, half)
                ax.set_aspect("equal")
                ax.set_title(f"cut {si + 1} of {N_SLICES}\n"
                             f"wall {tf / scale * 100:.2f}% -> {tw / scale * 100:.2f}%",
                             fontsize=10)
                ax.tick_params(labelsize=7)
                if si == 0:
                    ax.legend(fontsize=9, loc="upper right")

            fig.suptitle(f"{obj} — section across the wall "
                         f"(view = ±{args.window_walls:.0f} wall thicknesses)",
                         fontsize=12)
            fig.tight_layout()
            p = out / f"{obj}_wall_section.png"
            fig.savefig(p, dpi=170)
            plt.close(fig)
            print(f"    -> {p}")
            print(flush=True)

    print("Read it this way: if the red profile is pinched narrower than the grey,")
    print("or buckles into wiggles, the smoothing is crossing the wall and")
    print("crumpling the shell. If red merely rounds off where grey has a sharp")
    print("corner, and holds the same thickness, wear is behaving.")


if __name__ == "__main__":
    main()
