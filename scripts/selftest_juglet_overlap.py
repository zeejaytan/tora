"""Known-answer gate for the overlap test in diagnose_juglet_selection.py.

The overlap test decides whether the Juglet's hand reassembly sets sherds into
each other, from a generalised winding number and an exact point-to-triangle
distance written for this purpose (the tora env has no ray library). Run this
before trusting it: shapes with exact answers, then two dense boxes set 0.1 mm
INTO each other (must read 100% inside at -0.100 mm) and the same boxes 0.1 mm
APART (must read 0% inside at +0.100 mm). The second pair is the one that
could fail: a test that always answered "inside" passes everything else.

    python scripts/selftest_juglet_overlap.py     # exit 0 = all pass

Passed locally 2026-09-11 before job 30419474's successor was submitted.
"""
import sys
from pathlib import Path

import numpy as np
import trimesh
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from diagnose_juglet_selection import (overlap, surface_distance,  # noqa: E402
                                       winding)

fails = 0


def check(name, got, want, tol):
    global fails
    got, want = np.asarray(got, float), np.asarray(want, float)
    ok = bool(np.all(np.abs(got - want) <= tol))
    fails += not ok
    print(("PASS " if ok else "FAIL ") + name + "\n   got  " +
          np.array2string(got, precision=4) + "\n   want " +
          np.array2string(want, precision=4))


def dense_box(cx):
    m = trimesh.creation.box(extents=[2, 2, 2])
    m = m.subdivide().subdivide().subdivide().subdivide()
    m.apply_translation([cx, 0, 0])
    return m


def pair(sep):
    """Two 2 mm boxes whose facing sides are `sep` apart (negative = overlap)."""
    cx = 2.0 + sep
    boxes = (dense_box(0.0), dense_box(cx))
    sherds = [(np.asarray(m.vertices), np.asarray(m.vertex_normals))
              for m in boxes]
    tris = [np.asarray(m.vertices)[np.asarray(m.faces)] for m in boxes]
    T, M = [], []
    for i, (v, _n) in enumerate(sherds):
        o = sherds[1 - i][0]
        d, idx = cKDTree(o).query(v, k=1)
        T.append(dict(gap=d, facing=np.zeros(len(v)),
                      partner=-np.ones(len(v)),
                      owner=np.full(len(v), 1 - i), foot=o[idx]))
        # "Join dots": the side facing the other box. Rim excluded: when the
        # boxes overlap it lies exactly on the other box's side walls, a tie.
        face = (v[:, 0] > 0.999) if i == 0 else (v[:, 0] < cx - 0.999)
        face &= (np.abs(v[:, 1]) < 0.95) & (np.abs(v[:, 2]) < 0.95)
        M.append(dict(tight=face))
    return overlap(sherds, tris, T, M, jf=1.0, push_mm=0.05, n_ctrl=300)


def main():
    b = trimesh.creation.box(extents=[2, 2, 2])
    tb = np.asarray(b.vertices)[np.asarray(b.faces)]
    qb = np.array([[0, 0, 0], [0.5, 0.5, 0.9], [2, 0, 0], [2, 2, 2],
                   [1.5, 0.3, 0.2], [0.2, 1.3, 0]], float)
    check("box winding", winding(qb, tb) > 0.5, [1, 1, 0, 0, 0, 0], 0)
    check("box distance", surface_distance(qb, tb),
          [1, 0.1, 1, np.sqrt(3), 0.5, 0.3], 1e-9)

    s = trimesh.creation.icosphere(subdivisions=5, radius=1.0)
    ts = np.asarray(s.vertices)[np.asarray(s.faces)]
    qs = np.array([[0, 0, 0], [0.5, 0.2, 0.1], [0, 0, 2], [1.5, 0, 0],
                   [0, 0, 0.99], [0, 0, 1.01]], float)
    check("sphere winding", winding(qs, ts), [1, 1, 0, 0, 1, 0], 1e-6)
    check("sphere distance", surface_distance(qs, ts),
          [1, 1 - np.sqrt(0.30), 1, 0.5, 0.01, 0.01], 2e-3)

    # Flipped winding must flip the sign: guards the orientation convention.
    check("inward-wound box reads -1 inside", winding(qb[:1], tb[:, ::-1]),
          [-1], 1e-9)

    res = pair(-0.1)
    check("overlap: control trusted", [res["trusted"]], [1], 0)
    check("overlap: every face dot inside", [res.get("inside_pct", 0)],
          [100], 1e-9)
    check("overlap: median depth 0.1 mm", [res["signed_gap_pct"]["50"]],
          [-0.1], 1e-9)

    res = pair(+0.1)
    check("gap: no face dot inside", [res.get("inside_pct", -1)], [0], 1e-9)
    check("gap: median +0.1 mm", [res["signed_gap_pct"]["50"]], [0.1], 1e-9)

    print("\nALL PASS" if not fails else "\n" + str(fails) + " FAILED")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
