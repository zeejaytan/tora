"""Does the break edge of a pot tell two look-alike fragments apart?

`scripts/check_identity_swap.py` found that TORA builds `narrow_bottle3` and
then puts its two big flaps on the wrong sides of it -- the same exchange in all
ten attempts. That leaves two readings which lead to OPPOSITE conclusions and
which no score computed so far can separate:

  (a) the break edges do distinguish the two flaps, the information was there in
      good condition, and the model did not use it  -> the METHOD failed, and it
      failed at placement rather than at telling fragments apart;
  (b) the two flaps genuinely fit either way, the object has two valid answers,
      and our reference is arbitrary at that seam  -> the REFERENCE was wrong,
      and every reading that leans on this pot has to be redone.

This script decides between them by putting the flaps in each other's places and
looking at the joins.

WHY THIS NEEDS THE SOURCE MESHES. The saved 5000-point eval clouds cannot answer
it: their points sit 1.8% of pot size apart, and the join gap in the CORRECT
assembly already reads 1.8-2.3% -- that is the sampling interval, not a gap. The
meshes carry ~500k vertices per flap, 0.22% apart, and the correct assembly's
seam reads 0.1-0.2%. The view has to resolve the scale being tested.

WHAT COUNTS AS A BREAK SURFACE. The real Fractura data has `shared_faces` all
-1, so there is no break-face labelling and it has to be found geometrically. A
first attempt took every vertex within 1% of another fragment; that band's
distances came out spread almost evenly from 0 to the cutoff, because it
captures the outer wall near the break edge as well as the break face itself.
What is used instead is a fixed FRACTION -- each fragment's closest 2% of
vertices in the TRUE assembly. That set is a property of the sherd rather than
of the arrangement, so the same points are measured in both arrangements.

BEING GENEROUS TO THE SWAP. If the swap is only ever tried in one pose it can be
made to look bad by a poor fit. So the swapped bottle is given every chance:
each flap is first placed by best rigid fit into the other's footprint (PCA over
the four proper axis alignments, then trimmed ICP), and then BOTH flaps are
freed to shuffle against everything else until the joins close as far as they
ever will.

THE CONTROL, and it is the part that matters. The identical settling procedure
is run on the TRUE arrangement. If the optimiser is sound it must leave the true
bottle where it is. An earlier version of this test failed exactly here -- it
asked each flap to mate with the anchor and sliver alone, and scored a flap
sitting in its own correct place at a 25% gap, because most of that flap's break
surface mates with the OTHER FLAP, which had been left out of the target. The
control caught it. Without a control this test is worthless.

Usage:
  python scripts/check_seam_swap.py --mesh artifacts/nb3seam/nb3_mesh_vertices.npz \
      --flaps 0 3 --out artifacts/nb3seam/nb3_seam.npz
"""

import argparse
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))

from readout import unit_box_scale  # noqa: E402

FRACTION = 0.02        # closest 2% of a fragment's vertices = its break surface
RNG = np.random.default_rng(0)


def query(tree, pts):
    return tree.query(pts, k=1, workers=-1)


def kabsch(A, B):
    ca, cb = A.mean(0), B.mean(0)
    U, _, Vt = np.linalg.svd((A - ca).T @ (B - cb))
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1.0, 1.0, d]) @ U.T
    return R, cb - R @ ca


def break_surfaces(V, unit):
    """Each fragment's closest FRACTION of vertices, in the true assembly."""
    trees = {k: cKDTree(V[k]) for k in V}
    seam = {}
    for k in V:
        d = np.full(len(V[k]), np.inf)
        for j in V:
            if j != k:
                dd, _ = query(trees[j], V[k])
                d = np.minimum(d, dd)
        d /= unit
        seam[k] = d <= np.quantile(d, FRACTION)
    return seam


def principal_axes(P):
    return np.linalg.svd(P - P.mean(0), full_matrices=False)[2]


def fit_into(src_full, tgt_full, n=20000, iters=60, trim=0.9):
    """Best rigid placement of one fragment into another's footprint."""
    src = src_full[RNG.choice(len(src_full), min(n, len(src_full)), replace=False)]
    tgt = tgt_full[RNG.choice(len(tgt_full), min(n, len(tgt_full)), replace=False)]
    tree = cKDTree(tgt)
    Vs, Vt = principal_axes(src), principal_axes(tgt)
    best = None
    for s in [(1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)]:
        R = Vt.T @ np.diag(s).astype(float) @ Vs
        t = tgt.mean(0) - R @ src.mean(0)
        for _ in range(iters):
            d, idx = query(tree, src @ R.T + t)
            keep = d <= np.quantile(d, trim)
            R, t = kabsch(src[keep], tgt[idx[keep]])
        d, _ = query(tree, src @ R.T + t)
        rms = float(np.sqrt(np.mean(np.sort(d)[: int(trim * len(d))] ** 2)))
        if best is None or rms < best[2]:
            best = (R, t, rms)
    return best


