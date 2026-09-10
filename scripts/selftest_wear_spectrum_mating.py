"""Synthetic self-test: does mating_faces pick the break and reject the wall?

Two thin slabs 4.5 mm thick (a pot wall), 40 mm long, pressed together at
x = 0. The break plane is the 4.5 x 40 mm face at x = 0 on each. Everything
else is wall. A correct detector keeps points with |x| ~ 0 whose normal is
+/-x, and rejects the far-more-numerous wall points at the same |x|.
"""
import sys
import numpy as np
import trimesh
sys.path.insert(0, "scripts")
from wear_fracture_spectrum import (mating_faces, probe_faces,
                                    ASPECT_MAX)

WALL = 4.5
rng = np.random.default_rng(0)


def slab(x0, x1, rough=0.0):
    m = trimesh.creation.box(extents=[x1 - x0, 40.0, WALL])
    m.apply_translation([(x0 + x1) / 2.0, 0, 0])
    m = m.subdivide_to_size(0.25)
    v = np.asarray(m.vertices, dtype=np.float64)
    if rough:                      # roughen only the break plane
        on = np.abs(np.abs(v[:, 0]) - min(abs(x0), abs(x1))) < 1e-6
        v[on, 0] += rng.normal(0, rough, on.sum())
    return trimesh.Trimesh(vertices=v, faces=np.asarray(m.faces), process=False)


for rough, label in [(0.0, "perfectly flat break"), (0.02, "rough break")]:
    a, b = slab(-20.0, -0.05, rough), slab(0.05, 20.0, rough)
    sherds = []
    for m in (a, b):
        sherds.append((np.asarray(m.vertices, dtype=np.float64),
                       np.asarray(m.vertex_normals, dtype=np.float64)))
    allv = np.concatenate([v for v, _ in sherds])
    diag = float(np.linalg.norm(allv.max(0) - allv.min(0)))

    faces, near, kept = mating_faces(sherds, diag, min_pts=50)
    print("")
    print(label + ":  near " + str(near) + " pts, kept " + str(kept) +
          " (" + format(100.0 * kept / near, ".1f") + "%)")
    if not faces:
        print("  DETECTOR FOUND NOTHING -- would skip this object")
        continue
    face = np.concatenate([f for f, _ in faces], axis=0)
    # truth: a break-face point sits within a hair of x = +/-0.05
    onbreak = np.abs(np.abs(face[:, 0]) - 0.05) < max(4 * rough, 1e-3)
    print("  purity: " + format(100.0 * onbreak.mean(), ".1f") +
          "% of kept points are actually on the break plane")
    print("  x-spread of kept: " + format(face[:, 0].min(), ".3f") + " .. " +
          format(face[:, 0].max(), ".3f") + " mm  (break at +/-0.05)")
    for R in [0.40, 0.80, 1.60, 3.20, 6.40]:
        st = probe_faces(faces, R, 4000, rng)
        if st is None:
            print("  R " + format(R, "5.2f") + "  too few probes")
            continue
        print("  R " + format(R, "5.2f") + "  texture " +
              format(st["texture"], ".5f") + "  off-face " +
              format(100 * st["off_face"], "5.1f") + "%  aspect " +
              format(st["aspect"], "5.2f") + "  spread " +
              format(st["texture_spread"], ".5f") +
              ("  SLIVER" if st["aspect"] > ASPECT_MAX else ""))
