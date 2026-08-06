"""Which objects does the wear model CRUMPLE instead of wearing?

The radius sweep settled the egg question, and not the way I guessed. The
measurement is not blind — it works fine at a 1.2% neighbourhood. What it shows
is that on eggshell, wear makes the break surface ROUGHER:

    egg1  at 1.2% radius   fresh 0.224 -> worn 0.667   (+198%)
    egg2  at 1.2% radius   fresh 0.467 -> worn 0.826   (+77%)
  vs
    blue_pot               fresh 0.029 -> worn 0.011   (-62%)
    galli_pot              fresh 0.106 -> worn 0.055   (-48%)

Thick-walled pots smooth by 40-60% at every scale, exactly as intended. Thin
shells do the opposite.

The mechanism is geometric and it should have been predictable. On a thin-walled
vessel the fracture surface IS the wall in cross-section — a ribbon no wider than
the wall itself. The smoothing kernel is 5% of the object's size. When the kernel
is wider than the ribbon it is smoothing, it stops averaging along the surface
and starts dragging the inner and outer wall toward each other, crumpling the
shell instead of rounding its edge. Crumpling adds high-frequency geometry, so
roughness rises.

This is not an egg curiosity. The Juglet is thin-walled, and it is the object
this entire effort exists to solve. Any thin-walled example in the training set
is teaching the model to expect crumpled shells, which is not what a worn sherd
looks like.

This survey finds every affected object. The signature is unambiguous and needs
no threshold-picking: wear should DECREASE roughness. Any object where it
increases is being crumpled.

Usage:
  python scripts/survey_thin_wall_wear.py
"""

import argparse
import json
import sys
from pathlib import Path

import h5py
import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wear_ops import apply_wear  # noqa: E402

# 1.2% of object size: fine enough to sit inside a thin wall, coarse enough that
# the reading has not yet collapsed to zero (it does by 0.5% on every object).
PROBE_RADIUS = 0.012


def _sample(v, f, n_pts, seed):
    m = trimesh.Trimesh(vertices=v.astype(np.float64), faces=f.astype(np.int64),
                        process=False)
    if len(m.faces) < 8 or max(m.extents) <= 0:
        return None, None, None, 0.0
    pts, fid = trimesh.sample.sample_surface(m, n_pts, seed=seed)
    return pts, m.face_normals[fid], m, float(max(m.extents))


def relief_at(v, f, radius_frac, n_pts=4000, seed=0):
    from scipy.spatial import cKDTree

    pts, fn, _, scale = _sample(v, f, n_pts, seed)
    if pts is None:
        return 0.0
    tree = cKDTree(pts)
    rel = np.zeros(len(pts))
    for i, ne in enumerate(tree.query_ball_point(pts, radius_frac * scale)):
        if len(ne) >= 3:
            rel[i] = 1.0 - float(np.clip(fn[ne] @ fn[i], -1, 1).mean())
    return float(np.percentile(rel, 90))