def seam_gap(V, pose, seam, unit, k):
    """Gap from fragment k's break surface to every other fragment, in %."""
    S = V[k][seam[k]] @ pose[k][0].T + pose[k][1]
    best = np.full(len(S), np.inf)
    for j in V:
        if j == k:
            continue
        d, _ = query(cKDTree(V[j] @ pose[j][0].T + pose[j][1]), S)
        best = np.minimum(best, d)
    return 100 * best / unit


def settle(V, pose, seam, flaps, rounds=8, iters=25, trim=0.75):
    """Let the flaps shuffle until the joins close as far as they ever will."""
    pose = {k: (R.copy(), t.copy()) for k, (R, t) in pose.items()}
    for _ in range(rounds):
        for k in flaps:
            tgt = np.concatenate([V[j] @ pose[j][0].T + pose[j][1]
                                  for j in V if j != k])
            tree, S0 = cKDTree(tgt), V[k][seam[k]]
            R, t = pose[k]
            for _ in range(iters):
                d, idx = query(tree, S0 @ R.T + t)
                keep = d <= np.quantile(d, trim)
                R, t = kabsch(S0[keep], tgt[idx[keep]])
            pose[k] = (R, t)
    return pose


def row(tag, g):
    q = np.percentile(g, [50, 75, 90, 95])
    print(f"{tag:<46}" + "".join(f"{v:8.2f}%" for v in q) + f"{g.mean():8.2f}%")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mesh", required=True, help="npz of per-fragment vertices")
    ap.add_argument("--flaps", nargs=2, type=int, required=True,
                    help="the two fragments the model exchanges")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    z = np.load(a.mesh)
    V = {int(k[1:]): z[k].astype(np.float64) for k in z.files}
    unit = unit_box_scale(np.concatenate([V[k] for k in sorted(V)]))
    A, B = a.flaps
    print(f"object size (longest bbox side) = {unit:.3f} scan units")
    print("fragments: " + ", ".join(f"{k}:{len(V[k])} verts" for k in sorted(V)))

    seam = break_surfaces(V, unit)
    spacing = []
    for k in sorted(V):
        sub = V[k][::7]
        d, _ = cKDTree(sub).query(sub, k=2, workers=-1)
        spacing.append(100 * np.median(d[:, 1]) / unit)
    print(f"\nvertex spacing, the floor this can resolve: "
          f"{min(spacing):.2f}-{max(spacing):.2f}% of object size")
    print("break surface = closest 2% of each fragment's vertices, "
          "taken from the TRUE assembly")

    I3, Z3 = np.eye(3), np.zeros(3)
    true = {k: (I3.copy(), Z3.copy()) for k in V}
    RA, tA, rmsA = fit_into(V[A], V[B])
    RB, tB, rmsB = fit_into(V[B], V[A])
    print(f"\nbest rigid fit of {A} into {B}'s footprint: trimmed RMS "
          f"{100 * rmsA / unit:.2f}% of object size; "
          f"{B} into {A}'s: {100 * rmsB / unit:.2f}%")
    swap = dict(true)
    swap[A], swap[B] = (RA, tA), (RB, tB)

    print(f"\n{'':46}" + "".join(f"{q:>9}" for q in
                                 ["p50", "p75", "p90", "p95", "mean"]))
    res = {}
    for name, pose in [("true", true), ("swapped", swap)]:
        settled = settle(V, pose, seam, (A, B))
        for label, p in [("as given", pose), ("settled", settled)]:
            for k in (A, B):
                g = seam_gap(V, p, seam, unit, k)
                res[f"{name}_{label.split()[0]}_{k}"] = g
                row(f"{name}, {label}: fragment {k} break surface", g)
        for k in sorted(V):
            res[f"pose_{name}_{k}_R"] = settled[k][0]
            res[f"pose_{name}_{k}_t"] = settled[k][1]

    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(a.out, unit=unit, flaps=np.array([A, B]),
                            **{f"seam{k}": seam[k] for k in V}, **res)
        print("\nwrote", a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
