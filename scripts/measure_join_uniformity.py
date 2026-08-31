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
    print(f"\n  {'level':<16} {'n':>3}  {'p10':>8} {'p50':>8} {'p90':>8}   {'vtx spacing':>12}")
    print(f"  {'-'*16} {'-'*3}  {'-'*8} {'-'*8} {'-'*8}   {'-'*12}")
    for lvl in sorted(rows):
        a = np.array(rows[lvl])
        print(f"  {lvl:<16} {len(a):>3}  {np.median(a[:,0]):>8.4f} "
              f"{np.median(a[:,1]):>8.4f} {np.median(a[:,2]):>8.4f}"
              f"   {np.median(a[:,3]):>12.4f}")
    h.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/data/gpfs/projects/punim2657/TORA")
    ap.add_argument("--limit", type=int, default=12)
    # BEFORE AND AFTER IN ONE LOG. A rebuild is only believable against the
    # file it replaces, measured by the same instrument in the same run --
    # comparing two logs written weeks apart is how a changed default goes
    # unnoticed. Naming a file here ADDS it; the two references always run.
    ap.add_argument("--src", default="", help="extra hdf5 to measure first")
    ap.add_argument("--dataset", default="bbad_vessels")
    a = ap.parse_args()
    root = Path(a.root)
    if a.src:
        run(Path(a.src), a.dataset, a.limit)
    run(root / "dataset/bbad_vessels.hdf5", "bbad_vessels", a.limit)
    run(root / "dataset/erosion_sweep.hdf5", "erosion_sweep", a.limit)
    print("\n  All columns are % of object size; p10/p50/p90 are of the contact")
    print("  band only. READ p10 AGAINST THE VERTEX SPACING: a p10 below the")
    print("  spacing is not a gap, it is two surfaces still touching, sampled.")


if __name__ == "__main__":
    main()
