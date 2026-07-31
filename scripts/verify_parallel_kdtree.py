"""Prove the parallel spatial queries give IDENTICAL results, and measure the gain.

`workers=-1` only splits a nearest-neighbour search across cores, so results
should be bit-identical. That is the claim; this checks it rather than trusting
it, because the speed-up is worthless if it perturbs the wear model that every
downstream dataset depends on.

Runs the same wear operation twice on the same fragments — once single-threaded,
once parallel — and compares the output vertices exactly.

Usage:
  python scripts/verify_parallel_kdtree.py [--object limb3]
"""

import argparse
import sys
import time
from pathlib import Path

import h5py
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import parallel_kdtree as pk  # noqa: E402


def load(src, dataset, obj):
    with h5py.File(src, "r") as h:
        grp = h[dataset][obj]
        g = grp["pieces"] if "pieces" in grp else grp
        keys = sorted(g.keys(), key=lambda s: int(s) if s.isdigit() else s)
        return [(np.asarray(g[k]["vertices"][:], dtype=np.float64),
                 np.asarray(g[k]["faces"][:], dtype=np.int64)) for k in keys]


def run_wear(pieces):
    # imported AFTER the patch state is set, so the swap is picked up
    from wear_ops import apply_wear
    return apply_wear(pieces, smoothing=1.0, recession=0.0015,
                      chip_count=4, chip_size=0.003, seed=0)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", default="/data/gpfs/projects/punim2657/TORA/dataset/real_heldout_norm.hdf5")
    ap.add_argument("--dataset", default="real_heldout_norm")
    ap.add_argument("--object", default="limb3")
    args = ap.parse_args()

    pieces = load(args.src, args.dataset, args.object)
    print(f"{args.object}: {len(pieces)} fragments, "
          f"{sum(len(v) for v, _ in pieces)} vertices", flush=True)

    pk.disable_parallel_kdtree()
    t0 = time.time()
    serial = run_wear(pieces)
    t_serial = time.time() - t0
    print(f"  single-threaded: {t_serial:7.1f}s", flush=True)

    pk.enable_parallel_kdtree()
    t0 = time.time()
    par = run_wear(pieces)
    t_par = time.time() - t0
    print(f"  all cores      : {t_par:7.1f}s   speedup x{t_serial / max(t_par, 1e-9):.1f}",
          flush=True)

    print()
    same = True
    for i, ((v1, f1), (v2, f2)) in enumerate(zip(serial, par)):
        if v1.shape != v2.shape or f1.shape != f2.shape:
            print(f"  fragment {i}: SHAPE DIFFERS {v1.shape} vs {v2.shape}")
            same = False
            continue
        dv = float(np.abs(v1 - v2).max())
        df = int(np.abs(f1 - f2).max()) if f1.size else 0
        if dv > 0 or df > 0:
            print(f"  fragment {i}: max vertex diff {dv:.3e}, face diff {df}")
            same = False

    print("RESULT:", "identical — safe to use" if same
          else "DIFFERS — do not use, results would change")


if __name__ == "__main__":
    main()
