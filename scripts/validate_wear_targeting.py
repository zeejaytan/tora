"""Check that per-object wear TARGETING lands every pot at the intended roughness.

A fixed wear dose does not produce a fixed amount of wear. At the same setting
`blue_pot` reached relief 0.110 while `limb3` only reached 0.171 — and the
training-set mean of 0.183 concealed that spread, so a good part of the training
material never reached the condition we care about (the Juglet measures 0.171,
lower = more worn).

Raising the smoothing kernel does not fix it either: the mollifier SATURATES
(limb3 0.1707 -> 0.1789 -> 0.1820 as the kernel grows 0.05 -> 0.12), the same
plateau GARF hit in Exp 7/7b. The lever is per-object strength, targeted.

This verifies `wear_to_target` actually hits the target across the full object
set — ceramics AND bone, whose break geometry differs — so that a dataset built
on it is uniformly worn rather than uniformly *dosed*.

Usage:
  python scripts/validate_wear_targeting.py [--target 0.15]
"""

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fracture_mesh_ops import piece_relief_stats  # noqa: E402
from wear_ops import wear_to_target  # noqa: E402

JUGLET_RELIEF = 0.171


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", default="/data/gpfs/projects/punim2657/TORA/dataset/real_heldout_norm.hdf5")
    ap.add_argument("--dataset", default="real_heldout_norm")
    ap.add_argument("--objects", default="")
    ap.add_argument("--target", type=float, default=0.15,
                    help="target relief; default 0.15 is comfortably PAST the "
                         "Juglet's 0.171 (lower = more worn)")
    ap.add_argument("--tol", type=float, default=0.03)
    args = ap.parse_args()

    print(f"Per-object wear targeting — target relief {args.target:.3f} "
          f"(Juglet = {JUGLET_RELIEF:.3f}, lower = more worn)")
    print()
    print("  object       original   achieved   at/past target?")

    hits, total = 0, 0
    with h5py.File(args.src, "r") as h:
        ds = h[args.dataset]
        objs = ([o.strip() for o in args.objects.split(",") if o.strip()]
                or sorted(ds.keys()))
        for obj in objs:
            grp = ds[obj]
            g = grp["pieces"] if "pieces" in grp else grp
            keys = sorted(g.keys(), key=lambda s: int(s) if s.isdigit() else s)
            pieces = [(np.asarray(g[k]["vertices"][:], dtype=np.float64),
                       np.asarray(g[k]["faces"][:], dtype=np.int64)) for k in keys]
            r0 = float(np.mean([piece_relief_stats(v, f)["relief_p90"] for v, f in pieces]))
            _, r1 = wear_to_target(pieces, target_relief=args.target)
            total += 1
            good = r1 <= args.target + args.tol
            hits += int(good)
            print("  %-12s %.4f     %.4f     %s" %
                  (obj, r0, r1, "yes" if good else "NO — saturated short of target"),
                  flush=True)

    print()
    print(f"RESULT: {hits}/{total} objects reached the target within {args.tol:.2f}")
    if hits < total:
        print("  Objects that saturate short cannot be worn further by smoothing.")
        print("  For those, wear must come from material loss (recession/chipping),")
        print("  or they should be excluded from the worn arm of the training set.")


if __name__ == "__main__":
    main()
