"""Do a method's sherds pass through each other? (U17 Revision 4 groundwork, ticket 06 follow-up)

Reads ONLY attempt bundles (rank_convert.py output), like l2_measure.py: no answer key.
Layer 2 measures how close a sherd's break sits to its neighbours' breaks, so a sherd sunk
into another reads as a tight join (TORA plate, job 32330575: misplaced floor sherds lying
across the rim ranked above every correct attempt; seen by the conservator 2026-10-05).
This measures the overlap directly.

For every attempt and every sherd j: each of j's surface samples (whole surface, evenly by
area) is tested against every other sherd k. A sample is INSIDE k when k's nearest surface
sample lies within k's wall thickness and the sample sits behind it, against k's outward
normal, by more than DEPTH_T of k's wall. Touching at a correct break is ~0 deep and is not
counted. Everything is in percent of pot size, as in l2_measure.py.

Per sherd, per attempt:
  inside_pct   share of the sherd's surface lying inside some other sherd, %
  depth_pct    95th percentile depth of those samples, % of pot (0 if none)
  into         the sherd it overlaps most (-1 if none)

Normals: face normals oriented outward per sherd by the sign of its enclosed volume. A
sherd mesh that is not closed gives an unreliable sign; the count of open edges per sherd
is written to the output so that can be checked rather than assumed.

Usage: python scripts/overlap_measure.py --bundles DIR --out overlap.json [--workers N]
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
from l2_measure import SEED, SPACING_PCT, resample, volume  # noqa: E402

DEPTH_T = 0.25   # deeper than this share of the other sherd's wall = inside, not touching
SAME_COS = 0.7   # skins this parallel (~45 deg), touching and facing the same way = stacked

_S = None


def signed_volume(v, f):
    return np.einsum("ij,ij->i", v[f[:, 0]], np.cross(v[f[:, 1]], v[f[:, 2]])).sum() / 6


def open_edges(f):
    e = np.sort(np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]), axis=1)
    _, n = np.unique(e, axis=0, return_counts=True)
    return int((n == 1).sum())


def prep_sherd(v, f, pot, rng):
    v = v * 100.0 / pot
    p, n, area = resample(v, f, SPACING_PCT, rng)
    if signed_volume(v, f) < 0:
        n = -n
    return dict(p=p, n=n, thick=2 * volume(v, f) / area, open=open_edges(f))


def load(bundles: Path):
    z = np.load(bundles / "sherds.npz")
    pot = float(z["pot_mm"])
    rng = np.random.default_rng(SEED)
    return pot, [prep_sherd(z[f"v{j}"].astype(float), z[f"f{j}"], pot, rng)
                 for j in range(int(z["k"]))]


def _init(bundles):
    global _S
    _S = load(Path(bundles))


def inside(X, M, P, N, thick, tree):
    """Per point of X (normals M): how far inside the sherd (P, N) it is, or 0.

    Two ways in. Behind the surface by more than DEPTH_T of its wall. Or lying ON the
    surface facing the same way (normals within ~45 deg): one skin laid on another, as a
    sherd stacked on its neighbour would be, which has no depth. Faces touching at a
    correct break face each other (opposite normals) and count as neither. A stacked skin
    is given a depth of half the wall, so it reads as overlap, not as a graze.
    """
    d, i = tree.query(X, distance_upper_bound=thick)
    z = np.isfinite(d)
    depth = np.zeros(len(X))
    depth[z] = -np.einsum("ij,ij->i", X[z] - P[i[z]], N[i[z]])
    depth[depth < DEPTH_T * thick] = 0.0
    skin = np.zeros(len(X), bool)
    skin[z] = (d[z] < DEPTH_T * thick) & (np.einsum("ij,ij->i", M[z], N[i[z]]) > SAME_COS)
    # stacked means covered: the other skin must reach round the point on every side. At
    # a correct join the outer skins of two sherds meet edge to edge, facing the same way;
    # there the other skin lies all to one side, and its centre is off by about a spacing.
    if skin.any():
        for q in np.flatnonzero(skin):
            nb = P[tree.query_ball_point(X[q], 2 * SPACING_PCT)] - X[q]
            n = N[i[q]]
            off = nb.mean(0) - (nb.mean(0) @ n) * n
            skin[q] = np.linalg.norm(off) < 0.5 * SPACING_PCT
    depth[skin] = np.maximum(depth[skin], 0.5 * thick)
    return depth


def measure(path):
    pot, sh = _S
    b = np.load(path)
    R, T = b["R"].astype(float), b["t"].astype(float) * 100.0 / pot
    placed = [(s["p"] @ r.T + t, s["n"] @ r.T) for s, r, t in zip(sh, R, T)]
    trees = [cKDTree(P) for P, _ in placed]
    rows = []
    for j, (X, M) in enumerate(placed):
        best = np.zeros(len(X))
        into, most = -1, 0
        for k, (P, N) in enumerate(placed):
            if k == j:
                continue
            dep = inside(X, M, P, N, sh[k]["thick"], trees[k])
            if (dep > 0).sum() > most:
                into, most = k, int((dep > 0).sum())
            best = np.maximum(best, dep)
        hit = best > 0
        rows.append(dict(inside_pct=round(100 * float(hit.mean()), 3),
                         depth_pct=round(float(np.percentile(best[hit], 95)) if hit.any() else 0.0, 3),
                         into=into))
    return dict(id=Path(path).stem, sherds=rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bundles", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int,
                    default=int(os.environ.get("SLURM_CPUS_PER_TASK", "1")))
    a = ap.parse_args()
    paths = sorted((a.bundles / "bundles").glob("*.npz"))
    if a.limit:
        paths = paths[: a.limit]
    with Pool(a.workers, initializer=_init, initargs=(str(a.bundles),)) as pool:
        rows = pool.map(measure, paths, chunksize=2)
    _init(str(a.bundles))
    pot, sh = _S
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(dict(
        pot_mm=pot, units="percent of pot size / percent of sherd surface",
        settings=dict(SPACING_PCT=SPACING_PCT, DEPTH_T=DEPTH_T, SAME_COS=SAME_COS),
        sherd_info=[dict(samples=len(s["p"]), wall_pct=round(s["thick"], 3),
                         open_edges=s["open"]) for s in sh],
        attempts=rows), indent=0))
    worst = np.array([max(s["inside_pct"] for s in r["sherds"]) for r in rows])
    print(f"{len(rows)} attempts -> {a.out}; worst sherd's surface inside another, %: "
          f"quartiles {np.percentile(worst, [25, 50, 75]).round(2)}; "
          f"open edges per sherd {[s['open'] for s in sh]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
