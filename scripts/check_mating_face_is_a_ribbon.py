"""Is the mating-normal selection a break RIBBON, or a patch of vessel wall?

The off-face gate inside `wear_fracture_spectrum.py` cannot answer this and I
should not have relied on it alone: it asks whether a patch is locally ONE
surface, and a pot's outer wall is also locally one surface, so the wall passes
it cleanly. The 2D scatter in `face_selection.png` cannot answer it either --
it projects through a hollow object, so a ribbon along a break edge and a broad
area on the far wall are drawn on top of each other.

A break face is a ribbon as wide as the WALL -- 2.0-6.1 mm on these pots -- and
as long as the break. A patch of wall is broad in both directions. That is the
difference to measure, and it is invariant to viewpoint.

WHY THE OBVIOUS VERSION OF THIS TEST IS WRONG, kept here because it ran first
and refused all eight pots. Taking the two principal directions of a whole
selected face and calling the smaller extent the ribbon width assumes the
ribbon is straight. On a sherd it is not: the break runs around the sherd's
entire perimeter, a closed loop. Both principal extents of a loop are the
LOOP's diameter, and the ribbon width appears in neither. `pink_bowl` face 0
came back 99.5 x 56.3 mm from 4345 points -- but 4345 points at this mesh's
0.136 mm spacing is under ~120 mm2 of surface, far too little to fill
99 x 56 mm. Sparse points around a loop, read as a solid slab. A perfect
selection fails that test, so its refusal means nothing. Same category as the
error it was built to catch: the measurement was broken.

WHAT ACTUALLY SEPARATES THEM, measured locally so curvature cannot confuse it.
Around a break-face point the surface spans the along-break direction and the
across-wall direction. Widen the neighbourhood and the along-break extent keeps
growing while the across-wall extent STOPS at the wall thickness. On a patch of
wall neither stops. So sweep the neighbourhood radius and watch whether the
narrow extent saturates:

    break ribbon, 4.5 mm wall:  r=2 -> ~4    r=8 -> ~4.5   r=16 -> ~4.5
    patch of wall:              r=2 -> ~4    r=8 -> ~16    r=16 -> ~32

The two are indistinguishable at small r and separate by 7x at large r, which
is why a single scale cannot decide it.

AND THE TEST CARRIES ITS OWN CONTROL, because a test that cannot fail proves
nothing. The same measurement runs on points whose normals point AWAY from the
neighbouring sherd -- outer vessel surface by construction, never break face.
Those MUST come back unsaturated. If they saturate too, this instrument is
broken as well and neither column can be quoted.

Usage:
  python scripts/check_mating_face_is_a_ribbon.py
      --erosion dataset/erosion_ceramics.hdf5
      --raw     dataset/fractura_real.hdf5 --rungs e000
"""

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np
import trimesh
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wear_fracture_spectrum import (BAND_FRAC, MATING_DOT, MATING_K,  # noqa
                                    load_sherds, mating_faces, raw_scales)

RADII = [2.0, 4.0, 8.0, 16.0]
N_SAMPLE = 300
SATURATE_MAX_WALLS = 2.5    # widest saturated width still callable a ribbon
GROWTH_MAX = 1.6            # narrow extent may not grow this much r=4 -> r=16


def band_extents(pts, nrms, tree, radii, rng):
    """Median in-surface narrow and long extent vs neighbourhood radius.

    At each sampled point the neighbours are projected onto the plane
    perpendicular to that point's normal, so the two numbers are the extents
    WITHIN the surface: along the break and across the wall.
    """
    idx = rng.choice(len(pts), min(N_SAMPLE, len(pts)), replace=False)
    out = {}
    for r in radii:
        narrow, long_ = [], []
        for i in idx:
            nb = tree.query_ball_point(pts[i], r)
            if len(nb) < 30:
                continue
            d = pts[nb] - pts[i]
            n = nrms[i]
            a = np.array([1.0, 0.0, 0.0])
            if abs(n[0]) > 0.9:
                a = np.array([0.0, 1.0, 0.0])
            e1 = np.cross(n, a)
            e1 /= np.linalg.norm(e1) + 1e-12
            e2 = np.cross(n, e1)
            p2 = np.column_stack([d @ e1, d @ e2])
            _w, u = np.linalg.eigh(p2.T @ p2)
            pr = p2 @ u[:, ::-1]
            lo, hi = np.percentile(pr, [2, 98], axis=0)
            ext = np.abs(hi - lo)
            long_.append(float(ext[0]))
            narrow.append(float(ext[1]))
        out[r] = ((float(np.median(narrow)), float(np.median(long_)),
                   len(narrow)) if narrow else (float("nan"),) * 2 + (0,))
    return out


def wall_thickness(v, f):
    m = trimesh.Trimesh(vertices=v, faces=f, process=False)
    a = float(m.area)
    if a <= 0:
        return None
    return 2.0 * abs(float(m.volume)) / a


