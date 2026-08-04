"""Isolate surface recession: does it open the join on its own, and monotonically?

Validation job 28756223 left one unexplained arm. On `blue_pot`, recession
COMBINED with smoothing opens the join well (x1.40), but recession ALONE
(`loss_only`) gives x0.98 — very slightly closed. Recession is supposed to be
the most direct form of loss there is, so that is either a real defect or a
measurement artefact, and it matters because recession is what carries wear on
objects whose surfaces will not smooth any further.

Prime suspect: `_smoothed_normals` relies on trimesh vertex normals, which need
consistent face winding. Scanned meshes frequently have patches wound the wrong
way; where that happens the surface would be pushed OUTWARD, closing the join
instead of opening it.

Tests recession alone at increasing magnitudes, with no chipping and no
smoothing, and reports whether the join opens monotonically. Also reports how
many band normals point inward, which would confirm the winding hypothesis.

Usage:
  python scripts/diagnose_recession.py [--objects blue_pot,vert9,coxae]
"""

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np
import trimesh
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wear_ops import _band_mask, _smoothed_normals, recede_surface  # noqa: E402


def joint_gap(pieces, max_pts=40000, seed=0):
    rng = np.random.default_rng(seed)
    subs = [v if len(v) <= max_pts else v[rng.choice(len(v), max_pts, replace=False)]
            for v, _ in pieces]
    trees = [cKDTree(s) for s in subs]
    out = []
    for i, s in enumerate(subs):
        best = np.full(len(s), np.inf)
        for j, t in enumerate(trees):
            if i != j:
                d, _ = t.query(s, workers=-1)
                best = np.minimum(best, d)
        out.append(float(np.percentile(best, 10)))
    return float(np.mean(out))


def inward_normal_fraction(pieces):
    """Fraction of band normals pointing INTO the object's own centroid.

    A correctly wound closed mesh has outward normals everywhere, so this should
    be ~0. A large value means winding is inconsistent, and recession would push
    parts of the surface the wrong way.
    """
    fracs = []
    for i, (v, f) in enumerate(pieces):
        _, feather = _band_mask(pieces, i, v)
        band = feather > 0.02
        if not band.any():
            continue
        nrm = _smoothed_normals(v, f, band)
        c = v.mean(0)
        outward = v[band] - c
        outward /= (np.linalg.norm(outward, axis=1, keepdims=True) + 1e-12)
        dots = np.einsum("ij,ij->i", nrm[band], outward)
        fracs.append(float(np.mean(dots < 0)))
    return float(np.mean(fracs)) if fracs else float("nan")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", default="/data/gpfs/projects/punim2657/TORA/dataset/real_heldout_norm.hdf5")
    ap.add_argument("--dataset", default="real_heldout_norm")
    ap.add_argument("--objects", default="blue_pot,vert9,coxae")
    args = ap.parse_args()

    print("Recession in isolation — no chipping, no smoothing")
    print("  the join should open monotonically with recession")
    print()

    with h5py.File(args.src, "r") as h:
        for obj in [o.strip() for o in args.objects.split(",") if o.strip()]:
            grp = h[args.dataset][obj]
            g = grp["pieces"] if "pieces" in grp else grp
            keys = sorted(g.keys(), key=lambda s: int(s) if s.isdigit() else s)
            pieces = [(np.asarray(g[k]["vertices"][:], dtype=np.float64),
                       np.asarray(g[k]["faces"][:], dtype=np.int64)) for k in keys]

            g0 = joint_gap(pieces)
            inw = inward_normal_fraction(pieces)
            print(f"  {obj}: gap {g0:.5f}, band normals pointing inward: {inw * 100:.1f}%",
                  flush=True)
            if inw > 0.2:
                print("      ^ winding is inconsistent — recession will push part of "
                      "the surface the WRONG way", flush=True)

            prev = 1.0
            for rec in [0.0005, 0.0015, 0.0030, 0.0060]:
                w = recede_surface(pieces, recession_frac=rec)
                ratio = joint_gap(w) / max(g0, 1e-12)
                trend = "" if ratio >= prev - 0.01 else "   <-- went backwards"
                print(f"      recession {rec:.4f} -> gap x{ratio:.3f}{trend}", flush=True)
                prev = ratio
            print(flush=True)


if __name__ == "__main__":
    main()
