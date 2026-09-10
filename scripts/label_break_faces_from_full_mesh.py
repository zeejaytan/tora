"""GROUND TRUTH for which sherd points are break face, from the intact pot.

Three proxies for this question have now failed, and each failed in a way its
own numbers could not reveal:

  1. the off-face gate inside `wear_fracture_spectrum.py` -- asks whether a
     patch is locally ONE surface. A pot's outer wall is one surface. Passes.
  2. `face_selection.png` -- projects through a hollow object, so a ribbon on
     the near break and a broad area on the far wall are drawn on top of each
     other.
  3. the ribbon-width tests in `check_mating_face_is_a_ribbon.py` -- both the
     global-extent version (a break runs around the sherd's perimeter as a
     closed loop; both principal extents of a loop are the loop's diameter) and
     the local-saturation version. The local one carried a control and the
     control fired: outer surface read as ribbon on five of eight pots. The
     reason is in its own output -- the selection is already restricted to
     points within 2% of object size of a neighbour, a band 2.7-6.7 mm wide on
     these pots, which is the wall thickness to within a factor of two. Band
     width cannot separate the two when both bands are the same width by
     construction.

There is no need for a fourth proxy, because the answer is in the dataset.
`fractura_real.hdf5` carries `full_mesh` for every pot: the INTACT vessel,
before it was broken, at 1.0-6.2 M vertices. A sherd point that came from the
original pot surface lies ON that mesh. A point on a break face lies in the
interior of the wall, off it by up to half a wall thickness. That is a label,
not an indicator, and no viewpoint or patch shape enters it.

WHAT THIS CAN STILL GET WRONG, stated before it runs. The two meshes must share
a coordinate frame: erosion pieces are normalised to max|v| = 0.5 and rescaled
here by the same `raw_scales` factor the instrument uses. If the frames do not
match, essentially every point reads as break face. So the read-out prints the
full distance distribution and the fraction of the WHOLE sherd called break
face -- on a thin-walled pot that must be a minority. Both numbers make a frame
error loud rather than silent.

Reported per pot:
  PURITY  -- of the points the instrument measures, the fraction truly on a
             break face. This is what decides whether job 30356470 is quotable.
  RECALL  -- of all true break-face points, the fraction the instrument keeps.
             Low recall biases the measurement toward whichever parts of the
             break the selection happens to favour; it does not void it.
  and the same purity for the OUTWARD set (normals facing away, outer surface
  by construction) which must come back near zero, and for v1's near-only
  selection, which is the contamination that voided job 30352180.

Usage:
  python scripts/label_break_faces_from_full_mesh.py
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
                                    load_sherds, raw_scales)

TAU_SPACINGS = 3.0      # off the intact surface by this many point spacings
MAX_FULL = 1500000      # cap on intact-mesh vertices held at once


def spacing(pts, rng, n=20000):
    s = pts[rng.choice(len(pts), min(n, len(pts)), replace=False)]
    d, _ = cKDTree(pts).query(s, k=2, workers=-1)
    return float(np.median(d[:, 1]))


def masks(sherds, diag):
    """near / mating / outward, per sherd, as boolean masks on its vertices."""
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
        dot = np.sum(n * u, axis=1)
        near = d1 < BAND_FRAC * diag
        out.append((near, near & (dot > MATING_DOT),
                    near & (dot < -MATING_DOT)))
        del others, tree
    return out


def pct(a, b):
    return (100.0 * a / b) if b else float("nan")


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

    print("Break face = sherd point further than " +
          format(TAU_SPACINGS, ".0f") + " point spacings from the INTACT pot")
    print("surface (fractura_real.hdf5 full_mesh). A label, not an indicator.")
    print("")
    print("Sanity, read these first: on a thin-walled pot the break face is a")
    print("MINORITY of each sherd's surface. If 'whole sherd' approaches 100%,")
    print("the two meshes are not in the same frame and nothing below counts.")
    print("")

    rows = []
    with h5py.File(a.raw, "r") as fr, h5py.File(a.erosion, "r") as fe:
        for tag in sorted(fe[a.group].keys()):
            pot, rung = tag.rsplit("_", 1)
            if (want and pot not in want) or (want_r and rung not in want_r):
                continue
            if pot not in scale_of or pot not in fr[a.raw_group]:
                continue
            grp = fr[a.raw_group][pot]
            if "full_mesh" not in grp:
                print(tag + ": no full_mesh, skipped")
                continue

            fv = np.asarray(grp["full_mesh"]["vertices"][:], dtype=np.float64)
            if len(fv) > MAX_FULL:
                fv = fv[rng.choice(len(fv), MAX_FULL, replace=False)]
            s_full = spacing(fv, rng)
            ftree = cKDTree(fv)

            s = scale_of[pot]
            sherds = load_sherds(fe, a.group, tag, 250000, rng)
            sherds = [(v * s, n) for v, n in sherds]
            allv = np.concatenate([v for v, _ in sherds], axis=0)
            diag = float(np.linalg.norm(allv.max(0) - allv.min(0)))
            s_sherd = spacing(allv, rng)
            tau = TAU_SPACINGS * max(s_full, s_sherd)
            del allv
            mk = masks(sherds, diag)

            tot = dict(all=0, brk=0, near=0, near_b=0, mat=0, mat_b=0,
                       out=0, out_b=0)
            dsel = []
            for (v, _n), (near, mat, outw) in zip(sherds, mk):
                d, _ = ftree.query(v, k=1, workers=-1)
                brk = d > tau
                tot["all"] += len(v)
                tot["brk"] += int(brk.sum())
                tot["near"] += int(near.sum())
                tot["near_b"] += int((near & brk).sum())
                tot["mat"] += int(mat.sum())
                tot["mat_b"] += int((mat & brk).sum())
                tot["out"] += int(outw.sum())
                tot["out_b"] += int((outw & brk).sum())
                if mat.sum():
                    dsel.append(d[mat])

            q = (np.percentile(np.concatenate(dsel), [5, 25, 50, 75, 95])
                 if dsel else np.full(5, np.nan))
            print(tag + "   intact mesh " + str(len(fv)) + " verts, spacing " +
                  format(s_full, ".3f") + " mm; sherd spacing " +
                  format(s_sherd, ".3f") + " mm; threshold " +
                  format(tau, ".3f") + " mm")
            print("   whole sherd: " + format(pct(tot["brk"], tot["all"]),
                                              ".1f") + "% break face  (" +
                  str(tot["brk"]) + " of " + str(tot["all"]) + ")")
            print("   distance off the intact surface, MATING points, mm: " +
                  "  ".join(format(x, ".2f") for x in q) + "   (5/25/50/75/95)")
            print("   PURITY  mating " + format(pct(tot["mat_b"], tot["mat"]),
                                                "5.1f") + "%" +
                  "   near-only (v1) " + format(pct(tot["near_b"],
                                                    tot["near"]), "5.1f") +
                  "%   outward " + format(pct(tot["out_b"], tot["out"]),
                                          "5.1f") + "% (must be low)")
            print("   RECALL  mating keeps " +
                  format(pct(tot["mat_b"], tot["brk"]), ".1f") +
                  "% of all break-face points")
            rows.append((tag, pct(tot["mat_b"], tot["mat"]),
                         pct(tot["near_b"], tot["near"]),
                         pct(tot["out_b"], tot["out"]),
                         pct(tot["mat_b"], tot["brk"]),
                         pct(tot["brk"], tot["all"])))
            print("")
            del ftree, fv, sherds, mk

    print("=" * 78)
    print("pot".ljust(22) + "purity".rjust(8) + "v1".rjust(8) +
          "outward".rjust(9) + "recall".rjust(8) + "sherd%".rjust(8))
    print("=" * 78)
    for r in rows:
        print(r[0].ljust(22) + "".join(format(x, "8.1f") for x in r[1:5]) +
              format(r[5], "8.1f"))
    if rows:
        p = [r[1] for r in rows]
        print("")
        print("mating purity: min " + format(min(p), ".1f") + "%, median " +
              format(float(np.median(p)), ".1f") + "%, max " +
              format(max(p), ".1f") + "%")
        print("")
        print("Job 30356470 is quotable only on pots whose purity is high. "
              "Where it is")
        print("not, the number that comes out is a blend of break face and "
              "vessel wall,")
        print("which is what voided job 30352180.")


if __name__ == "__main__":
    main()
