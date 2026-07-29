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

import sys
from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vessel_features import vessel_features  # noqa: E402


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

    contact, tight, touched = [], [], 0
    for i, (a, b) in enumerate(slices):
        best = np.full(b - a, np.inf)
        for j in range(k):
            if i == j:
                continue
            d, _ = trees[j].query(pts[a:b])
            best = np.minimum(best, d)
        c = float(np.mean(best < tau))
        contact.append(c)
        # NOTE: this is TIGHT CONTACT, not interpenetration. An earlier version
        # called it "overlap" and it correlated POSITIVELY with quality (+0.69),
        # which is the giveaway: correctly seated fragments sit close together.
        # Detecting true interpenetration needs inside/outside tests on
        # watertight meshes, which point clouds alone cannot provide.
        tight.append(float(np.mean(best < tau_pen)))
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
        "tight_contact": float(np.mean(tight)),
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
            try:
                rec.update(vessel_features(g))
            except Exception:
                rec.update({"axis_residual": np.nan, "profile_smooth": np.nan,
                            "thickness_cv": np.nan, "radial_gap": np.nan})
            if args.validate:
                rec["true_seating"] = true_seating(g, gt, sl, thr)
            rows.append(rec)

    if not rows:
        print("no assemblies found")
        return

    feats = ["contact", "connectivity", "tight_contact", "compactness", "shell",
             "axis_residual", "profile_smooth", "thickness_cv", "radial_gap"]
    rows = [r for r in rows if not any(
        isinstance(r.get(f), float) and np.isnan(r.get(f)) for f in feats)]
    print(f"\n=== scored {len(rows)} assemblies from {args.clouds_dir} ===")

    if args.validate:
        from scipy.stats import spearmanr, wilcoxon
        byobj = {}
        for r in rows:
            byobj.setdefault(r["name"], []).append(r)

        # THE RIGHT TEST. Selection happens WITHIN one object, choosing among its
        # attempts. A global correlation across different objects answers a
        # different question and can flatly disagree -- an earlier version of this
        # script reported `shell` at rho=-0.03 (useless) yet recovering 75% of the
        # headroom, which is exactly that mismatch.
        print("\nWithin-object ranking — does the score order THIS pot's attempts")
        print("the way real quality does? (ground truth used ONLY to check)")
        for f in feats:
            rhos = []
            for v in byobj.values():
                ys = [g["true_seating"] for g in v]
                if len(v) < 3 or len(set(ys)) < 2:
                    continue                      # no signal to rank
                rho, _ = spearmanr([g[f] for g in v], ys)
                if not np.isnan(rho):
                    rhos.append(rho)
            if not rhos:
                print(f"  {f:<15s} (no rankable objects)")
                continue
            m = float(np.mean(rhos))
            try:
                _, p = wilcoxon(rhos, alternative="two-sided")
            except Exception:
                p = float("nan")
            flag = "  <-- ranks correctly" if m > 0.2 and p < 0.05 else ""
            print(f"  {f:<15s} mean rho={m:+.3f}  n={len(rhos):2d} objects  p={p:.4f}{flag}")

        print("\nPicking one attempt per object (is the gain real?):")
        per_obj_mean = {k: np.mean([g["true_seating"] for g in v]) for k, v in byobj.items()}
        base = float(np.mean(list(per_obj_mean.values())))
        ceil = float(np.mean([max(g["true_seating"] for g in v) for v in byobj.values()]))
        print(f"  take an attempt at random : {base:.3f}")
        print(f"  an oracle picking the best: {ceil:.3f}   (headroom {ceil - base:+.3f})")
        for f in feats:
            for sign, lab in ((1, ""), (-1, " (low)")):
                sel = {k: max(v, key=lambda r: sign * r[f])["true_seating"]
                       for k, v in byobj.items()}
                got = float(np.mean(list(sel.values())))
                if got <= base + 1e-9:
                    continue
                a = [sel[k] for k in byobj]
                b = [per_obj_mean[k] for k in byobj]
                try:
                    _, p = wilcoxon(a, b, alternative="greater")
                except Exception:
                    p = float("nan")
                frac = (got - base) / (ceil - base) if ceil > base else 0.0
                sig = "SIGNIFICANT" if p < 0.05 else "not significant"
                print(f"  select by {f}{lab:<6s}: {got:.3f}  "
                      f"({frac * 100:3.0f}% of headroom)  p={p:.4f}  {sig}")

    if args.out_json:
        open(args.out_json, "w").write(json.dumps(rows, indent=2))
        print(f"\nwrote {args.out_json}")


if __name__ == "__main__":
    main()
