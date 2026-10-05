"""Synthetic check of Layer 1 (--profile outer). Run on Spartan (CPU job), not the laptop.

A plate and a bottle (6 mm wall) cut into sherds; one sherd at a time pushed out 2/5 mm,
lifted 15 mm, tilted 90 deg, turned upside down or inside out. Prints that sherd's reading
/ the attempt's, U if a sherd is unjudged, then the verdict: P pass / F fail (cut-off
--profile-mm, default 1.72 = the calibrated 1.72% of a ~100 mm pot; --unjudged fail makes
an unjudged sherd fail the attempt). Correct attempts must read ~0, no U, and P.

Usage: python scripts/l1_synthetic.py [--near MM ...] [--no-whole] [--unjudged fail]
       (None = whole outer surface)
"""
import argparse
import sys
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation as Rot

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rank_attempts as RA  # noqa: E402

T = 6.0
KINDS = ("push2", "push5", "lift15", "tilt90", "upside", "flip")


def poly(pts, step=0.5):
    pts = np.asarray(pts, float)
    out = []
    for a, b in zip(pts[:-1], pts[1:]):
        n = max(2, int(np.linalg.norm(b - a) / step))
        out.append(a + (b - a) * np.linspace(0, 1, n, endpoint=False)[:, None])
    out.append(pts[-1:])
    P = np.concatenate(out)
    return P, np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]


def arc(c, R, a0, a1, n=30):
    a = np.linspace(a0, a1, n)
    return np.c_[c[0] + R * np.cos(a), c[1] + R * np.sin(a)]


def plate():
    return np.r_[[[0, 0], [70, 0]], arc((70, 12), 12, -np.pi / 2, -0.25, 15)[1:], [[110, 28]]]


def bottle():
    return np.r_[[[0, 0]], [[30, 0]], arc((30, 15), 15, -np.pi / 2, 0, 10)[1:],
                 [[45, 50]], [[34, 75]], [[12, 95]], [[12, 125]]]


def build(prof, cuts_s, cuts_th, rng):
    P, s = poly(prof)
    dP = np.gradient(P, axis=0)
    dP /= np.linalg.norm(dP, axis=1, keepdims=True)
    n2 = np.c_[dP[:, 1], -dP[:, 0]]
    sherds = []
    for (s0, s1), ths in zip(cuts_s, cuts_th):
        for t0, t1 in ths:
            sel = (s >= s0) & (s < s1)
            pts, nrm = [], []
            for side in (+1, -1):
                for (r, h), (nr, nh) in zip(P[sel] + side * T / 2 * n2[sel], side * n2[sel]):
                    m = max(2, int(abs(r) * (t1 - t0) / 0.7))
                    th = np.linspace(t0, t1, m)
                    pts.append(np.c_[r * np.cos(th), r * np.sin(th), np.full(m, h)])
                    nrm.append(np.c_[nr * np.cos(th), nr * np.sin(th), np.full(m, nh)])
            p = np.concatenate(pts)
            sherds.append((p + rng.normal(0, 0.2, p.shape), np.concatenate(nrm)))
    return sherds


def move(sh, k, kind):
    out = [(p.copy(), n.copy()) for p, n in sh]
    p, n = out[k]
    c = p.mean(0)
    ur = np.r_[c[:2], 0]
    ur /= np.linalg.norm(ur) + 1e-12
    ut = np.cross([0, 0, 1], ur)
    if kind.startswith("push"):
        p = p + float(kind[4:]) * ur
    elif kind == "lift15":
        p = p + [0, 0, 15]
    else:
        ax, deg = {"tilt90": (ut, 90), "upside": (ur, 180), "flip": ([0, 0, 1], 180)}[kind]
        R = Rot.from_rotvec(np.radians(deg) * np.asarray(ax, float)).as_matrix()
        p, n = (p - c) @ R.T + c, n @ R.T
    out[k] = (p, n)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--near", nargs="*", type=float, default=[])
    ap.add_argument("--no-whole", action="store_true", help="skip the whole-surface pass")
    ap.add_argument("--unjudged", choices=("report", "fail"), default="report")
    ap.add_argument("--profile-mm", type=float, default=1.72)
    a = ap.parse_args()
    RA.PROFILE, RA.IO_GATE = "outer", False
    RA.UNJUDGED_FAIL, RA.PROFILE_MM = a.unjudged == "fail", a.profile_mm
    v = lambda r: "P" if r["layer1_pass"] else "F"  # noqa: E731
    G = Rot.random(random_state=1).as_matrix()
    for near in ([] if a.no_whole else [None]) + a.near:
        RA.NEAR_MM = near
        print(f"\n######## near-join only: {near} mm")
        for name, prof, cs, ct, ks in [
            ("plate", plate(), [(0, 40), (40, 1e9)],
             [[(0, 2 * np.pi)], [(0, 2), (2, 4), (4, 2 * np.pi)]], [0, 1, 2]),
            ("bottle", bottle(), [(0, 25), (25, 75), (75, 1e9)],
             [[(0, 2 * np.pi)], [(0, 2), (2, 4.2), (4.2, 2 * np.pi)], [(0, 3), (3, 2 * np.pi)]],
             [0, 2, 4]),
        ]:
            sh = build(prof, cs, ct, np.random.default_rng(0))
            run = lambda S: RA.layer1([(p @ G.T, n @ G.T) for p, n in S])  # noqa: E731
            r = run(sh)
            print(f"{name}: correct {r['profile_mm']:.2f} per sherd {r['sherd_dev_mm']}"
                  + (" U" if r["unjudged"] else "") + " " + v(r))
            for k in ks:
                row = []
                for kind in KINDS:
                    r = run(move(sh, k, kind))
                    row.append(f"{kind} {r['sherd_dev_mm'][k]}/{r['profile_mm']:.1f}"
                               + ("U" if r["unjudged"] else "") + v(r))
                print(f"  sherd {k}: " + "  ".join(row), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