def wall_thickness(v, f, n_pts=4000, seed=0):
    """Distance across the wall, without ray-casting.

    The earlier ray-cast returned nan on every object — trimesh needs an engine
    that is not installed here. This gets the same quantity from geometry alone:
    for each surface point, find the nearest point whose normal faces the
    OPPOSITE way. On a shell that is the far side of the wall.

    Returned as a fraction of object size, so it can be compared directly with
    the smoothing kernel (0.05) and the measuring radius (0.03).
    """
    from scipy.spatial import cKDTree

    pts, fn, _, scale = _sample(v, f, n_pts, seed)
    if pts is None or scale <= 0:
        return float("nan")
    tree = cKDTree(pts)
    # 64 nearest neighbours is plenty to cross a thin wall; on a thick object no
    # opposite-facing point will be found and the entry is dropped
    d, idx = tree.query(pts, k=min(64, len(pts)), workers=-1)
    out = []
    for i in range(len(pts)):
        opp = np.where(fn[idx[i]] @ fn[i] < -0.5)[0]
        if len(opp):
            out.append(d[i, opp[0]])
    return float(np.median(out) / scale) if out else float("nan")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", default="/data/gpfs/projects/punim2657/TORA/dataset/real_finetune.hdf5")
    ap.add_argument("--dataset", default="real_finetune")
    ap.add_argument("--out-json", default="")
    ap.add_argument("--smoothing-kernel", type=float, default=0.05)
    args = ap.parse_args()

    print("Which objects does the wear model CRUMPLE instead of wear?")
    print(f"  probe radius {PROBE_RADIUS * 100:.1f}% of object size")
    print(f"  smoothing kernel {args.smoothing_kernel * 100:.1f}% of object size")
    print("  wear should REDUCE roughness. An increase means the kernel is wider")
    print("  than the wall it is smoothing, and the shell is being crumpled.")
    print()
    print(f"  {'object':<28s} {'wall':>7s} {'fresh':>8s} {'worn':>8s} {'change':>9s}  verdict")

    results = {}
    with h5py.File(args.src, "r") as h:
        ds = h[args.dataset]
        for obj in sorted(ds.keys()):
            grp = ds[obj]
            g = grp["pieces"] if "pieces" in grp else grp
            keys = sorted(g.keys(), key=lambda s: int(s) if s.isdigit() else s)
            pieces = [(np.asarray(g[k]["vertices"][:], dtype=np.float64),
                       np.asarray(g[k]["faces"][:], dtype=np.int64)) for k in keys]
            if len(pieces) < 2:
                continue

            wt = float(np.nanmedian([wall_thickness(v, f) for v, f in pieces]))
            worn = apply_wear(pieces, smoothing=1.0, smoothing_passes=3,
                              recession=0.0020, chip_count=4, chip_size=0.0022)
            a = float(np.mean([relief_at(v, f, PROBE_RADIUS) for v, f in pieces]))
            b = float(np.mean([relief_at(v, f, PROBE_RADIUS) for v, f in worn]))
            chg = 100.0 * (b - a) / a if a > 1e-9 else float("nan")

            crumpled = np.isfinite(chg) and chg > 0
            verdict = "CRUMPLED" if crumpled else "ok"
            wt_s = f"{wt * 100:.2f}%" if np.isfinite(wt) else "  --  "
            print(f"  {obj:<28s} {wt_s:>7s} {a:>8.4f} {b:>8.4f} {chg:>8.1f}%  {verdict}",
                  flush=True)
            results[obj] = {"wall_frac": wt, "relief_fresh": a, "relief_worn": b,
                            "change_pct": chg, "crumpled": bool(crumpled),
                            "n_pieces": len(pieces)}

    bad = [k for k, v in results.items() if v["crumpled"]]
    print()
    print(f"  {len(bad)} of {len(results)} objects crumpled: {', '.join(bad) or 'none'}")

    walls = [(v["wall_frac"], v["crumpled"]) for v in results.values()
             if np.isfinite(v["wall_frac"])]
    if walls:
        cw = [w for w, c in walls if c]
        ow = [w for w, c in walls if not c]
        if cw and ow:
            print(f"  crumpled objects' walls: {min(cw) * 100:.2f}-{max(cw) * 100:.2f}% "
                  f"of object size")
            print(f"  intact objects' walls:   {min(ow) * 100:.2f}-{max(ow) * 100:.2f}%")
            print(f"  smoothing kernel:        {args.smoothing_kernel * 100:.2f}%")
            print()
            print("  If the crumpled group sits below the kernel and the intact group")
            print("  above it, the fix is to scale the kernel to the WALL rather than")
            print("  to the object -- not to drop the thin-walled objects, which are")
            print("  the ones we most need to train on.")

    if args.out_json:
        Path(args.out_json).write_text(json.dumps(results, indent=2))
        print(f"\n  wrote {args.out_json}")


if __name__ == "__main__":
    main()
