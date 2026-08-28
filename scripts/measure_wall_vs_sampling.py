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
the thing suspected of being too coarse to see it.

CORRECTED. The first version of this took each vertex, looked at its 64 nearest
neighbours and took the first one whose normal opposed it. That was wrong and it
returned confident, plausible numbers: the mesh has ~0.2% of object between
vertices and the wall is several percent thick, so 64 neighbours never reach the
far face at all. What it actually found was local creases. It read walls of 0.27%
on objects whose volume-to-area ratio says 4%.

The honest instrument is a ray. From a surface point, fire along -normal into the
solid and take the first face you hit; that distance IS the wall. These meshes are
watertight (checked: euler 2 on the scans), so the ray has something to hit.

The env has neither embree nor rtree, so trimesh cannot cast rays here, and
installing into the training environment for a diagnostic is not worth the risk
of disturbing it. The ray is therefore marched by hand: step inward one mean
face-edge at a time and stop at the first step whose nearest face centroid is
both within a step and facing back at us. Same measurement, no new dependency,
and its resolution is one face edge -- which is stated rather than hidden. Two
independent estimates are reported so a repeat of the same mistake is visible:

  wall (ray)   median first-hit distance, over area-weighted surface samples
  wall (2V/A)  twice volume over area -- the mean thickness of a closed shell,
               a global figure that needs no ray casting

They measure the same thing by different routes. If they disagree by more than
about a factor of two, neither should be believed.

Reported per level, all as % of object size:
  spacing     TORA's own point spacing, sqrt(2 * area / 5000)
  cells       wall (ray) / spacing -- how many sampling cells fit through the
              wall.
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
import trimesh
from scipy.spatial import cKDTree

from compare_wear_severity import object_size, split_tag
from measure_gap_as_network_sees import load_meshes

NUM_POINTS = 5000
MAX_V = 60000          # vertices sampled per fragment for the thickness probe
OPPOSED = -0.7         # dot product below which two normals count as opposed


def wall_thickness(mesh, rng, n_rays=1500, max_steps=600):
    """March inward from the surface and stop at the first face looking back.

    Origins are area-weighted surface samples, not vertices, so a densely
    tessellated patch cannot dominate. Points that land on a FRACTURE face fire
    along the break rather than through the wall and return the length of the
    fragment; those are long, and the median is taken precisely so they cannot
    drag the answer.

    Resolution is one mean face edge: on the training meshes about 0.7% of
    object, on the scans about 0.11%. Both are far below the walls being
    measured, which is the property the previous version did not have.
    """
    nf = len(mesh.faces)
    if nf < 50:
        return None
    size = float(np.linalg.norm(mesh.extents))
    step = float(np.sqrt(mesh.area / nf))
    if step <= 0:
        return None
    nsteps = int(min(max_steps, max(20, (0.5 * size) / step)))
    n_rays = int(min(n_rays, max(200, nf // 4)))

    cent = np.asarray(mesh.triangles_center)
    fn = np.asarray(mesh.face_normals)
    tree = cKDTree(cent)

    pts, fidx = trimesh.sample.sample_surface(mesh, n_rays)
    nrm = fn[fidx]
    ts = np.arange(1, nsteps + 1, dtype=np.float64) * step
    probe = pts[:, None, :] - nrm[:, None, :] * ts[None, :, None]
    d, idx = tree.query(probe.reshape(-1, 3), workers=-1)
    d = d.reshape(n_rays, nsteps)
    idx = idx.reshape(n_rays, nsteps)

    facing_back = np.einsum("ij,ikj->ik", nrm, fn[idx]) < -0.5
    hit = (d < 1.2 * step) & facing_back
    hit[:, :2] = False                 # the face we started on
    has = hit.any(axis=1)
    if has.sum() < 20:
        return None
    return float(np.median(ts[np.argmax(hit, axis=1)[has]]))


def shell_thickness(meshes):
    """2 * volume / area: the mean thickness of a closed shell. No rays."""
    vol = float(sum(abs(m.volume) for m in meshes))
    area = float(sum(m.area for m in meshes))
    if area <= 0:
        return None
    return 2.0 * vol / area


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
                shell = shell_thickness(meshes)
                del meshes
                gc.collect()
                if not walls or shell is None:
                    continue
                wall = float(np.median(walls))
                rows[lvl].append((100 * wall / size, 100 * shell / size,
                                  100 * spacing / size, wall / spacing))
                print("    " + tag.ljust(40) + " wall(ray) " +
                      format(100 * wall / size, "6.2f") + "%  wall(2V/A) " +
                      format(100 * shell / size, "6.2f") + "%  spacing " +
                      format(100 * spacing / size, "5.2f") + "%  cells " +
                      format(wall / spacing, "5.2f"), flush=True)
            except Exception as e:                        # noqa: BLE001
                print("  skip " + str(obj) + "/" + str(lvl) + ": " + str(e),
                      flush=True)
    h.close()
    if not rows:
        return
    print("")
    print("  level              n  wall ray %  wall 2V/A %  spacing %  cells")
    print("  ---------------- ---  ----------  -----------  ---------  -----")
    for lvl in sorted(rows):
        a = np.array(rows[lvl])
        print("  " + str(lvl).ljust(16) + " " + str(len(a)).rjust(3) + "  " +
              format(np.median(a[:, 0]), "10.2f") + "  " +
              format(np.median(a[:, 1]), "11.2f") + "  " +
              format(np.median(a[:, 2]), "9.2f") + "  " +
              format(np.median(a[:, 3]), "5.2f"))
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
