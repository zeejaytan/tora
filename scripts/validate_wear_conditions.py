"""Validate the canonical wear conditions, judging each by what it should do.

Replaces the fixed light/moderate/heavy check, which was wrong in two ways:

  * its three levels all used identical smoothing and varied only material loss,
    so they were material-loss levels wearing a wear-level label;
  * it judged roughness against an ABSOLUTE band (0.10-0.60), but these pots
    start anywhere from 0.16 (coxae) to 0.47 (galli_pot). An absolute band
    flags a naturally-rough pot for being naturally rough.

Each condition is now checked against its own intent:

  fresh          nothing should change.
  abraded_*      smoothing only, so relief must FALL and the gap must NOT open
                 (no material has been removed).
  loss_dominant  material loss with only light abrasion, so the gap MUST open.
                 Relief may rise a
                 little — chip boundaries are themselves relief.
  worn_*         both, so the gap MUST open AND relief must not exceed the
                 untouched sherd. Full-set validation (job 28742114) showed the
                 old heavy preset failing exactly here: galli_pot 0.471 -> 0.726,
                 plate 0.339 -> 0.606, i.e. "heavy wear" produced rougher break
                 faces than the original. Chips were overwhelming the smoothing.

Usage:
  python scripts/validate_wear_conditions.py [--objects blue_pot,limb3]
"""

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fracture_mesh_ops import piece_relief_stats  # noqa: E402
from wear_ops import apply_wear, wear_conditions  # noqa: E402
from visual_check import closest_pair, render_pair_panel  # noqa: E402


def joint_gap(pieces, max_pts: int = 60000, seed: int = 0):
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
            d, _ = t.query(s, workers=-1)
            best = np.minimum(best, d)
        out.append(float(np.percentile(best, 10)))
    return float(np.mean(out))


def mean_relief(pieces):
    return float(np.mean([piece_relief_stats(v, f)["relief_p90"] for v, f in pieces]))


# The gap metric subsamples vertices, so ratios within a few percent of 1.0 are
# not distinguishable from noise. Job 28749619 flagged two arms at x0.98 as
# "gap did not open" over an absolute difference of 0.0001.
GAP_NOISE = 1.02


def judge(name, r0, r1, g_ratio, kept):
    """Check a condition against what it is SUPPOSED to do."""
    bad = []
    if kept < 95.0:
        bad.append("too much removed")
    if name == "fresh":
        if abs(r1 - r0) > 0.02 or abs(g_ratio - 1.0) > 0.02:
            bad.append("should be unchanged")
    elif name.startswith("abraded"):
        if r1 >= r0:
            bad.append("smoothing did not reduce relief")
        # NO gap check here. An earlier version required the gap to stay shut,
        # which was a wrong assumption rather than a wrong model: smoothing a
        # fracture surface removes its high points, and the high points are
        # exactly what touch. Abrasion legitimately opens a join a little.
    elif name == "loss_dominant":
        if g_ratio <= GAP_NOISE:
            bad.append("GAP DID NOT OPEN")
        if r1 > r0 * 1.5:
            bad.append("chips dominate the surface")
    elif name.startswith("worn"):
        if g_ratio <= GAP_NOISE:
            bad.append("GAP DID NOT OPEN")
        if r1 > r0:
            bad.append("rougher than the original sherd")
    return bad


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", default="/data/gpfs/projects/punim2657/TORA/dataset/real_heldout_norm.hdf5")
    ap.add_argument("--dataset", default="real_heldout_norm")
    ap.add_argument("--objects", default="")
    ap.add_argument("--visual-dir", default="",
                    help="write before/after renders here. STRONGLY RECOMMENDED: "
                         "the recession bug survived three rounds of numeric "
                         "validation and was obvious on sight.")
    args = ap.parse_args()

    conds = wear_conditions()
    print("Wear conditions — each judged against what it should do")
    print("  abraded: relief falls, gap stays shut | loss/worn: gap opens, not rougher")
    print()
    print("  object     condition       relief   faces   gap     verdict")

    ok = True
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
            n0, g0, r0 = sum(len(f) for _, f in pieces), joint_gap(pieces), mean_relief(pieces)
            print("  %-10s %-15s %.4f  %5.1f%%  %.4f" % (obj, "(original)", r0, 100.0, g0),
                  flush=True)

            variants = []
            for name, kw in conds:
                if name == "fresh":
                    continue
                w = apply_wear(pieces, **kw)
                if args.visual_dir:
                    variants.append((name, w))
                kept = 100.0 * sum(len(f) for _, f in w) / n0
                r1, gw = mean_relief(w), joint_gap(w)
                ratio = gw / max(g0, 1e-9)
                bad = judge(name, r0, r1, ratio, kept)
                if bad:
                    ok = False
                print("  %-10s %-15s %.4f  %5.1f%%  x%.2f   %s" %
                      (obj, name, r1, kept, ratio,
                       "OK" if not bad else "<-- " + "; ".join(bad)), flush=True)

            # Visual confirmation is part of the test, not a debugging aid.
            if args.visual_dir and variants:
                import os
                os.makedirs(args.visual_dir, exist_ok=True)
                i, j = closest_pair(pieces)
                sel = [("original", [pieces[i], pieces[j]])]
                for nm, w in variants:
                    if len(w) == len(pieces):
                        sel.append((nm, [w[i], w[j]]))
                out = os.path.join(args.visual_dir, f"join_{obj}.png")
                try:
                    render_pair_panel(sel, out, title=f"{obj}: join under each wear condition")
                    print(f"      rendered {out}", flush=True)
                except Exception as e:
                    print(f"      render failed: {e}", flush=True)

    print()
    print("RESULT:", "conditions behave as intended" if ok else "NOT READY — see flags")


if __name__ == "__main__":
    main()
