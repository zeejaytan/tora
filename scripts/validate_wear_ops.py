"""Check that edge recession + chipping behaves like real wear, not like noise.

Validates the conservator-specified wear model (`wear_ops.recede_and_chip`)
before any training data is built on it. Three things must hold:

  joint_gap   MUST INCREASE. This is the point: worn sherds no longer meet
              tightly, so gaps open at the joins. No previous training data had
              this — fragments always still mated perfectly, just with smoother
              faces. It changes the assembly problem, not just its appearance.

  faces_kept  should stay HIGH (~95%+). Chips are small and local, not a
              uniform shrink of the sherd.

  relief      must stay SANE. The previous material-loss attempt drove this to
              ~1.0 (six times rougher) because per-vertex displacement
              corrugates the surface. Removing geometry cannot do that, and this
              is the check that proves it.

Usage:
  python scripts/validate_wear_ops.py [--src ...] [--objects limb3,blue_pot]
"""

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fracture_mesh_ops import piece_relief_stats  # noqa: E402
from wear_ops import recede_and_chip  # noqa: E402


def joint_gap(pieces):
    """How tightly do the pieces meet? 10th-percentile nearest-other-piece distance."""
    out = []
    for i, (v, _) in enumerate(pieces):
        best = np.full(len(v), np.inf)
        for j, (w, _) in enumerate(pieces):
            if i == j:
                continue
            d, _ = cKDTree(w).query(v)
            best = np.minimum(best, d)
        out.append(float(np.percentile(best, 10)))
    return float(np.mean(out))


def mean_relief(pieces):
    return float(np.mean([piece_relief_stats(v, f)["relief_p90"] for v, f in pieces]))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", default="/data/gpfs/projects/punim2657/TORA/dataset/real_heldout_norm.hdf5")
    ap.add_argument("--dataset", default="real_heldout_norm")
    ap.add_argument("--objects", default="limb3,blue_pot")
    args = ap.parse_args()

    settings = [(0.002, 4, 0.008), (0.004, 6, 0.010), (0.008, 10, 0.014)]
    print("Does edge recession + chipping behave like real wear?")
    print("  gap MUST rise | faces should stay high | relief must stay sane (~0.2-0.4)")
    print()
    print("  object     setting             relief   faces_kept   joint_gap")

    with h5py.File(args.src, "r") as h:
        for obj in [o.strip() for o in args.objects.split(",") if o.strip()]:
            grp = h[args.dataset][obj]
            g = grp["pieces"] if "pieces" in grp else grp
            keys = sorted(g.keys(), key=lambda s: int(s) if s.isdigit() else s)
            pieces = [(np.asarray(g[k]["vertices"][:], dtype=np.float64),
                       np.asarray(g[k]["faces"][:], dtype=np.int64)) for k in keys]

            n0 = sum(len(f) for _, f in pieces)
            g0 = joint_gap(pieces)
            print("  %-10s %-19s %.4f   %6.1f%%      %.5f" %
                  (obj, "original", mean_relief(pieces), 100.0, g0), flush=True)

            for rec, chips, cf in settings:
                w = recede_and_chip(pieces, recession_frac=rec,
                                    chip_count=chips, chip_frac=cf)
                n = sum(len(f) for _, f in w)
                gw = joint_gap(w)
                print("  %-10s rec=%.3f chips=%2d   %.4f   %6.1f%%      %.5f  (gap x%.1f)" %
                      (obj, rec, chips, mean_relief(w), 100.0 * n / n0, gw,
                       gw / max(g0, 1e-9)), flush=True)


if __name__ == "__main__":
    main()
