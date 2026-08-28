"""Wall thickness against the spacing of the points TORA is given.

`measure_faces_as_network_sees.py` found that TORA's own overlap rule flags
~43% of its 5000 points as contact, but only about a quarter of those sit
across a fracture -- the rest are wall continuing across the join, where the
two normals point the SAME way. The median mating angle is ~90 degrees, which
is the signature of that mixture, and it splits by vessel: bottles near 160,
bowls and vases near 87.

The obvious mechanism is that these vessels are thin-walled and the sampling is
coarse, so a single sampling cell straddles the whole wall and the break face
never gets a row of points to itself. That is a ratio, so measure it.

Wall thickness is measured on the MESH, not on the sample, because the sample is
the thing suspected of being too coarse to see it. For a sample of vertices,
take the vertex normal, walk along -normal, and find the nearest vertex of the
same fragment whose normal opposes it (dot < -0.7). That distance is the local
wall thickness. The median over vertices is the fragment's wall.

Reported per level, all as % of object size:
  wall        median wall thickness
  spacing     TORA's own point spacing, sqrt(2 * area / 5000)
  cells       wall / spacing -- how many sampling cells fit through the wall.
              Below 1 means one point straddles the whole wall, so the break
              face cannot get a row of points of its own and orientation
              across the join is a blend of fracture and outer surface.
"""

import argparse
import gc
from collections import defaultdict
from pathlib import Path

import h5py
import numpy as np
from scipy.spatial import cKDTree

from compare_wear_severity import object_size, split_tag
from measure_gap_as_network_sees import load_meshes

NUM_POINTS = 5000
MAX_V = 60000          # vertices sampled per fragment for the thickness probe
OPPOSED = -0.7         # dot product below which two normals count as opposed


def wall_thickness(mesh, rng):
    """Median distance to the nearest same-fragment vertex facing the other way."""
    v = np.asarray(mesh.vertices)
    n = np.asarray(mesh.vertex_normals)
    if len(v) < 50:
        return None
    idx = (rng.choice(len(v), MAX_V, replace=False) if len(v) > MAX_V
           else np.arange(len(v)))
    tree = cKDTree(v)
    # 64 nearest neighbours is enough to cross a thin wall; the first opposed
    # one is the other face. Points on a rim have no opposed neighbour and
    # drop out, which is correct -- a rim has no thickness to measure.
    k = min(64, len(v))
    d, nb = tree.query(v[idx], k=k, workers=-1)
    dots = np.einsum("ij,ikj->ik", n[idx], n[nb])
    ok = dots < OPPOSED
    ok[:, 0] = False
    has = ok.any(axis=1)
    if not has.any():
        return None
    first = np.argmax(ok, axis=1)[has]
    return float(np.median(d[has, first]))


def run(src, dataset, limit):
    if not Path(src).exists():
        print("missing " + str(src))
        return
    rng = np.random.default_rng(0)
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

    print("")
    print("=" * 78)
    print(dataset + "  (" + str(len(usable)) + " objects)")
    print("=" * 78)
    print("")
    rows = defaultdict(list)
    for obj in usable:
        for lvl, tag in sorted(groups[obj].items()):
            try:
                meshes = load_meshes(dg[tag])
                if meshes is None or len(meshes) < 2:
                    continue
                size = object_size([np.asarray(m.vertices) for m in meshes])
                total_area = float(sum(m.area for m in meshes))
                spacing = float(np.sqrt(2 * total_area / NUM_POINTS + 1e-4))
                walls = [w for w in (wall_thickness(m, rng) for m in meshes)
                         if w is not None]
                del meshes
                gc.collect()
                if not walls:
                    continue
                wall = float(np.median(walls))
                rows[lvl].append((100 * wall / size, 100 * spacing / size,
                                  wall / spacing))
                print("    " + tag.ljust(44) + " wall " +
                      format(100 * wall / size, "6.3f") + "%  spacing " +
                      format(100 * spacing / size, "5.2f") + "%  cells " +
                      format(wall / spacing, "5.2f"), flush=True)
            except Exception as e:                        # noqa: BLE001
                print("  skip " + str(obj) + "/" + str(lvl) + ": " + str(e),
                      flush=True)
    h.close()
    if not rows:
        return
    print("")
    print("  level              n    wall %  spacing %  cells through wall")
    print("  ---------------- ---  --------  ---------  ------------------")
    for lvl in sorted(rows):
        a = np.array(rows[lvl])
        print("  " + str(lvl).ljust(16) + " " + str(len(a)).rjust(3) + "  " +
              format(np.median(a[:, 0]), "8.3f") + "  " +
              format(np.median(a[:, 1]), "9.2f") + "  " +
              format(np.median(a[:, 2]), "18.2f"))
    print("")
    print("  cells below 1: one sampled point straddles the whole wall, so the")
    print("  break face never gets a row of points of its own.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--limit", type=int, default=8)
    ap.add_argument("--only", default=None,
                    choices=["bbad_vessels", "erosion_sweep"])
    a = ap.parse_args()
    root = Path(a.root)
    for name in ("bbad_vessels", "erosion_sweep"):
        if a.only and a.only != name:
            continue
        run(root / ("dataset/" + name + ".hdf5"), name, a.limit)


if __name__ == "__main__":
    main()
