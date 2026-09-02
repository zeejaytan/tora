"""Rescore part accuracy off saved clouds, with the threshold in a unit box.

WHY THIS EXISTS. tora/eval/evaluator.py used to multiply the point clouds back
to their original units before scoring:

    pts_gt_rescaled = pts_gt * scales.view(B, 1, 1)
    part_acc, _ = compute_part_acc(pts_gt_rescaled, pts_pred_rescaled, ...)

and compute_part_acc thresholds squared chamfer distance at a fixed 0.01. That
is only meaningful if every dataset arrives in the same units. They do not:

    Breaking Bad vessels     scale ~0.50
    Fractura bone_synthetic  scale ~0.56
    Fractura ceramics (real) scale ~61   (millimetres)
    Fractura bones (real)    scale ~24   (millimetres)
    Fractura egg (real)      scale ~52   (millimetres)

Breaking Bad states tau = 0.01 inside a unit-length box -- "We re-scale each of
them to fit a unit-length box for parameter choice consistency. This
normalization scheme allows our method to be scale invariant" (Sellan et al.
2022). Rescaling to millimetres first destroys exactly that invariance. Every
real Fractura object then scored exactly 1/n_parts, which is the free anchor.

The evaluator has since been fixed (tora/eval/metrics.py:unit_box_scale, guarded
by scripts/check_metric_scale_invariance.py). This script exists to rescore runs
that were evaluated BEFORE that fix, straight from the visualizer's saved npz,
without spending GPU time.

CORRECTION, 2026-09-02. An earlier version of this file used a fixed threshold
of 0.04 in the dataloader frame, derived from assuming that frame has a bounding
box of side 2 (because max|coord| = 1). It does not. center_pcd centres by
centroid, not by bounding-box centre, so a real object's box side is smaller --
1.695 for narrow_bottle4. That made the old threshold about 40% too loose, and a
0.16 column 5.6x looser still was printed alongside it. Numbers computed with
that version, including the 38%/40% figures once written into
docs/notes/FRACTURA_WHY_IT_FAILS.md, are wrong and were withdrawn.

The threshold is now derived per object exactly as the evaluator derives it:
divide both clouds by the longest side of the GROUND TRUTH bounding box, then
apply 0.01 there. Measured on the ground truth, never the prediction -- a
scattered prediction has a bigger box than the object it is rebuilding, and
using it would hand a failing assembly a more forgiving tolerance.

Usage:
  python scripts/rescore_part_acc.py --clouds <run_dir>/clouds
  python scripts/rescore_part_acc.py --clouds <run_dir>/clouds --absolute
  python scripts/rescore_part_acc.py --clouds <run_dir>/clouds --which proposed
"""

import argparse
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment

# Breaking Bad's tau, in the frame Breaking Bad states it in: a unit-length box.
# compute_part_acc thresholds pytorch3d's chamfer_distance with
# point_reduction="mean", which is the mean of SQUARED distances, so this is a
# squared tolerance -- 0.1 of the object's longest dimension, linearly.
TAU = 0.01

# The shipped metric, kept for --absolute so the two can be compared on the same
# predictions. This is the number that was scale-dependent.
TAU_ABSOLUTE = 0.01


def unit_box_scale(pts: np.ndarray) -> float:
    """Longest side of a cloud's axis-aligned bounding box."""
    return float(max((pts.max(axis=0) - pts.min(axis=0)).max(), 1e-8))


def chamfer(a: np.ndarray, b: np.ndarray) -> float:
    """Symmetric mean of squared nearest-neighbour distances, as pytorch3d does."""
    d = ((a[:, None, :] - b[None, :, :]) ** 2).sum(-1)
    return 0.5 * (d.min(axis=1).mean() + d.min(axis=0).mean())


