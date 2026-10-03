"""How tightly do a method's attempts sit at their breaks? (U17 ticket 02, Layer 2 groundwork)

Reads ONLY attempt bundles (rank_convert.py output), like rank_attempts.py: no answer key.
For every attempt and every sherd: the sherd's break surface is nudged onto its
neighbours' break surfaces (bounded move), and the remaining gap is measured.

Everything is in PERCENT OF POT SIZE (pot size = longest side of the pot's box, the
converter's --pot-mm). The Fractura pots have no known real size, and GARF places sherds
inside a box scaled to the pot, so a fixed millimetre gap would mean different things on
different pots.

Mesh density is taken out: each sherd's surface is resampled evenly by area at SPACING_PCT
of pot size, whatever its triangle count (Fractura sherds carry ~20x the Juglet's points).

Break surface (no labels): a sample is on a break if its face normal lies across the local
wall, i.e. |normal . wall direction| < BREAK_COS, where the wall direction is the thinnest
direction of the surface within BALL_T wall thicknesses. Wall thickness per sherd is
2 x volume / area (a thin shell's two skins carry nearly all the area).

Per sherd, per attempt (before and after nudge):
  gap_pct      median distance from its break samples to the nearest neighbour break
               sample, over samples with one within ZONE_PCT (in contact)
  close        share of those within CLOSE_PCT
  contact      number of break samples in contact
  nudge_pct, nudge_deg   the move the nudge used (bounded by NUDGE_PCT, NUDGE_DEG)

Usage: python scripts/l2_measure.py --bundles DIR --out l2.json [--pot-mm 65] [--workers N]
"""
import argparse
import json
import os
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rank_convert import kabsch  # noqa: E402

SPACING_PCT = 1.0    # resampling spacing (Juglet: 0.65 mm)
BALL_T = 3.0         # wall-direction ball radius, in wall thicknesses (1.3 found ~1% breaks: too few samples)
BREAK_COS = 0.5      # |normal . wall| below this = break (normal within 60..90 deg of wall)
ZONE_PCT = 7.7       # neighbour search zone (Juglet: 5 mm)
CLOSE_PCT = 2.3      # "close" (Juglet: 1.5 mm)
NUDGE_PCT = 7.7      # no sample moves further than this (Juglet: 5 mm)
NUDGE_DEG = 20.0
ICP_ITERS = 30
ICP_KEEP = 0.7       # trimmed ICP: matches kept per iteration
SEED = 3

_S = None


def resample(v, f, spacing, rng):
    """Even-by-area samples of a mesh surface: points and face normals."""
    a, b, c = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
    cr = np.cross(b - a, c - a)
    area = 0.5 * np.linalg.norm(cr, axis=1)
    n_pts = max(200, int(area.sum() / spacing ** 2))
    fi = rng.choice(len(f), n_pts, p=area / area.sum())
    r1, r2 = rng.random(n_pts), rng.random(n_pts)
    s = np.sqrt(r1)
    p = (1 - s)[:, None] * a[fi] + (s * (1 - r2))[:, None] * b[fi] + (s * r2)[:, None] * c[fi]
    nrm = cr[fi] / (np.linalg.norm(cr[fi], axis=1, keepdims=True) + 1e-12)
    return p, nrm, float(area.sum())


def volume(v, f):
    return abs(np.einsum("ij,ij->i", v[f[:, 0]], np.cross(v[f[:, 1]], v[f[:, 2]])).sum()) / 6


def prep_sherd(v, f, pot, rng):
    """v in mm -> break samples in % of pot, plus the sherd's wall thickness (% of pot)."""
    v = v * 100.0 / pot
    p, n, area = resample(v, f, SPACING_PCT, rng)
    t = 2 * volume(v, f) / area
    tree = cKDTree(p)
    wall = np.empty_like(p)
    for i, nb in enumerate(tree.query_ball_point(p, BALL_T * t)):
        q = p[nb] - p[nb].mean(0)
        wall[i] = np.linalg.eigh(q.T @ q)[1][:, 0]
    brk = np.abs(np.einsum("ij,ij->i", n, wall)) < BREAK_COS
    return dict(p=p[brk], n_all=len(p), thick=t)


