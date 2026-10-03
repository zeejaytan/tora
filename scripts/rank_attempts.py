"""Rank one pot's attempts without the answer key (U17 ranker).

Ticket .scratch/attempt-ranker/issues/01 (Layer 1). Reads ONLY what rank_convert.py
wrote to --bundles: sherds.npz (each sherd's scan in its own neutral frame, mm) and
bundles/<id>.npz (where one attempt put each sherd). It never opens a reference
file; check_attempt_ranker.py fails if it tries.

Layer 1 -- does the attempt form a vessel?
  axis      one axis of rotation for the whole attempt: the line that the sherds'
            surface normals pass closest to (a surface of revolution has every
            normal crossing its axis). Trimmed least squares, distances in mm.
  profile   heights along the axis cut into BIN_MM bins; in each bin each sherd's
            outer wall radius (OUTER_PCT percentile of its radii there); the pot's
            profile is the median over sherds per bin, smoothed over 3 bins.
            Deviation = DEV_PCT percentile of |sherd outer radius - profile|, mm.
  inside out a sherd whose curvature centre lies away from the attempt's centre
            (check_inside_out.rule_flag; agreed with the key on 212/212 Juglet
            placements, juglet-cause/14).
  pass      profile deviation <= PROFILE_MM and no sherd inside out.

Order: passing attempts first, then by profile deviation. The least-sure sherd is
the one furthest from the profile (an inside-out sherd outranks that).

Cut-offs are pre-registered in .scratch/attempt-ranker/preregistration.md; change
them there, before a labelled run, or not at all.

Usage: python scripts/rank_attempts.py --bundles DIR --out ranks.json [--workers N]
       [--pot-mm 100 --bin-pct P --profile-pct P]

--bin-pct / --profile-pct give the bin and the pass cut-off in % of pot size (longest box
side, --pot-mm) instead of mm; for pots with no real size (Fractura). The Juglet values
7 mm on a 65 mm pot are 10.77%.

--profile outer (ticket 05, after job 32159300): the height bands fail on flat floors (one
band spans centre to rim, so a centre sherd "misses" the rim's radius). As SfS++ checks its
profile curve (one surface, orthogonal distance to a locally fitted line; supp. Alg. 3),
each sherd's OUTER surface, in the (distance from axis, height) half-plane, is compared
with the OTHER sherds' outer surface: per point, the offset along the others' local
profile normal (mean of the OUTER_K nearest). Points that run past the others' reach
(sideways distance > COVER_PCT of pot) are not judged; a sherd with fewer than MIN_COVER
judged points is not judged at all. Sherd deviation = median offset; attempt
deviation = worst judged sherd; unjudged sherds are listed (a sherd that touches the
others' outline nowhere, e.g. a rim sherd stood on end). Outer = the 2D normal points away from a cavity point
(on the axis, median height), as SfS++ splits inner from outer surfaces.
--io-gate off: inside-out sherds are still reported but do not fail the attempt (the
sphere rule misreads S-shaped neck sherds and flat floor sherds, job 32159300).
"""
import argparse
import json
import os
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_inside_out import rule_flag  # noqa: E402

BIN_MM = 7.0        # SfS++ profile bins
PROFILE_MM = 7.0    # SfS++ rejection threshold
OUTER_PCT = 95      # a sherd's outer wall radius in a bin
DEV_PCT = 90        # attempt deviation = this percentile over (sherd, bin)
MIN_PTS = 20        # (sherd, bin) cells with fewer points are skipped
AXIS_PTS = 6000     # points used for the axis fit
AXIS_TRIM = 0.8     # fraction of normal lines kept (break faces, handle)
N_DIRS = 1500
AXIS_STARTS = 10    # best grid directions polished
IO_PTS = 3000
OUTER_PTS = 3000    # --profile outer: points per sherd in the half-plane comparison
OUTER_K = 8         # neighbours that set the others' local profile line
OUTER_NMIN = 0.7    # in-plane share of a normal (drops side break faces)
COVER_MM = 2.0      # sideways reach beyond the others (set from --cover-pct)
MIN_COVER = 20      # judged outer points a sherd needs to be judged itself
PROFILE = "bands"
IO_GATE = True

_SH = None


