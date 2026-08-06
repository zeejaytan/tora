"""Is the wall being pinched? Measure it directly; render what moved.

The cross-section attempt failed. Both egg panels came out completely blank,
and the rest were sparse fragments in a window sized by a wall estimate that
disagreed with the survey's by a factor of 25. That is the fifth view in this
project to fail the same way -- a picture scaled to the wrong quantity -- and
the operating rule for that is explicit: stop drawing proxies and render the
measured quantity itself, per-vertex and unbinned.

So this drops the slicing entirely and asks the question two ways, neither of
which needs a viewpoint to be chosen well:

  1. WALL THICKNESS across the fracture band, before and after wear, using the
     estimator that already produced coherent numbers in the survey (eggs
     1.2-1.6%, bones 6-7%, which match what those objects physically are).
     Pinching has one unambiguous signature: the wall gets thinner. Nothing
     about wear should thin the wall away from the broken edge -- surface
     recession retreats the mating face, it does not squeeze the shell.

  2. PER-VERTEX DISPLACEMENT, rendered in 3D, coloured by how far each vertex
     moved. Chipping is switched off so vertex correspondence is exact and the
     displacement is a real per-vertex quantity rather than a nearest-point
     approximation. If wear is behaving, movement is confined to a band along
     the broken edge. If the shell is being crumpled, movement spreads across
     the whole face of the sherd, far from any break.

The second is the honest picture: no slice, no projection, no binning, and the
thing being coloured is exactly the thing in question.

Usage:
  python scripts/probe_wall_pinch.py --objects egg__egg1,ceramics__blue_pot
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


def wall_thickness_frac(v, f, restrict=None, n_pts=6000, seed=0):
    """Median wall thickness as a fraction of object size.

    Same estimator as the survey: sample the surface, and for each point find
    the nearest sample whose normal faces the opposite way -- on a shell that is
    the far side of the wall. `restrict` limits sampling to points near a given
    set of vertices (used to look only at the fracture band).
    """
    m = trimesh.Trimesh(vertices=v.astype(np.float64), faces=f.astype(np.int64),
                        process=False)
    if len(m.faces) < 8 or max(m.extents) <= 0:
        return float("nan")
    scale = float(max(m.extents))
    pts, fid = trimesh.sample.sample_surface(m, n_pts, seed=seed)
    fn = m.face_normals[fid]

    if restrict is not None and len(restrict):
        d, _ = cKDTree(restrict).query(pts, workers=-1)
        keep = d < 0.03 * scale
        if keep.sum() < 200:
            keep = np.ones(len(pts), bool)
        pts, fn = pts[keep], fn[keep]

    tree = cKDTree(pts)
    k = min(64, len(pts))
    d, idx = tree.query(pts, k=k, workers=-1)
    out = []
    for i in range(len(pts)):
        opp = np.where(fn[idx[i]] @ fn[i] < -0.5)[0]
        if len(opp):
            out.append(d[i, opp[0]])
    return float(np.median(out) / scale) if out else float("nan")


def render_displacement(vf, vw, band, obj, path, max_pts=40000, seed=0):
    """3D scatter of every vertex, coloured by how far it moved. No binning."""
    disp = np.linalg.norm(vw - vf, axis=1)
    scale = float(np.linalg.norm(vf.max(0) - vf.min(0)))
    rng = np.random.default_rng(seed)
    sel = (np.arange(len(vf)) if len(vf) <= max_pts
           else rng.choice(len(vf), max_pts, replace=False))

    p = vf[sel]
    c = disp[sel] / scale * 100.0  # percent of object size
    hi = float(np.percentile(c, 99.5)) if len(c) else 1.0
    hi = max(hi, 1e-6)

    fig = plt.figure(figsize=(16, 5.4))
    for k, (el, az, title) in enumerate((
            (20, -60, "three-quarter"), (0, 0, "edge on"), (90, -90, "face on"))):
        ax = fig.add_subplot(1, 3, k + 1, projection="3d")
        s = ax.scatter(p[:, 0], p[:, 1], p[:, 2], c=c, s=1.0, cmap="inferno",
                       vmin=0, vmax=hi, linewidths=0)
        ax.view_init(elev=el, azim=az)
        ax.set_title(title, fontsize=10)
        ax.set_xticks([]); ax.set_yticks([]); ax.set_zticks([])
        try:
            ax.set_box_aspect((np.ptp(p[:, 0]), np.ptp(p[:, 1]), np.ptp(p[:, 2])))
        except Exception:
            pass
        if k == 2:
            cb = fig.colorbar(s, ax=ax, fraction=0.03, pad=0.02)
            cb.set_label("vertex moved (% of object size)", fontsize=8)
            cb.ax.tick_params(labelsize=7)

    moved = disp > 1e-9
    frac_moved = 100.0 * moved.mean()
    frac_band = 100.0 * band.mean()
    fig.suptitle(
        f"{obj} — how far each vertex moved under wear\n"
        f"{frac_moved:.1f}% of vertices moved; the fracture band is "
        f"{frac_band:.1f}% of the sherd",
        fontsize=12)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return frac_moved, frac_band, float(np.max(c)) if len(c) else 0.0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", default="/data/gpfs/projects/punim2657/TORA/dataset/real_finetune.hdf5")
    ap.add_argument("--dataset", default="real_finetune")
    ap.add_argument("--objects", default="egg__egg1,egg__egg2,bones__limb2,ceramics__blue_pot")
    ap.add_argument("--out-dir", default="/data/gpfs/projects/punim2657/TORA/wall_pinch")
    args = ap.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    print("Is the wall being pinched?")
    print("  Chipping is OFF, so every vertex keeps its identity and the")
    print("  displacement below is exact rather than a nearest-point estimate.")
    print()
    print("  Wall thickness measured across the FRACTURE BAND, as % of object size.")
    print("  Wear should not thin the wall. If it does, the shell is being squeezed.")
    print()
    print(f"  {'object':<24s} {'wall fresh':>11s} {'wall worn':>10s} {'change':>9s} "
          f"{'moved':>8s} {'band':>7s}")

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
                              recession=0.0020, chip_count=0, chip_size=0.0)

            idx = int(np.argmax([len(v) for v, _ in pieces]))
            vf, ff = pieces[idx]
            vw, fw = worn[idx]
            if len(vw) != len(vf):
                print(f"  {obj}: vertex count changed ({len(vf)} -> {len(vw)}); "
                      f"cannot pair vertices")
                continue

            band, _ = _band_mask(pieces, idx, vf)
            tf = wall_thickness_frac(vf, ff, restrict=vf[band] if band.any() else None)
            tw = wall_thickness_frac(vw, fw, restrict=vf[band] if band.any() else None)
            chg = 100.0 * (tw - tf) / tf if np.isfinite(tf) and tf > 0 else float("nan")

            p = out / f"{obj}_displacement.png"
            frac_moved, frac_band, peak = render_displacement(vf, vw, band, obj, p)

            print(f"  {obj:<24s} {tf * 100:>10.2f}% {tw * 100:>9.2f}% {chg:>8.1f}% "
                  f"{frac_moved:>7.1f}% {frac_band:>6.1f}%", flush=True)
            print(f"      furthest any vertex moved: {peak:.2f}% of object size")
            print(f"      -> {p}", flush=True)

    print()
    print("Two things to read together:")
    print("  * wall change. Negative means the shell is being squeezed thinner,")
    print("    which no part of wear is supposed to do.")
    print("  * moved vs band. If far more of the sherd moved than lies in the")
    print("    fracture band, the smoothing is reaching well past the broken")
    print("    edge and deforming the body of the sherd.")


if __name__ == "__main__":
    main()