def load(bundles: Path, pot_mm):
    z = np.load(bundles / "sherds.npz")
    pot = float(z["pot_mm"]) if "pot_mm" in z.files else pot_mm
    if pot is None:
        sys.exit("sherds.npz has no pot_mm: pass --pot-mm")
    rng = np.random.default_rng(SEED)
    return pot, [prep_sherd(z[f"v{j}"].astype(float), z[f"f{j}"], pot, rng)
                 for j in range(int(z["k"]))]


def _init(bundles, pot_mm):
    global _S
    _S = load(Path(bundles), pot_mm)


def gap(X, tree):
    d, _ = tree.query(X, distance_upper_bound=ZONE_PCT)
    z = np.isfinite(d)
    if z.sum() < 10:
        return None, 0.0, int(z.sum())
    return float(np.median(d[z])), float((d[z] < CLOSE_PCT).mean()), int(z.sum())


def nudge(P, tree, Q):
    R, t = np.eye(3), np.zeros(3)
    for _ in range(ICP_ITERS):
        X = P @ R.T + t
        d, i = tree.query(X, distance_upper_bound=ZONE_PCT)
        z = np.isfinite(d)
        if z.sum() < 10:
            break
        keep = z & (d <= np.quantile(d[z], ICP_KEEP))
        dR, dt = kabsch(X[keep], Q[i[keep]])
        R2, t2 = dR @ R, dR @ t + dt
        move = np.linalg.norm(P @ R2.T + t2 - P, axis=1).max()
        ang = np.degrees(np.arccos(np.clip((np.trace(R2) - 1) / 2, -1, 1)))
        if move > NUDGE_PCT or ang > NUDGE_DEG:
            break
        if np.allclose(R2, R, atol=1e-7) and np.allclose(t2, t, atol=1e-6):
            R, t = R2, t2
            break
        R, t = R2, t2
    move = float(np.linalg.norm(P @ R.T + t - P, axis=1).max())
    ang = float(np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1))))
    return R, t, move, ang


def measure(path):
    pot, sh = _S
    b = np.load(path)
    placed = [s["p"] @ R.T + t * 100.0 / pot
              for s, R, t in zip(sh, b["R"].astype(float), b["t"].astype(float))]
    rows = []
    for j, P in enumerate(placed):
        Q = np.concatenate([placed[k] for k in range(len(placed)) if k != j])
        tree = cKDTree(Q)
        g0, c0, n0 = gap(P, tree)
        R, t, mv, ang = nudge(P, tree, Q)
        g1, c1, n1 = gap(P @ R.T + t, tree)
        rows.append(dict(gap0=g0, close0=c0, contact0=n0, gap=g1, close=c1, contact=n1,
                         nudge_pct=round(mv, 3), nudge_deg=round(ang, 2)))
    return dict(id=Path(path).stem, sherds=rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bundles", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--pot-mm", type=float, default=None)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int,
                    default=int(os.environ.get("SLURM_CPUS_PER_TASK", "1")))
    a = ap.parse_args()
    paths = sorted((a.bundles / "bundles").glob("*.npz"))
    if a.limit:
        paths = paths[: a.limit]
    with Pool(a.workers, initializer=_init, initargs=(str(a.bundles), a.pot_mm)) as pool:
        rows = pool.map(measure, paths, chunksize=2)
    _init(str(a.bundles), a.pot_mm)
    pot, sh = _S
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(dict(
        pot_mm=pot, units="percent of pot size",
        settings=dict(SPACING_PCT=SPACING_PCT, BALL_T=BALL_T, BREAK_COS=BREAK_COS,
                      ZONE_PCT=ZONE_PCT, CLOSE_PCT=CLOSE_PCT, NUDGE_PCT=NUDGE_PCT,
                      NUDGE_DEG=NUDGE_DEG),
        sherd_info=[dict(break_samples=len(s["p"]), samples=s["n_all"],
                         wall_pct=round(s["thick"], 3)) for s in sh],
        attempts=rows), indent=0))
    g = np.array([s["gap"] for r in rows for s in r["sherds"] if s["gap"] is not None])
    print(f"{len(rows)} attempts -> {a.out}; per-sherd gap after nudge, % of pot: "
          f"quartiles {np.percentile(g, [25, 50, 75]).round(2)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