def fib_hemisphere(n):
    i = np.arange(n) + 0.5
    z = i / n
    phi = np.pi * (1 + 5 ** 0.5) * i
    r = np.sqrt(1 - z * z)
    return np.c_[r * np.cos(phi), r * np.sin(phi), z]


def vertex_normals(v, f):
    fn = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]])
    n = np.zeros_like(v)
    for k in range(3):
        np.add.at(n, f[:, k], fn)
    return n / (np.linalg.norm(n, axis=1, keepdims=True) + 1e-12)


def load_sherds(bundles: Path):
    z = np.load(bundles / "sherds.npz")
    k = int(z["k"])
    out = []
    for j in range(k):
        v, f = z[f"v{j}"].astype(float), z[f"f{j}"]
        out.append((v, vertex_normals(v, f)))
    return out


def _init(bundles):
    global _SH
    _SH = load_sherds(Path(bundles))


def axis_cost(d, p, n):
    d = d / np.linalg.norm(d)
    m = np.cross(n, d)
    w = np.linalg.norm(m, axis=1)
    keep = w > 0.3
    p, m, w = p[keep], m[keep] / w[keep, None], w[keep]
    # distance from normal line i to axis (c, d) = |(p_i - c) . m_i|; c in plane _|_ d
    e1 = np.cross(d, [1, 0, 0] if abs(d[0]) < 0.9 else [0, 1, 0])
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(d, e1)
    A = np.c_[m @ e1, m @ e2]
    b = np.einsum("ij,ij->i", p, m)
    for _ in range(2):                       # trimmed least squares
        sol = np.linalg.lstsq(A, b, rcond=None)[0] if len(A) >= 3 else np.zeros(2)
        r2 = (A @ sol - b) ** 2
        cut = np.quantile(r2, AXIS_TRIM)
        A2, b2 = A[r2 <= cut], b[r2 <= cut]
        if len(A2) >= 3:
            sol = np.linalg.lstsq(A2, b2, rcond=None)[0]
        r2 = np.sort((A @ sol - b) ** 2)[: int(AXIS_TRIM * len(b))]
    c = sol[0] * e1 + sol[1] * e2
    return float(r2.mean()), c


def fit_axis(p, n):
    dirs = fib_hemisphere(N_DIRS)
    costs = np.array([axis_cost(d, p, n)[0] for d in dirs])
    def polish(x0):                     # Nelder-Mead stalls on the trimmed cost:
        res = minimize(lambda x: axis_cost(x, p, n)[0], x0, method="Nelder-Mead",
                       options=dict(xatol=1e-6, fatol=1e-9, maxiter=600))
        for _ in range(4):              # restart from where it stopped
            nxt = minimize(lambda x: axis_cost(x, p, n)[0], res.x / np.linalg.norm(res.x),
                           method="Nelder-Mead",
                           options=dict(xatol=1e-6, fatol=1e-9, maxiter=600))
            if nxt.fun >= res.fun - 1e-9:
                break
            res = nxt
        return res
    best = None
    for d0 in dirs[np.argsort(costs)[:AXIS_STARTS]]:
        res = polish(d0)
        if best is None or res.fun < best.fun:
            best = res
    d = refine(best.x / np.linalg.norm(best.x), p, n)
    cost, c = axis_cost(d, p, n)
    return d, c, float(np.sqrt(cost))


def _fixed_cost(d, p, n):
    """Plain least squares over a fixed set of lines: smooth in d."""
    d = d / np.linalg.norm(d)
    m = np.cross(n, d)
    m /= np.linalg.norm(m, axis=1, keepdims=True)
    e1 = np.cross(d, [1, 0, 0] if abs(d[0]) < 0.9 else [0, 1, 0])
    e1 /= np.linalg.norm(e1)
    A = np.c_[m @ e1, m @ np.cross(d, e1)]
    b = np.einsum("ij,ij->i", p, m)
    sol = np.linalg.lstsq(A, b, rcond=None)[0]
    return float(((A @ sol - b) ** 2).mean())


