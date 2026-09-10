"""Is the mating-normal selection a break RIBBON, or a patch of vessel wall?

The off-face gate in `wear_fracture_spectrum.py` cannot answer this and I should
not have relied on it alone: it asks whether a patch is locally ONE surface, and
the outer wall of a pot is also locally one surface, so the wall passes the gate
cleanly. The 2D scatter in `face_selection.png` cannot answer it either -- it
projects through the object, so a ribbon along an edge and a broad area on the
far wall land on top of each other.

This is the check a viewpoint cannot distort. A break face on a sherd is a
ribbon whose width is the WALL THICKNESS -- about 4.5 mm on these pots -- and
whose length runs along the break, typically tens of millimetres. A patch of
vessel wall has no such constraint: it is wide in both directions. So for each
sherd's selected points, take the two in-surface principal directions and
measure the extent along each. The narrow one should be about one wall
thickness. If it is several times that, the selection is on the wall and every
number measured from it is void, exactly as version 1's was.

Wall thickness is measured independently on the same sherd as 2 x volume / area,
the instrument already used on the RePAIR plaques, so the comparison does not
depend on a number typed in from a note.

Usage:
  python scripts/check_mating_face_is_a_ribbon.py \
      --erosion dataset/erosion_ceramics.hdf5 \
      --raw     dataset/fractura_real.hdf5 \
      --pots    pink_bowl,blue_pot --rungs e000
"""

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wear_fracture_spectrum import (BAND_FRAC, MATING_DOT,  # noqa: E402
                                    load_sherds, mating_faces, raw_scales)

RIBBON_MAX_WALLS = 2.0     # a break ribbon wider than this many walls is wall


def extents(pts):
    """Extent along each principal direction, widest first."""
    q = pts - pts.mean(axis=0)
    _w, u = np.linalg.eigh(q.T @ q)
    proj = q @ u[:, ::-1]
    p1, p99 = np.percentile(proj, [1, 99], axis=0)
    return np.abs(p99 - p1)


def wall_thickness(v, f):
    m = trimesh.Trimesh(vertices=v, faces=f, process=False)
    a = float(m.area)
    if a <= 0:
        return None, False
    return 2.0 * abs(float(m.volume)) / a, bool(m.is_watertight)


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

    print("A break face is a ribbon one wall thick. Selection is on the wall")
    print("if the narrow extent exceeds " + format(RIBBON_MAX_WALLS, ".1f") +
          " wall thicknesses.")
    print("mating gate: near < " + format(100 * BAND_FRAC, ".0f") +
          "% of object size AND normal dot direction > " +
          format(MATING_DOT, ".2f"))
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
                t, wt = wall_thickness(v, f)
                walls.append((t, wt))

            sherds = load_sherds(fe, a.group, tag, 250000, rng)
            sherds = [(v * s, n) for v, n in sherds]
            allv = np.concatenate([v for v, _ in sherds], axis=0)
            diag = float(np.linalg.norm(allv.max(0) - allv.min(0)))
            faces, near, kept = mating_faces(sherds, diag)

            print(tag + "   diag " + format(diag, ".1f") + " mm, " +
                  str(len(faces)) + " selected faces of " + str(len(keys)) +
                  " sherds, kept " +
                  format(100.0 * kept / max(near, 1), ".1f") + "% of near")
            verdicts = []
            for i, (fp, _n) in enumerate(faces):
                e = extents(fp)
                long_, narrow = float(e[0]), float(e[1])
                wt = walls[i][0] if i < len(walls) else None
                ratio = (narrow / wt) if wt else float("nan")
                ok = np.isfinite(ratio) and ratio <= RIBBON_MAX_WALLS
                verdicts.append(ok)
                print("   face " + str(i) + "  " + str(len(fp)).rjust(6) +
                      " pts   long " + format(long_, "6.1f") +
                      "   narrow " + format(narrow, "5.1f") +
                      "   wall " + (format(wt, "5.2f") if wt else "  n/a") +
                      ("  watertight" if walls[i][1] else "  NOT watertight") +
                      "   narrow/wall " + format(ratio, "5.2f") + "   " +
                      ("RIBBON" if ok else "TOO WIDE -- on the wall"))
            if verdicts and not all(verdicts):
                print("   VERDICT: at least one face is not a break ribbon. "
                      "Numbers from this pot are void.")
            elif verdicts:
                print("   VERDICT: every selected face is a break ribbon.")
            print("")


if __name__ == "__main__":
    main()
