"""Rescore part accuracy with a threshold that does not depend on object units.

WHY THIS EXISTS. tora/eval/evaluator.py multiplies the point clouds back to
their original units before scoring:

    pts_gt_rescaled = pts_gt * scales.view(B, 1, 1)
    part_acc, _ = compute_part_acc(pts_gt_rescaled, pts_pred_rescaled, ...)

and compute_part_acc thresholds chamfer distance at a fixed 0.01. That is only
meaningful if every dataset arrives in the same units. They do not:

    Breaking Bad vessels     scale ~0.50     0.01 is  2% of the object
    Fractura bone_synthetic  scale ~0.56     0.01 is  2% of the object
    Fractura ceramics (real) scale ~74       0.01 is  0.014% of the object
    Fractura bones (real)    scale ~24       0.01 is  0.04%  of the object
    Fractura egg (real)      scale ~52       0.01 is  0.02%  of the object

The real Fractura subsets are stored in millimetres. Asking a fragment to land
within a hundredth of a millimetre is asking for the impossible, so every real
object scores exactly one seated fragment -- the anchor, which is placed at
ground truth by construction and has chamfer ~0. Job 24342475 read 0 earned
fragments on all 27 real objects across three materials, and that number was
the threshold, not the model.

WHAT THIS DOES. The visualizer's npz keeps everything in the dataloader's
normalized frame plus the scale factor, so nothing needs rerunning. This scores
in that normalized frame, where every object has max|coord| = 1, and sweeps the
threshold. The like-for-like setting is 0.02: Breaking Bad objects sit at
scale 0.5, so the published 0.01-after-rescaling equals 0.02 before it.

It also reproduces the shipped metric (--absolute) so the two can be compared
on the same predictions, which is the check that this script is right.

Usage:
  python scripts/rescore_part_acc.py --clouds <run_dir>/clouds [--absolute]
"""

import argparse
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment

# Normalized-frame equivalents of the published 0.01. Breaking Bad objects sit
# at scale ~0.5, so 0.02 is the like-for-like number; the rest bracket it.
THRESHOLDS = (0.005, 0.01, 0.02, 0.05, 0.10)


def chamfer(a: np.ndarray, b: np.ndarray) -> float:
    """Symmetric mean chamfer distance between two small point sets."""
    d = np.linalg.norm(a[:, None, :] - b[None, :, :], axis=-1)
    return 0.5 * (d.min(axis=1).mean() + d.min(axis=0).mean())


def part_acc(pts_gt, pts_pred, ppp, thresholds):
    """Fraction of parts whose chamfer to their matched GT part is under each threshold.

    Hungarian matching on the chamfer cost, as compute_part_acc does: parts are
    interchangeable, so a prediction is allowed to claim any GT part once.
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
    return {t: float((matched < t).mean()) for t in thresholds}, matched


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clouds", required=True, help="a run's clouds/ directory")
    ap.add_argument("--absolute", action="store_true",
                    help="reproduce the shipped metric: rescale by the object's "
                         "own scale, then threshold at a fixed 0.01")
    a = ap.parse_args()

    files = sorted(Path(a.clouds).glob("*.npz"))
    if not files:
        raise SystemExit(f"no npz under {a.clouds}")

    per_obj = defaultdict(lambda: defaultdict(list))
    scales = []
    for f in files:
        d = np.load(f, allow_pickle=True)
        key = "generations_proposed" if "generations_proposed" in d else "generations_pred"
        gens = d[key]
        gt = d["pts_gt"]
        ppp = d["points_per_part"]
        scale = float(d["scale"]) if "scale" in d else 1.0
        scales.append(scale)
        name = str(d["name"])
        for g in gens:
            if a.absolute:
                acc, _ = part_acc(gt * scale, g * scale, ppp, (0.01,))
            else:
                acc, _ = part_acc(gt, g, ppp, THRESHOLDS)
            for t, v in acc.items():
                per_obj[name][t].append(v)

    ts = (0.01,) if a.absolute else THRESHOLDS
    mode = ("shipped metric: rescaled to original units, threshold 0.01"
            if a.absolute else
            "normalized frame, max|coord| = 1; 0.02 is the Breaking Bad equivalent")
    print(f"\n{Path(a.clouds).parent.name}")
    print(f"{mode}")
    print(f"object scale: median {np.median(scales):.3f}\n")

    nw = max(len(n) for n in per_obj)
    print(f"{'object':{nw}s}  draws  " + "  ".join(f"t={t:<6.3f}" for t in ts))
    for name, by_t in sorted(per_obj.items()):
        n = len(by_t[ts[0]])
        cells = "  ".join(f"{100 * np.mean(by_t[t]):7.1f}%" for t in ts)
        print(f"{name:{nw}s}  {n:5d}  {cells}")

    print(f"\n{'ALL':{nw}s}  {'':5s}  " + "  ".join(
        f"{100 * np.mean([v for by_t in per_obj.values() for v in by_t[t]]):7.1f}%" for t in ts))
    print("\nThese percentages include the anchor fragment, which is placed at")
    print("ground truth by construction. On a 4-fragment pot the anchor alone")
    print("is 25%, so read anything at or below 1/n_parts as nothing placed.\n")


if __name__ == "__main__":
    main()
