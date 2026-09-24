"""Are TORA's sherds put down inside out, and can "outside faces out" catch it?

Ticket .scratch/juglet-cause/issues/14-inside-out-sherds.md. For every sherd in
every saved attempt (solid sherds, generations_proposed):

  label  (answer key)   the sherd's curvature direction in its true pose, turned
                        by its rigid move, is reversed -> inside out
  rule   (no key)       its curvature centre lies on the far side from the
                        assembled attempt's centroid -> flagged inside out
  strict home           own-place home AND each point, on average, within SEAT_PCT
                        of its own true point (a turned-over sherd fails this)

and tries one reference-free correction: turn a flagged sherd 180 deg about an
in-wall axis through its centroid, keeping the one of 12 axes whose edge points
sit closest to the other sherds.

Usage (from C:\\PR\\tora):
  python scripts/check_inside_out.py LABEL=NPZ [LABEL=NPZ ...] [--held 0,6] \\
      [--json out.json]
  --held applies to every NPZ given in that call (sherds pinned by the job).
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parent))
from own_place import SEAT_PCT, score_draw  # noqa: E402
from readout import part_slices, unit_box_scale  # noqa: E402

FLAT = 3.0          # undecidable if sphere radius > FLAT x sherd's longest side
REVERSED = -0.5     # label: curvature direction cosine below this = inside out
N_AXES = 12
EDGE_FRAC = 0.10


def kabsch(a, b):
    ca, cb = a.mean(0), b.mean(0)
    u, _, vt = np.linalg.svd((a - ca).T @ (b - cb))
    d = np.sign(np.linalg.det(vt.T @ u.T))
    r = vt.T @ np.diag([1, 1, d]) @ u.T
    return r, cb - r @ ca


def curvature(pts):
    """(unit direction centroid -> sphere centre, decidable?)"""
    a = np.c_[2 * pts, np.ones(len(pts))]
    sol = np.linalg.lstsq(a, (pts ** 2).sum(1), rcond=None)[0]
    c = sol[:3]
    rad = np.sqrt(max(sol[3] + c @ c, 0.0))
    d = c - pts.mean(0)
    ok = rad < FLAT * np.ptp(pts, 0).max() and np.linalg.norm(d) > 0
    return d / (np.linalg.norm(d) + 1e-12), bool(ok)


def rule_flag(sherd, centre):
    d, ok = curvature(sherd)
    return (d @ (centre - sherd.mean(0)) < 0) if ok else None


def rot_about(axis, ang):
    k = axis / np.linalg.norm(axis)
    kx = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + np.sin(ang) * kx + (1 - np.cos(ang)) * kx @ kx


def correct(sherd, others):
    """Flip 180 deg about the in-wall axis whose edge points sit closest to the rest."""
    d, _ = curvature(sherd)
    e1 = np.cross(d, [1, 0, 0] if abs(d[0]) < 0.9 else [0, 1, 0])
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(d, e1)
    tree, m = cKDTree(others), sherd.mean(0)
    best = None
    for th in np.linspace(0, np.pi, N_AXES, endpoint=False):
        cand = (sherd - m) @ rot_about(np.cos(th) * e1 + np.sin(th) * e2, np.pi).T + m
        gap = np.sort(tree.query(cand)[0])[: max(1, int(EDGE_FRAC * len(cand)))].mean()
        if best is None or gap < best[0]:
            best = (gap, cand)
    return best[1]


def own_point_pct(g, p, unit):
    return 100.0 * np.linalg.norm(g - p, axis=1).mean() / unit


def run(label, npz, held):
    d = np.load(npz, allow_pickle=True)
    gt = d["pts_gt"].astype(float)
    sl = list(part_slices(d["points_per_part"]))
    unit = unit_box_scale(gt)
    gcentre = gt.mean(0)
    truth_rule = [rule_flag(gt[a:b], gcentre) for a, b in sl]   # prediction 1
    rows, per_attempt = [], []
    for t, pred in enumerate(d["generations_proposed"].astype(float)):
        dr = score_draw(gt, pred, d["points_per_part"])
        centre = pred.mean(0)
        n_flag = n_strict = 0
        for s, (a, b) in enumerate(sl):
            if s in held or s == dr.anchor:   # pinned sherds are not placements
                continue
            g, p = gt[a:b], pred[a:b]
            r, _ = kabsch(g, p)
            dg, ok = curvature(g)
            label_io = bool((r @ dg) @ dg < REVERSED) if ok else None
            flag = rule_flag(p, centre)
            opp = own_point_pct(g, p, unit)
            strict = dr.status[s] == "own" and opp < SEAT_PCT
            fixed = None
            if flag:
                q = correct(p, np.delete(pred, np.s_[a:b], 0))
                fixed = own_point_pct(g, q, unit) < SEAT_PCT
            turn = float(np.degrees(np.arccos(np.clip((np.trace(r) - 1) / 2, -1, 1))))
            rows.append(dict(obj=label, t=t, s=s, chamfer_home=dr.status[s] == "own",
                             strict=bool(strict), label=label_io, flag=flag,
                             fixed=fixed, turn=round(turn, 1), own_pt=round(opp, 2)))
            n_flag += bool(flag)
            n_strict += strict
        per_attempt.append((n_flag, n_strict))
    return str(d["name"]), truth_rule, rows, per_attempt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cases", nargs="+")
    ap.add_argument("--held", default="")
    ap.add_argument("--json")
    a = ap.parse_args()
    held = {int(x) for x in a.held.split(",") if x}
    out = []
    for case in a.cases:
        label, npz = case.split("=", 1)
        name, truth, rows, att = run(label, Path(npz), held)
        dec = [x for x in truth if x is not None]
        home = [r for r in rows if r["chamfer_home"]]
        both = [r for r in home if r["label"] is not None and r["flag"] is not None]
        agree = sum(r["label"] == r["flag"] for r in both)
        io = sum(bool(r["label"]) for r in home)
        fl_home = [r for r in home if r["flag"]]
        fixed = sum(bool(r["fixed"]) for r in fl_home)
        nf, ns = np.array(att).T
        rho = spearmanr(nf, ns)[0] if nf.std() and ns.std() else float("nan")
        free = len(rows)
        print(f"{label} ({name}), {len(att)} attempts, {free} free placements")
        print(f"  P1 correct assembly: rule says inside out on {sum(dec)} of {len(dec)} "
              f"decidable sherds ({len(truth) - len(dec)} too flat)")
        print(f"  home by chamfer {len(home)}, strict home {sum(r['strict'] for r in rows)}; "
              f"inside out (label) among chamfer-home: {io}")
        print(f"  P2 rule agrees with label on {agree}/{len(both)} decidable chamfer-home")
        print(f"  P4 flagged vs strict-home per attempt: rho {rho:.2f} "
              f"(flags per attempt {nf.min()}-{nf.max()})")
        print(f"  P5 flagged & chamfer-home: {len(fl_home)}, strict home after correction: {fixed}")
        out.append(dict(label=label, name=name, truth_rule=truth, rows=rows,
                        per_attempt=att, rho=rho))
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps(out, default=lambda o: o.item() if hasattr(o, "item") else str(o)))


if __name__ == "__main__":
    main()
