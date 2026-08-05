"""Measure wear as MATERIAL LOSS, which is what a conservator means by it.

Conservator's correction (2026-08-05): "I look at the wear-ness in the loss of
material sense."

Everything here had been reporting wear as `relief_p90` — surface normal
variation, i.e. how SMOOTH the break face is. That is a different quantity. A
sherd can be gently polished but essentially intact, or rough but substantially
eaten away. Reporting smoothness and calling it wear conflates the two, and it
produced at least one wrong conclusion: "the Juglet is more worn than our
simulated range" was really "the Juglet is SMOOTHER than our range", which
implies nothing about how much of it is missing.

The drift had a cause worth naming. For a real archaeological sherd, material
loss is UNMEASURABLE — there is no pristine original to compare against — while
smoothness can be measured from the object alone. So the available metric
quietly replaced the meaningful one.

For SIMULATED wear that excuse does not hold: we know exactly what was removed.
This reports it directly.

Measures per condition:
    volume loss %       material gone, as a fraction of the original solid
    mean recession      how far the break face retreated, in mm-equivalent
                        (fraction of object size — multiply by the real object's
                        size for physical units)
    surface loss %      break-face area removed by chipping
    relief              kept for continuity, now clearly labelled as SMOOTHNESS
                        and not as wear

Usage:
  python scripts/measure_material_loss.py --object blue_pot
"""

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np
import trimesh
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fracture_mesh_ops import piece_relief_stats  # noqa: E402
from wear_ops import apply_wear, wear_conditions  # noqa: E402


def solid_volume(pieces):
    """Total enclosed volume. Meaningful only if the meshes are near-watertight."""
    tot = 0.0
    for v, f in pieces:
        try:
            tot += abs(float(trimesh.Trimesh(vertices=v, faces=f,
                                             process=False).volume))
        except Exception:
            return float("nan")
    return tot


def surface_area(pieces):
    tot = 0.0
    for v, f in pieces:
        try:
            tot += float(trimesh.Trimesh(vertices=v, faces=f, process=False).area)
        except Exception:
            return float("nan")
    return tot


def mean_recession(before, after, max_pts=60000, seed=0):
    """How far the surface actually moved, averaged over points that moved."""
    rng = np.random.default_rng(seed)
    moved = []
    for (v0, _), (v1, _) in zip(before, after):
        a = v0 if len(v0) <= max_pts else v0[rng.choice(len(v0), max_pts, replace=False)]
        d, _ = cKDTree(v1).query(a, workers=-1)
        sig = d[d > 1e-9]
        if len(sig):
            moved.append(float(sig.mean()))
    return float(np.mean(moved)) if moved else 0.0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", default="/data/gpfs/projects/punim2657/TORA/dataset/real_heldout_norm.hdf5")
    ap.add_argument("--dataset", default="real_heldout_norm")
    ap.add_argument("--objects", default="blue_pot,limb3,plate")
    args = ap.parse_args()

    print("Wear measured as MATERIAL LOSS (what a conservator means by wear)")
    print("  relief is SMOOTHNESS, shown for continuity — it is not a wear measure")
    print()

    with h5py.File(args.src, "r") as h:
        ds = h[args.dataset]
        for obj in [o.strip() for o in args.objects.split(",") if o.strip()]:
            grp = ds[obj]
            g = grp["pieces"] if "pieces" in grp else grp
            keys = sorted(g.keys(), key=lambda s: int(s) if s.isdigit() else s)
            pieces = [(np.asarray(g[k]["vertices"][:], dtype=np.float64),
                       np.asarray(g[k]["faces"][:], dtype=np.int64)) for k in keys]

            scale = float(np.linalg.norm(
                np.concatenate([v for v, _ in pieces]).max(0)
                - np.concatenate([v for v, _ in pieces]).min(0)))
            v0, a0 = solid_volume(pieces), surface_area(pieces)
            r0 = float(np.mean([piece_relief_stats(v, f)["relief_p90"]
                                for v, f in pieces]))
            print(f"  {obj}  (object size {scale:.3f}, volume {v0:.6f})")
            print(f"    {'condition':<15s} {'material lost':>13s} {'recession':>11s} "
                  f"{'area lost':>10s} {'[smoothness]':>13s}")
            print(f"    {'original':<15s} {'0.00%':>13s} {'0.00000':>11s} "
                  f"{'0.00%':>10s} {r0:>13.4f}")

            for name, kw in wear_conditions():
                if name == "fresh":
                    continue
                w = apply_wear(pieces, **kw)
                v1, a1 = solid_volume(w), surface_area(w)
                rec = mean_recession(pieces, w)
                r1 = float(np.mean([piece_relief_stats(v, f)["relief_p90"]
                                    for v, f in w]))
                dv = 100.0 * (v0 - v1) / v0 if v0 and np.isfinite(v1) else float("nan")
                da = 100.0 * (a0 - a1) / a0 if a0 and np.isfinite(a1) else float("nan")
                print(f"    {name:<15s} {dv:>12.2f}% {rec / scale:>11.5f} "
                      f"{da:>9.2f}% {r1:>13.4f}", flush=True)
            print()


if __name__ == "__main__":
    main()
