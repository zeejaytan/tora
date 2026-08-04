"""Check the SDF offset against the displacement implementation it would replace.

The wear model is what every downstream dataset depends on, so a replacement has
to be shown equivalent-or-better before it is adopted — the same discipline used
for the 30x speedup, which was only trusted after its numbers matched.

Three questions, and the third is the one that could kill it:

  1. Does it open the joins?            It must, at least as well as displacement.
  2. Does it preserve material?         An offset should remove a predictable
                                        amount, not gut the fragment.
  3. DOES IT DESTROY THE RELIEF?        An SDF is sampled on a grid, so detail
                                        finer than a voxel is lost. Relief IS the
                                        signal this whole investigation is about
                                        (break-surface texture at 0.92 fresh vs
                                        0.71 worn), so an offset that silently
                                        smooths the break face would be worse
                                        than the approximation it replaces, however
                                        mathematically clean.

Question 3 is why this is validated rather than assumed correct. Run at several
grid resolutions: if relief falls with a coarser grid, the grid is the cause and
must be raised.

Usage:
  python scripts/validate_sdf_offset.py [--objects blue_pot,limb3] [--grids 128,256]
"""

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fracture_mesh_ops import piece_relief_stats  # noqa: E402
from wear_ops import recede_surface  # noqa: E402
import sdf_offset  # noqa: E402


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


def mean_relief(pieces):
    vals = []
    for v, f in pieces:
        try:
            vals.append(piece_relief_stats(v, f)["relief_p90"])
        except Exception:
            pass
    return float(np.mean(vals)) if vals else float("nan")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", default="/data/gpfs/projects/punim2657/TORA/dataset/real_heldout_norm.hdf5")
    ap.add_argument("--dataset", default="real_heldout_norm")
    ap.add_argument("--objects", default="blue_pot,limb3")
    ap.add_argument("--grids", default="128,256")
    ap.add_argument("--recession", type=float, default=0.0015)
    args = ap.parse_args()

    if not sdf_offset.available():
        print("NO SDF BACKEND INSTALLED — cannot evaluate.")
        print("  pip install mesh-to-sdf   (or mesh2sdf)")
        print("  The displacement implementation remains in use; this is not a failure,")
        print("  only an inability to test the replacement.")
        return

    grids = [int(g) for g in args.grids.split(",")]
    print("SDF offset vs the displacement it would replace")
    print("  gap must open | material loss predictable | RELIEF MUST SURVIVE")
    print()

    with h5py.File(args.src, "r") as h:
        for obj in [o.strip() for o in args.objects.split(",") if o.strip()]:
            grp = h[args.dataset][obj]
            g = grp["pieces"] if "pieces" in grp else grp
            keys = sorted(g.keys(), key=lambda s: int(s) if s.isdigit() else s)
            pieces = [(np.asarray(g[k]["vertices"][:], dtype=np.float64),
                       np.asarray(g[k]["faces"][:], dtype=np.int64)) for k in keys]

            g0, r0 = joint_gap(pieces), mean_relief(pieces)
            print(f"  {obj}: gap {g0:.5f}  relief {r0:.4f}", flush=True)

            disp = recede_surface(pieces, recession_frac=args.recession)
            print(f"      displacement      gap x{joint_gap(disp) / g0:.2f}   "
                  f"relief {mean_relief(disp):.4f}", flush=True)

            for grid in grids:
                off, ok = sdf_offset.offset_pieces(pieces, distance_frac=args.recession,
                                                   grid=grid, verbose=False)
                if not ok:
                    print(f"      SDF grid {grid:<4d}     INCOMPLETE — some fragments "
                          f"fell back; do not build a dataset on this", flush=True)
                    continue
                r1 = mean_relief(off)
                flag = ""
                if r1 < r0 * 0.6:
                    flag = "   <-- RELIEF DESTROYED, grid too coarse"
                print(f"      SDF grid {grid:<4d}     gap x{joint_gap(off) / g0:.2f}   "
                      f"relief {r1:.4f}{flag}", flush=True)
            print(flush=True)

    print("Adopt the SDF offset only if it opens joins at least as well AND keeps")
    print("relief. Mathematical cleanliness does not justify destroying the signal.")


if __name__ == "__main__":
    main()
