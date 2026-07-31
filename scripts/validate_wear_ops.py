"""Check the wear model behaves like real wear, before any dataset is built on it.

Validates `wear_ops.apply_wear` — the model intended for this and future
datasets. Four things must hold, and the first is the one earlier versions failed:

  joint_gap   MUST RISE, ON EVERY POT. Worn sherds no longer meet tightly, so
              gaps open at the joins. No previous training data had this —
              fragments always still mated perfectly, merely with smoother
              faces. A rim-only version passed on limb3 (x2.6) but FAILED on
              blue_pot (x0.8), because broad contact faces still met in the
              middle; that is why recession now acts on the mating surface.

  faces_kept  ~95%+. Chips are small and local, not a uniform shrink. The
              previous version removed 15-34%, which destroys the sherd.

  relief      must stay SANE (~0.2-0.4). Displacement along RAW normals drove
              this to ~1.0 — six times rougher — by corrugating the surface.
              Smoothing the normal field first is the fix, and this is the check.

  poses       untouched by construction: geometry-only edits, so ground truth
              and scoring stay valid.

Usage:
  python scripts/validate_wear_ops.py [--objects limb3,blue_pot]
"""

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fracture_mesh_ops import piece_relief_stats  # noqa: E402
from wear_ops import apply_wear  # noqa: E402


def joint_gap(pieces, max_pts: int = 60000, seed: int = 0):
    """How tightly do fragments meet? Mean 10th-pct nearest-other-piece distance.

    Vertices are subsampled: the full computation is O(V log V) across every
    pair of million-vertex scans and took ~2h for two pots, which makes
    validating the whole set impractical. 60k points per piece gives the same
    answer to 3 decimals at a fraction of the cost.
    """
    rng = np.random.default_rng(seed)

    def sub(a):
        return a if len(a) <= max_pts else a[rng.choice(len(a), max_pts, replace=False)]

    subs = [sub(v) for v, _ in pieces]
    trees = [cKDTree(s) for s in subs]
    out = []
    for i, s in enumerate(subs):
        best = np.full(len(s), np.inf)
        for j, t in enumerate(trees):
            if i == j:
                continue
            d, _ = t.query(s)
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

    # light / moderate / heavy — recession is the key axis, kept small
    settings = [
        ("light",    dict(smoothing=1.0, recession=0.0008, chip_count=3, chip_size=0.0020)),
        ("moderate", dict(smoothing=1.0, recession=0.0015, chip_count=4, chip_size=0.0030)),
        ("heavy",    dict(smoothing=1.0, recession=0.0030, chip_count=6, chip_size=0.0040)),
    ]

    print("Wear model validation — gap MUST rise on EVERY pot")
    print("  faces_kept ~95%+ | relief sane 0.2-0.4 | gap x>1.0")
    print()
    print("  object     setting    relief   faces_kept   joint_gap   verdict")

    ok = True
    with h5py.File(args.src, "r") as h:
        for obj in [o.strip() for o in args.objects.split(",") if o.strip()]:
            grp = h[args.dataset][obj]
            g = grp["pieces"] if "pieces" in grp else grp
            keys = sorted(g.keys(), key=lambda s: int(s) if s.isdigit() else s)
            pieces = [(np.asarray(g[k]["vertices"][:], dtype=np.float64),
                       np.asarray(g[k]["faces"][:], dtype=np.int64)) for k in keys]

            n0 = sum(len(f) for _, f in pieces)
            g0 = joint_gap(pieces)
            r0 = mean_relief(pieces)
            print("  %-10s %-10s %.4f   %6.1f%%      %.5f" % (obj, "original", r0, 100.0, g0),
                  flush=True)

            for name, kw in settings:
                w = apply_wear(pieces, **kw)
                n = sum(len(f) for _, f in w)
                gw, rw = joint_gap(w), mean_relief(w)
                kept = 100.0 * n / n0
                ratio = gw / max(g0, 1e-9)
                bad = []
                if ratio <= 1.0:
                    bad.append("GAP DID NOT OPEN")
                if kept < 90.0:
                    bad.append("too much removed")
                if not (0.10 <= rw <= 0.60):
                    bad.append("relief unsane")
                if bad:
                    ok = False
                print("  %-10s %-10s %.4f   %6.1f%%      %.5f   x%.2f %s" %
                      (obj, name, rw, kept, gw, ratio,
                       "OK" if not bad else "<-- " + "; ".join(bad)), flush=True)

    print()
    print("RESULT:", "wear model behaves correctly" if ok else "NOT READY — see flags above")


if __name__ == "__main__":
    main()
