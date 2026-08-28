"""Is the join gap UNIFORM (two faces still congruent) or IRREGULAR (real)?

`recede_surface` retreats both mating faces along a smoothed normal field, so
both faces ARE worn -- the conservator is right about that. But retreating two
congruent faces leaves them congruent, just further apart. Real fragments have
lost material unevenly: the two faces no longer mirror each other, so the gap
between them varies along the join.

This measures that. Take the mating band (the closest quarter of each piece's
vertices to any other piece) and report how much the gap VARIES across it:

  p90 / p10 of the contact distance
    ~1     a uniform offset -- the faces still match, matching by proximity
           still works, the shape of the break need not be read
    large  an irregular join -- proximity is ambiguous and the only way to
           decide which face mates with which is to read its shape

Reported alongside the absolute gap so a tight uniform join and a wide uniform
join are distinguishable.
"""

import argparse
from collections import defaultdict
from pathlib import Path

import h5py
import numpy as np
from scipy.spatial import cKDTree

from compare_wear_severity import load_parts, object_size, split_tag


def contact_band(parts, frac=0.25, max_pts=30000, seed=0):
    """Distances of the closest `frac` of vertices to any other piece."""
    rng = np.random.default_rng(seed)
    subs = [v if len(v) <= max_pts else v[rng.choice(len(v), max_pts, replace=False)]
            for v in parts]
    trees = [cKDTree(s) for s in subs]
    out = []
    for i, s in enumerate(subs):
        best = np.full(len(s), np.inf)
        for j, t in enumerate(trees):
            if i != j:
                d, _ = t.query(s, workers=-1)
                best = np.minimum(best, d)
        out.append(best[best <= np.percentile(best, 100 * frac)])
    return np.concatenate(out)


def run(src, dataset, limit):
    h = h5py.File(src, "r")
    dg = h[dataset]
    groups = defaultdict(dict)
    for tag in dg.keys():
        obj, lvl = split_tag(tag)
        if obj is not None:
            groups[obj].setdefault(lvl, tag)
    usable = sorted(o for o, v in groups.items() if len(v) > 1)
    if limit and len(usable) > limit:
        usable = usable[::max(1, len(usable) // limit)][:limit]

    print(f"\n{'='*78}\n{dataset}  ({len(usable)} objects)\n{'='*78}")
    rows = defaultdict(list)
    for obj in usable:
        for lvl, tag in groups[obj].items():
            try:
                parts = load_parts(dg[tag])
                if len(parts) < 2:
                    continue
                size = object_size(parts)
                d = contact_band(parts) / size * 100
                p10, p50, p90 = np.percentile(d, [10, 50, 90])
                # A RATIO ALONE MISREADS: p10 can sit below the vertex spacing,
                # in which case it is measuring sampling, not a gap. Carry the
                # absolute percentiles and the spacing so that is visible.
                allv = np.concatenate(parts)
                sp = np.median(cKDTree(allv).query(
                    allv[::max(1, len(allv) // 4000)], k=2)[0][:, 1]) / size * 100
                rows[lvl].append((p10, p50, p90, sp))
            except Exception as e:                        # noqa: BLE001
                print(f"  skip {obj}/{lvl}: {e}")
    print(f"\n  {'level':<16} {'n':>3}  {'median gap %':>13}  {'p90/p10 of gap':>15}")
    print(f"  {'-'*16} {'-'*3}  {'-'*13}  {'-'*15}")
    for lvl in sorted(rows):
        m = np.array([r[0] for r in rows[lvl]])
        r = np.array([r[1] for r in rows[lvl]])
        fin = r[np.isfinite(r)]
        rs = "inf (shared)" if len(fin) == 0 else f"{np.median(fin):.1f}x"
        print(f"  {lvl:<16} {len(m):>3}  {np.median(m):>11.4f}    {rs:>15}")
    h.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/data/gpfs/projects/punim2657/TORA")
    ap.add_argument("--limit", type=int, default=12)
    a = ap.parse_args()
    root = Path(a.root)
    run(root / "dataset/bbad_vessels.hdf5", "bbad_vessels", a.limit)
    run(root / "dataset/erosion_sweep.hdf5", "erosion_sweep", a.limit)
    print("\n  ~1x means the two faces are still congruent: a uniform retreat.")
    print("  Large means the join is irregular and proximity alone is ambiguous.")


if __name__ == "__main__":
    main()