def outward_faces(sherds, diag):
    """Points near another sherd but facing AWAY from it: outer wall, always."""
    out = []
    for i, (v, n) in enumerate(sherds):
        others = np.concatenate([w for j, (w, _) in enumerate(sherds)
                                 if j != i], axis=0)
        tree = cKDTree(others)
        k = min(MATING_K, len(others))
        d, idx = tree.query(v, k=k, workers=-1)
        d1 = d[:, 0] if k > 1 else d
        target = others[idx].mean(axis=1) if k > 1 else others[idx]
        u = target - v
        u /= np.linalg.norm(u, axis=1, keepdims=True) + 1e-12
        sel = (d1 < BAND_FRAC * diag) & (np.sum(n * u, axis=1) < -MATING_DOT)
        if sel.sum() >= 400:
            out.append((v[sel], n[sel]))
        del others, tree
    return out


def report(label, faces, walls, rng):
    rows = []
    for i, (fp, fn) in enumerate(faces):
        tree = cKDTree(fp)
        ext = band_extents(fp, fn, tree, RADII, rng)
        wt = walls[i] if i < len(walls) and walls[i] else float("nan")
        line = ("   " + label + " face " + str(i) + "  " +
                str(len(fp)).rjust(6) + " pts  wall " + format(wt, "4.2f"))
        for r in RADII:
            nr, lg, _cnt = ext[r]
            line += ("   r" + format(r, ".0f") + " " + format(nr, "5.1f") +
                     "/" + format(lg, "5.1f"))
        n4, n16 = ext[4.0][0], ext[16.0][0]
        growth = n16 / max(n4, 1e-9)
        sat = (np.isfinite(n16) and np.isfinite(wt)
               and n16 <= SATURATE_MAX_WALLS * wt and growth <= GROWTH_MAX)
        line += ("   growth " + format(growth, "4.2f") + "   " +
                 ("SATURATED = ribbon" if sat else "unsaturated = wall"))
        print(line)
        rows.append(sat)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--erosion", required=True)
    ap.add_argument("--raw", required=True)
    ap.add_argument("--group", default="erosion_ceramics")
    ap.add_argument("--raw-group", default="ceramics")
    ap.add_argument("--pots", default="")
    ap.add_argument("--rungs", default="e000")
    a = ap.parse_args()

    scale_of, _ = raw_scales(a.raw, a.raw_group)
    want = [p for p in a.pots.split(",") if p] or None
    want_r = [r for r in a.rungs.split(",") if r] or None
    rng = np.random.default_rng(0)

    print("Narrow/long in-surface extent (mm) vs neighbourhood radius.")
    print("A break ribbon's NARROW extent stops at the wall thickness; a patch")
    print("of wall keeps growing. Ribbon if narrow at r=16 is under " +
          format(SATURATE_MAX_WALLS, ".1f") + " walls AND")
    print("grew under " + format(GROWTH_MAX, ".2f") + "x from r=4 to r=16.")
    print("MATING = near another sherd and facing it (what the instrument "
          "measures).")
    print("OUTWARD = near another sherd and facing away: outer surface by")
    print("construction. It MUST read unsaturated, or this test is broken too.")
    print("")

    with h5py.File(a.erosion, "r") as fe:
        for tag in sorted(fe[a.group].keys()):
            pot, rung = tag.rsplit("_", 1)
            if (want and pot not in want) or (want_r and rung not in want_r):
                continue
            if pot not in scale_of:
                continue
            s = scale_of[pot]
            g = fe[a.group][tag]["pieces"]
            keys = sorted(g.keys(), key=lambda x: (len(x), x))
            walls = []
            for k in keys:
                v = np.asarray(g[k]["vertices"][:], dtype=np.float64) * s
                f = np.asarray(g[k]["faces"][:], dtype=np.int64)
                walls.append(wall_thickness(v, f))

            sherds = load_sherds(fe, a.group, tag, 250000, rng)
            sherds = [(v * s, n) for v, n in sherds]
            allv = np.concatenate([v for v, _ in sherds], axis=0)
            diag = float(np.linalg.norm(allv.max(0) - allv.min(0)))
            faces, near, kept = mating_faces(sherds, diag)
            away = outward_faces(sherds, diag)

            print(tag + "   diag " + format(diag, ".1f") + " mm, " +
                  str(len(faces)) + " mating faces of " + str(len(keys)) +
                  " sherds, kept " +
                  format(100.0 * kept / max(near, 1), ".1f") + "% of near")
            mat = report("MATING ", faces, walls, rng)
            out = report("OUTWARD", away, walls, rng)
            frac = (100.0 * sum(mat) / len(mat)) if mat else 0.0
            print("   mating saturated: " + format(frac, ".0f") +
                  "% of faces   outward saturated: " +
                  (format(100.0 * sum(out) / len(out), ".0f") if out else "n/a")
                  + "% (must be 0)")
            if out and sum(out) > 0:
                print("   TEST INVALID for this pot: outer surface read as a "
                      "ribbon. Neither column means anything.")
            elif mat and all(mat):
                print("   VERDICT: every mating face is a break ribbon.")
            elif mat and not any(mat):
                print("   VERDICT: no mating face is a break ribbon -- the "
                      "selection is on the wall. Spectrum numbers are void.")
            else:
                print("   VERDICT: mixed. Per-face, not per-pot.")
            print("")


if __name__ == "__main__":
    main()
