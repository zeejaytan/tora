"""Re-score saved attempts against a re-seated reference (pr-workspace U20 ticket 11).

The conservator's lead (2026-11-08): rough training wins on the Juglet because the hand-set
reference `juglet_gt` has sherds slightly inside each other. `juglet_gt_snug` (ticket 08, job
34517825) moves each sherd rigidly by at most 0.73 mm / 1.8 deg to clear that. This scores every
saved attempt twice with own_place's own `score_draw`: against the truth cloud the run saved, and
against the same points carried onto the snug pose. Same ruler both times: the tolerance unit is
the saved truth's box, so only the reference changes.

How the truth points are carried over. A saved cloud is in the loader's frame, not the HDF5's.
1. Fit one similarity (scale, turn, shift) from the cloud's truth points to the OLD reference's
   vertices: 24 axis-aligned starts, then nearest-vertex Umeyama refinement. The fit residual is
   printed in mm and the job stops if it is over half a scan spacing (0.15 mm).
2. Each cloud slice is matched to the sherd its points lie on (median distance), one to one.
3. Each sherd's move old->new is its exact rigid fit over its own vertices (same vertex order
   in both files), carried into the cloud frame through the similarity.

    python scripts/rescore_on_new_reference.py --old juglet_gt.hdf5 --new juglet_gt_snug.hdf5 \
        --group juglet_gt --pot-mm 65 --json out.json RUN [RUN ...]
"""

import argparse
import itertools
import json
import sys
from pathlib import Path

import h5py
import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from own_place import CLOUDS, score_draw  # noqa: E402
from readout import clouds_by_object, unit_box_scale  # noqa: E402


def load_pieces(path, group, faces=False):
    with h5py.File(path, "r") as h:
        tag = sorted(t for t in h[group] if "pieces" in h[group][t])[0]
        g = h[group][tag]["pieces"]
        keys = sorted(g.keys(), key=lambda s: (len(s), s))
        V = [np.asarray(g[k]["vertices"][:], dtype=np.float64) for k in keys]
        if faces:
            return keys, V, [np.asarray(g[k]["faces"][:], dtype=np.int64) for k in keys]
        return keys, V


def kabsch(a, b, scale=False):
    """b ~ s R a + t (least squares). Returns s, R, t."""
    ca, cb = a.mean(0), b.mean(0)
    A, B = a - ca, b - cb
    U, S, Vt = np.linalg.svd(B.T @ A)
    D = np.diag([1, 1, np.sign(np.linalg.det(U @ Vt))])
    R = U @ D @ Vt
    s = float((S * np.diag(D)).sum() / (A ** 2).sum()) if scale else 1.0
    return s, R, cb - s * R @ ca


def rotations24():
    out = []
    for perm in itertools.permutations(range(3)):
        for signs in itertools.product((1, -1), repeat=3):
            M = np.zeros((3, 3))
            for i, (p, sg) in enumerate(zip(perm, signs)):
                M[i, p] = sg
            if np.linalg.det(M) > 0:
                out.append(M)
    return out


def fit_frame(P, V_all, iters=40):
    """Similarity mapping cloud points P onto the vertex set V_all (old pose)."""
    tree = cKDTree(V_all)
    rng = np.random.default_rng(0)
    Q = P[rng.choice(len(P), min(len(P), 4000), replace=False)]
    s0 = unit_box_scale(V_all) / unit_box_scale(P)
    best = None
    for R0 in rotations24():
        s, R = s0, R0
        t = V_all.mean(0) - s * R @ Q.mean(0)
        for _ in range(iters):
            X = s * Q @ R.T + t
            _, idx = tree.query(X)
            s, R, t = kabsch(Q, V_all[idx], scale=True)
        d, _ = tree.query(s * Q @ R.T + t)
        med = float(np.median(d))
        if best is None or med < best[0]:
            best = (med, s, R, t)
    return best


