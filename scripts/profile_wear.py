"""Find where the wear pipeline actually spends its time. Measure, don't guess.

I assumed the cost was spatial queries and parallelised them across 8 cores.
Verified correct — and it bought x1.0 (843s -> 810s, job 28449524). The KD-trees
were never the bottleneck.

So this times each stage and sub-step rather than reasoning about it. The
pipeline runs on full-resolution scans (~1.5M vertices per object) while the
downstream training only ever samples 5000 points, so there is likely a large
mismatch between the fidelity we compute and the fidelity anything consumes.

Usage:
  python scripts/profile_wear.py [--object limb3]
"""

import argparse
import sys
import time
from pathlib import Path

import h5py
import numpy as np
import trimesh
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))


class T:
    def __init__(self, label):
        self.label = label

    def __enter__(self):
        self.t = time.time()
        return self

    def __exit__(self, *a):
        print(f"    {self.label:<44s} {time.time() - self.t:8.2f}s", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", default="/data/gpfs/projects/punim2657/TORA/dataset/real_heldout_norm.hdf5")
    ap.add_argument("--dataset", default="real_heldout_norm")
    ap.add_argument("--object", default="limb3")
    args = ap.parse_args()

    with h5py.File(args.src, "r") as h:
        grp = h[args.dataset][args.object]
        g = grp["pieces"] if "pieces" in grp else grp
        keys = sorted(g.keys(), key=lambda s: int(s) if s.isdigit() else s)
        pieces = [(np.asarray(g[k]["vertices"][:], dtype=np.float64),
                   np.asarray(g[k]["faces"][:], dtype=np.int64)) for k in keys]

    nv = sum(len(v) for v, _ in pieces)
    nf = sum(len(f) for _, f in pieces)
    print(f"{args.object}: {len(pieces)} fragments, {nv} vertices, {nf} faces")
    print("  (downstream training samples only 5000 points per object)")
    print()

    v0, f0 = pieces[0]
    print(f"  --- per-fragment trimesh operations (fragment 0: {len(v0)} verts) ---")
    with T("Trimesh construction (process=False)"):
        m = trimesh.Trimesh(vertices=v0, faces=f0, process=False)
    with T("face_normals"):
        _ = m.face_normals
    with T("vertex_normals"):
        _ = m.vertex_normals
    with T("vertex_defects  (used for chip placement)"):
        try:
            _ = m.vertex_defects
        except Exception as e:
            print("      failed:", e)
    with T("sample_surface(20000)"):
        _ = trimesh.sample.sample_surface(m, 20000)

    print()
    print("  --- spatial ---")
    other = np.concatenate([v for v, _ in pieces[1:]], axis=0)
    with T(f"cKDTree build over {len(other)} pts"):
        tree = cKDTree(other)
    with T(f"query {len(v0)} verts (nearest)"):
        _ = tree.query(v0)

    print()
    print("  --- full stages ---")
    from fracture_mesh_ops import piece_relief_stats
    from wear_ops import recede_surface, recede_and_chip
    from fracture_mesh_ops import erode_fracture_band

    with T("erode_fracture_band (smoothing, all frags)"):
        sm = erode_fracture_band(pieces, strength=1.0, kernel_frac_max=0.05)
    cur = [(sm[i], pieces[i][1]) for i in range(len(pieces))]
    with T("recede_surface (all frags)"):
        cur = recede_surface(cur, recession_frac=0.0015)
    with T("recede_and_chip (all frags)"):
        cur = recede_and_chip(cur, recession_frac=0.0, chip_count=4, chip_frac=0.003)
    with T("piece_relief_stats (all frags, VALIDATION only)"):
        _ = [piece_relief_stats(v, f)["relief_p90"] for v, f in cur]


if __name__ == "__main__":
    main()
