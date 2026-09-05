"""S2 — let a roughly-correct assembly settle into place ("good enough, not perfect").

The diagnosis (C2b/C3) is specific: wear destroys the fine break-surface detail
that says *these two faces mate exactly here*, while leaving the coarse signal
that says *these two fragments are neighbours* intact. TORA therefore puts
fragments in roughly the right neighbourhood and never closes the join.

This is the conservator's move: accept the rough placement, then nudge pieces
together until they sit. Crucially it asks for far less than the model does --
it never tries to match worn surfaces point-for-point (that information is gone).
It only asks neighbouring fragments to TOUCH without overlapping.

  * pull mutually-nearest surface points of predicted-neighbour fragments into
    contact, but only across gaps already small enough to be plausible
    (`--max-corr`), so nothing teleports;
  * push apart fragments that interpenetrate;
  * stay near the model's own prediction (`--reg`), so this refines rather than
    re-solves.

USES NO GROUND TRUTH. Neighbours come from the model's own predicted layout and
the geometry of the fragments. Ground truth is touched only afterwards, to
score. Anything else would make the result meaningless.

Input is the `clouds/*.npz` written by FlowVisualizationCallback with
`save_assembly_npz=true`.

Usage:
  python scripts/refine_seating.py --clouds-dir <run>/clouds [--iters 60]
"""

import argparse
import glob
import json
import os
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))

from readout import part_slices, seating_from_clouds  # noqa: E402


def kabsch(P: np.ndarray, Q: np.ndarray):
    """Rigid transform taking P onto Q (both (N,3), paired)."""
    pc, qc = P.mean(0), Q.mean(0)
    H = (P - pc).T @ (Q - qc)
    U, _, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1.0, 1.0, d]) @ U.T
    return R, qc - R @ pc


def refine(pred: np.ndarray, slices, anchor: int, iters: int,
           max_corr: float, reg: float, push: float) -> np.ndarray:
    cur = pred.copy()
    orig = pred.copy()
    for _ in range(iters):
        trees = [cKDTree(cur[a:b]) for a, b in slices]
        for i, (a, b) in enumerate(slices):
            if i == anchor:
                continue
            P, Q = [], []
            for j, (c, d) in enumerate(slices):
                if i == j:
                    continue
                dist, idx = trees[j].query(cur[a:b], distance_upper_bound=max_corr)
                m = np.isfinite(dist)
                if m.sum() < 8:
                    continue
                src = cur[a:b][m]
                dst = cur[c:d][idx[m]]
                # pull toward contact: move only PART way, and never past the
                # surface -- we want them touching, not fused.
                P.append(src)
                Q.append(src + (dst - src) * 0.5)
            # keep it anchored to the model's own answer
            step = max(1, int(reg * (b - a)))
            P.append(cur[a:b][:step])
            Q.append(orig[a:b][:step])
            P, Q = np.vstack(P), np.vstack(Q)
            R, t = kabsch(P, Q)
            moved = cur[a:b] @ R.T + t
            # reject a step that drives this fragment INTO another one
            ok = True
            for j, (c, d) in enumerate(slices):
                if i == j:
                    continue
                dd, _ = trees[j].query(moved)
                if np.mean(dd < push) > 0.35:
                    ok = False
                    break
            if ok:
                cur[a:b] = moved
    return cur


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--clouds-dir", required=True)
    ap.add_argument("--iters", type=int, default=60)
    ap.add_argument("--max-corr", type=float, default=0.06)
    ap.add_argument("--reg", type=float, default=0.15)
    ap.add_argument("--push", type=float, default=0.004)
    ap.add_argument("--out-json", default=None)
    ap.add_argument(
        "--save-refined", default=None,
        help="Directory to write npz files with the refined poses in place "
             "of the model's, so they can be exported as meshes and looked "
             "at. Needed for objects with no valid ground truth, where the "
             "scores printed here mean nothing and the geometry is the "
             "entire result.")
    args = ap.parse_args()

    rows = []
    for fp in sorted(glob.glob(os.path.join(args.clouds_dir, "*.npz"))):
        z = np.load(fp, allow_pickle=True)
        if "generations_proposed" not in z:
            continue
        ppp = z["points_per_part"]
        slices = part_slices(ppp)
        if len(slices) < 2:
            continue
        gt = z["pts_gt"]
        # CORRECTED 2026-09-05. The scoring was this script's own copy of the
        # metric, thresholded at `0.01 / scale` and commented "evaluator
        # threshold, this frame". It was neither: 0.01 in the object's own units
        # is the WITHDRAWN absolute metric, and dividing by the scale rather
        # than its square does not even convert it correctly, because the
        # tolerance is compared against a squared distance. It now scores
        # through scripts/readout.py, which also takes the free anchor out.
        # Every before -> after seating pair this script printed before this
        # date was scored too strictly and must be rerun before it is quoted.
        sizes = [b - a for a, b in slices]
        anchor = int(np.argmax(sizes))          # dataset uses the largest part

        before, after, refined = [], [], []
        for g in z["generations_proposed"]:
            r = refine(g, slices, anchor, args.iters, args.max_corr,
                       args.reg, args.push)
            refined.append(r)
            before.append(seating_from_clouds(g, gt, slices))
            after.append(seating_from_clouds(r, gt, slices))

        if args.save_refined:
            os.makedirs(args.save_refined, exist_ok=True)
            # Copy the file through with the refined poses substituted, so
            # the mesh exporter needs no special case: it reads exactly the
            # same fields and cannot tell the difference.
            payload = {k: z[k] for k in z.files}
            payload["generations_proposed"] = np.stack(refined)
            np.savez(os.path.join(args.save_refined,
                                  os.path.basename(fp)), **payload)
        # seating_from_clouds already takes the free anchor out, so these are
        # the fraction of the LOOSE fragments seated, averaged over draws.
        k = len(slices)
        rows.append({"name": str(z["name"]), "k": k,
                     "before": float(np.mean(before)),
                     "after": float(np.mean(after))})
        print(f"  {rows[-1]['name'][:38]:<38s} k={k:2d} "
              f"seating {rows[-1]['before']:.3f} -> {rows[-1]['after']:.3f}", flush=True)

    if rows:
        b = np.mean([r["before"] for r in rows])
        a = np.mean([r["after"] for r in rows])
        print(f"\n=== S2 seating refinement over {len(rows)} variants ===")
        print(f"  mean seating BEFORE: {b:.3f}")
        print(f"  mean seating AFTER : {a:.3f}   ({a - b:+.3f})")
        improved = sum(1 for r in rows if r["after"] > r["before"] + 1e-9)
        worsened = sum(1 for r in rows if r["after"] < r["before"] - 1e-9)
        print(f"  improved {improved}/{len(rows)} | worsened {worsened}/{len(rows)}")
        if args.out_json:
            open(args.out_json, "w").write(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