def refine(d, p, n):
    """Freeze the kept lines, solve the smooth problem, re-pick, until the set holds.
    The trimmed cost jumps whenever a line enters or leaves the kept set, which is
    what left Nelder-Mead stopping at different points in different frames."""
    prev = None
    for _ in range(10):
        m = np.cross(n, d)
        w = np.linalg.norm(m, axis=1)
        idx = np.flatnonzero(w > 0.3)
        e1 = np.cross(d, [1, 0, 0] if abs(d[0]) < 0.9 else [0, 1, 0])
        e1 /= np.linalg.norm(e1)
        mm = m[idx] / w[idx, None]
        A = np.c_[mm @ e1, mm @ np.cross(d, e1)]
        b = np.einsum("ij,ij->i", p[idx], mm)
        r2 = (A @ np.linalg.lstsq(A, b, rcond=None)[0] - b) ** 2
        keep = idx[np.argsort(r2)[: int(AXIS_TRIM * len(idx))]]
        key = frozenset(keep.tolist())
        if key == prev:
            break
        prev = key
        res = minimize(_fixed_cost, d, args=(p[keep], n[keep]), method="BFGS",
                       options=dict(gtol=1e-10))
        d = res.x / np.linalg.norm(res.x)
    return d


def layer1(placed):
    """placed: list of (points, normals) in the attempt's frame, mm."""
    P = np.concatenate([p for p, _ in placed])
    N = np.concatenate([n for _, n in placed])
    step = max(1, len(P) // AXIS_PTS)
    d, c, axis_rms = fit_axis(P[::step], N[::step])
    h_all = (P - c) @ d
    if (((h_all - h_all.mean()) ** 3).mean()) < 0:   # one end, whatever the frame
        d, h_all = -d, -h_all
    if PROFILE == "outer":
        return _finish(placed, d, c, axis_rms, *outer_profile(placed, d, c, np.median(h_all)))
    lo = h_all.min()
    cells = {}                                 # (sherd, bin) -> outer radius
    for j, (p, _) in enumerate(placed):
        h = (p - c) @ d
        r = np.linalg.norm((p - c) - np.outer(h, d), axis=1)
        b = ((h - lo) // BIN_MM).astype(int)
        for k in np.unique(b):
            sel = r[b == k]
            if len(sel) >= MIN_PTS:
                cells[(j, int(k))] = float(np.percentile(sel, OUTER_PCT))
    bins = sorted({k for _, k in cells})
    prof = {k: np.median([v for (j, kk), v in cells.items() if kk == k]) for k in bins}
    smooth = {k: float(np.median([prof[x] for x in (k - 1, k, k + 1) if x in prof]))
              for k in bins}
    dev = {key: abs(v - smooth[key[1]]) for key, v in cells.items()}
    per_sherd = [max([dv for (j, _), dv in dev.items() if j == s], default=0.0)
                 for s in range(len(placed))]
    profile_mm = float(np.percentile(list(dev.values()), DEV_PCT)) if dev else float("nan")
    return _finish(placed, d, c, axis_rms, profile_mm, per_sherd)


def outer_points(placed, d, c, h_mid):
    """Each sherd's outer-surface points and profile normals in the (r, h) half-plane."""
    pts, nrm = [], []
    for p, n in placed:
        stp = max(1, len(p) // OUTER_PTS)
        s, n = p[::stp] - c, n[::stp]
        h = s @ d
        rad = s - np.outer(h, d)
        r = np.linalg.norm(rad, axis=1)
        u = rad / (r[:, None] + 1e-12)
        n2 = np.c_[np.einsum("ij,ij->i", n, u), n @ d]
        m = np.linalg.norm(n2, axis=1)
        x = np.c_[r, h]
        keep = (m > OUTER_NMIN) & (np.einsum("ij,ij->i", n2, x - [0.0, h_mid]) > 0)
        pts.append(x[keep])
        nrm.append(n2[keep] / m[keep, None])
    return pts, nrm


def outer_profile(placed, d, c, h_mid):
    """Each sherd's outer surface against the others' outer surface, (r, h) plane, mm."""
    pts, nrm = outer_points(placed, d, c, h_mid)
    per_sherd = []
    for j in range(len(pts)):
        if len(pts[j]) < MIN_PTS:
            per_sherd.append(float("nan"))
            continue
        Y = np.concatenate([x for k, x in enumerate(pts) if k != j])
        NY = np.concatenate([x for k, x in enumerate(nrm) if k != j])
        idx = cKDTree(Y).query(pts[j], k=OUTER_K)[1]
        y, ny = Y[idx].mean(1), NY[idx].mean(1)
        ny /= np.linalg.norm(ny, axis=1, keepdims=True) + 1e-12
        v = pts[j] - y
        off = np.abs(np.einsum("ij,ij->i", v, ny))
        side = np.abs(v[:, 0] * ny[:, 1] - v[:, 1] * ny[:, 0])
        cov = side <= COVER_MM
        per_sherd.append(float(np.median(off[cov])) if cov.sum() >= MIN_COVER
                         else float("nan"))
    judged = [x for x in per_sherd if np.isfinite(x)]
    return (max(judged) if judged else float("nan")), per_sherd


def _finish(placed, d, c, axis_rms, profile_mm, per_sherd):
    P = np.concatenate([p for p, _ in placed])
    centre = P.mean(0)
    io = []
    for j, (p, _) in enumerate(placed):
        stp = max(1, len(p) // IO_PTS)
        f = rule_flag(p[::stp], centre)
        if f:
            io.append(j)
    ok = bool(profile_mm <= PROFILE_MM and not (IO_GATE and io))   # NaN fails
    least = io[0] if io and IO_GATE else int(np.nanargmax(per_sherd))
    return dict(profile_mm=round(profile_mm, 3), axis_rms_mm=round(axis_rms, 3),
                inside_out=io, layer1_pass=ok, least_sure=least,
                unjudged=[j for j, x in enumerate(per_sherd) if not np.isfinite(x)],
                sherd_dev_mm=[round(x, 2) if np.isfinite(x) else None for x in per_sherd])


def score_bundle(path):
    b = np.load(path)
    placed = [(v @ R.T + t, n @ R.T) for (v, n), R, t in
              zip(_SH, b["R"].astype(float), b["t"].astype(float))]
    out = layer1(placed)
    out["id"] = Path(path).stem
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bundles", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--workers", type=int,
                    default=int(os.environ.get("SLURM_CPUS_PER_TASK", "1")))
    ap.add_argument("--pot-mm", type=float, help="pot size in mm, for the %% cut-offs")
    ap.add_argument("--bin-pct", type=float)
    ap.add_argument("--profile-pct", type=float)
    ap.add_argument("--profile", choices=("bands", "outer"), default="bands")
    ap.add_argument("--cover-pct", type=float, help="--profile outer: sideways reach, %% of pot")
    ap.add_argument("--io-gate", choices=("on", "off"), default="on")
    a = ap.parse_args()
    global BIN_MM, PROFILE_MM, PROFILE, IO_GATE, COVER_MM
    PROFILE, IO_GATE = a.profile, a.io_gate == "on"
    if a.bin_pct is not None or a.profile_pct is not None:
        if a.pot_mm is None:
            sys.exit("--bin-pct/--profile-pct need --pot-mm")
        if a.bin_pct is not None:
            BIN_MM = a.bin_pct * a.pot_mm / 100
        if a.profile_pct is not None:
            PROFILE_MM = a.profile_pct * a.pot_mm / 100
    if a.cover_pct is not None:
        if a.pot_mm is None:
            sys.exit("--cover-pct needs --pot-mm")
        COVER_MM = a.cover_pct * a.pot_mm / 100
    paths = sorted((a.bundles / "bundles").glob("*.npz"))
    if a.workers > 1:
        with Pool(a.workers, initializer=_init, initargs=(str(a.bundles),)) as pool:
            rows = pool.map(score_bundle, paths, chunksize=4)
    else:
        _init(str(a.bundles))
        rows = [score_bundle(p) for p in paths]
    rows.sort(key=lambda r: (not r["layer1_pass"],
                             r["profile_mm"] if np.isfinite(r["profile_mm"]) else np.inf))
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(dict(
        layer="1", cutoffs=dict(BIN_MM=BIN_MM, PROFILE_MM=PROFILE_MM,
                                OUTER_PCT=OUTER_PCT, DEV_PCT=DEV_PCT, pot_mm=a.pot_mm,
                                profile=PROFILE, COVER_MM=COVER_MM, OUTER_K=OUTER_K,
                                MIN_COVER=MIN_COVER, io_gate=IO_GATE),
        attempts=rows), indent=1))
    n_pass = sum(r["layer1_pass"] for r in rows)
    print(f"{len(rows)} attempts ranked, {n_pass} pass Layer 1 -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
