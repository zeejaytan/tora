"""Is the smoothness measure blind on thin-walled objects?

Trigger: building the v2 training set, the two egg objects reported smoothness
~1.21 and did not move at all under wear — 1.2078 fresh, 1.2298 after the
heaviest smoothing we can apply. Every other object moved by 20-45%. A number
that refuses to change when the thing it measures changes is a broken ruler
until proven otherwise, and that has already faked one finding in this project.

The suspected mechanism is specific and testable. `piece_relief_stats` measures
how much surface normals disagree within a neighbourhood of radius 3% of the
object's size. On a THIN-WALLED object, the inner and outer wall are closer
together than that radius, so every neighbourhood contains points from both
faces — whose normals point in OPPOSITE directions. The measure then reports
wall thinness, at a near-maximum value, and the fracture roughness it was meant
to capture is buried underneath.

This matters well beyond the eggs. The Juglet is thin-walled, and its measured
0.171 is the target the whole training set is being built to reach.

The test: sweep the neighbourhood radius. If the reading is genuine roughness it
will fall smoothly as the radius shrinks. If it is wall thickness, it will
COLLAPSE once the radius drops below the wall — a cliff, not a slope — and wear
will start showing up below that point.

Usage:
  python scripts/diagnose_relief_thin_shell.py --objects egg__egg1,ceramics__blue_pot
"""

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wear_ops import apply_wear  # noqa: E402

RADII = [0.030, 0.020, 0.012, 0.008, 0.005, 0.003, 0.002]


def relief_at(verts, faces, radius_frac, n_pts=4000, seed=0):
    """piece_relief_stats, but with the neighbourhood radius exposed."""
    from scipy.spatial import cKDTree

    m = trimesh.Trimesh(vertices=verts.astype(np.float64),
                        faces=faces.astype(np.int64), process=False)
    scale = float(max(m.extents))
    if scale <= 0 or len(m.faces) < 8:
        return 0.0
    pts, fid = trimesh.sample.sample_surface(m, n_pts, seed=seed)
    fn = m.face_normals[fid]
    tree = cKDTree(pts)
    relief = np.zeros(len(pts))
    for i, ne in enumerate(tree.query_ball_point(pts, radius_frac * scale)):
        if len(ne) < 3:
            continue
        relief[i] = 1.0 - float(np.clip(fn[ne] @ fn[i], -1, 1).mean())
    return float(np.percentile(relief, 90))


def wall_thickness(verts, faces, n_pts=2000, seed=0):
    """Median distance from the surface to the surface on the other side.

    Cast a ray inward along the normal; the first hit is the far wall. Gives a
    physical number to compare the neighbourhood radius against.
    """
    m = trimesh.Trimesh(vertices=verts.astype(np.float64),
                        faces=faces.astype(np.int64), process=False)
    pts, fid = trimesh.sample.sample_surface(m, n_pts, seed=seed)
    n = m.face_normals[fid]
    origins = pts - n * 1e-6
    try:
        loc, idx_ray, _ = m.ray.intersects_location(
            ray_origins=origins, ray_directions=-n, multiple_hits=False)
    except Exception:
        return float("nan"), float("nan")
    if not len(loc):
        return float("nan"), float(max(m.extents))
    d = np.linalg.norm(loc - origins[idx_ray], axis=1)
    d = d[d > 1e-9]
    return (float(np.median(d)) if len(d) else float("nan")), float(max(m.extents))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", default="/data/gpfs/projects/punim2657/TORA/dataset/real_finetune.hdf5")
    ap.add_argument("--dataset", default="real_finetune")
    ap.add_argument("--objects", default="egg__egg1,ceramics__blue_pot,ceramics__galli_pot")
    args = ap.parse_args()

    print("Does the smoothness measure see roughness, or wall thickness?")
    print("  Sweeping the neighbourhood radius. A genuine roughness reading falls")
    print("  gently; a wall-thickness artifact falls off a CLIFF once the radius")
    print("  drops below the wall, and wear becomes visible only below that point.")
    print()

    with h5py.File(args.src, "r") as h:
        ds = h[args.dataset]
        for obj in [o.strip() for o in args.objects.split(",") if o.strip()]:
            if obj not in ds:
                print(f"  {obj}: not in {args.dataset}")
                continue
            grp = ds[obj]
            g = grp["pieces"] if "pieces" in grp else grp
            keys = sorted(g.keys(), key=lambda s: int(s) if s.isdigit() else s)
            pieces = [(np.asarray(g[k]["vertices"][:], dtype=np.float64),
                       np.asarray(g[k]["faces"][:], dtype=np.int64)) for k in keys]

            t, ext = wall_thickness(*pieces[0])
            frac = t / ext if (ext and np.isfinite(t)) else float("nan")
            print(f"  {obj}  ({len(pieces)} sherds)")
            print(f"    wall thickness ~{frac * 100:.2f}% of object size "
                  f"(the measure's default radius is 3.00%)")
            if np.isfinite(frac) and frac < 0.03:
                print(f"    -> the default neighbourhood is WIDER than the wall: "
                      f"opposite faces land in the same neighbourhood")

            # heaviest wear we can apply, so any blindness is unmistakable
            worn = apply_wear(pieces, smoothing=1.0, smoothing_passes=3,
                              recession=0.0020, chip_count=4, chip_size=0.0022)

            print(f"    {'radius':>8s} {'fresh':>9s} {'worn':>9s} {'change':>9s}")
            for r in RADII:
                a = float(np.mean([relief_at(v, f, r) for v, f in pieces]))
                b = float(np.mean([relief_at(v, f, r) for v, f in worn]))
                chg = 100.0 * (b - a) / a if a > 1e-9 else float("nan")
                flag = "  <-- wear visible" if np.isfinite(chg) and chg < -8 else ""
                print(f"    {r * 100:>7.1f}% {a:>9.4f} {b:>9.4f} {chg:>8.1f}%{flag}",
                      flush=True)
            print(flush=True)

    print("If the eggs only show wear at radii below their wall thickness, then")
    print("every smoothness number reported for a thin-walled object -- INCLUDING")
    print("the Juglet's 0.171 -- is measuring the wrong thing, and the coverage")
    print("target for the training set has to be recomputed.")


if __name__ == "__main__":
    main()
