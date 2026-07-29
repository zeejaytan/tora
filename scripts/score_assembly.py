"""Judge a reassembly WITHOUT the answer key, and check whether that judgement works.

The model already produces good reassemblies of worn pots — it just cannot tell
which of its attempts is the good one, because "best" is currently picked by
consulting ground truth. Real archaeological material has no ground truth, so
that headroom is unreachable in practice. Measured headroom on worn pots:
+0.12 to +0.21 seating (job 28229895).

This scores candidate assemblies on properties a conservator can judge by eye,
none of which need the answer:

  contact       do fragments actually meet along their edges?
  connectivity  is every fragment joined to the assembly, or left floating?
  overlap       do fragments pass through each other? (never acceptable)
  compactness   is the result gathered like a vessel, or sprawling?
  shell         is the surface thin-walled like pottery, rather than a solid lump?

Ground truth is used ONLY to validate the scores afterwards — never to compute
them. If a score genuinely tracks assembly quality it must earn that on the
sweep, where the true answer is known, before being trusted on the Juglet.

Usage:
  python scripts/score_assembly.py --clouds-dir <run>/clouds [--validate]
"""

import argparse
import glob
import json
import os

import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial import cKDTree


def part_slices(ppp):
    out, s = [], 0
    for n in ppp:
        n = int(n)
        if n > 0:
            out.append((s, s + n))
            s += n
    return out


def gt_free_features(pts, slices, diag):
    """Assembly-quality features computed with NO ground truth."""
    tau = 0.02 * diag           # "touching" at vessel scale
    tau_pen = 0.004 * diag      # closer than this = passing through
    trees = [cKDTree(pts[a:b]) for a, b in slices]
    k = len(slices)

    contact, overlap, touched = [], [], 0
    for i, (a, b) in enumerate(slices):
        best = np.full(b - a, np.inf)
        for j in range(k):
            if i == j:
                continue
            d, _ = trees[j].query(pts[a:b])
            best = np.minimum(best, d)
        c = float(np.mean(best < tau))
        contact.append(c)
        overlap.append(float(np.mean(best < tau_pen)))
        if c > 0.01:
            touched += 1

    ext = pts.max(0) - pts.min(0)
    asm_diag = float(np.linalg.norm(ext)) + 1e-9
    part_diags = [float(np.linalg.norm(pts[a:b].max(0) - pts[a:b].min(0))) for a, b in slices]

    # shell-likeness: for a thin-walled vessel most points sit near the outer
    # surface, so distance-to-hull-ish spread stays small relative to the object
    c0 = pts.mean(0)
    r = np.linalg.norm(pts - c0, axis=1)
    shell = float(r.std() / (r.mean() + 1e-9))

    return {
        "contact": float(np.mean(contact)),
        "connectivity": touched / k,
        "overlap": float(np.mean(overlap)),
        "compactness": float(np.mean(part_diags) / asm_diag),
        "shell": shell,
    }


def true_seating(pred, gt, slices, thr):
    """Ground truth — VALIDATION ONLY, never used to choose."""
    k = len(slices)
    cd = np.zeros((k, k))
    tg = [cKDTree(gt[a:b]) for a, b in slices]
    tp = [cKDTree(pred[a:b]) for a, b in slices]
    for i, (a, b) in enumerate(slices):
        for j, (c, d) in enumerate(slices):
            d1, _ = tp[j].query(gt[a:b])
            d2, _ = tg[i].query(pred[c:d])
            cd[i, j] = (d1 ** 2).mean() + (d2 ** 2).mean()
    r, c = linear_sum_assignment((cd >= thr).astype(float))
    pa = float((cd[r, c] < thr).sum()) / k
    return (pa * k - 1.0) / (k - 1.0) if k > 1 else float("nan")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--clouds-dir", required=True)
    ap.add_argument("--validate", action="store_true",
                    help="also compute true seating and report how well each "
                         "score tracks it (requires valid ground truth)")
    ap.add_argument("--out-json", default=None)
    args = ap.parse_args()

    rows = []
    for fp in sorted(glob.glob(os.path.join(args.clouds_dir, "*.npz"))):
        z = np.load(fp, allow_pickle=True)
        if "generations_proposed" not in z:
            continue
        sl = part_slices(z["points_per_part"])
        if len(sl) < 2:
            continue
        gt = z["pts_gt"]
        scale = float(z["scale"]) if "scale" in z else 1.0
        thr = 0.01 / max(scale, 1e-9)
        diag = float(np.linalg.norm(gt.max(0) - gt.min(0)))
        for gi, g in enumerate(z["generations_proposed"]):
            rec = {"name": str(z["name"]), "gen": gi}
            rec.update(gt_free_features(g, sl, diag))
            if args.validate:
                rec["true_seating"] = true_seating(g, gt, sl, thr)
            rows.append(rec)

    if not rows:
        print("no assemblies found")
        return

    feats = ["contact", "connectivity", "overlap", "compactness", "shell"]
    print(f"\n=== scored {len(rows)} assemblies from {args.clouds_dir} ===")

    if args.validate:
        from scipy.stats import spearmanr
        print("\nDoes each score track real quality? (ground truth used ONLY here)")
        for f in feats:
            x = [r[f] for r in rows]
            y = [r["true_seating"] for r in rows]
            rho, p = spearmanr(x, y)
            flag = "  <-- usable" if abs(rho) > 0.3 and p < 0.05 else ""
            print(f"  {f:<13s} rho={rho:+.3f}  p={p:.4f}{flag}")

        # can a score pick the good attempt, per object?
        byobj = {}
        for r in rows:
            byobj.setdefault(r["name"], []).append(r)
        print("\nPicking one attempt per object:")
        base = np.mean([np.mean([g["true_seating"] for g in v]) for v in byobj.values()])
        ceil = np.mean([max(g["true_seating"] for g in v) for v in byobj.values()])
        print(f"  take a random attempt (average): {base:.3f}")
        print(f"  an oracle picking the best     : {ceil:.3f}   (headroom {ceil - base:+.3f})")
        for f in feats:
            for sign, lab in ((1, ""), (-1, " (low)")):
                sel = [max(v, key=lambda r: sign * r[f])["true_seating"] for v in byobj.values()]
                got = np.mean(sel)
                if got > base + 1e-9:
                    frac = (got - base) / (ceil - base) if ceil > base else 0.0
                    print(f"  select by {f}{lab:<6s}: {got:.3f}   "
                          f"({frac * 100:.0f}% of the available headroom)")

    if args.out_json:
        open(args.out_json, "w").write(json.dumps(rows, indent=2))
        print(f"\nwrote {args.out_json}")


if __name__ == "__main__":
    main()