def part_acc(pts_gt, pts_pred, ppp, threshold):
    """Fraction of parts whose chamfer to their matched GT part is under threshold.

    Hungarian matching on the chamfer cost, as compute_part_acc does: parts are
    interchangeable, so a prediction may claim any GT part once.
    """
    ppp = [int(n) for n in ppp if int(n) > 0]
    bounds = np.cumsum([0] + ppp)
    gt = [pts_gt[bounds[i]:bounds[i + 1]] for i in range(len(ppp))]
    pr = [pts_pred[bounds[i]:bounds[i + 1]] for i in range(len(ppp))]
    p = len(ppp)
    cost = np.zeros((p, p))
    for i in range(p):
        for j in range(p):
            cost[i, j] = chamfer(gt[i], pr[j])
    r, c = linear_sum_assignment(cost)
    matched = cost[r, c]
    return float((matched < threshold).mean()), len(ppp)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clouds", required=True, help="a run's clouds/ directory")
    ap.add_argument("--which", choices=("pred", "proposed"), default="pred",
                    help="pred = generations_pred, the raw flow output, which is "
                         "what the evaluator scores; proposed = the input parts "
                         "rigidly posed by the predicted SE(3)")
    ap.add_argument("--absolute", action="store_true",
                    help="reproduce the old shipped metric: rescale by the "
                         "object's own scale, then threshold at a fixed 0.01")
    a = ap.parse_args()

    files = sorted(Path(a.clouds).glob("*.npz"))
    if not files:
        raise SystemExit(f"no npz under {a.clouds}")

    rows = []
    for f in files:
        d = np.load(f, allow_pickle=True)
        key = "generations_" + ("pred" if a.which == "pred" else "proposed")
        if key not in d:
            raise SystemExit(f"{f.name} has no {key}; saved keys: {list(d.keys())}")
        gens = d[key]
        gt = d["pts_gt"]
        ppp = d["points_per_part"]
        scale = float(d["scale"]) if "scale" in d else 1.0
        name = str(d["name"])

        unit = unit_box_scale(gt)
        accs = []
        for g in gens:
            if a.absolute:
                acc, n = part_acc(gt * scale, g * scale, ppp, TAU_ABSOLUTE)
            else:
                acc, n = part_acc(gt / unit, g / unit, ppp, TAU)
            accs.append(acc)
        n_parts = int(sum(1 for v in ppp if int(v) > 0))
        rows.append((name, n_parts, len(accs), float(np.mean(accs)), scale, unit))

    mode = ("OLD shipped metric: rescaled to stored units, squared-CD threshold 0.01"
            if a.absolute else
            f"unit box: both clouds divided by the GT bbox longest side, tau = {TAU}")
    print(f"\n{Path(a.clouds).parent.name}   [{a.which}]")
    print(mode)
    print()

    nw = max(len(r[0]) for r in rows)
    print(f"{'object':{nw}s}  parts  draws  {'anchor floor':>12s}  {'scored':>8s}  "
          f"{'earned':>7s}  {'gt box':>7s}")
    tot_score, tot_floor = [], []
    for name, n_parts, n_draws, acc, scale, unit in sorted(rows):
        floor = 1.0 / n_parts
        tot_score.append(acc)
        tot_floor.append(floor)
        print(f"{name:{nw}s}  {n_parts:5d}  {n_draws:5d}  {100 * floor:11.1f}%  "
              f"{100 * acc:7.1f}%  {100 * (acc - floor):6.1f}%  {unit:7.3f}")

    ms, mf = float(np.mean(tot_score)), float(np.mean(tot_floor))
    print(f"\n{'MEAN':{nw}s}  {'':5s}  {'':5s}  {100 * mf:11.1f}%  "
          f"{100 * ms:7.1f}%  {100 * (ms - mf):6.1f}%")
    print("\nThe anchor fragment is placed at ground truth by construction and")
    print("always passes, so 1/n_parts is the floor a model earns nothing for.")
    print("Read the 'earned' column: that is what the model actually seated.\n")


if __name__ == "__main__":
    main()