def carry(gt, ppp, old, new, meshes, jf, tol_mm):
    """The saved truth cloud carried onto the new pose, plus a record of the fit."""
    from scipy.optimize import linear_sum_assignment
    ppp = [int(n) for n in np.asarray(ppp).reshape(-1) if int(n) > 0]
    cuts = np.cumsum([0] + ppp)
    med, s, R, t = fit_frame(gt, np.vstack(old))
    trees = [cKDTree(v) for v in old]
    X = s * gt @ R.T + t
    cost = np.array([[np.median(tr.query(X[a:b])[0]) for tr in trees]
                     for a, b in zip(cuts[:-1], cuts[1:])])
    rows, cols = linear_sum_assignment(cost)
    # refine on the surfaces themselves, each slice against its own sherd
    for _ in range(15):
        X = s * gt @ R.T + t
        tgt = np.empty_like(X)
        for r, c in zip(rows, cols):
            a, b = cuts[r], cuts[r + 1]
            tgt[a:b] = meshes[c].nearest.on_surface(X[a:b])[0]
        s, R, t = kabsch(gt, tgt, scale=True)
    X = s * gt @ R.T + t
    resid_mm = []
    for r, c in zip(rows, cols):
        a, b = cuts[r], cuts[r + 1]
        resid_mm.append(float(np.median(meshes[c].nearest.on_surface(X[a:b])[1]) * jf))
    med = float(np.median(resid_mm)) / jf
    if max(resid_mm) > tol_mm:
        raise SystemExit(f"frame fit off: per-sherd median residual {resid_mm} mm > {tol_mm}")
    out = gt.copy()
    moves = []
    for r, c in zip(rows, cols):
        _, Ri, ti = kabsch(old[c], new[c])
        a, b = cuts[r], cuts[r + 1]
        Y = Ri @ X[a:b].T
        Y = Y.T + ti
        out[a:b] = ((Y - t) / s) @ R          # back into the cloud frame
        moved = np.linalg.norm(Y - X[a:b], axis=1).max() * jf
        ang = np.degrees(np.arccos(np.clip((np.trace(Ri) - 1) / 2, -1, 1)))
        moves.append({"slice": int(r), "sherd": int(c), "max_move_mm": float(moved),
                      "turn_deg": float(ang)})
    return out, {"frame_resid_mm_median": med * jf, "per_sherd_resid_mm": resid_mm,
                 "scale": s, "moves": moves}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("runs", nargs="+", type=Path)
    ap.add_argument("--old", required=True)
    ap.add_argument("--new", required=True)
    ap.add_argument("--group", default="juglet_gt")
    ap.add_argument("--pot-mm", type=float, default=65.0, help="old reference's longest side, mm")
    ap.add_argument("--tol-mm", type=float, default=0.15)
    ap.add_argument("--json", type=Path, required=True)
    a = ap.parse_args()

    import trimesh
    ko, old, faces = load_pieces(a.old, a.group, faces=True)
    meshes = [trimesh.Trimesh(v, f, process=False) for v, f in zip(old, faces)]
    kn, new = load_pieces(a.new, a.group)
    assert ko == kn and all(o.shape == n.shape for o, n in zip(old, new)), "piece lists differ"
    jf = a.pot_mm / unit_box_scale(np.vstack(old))
    print(f"reference mm per unit {jf:.4f}; sherd moves old->new (mm, deg):")
    for k, o, n in zip(ko, old, new):
        _, Ri, ti = kabsch(o, n)
        mv = np.linalg.norm(o @ Ri.T + ti - o, axis=1).max() * jf
        fit = np.linalg.norm(o @ Ri.T + ti - n, axis=1).max() * jf
        ang = np.degrees(np.arccos(np.clip((np.trace(Ri) - 1) / 2, -1, 1)))
        print(f"  {k:10s} move {mv:.3f} turn {ang:.2f} (rigid fit residual {fit:.2e})")

    dump = {}
    for run in a.runs:
        for name, npz in sorted(clouds_by_object(run).items()):
            with np.load(npz, allow_pickle=True) as d:
                gt, ppp = d["pts_gt"], d["points_per_part"]
                preds = {c: d[k] for c, k in CLOUDS.items()}
            gt_new, rec = carry(gt, ppp, old, new, meshes, jf, a.tol_mm)
            unit = unit_box_scale(gt)
            row = {"fit": rec}
            for c, ps in preds.items():
                before = [score_draw(gt, p, ppp, unit) for p in ps]
                after = [score_draw(gt_new, p, ppp, unit) for p in ps]
                row[c] = {k: [getattr(x, k) for x in before] for k in ("own", "oriented")}
                row[c].update({k + "_snug": [getattr(x, k) for x in after]
                               for k in ("own", "oriented")})
                changed = [i for i, (x, y) in enumerate(zip(before, after))
                           if (x.own, x.oriented) != (y.own, y.oriented)]
                row[c]["changed"] = [{"attempt": i, "own": [before[i].own, after[i].own],
                                      "oriented": [before[i].oriented, after[i].oriented],
                                      "point_pct": [before[i].point_pct, after[i].point_pct]}
                                     for i in changed]
            key = f"{run}::{name}"
            dump[key] = row
            s = row["solid"]
            print(f"--- {key}\n    frame resid {rec['frame_resid_mm_median']:.3f} mm; "
                  f"solid own {sum(s['own'])}->{sum(s['own_snug'])}, right way round "
                  f"{sum(s['oriented'])}->{sum(s['oriented_snug'])}, best {max(s['oriented'])}->"
                  f"{max(s['oriented_snug'])}; attempts changed {len(s['changed'])} of {len(s['own'])}")
    a.json.parent.mkdir(parents=True, exist_ok=True)
    a.json.write_text(json.dumps(dump, indent=1))
    print("wrote", a.json)


if __name__ == "__main__":
    main()
