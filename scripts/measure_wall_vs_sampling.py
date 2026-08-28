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

TWO CORRECTIONS ARE BAKED INTO THIS FILE. Both were caught by cross-checking two
routes to the same number against each other, which is why both routes are still
reported.

  1. The first version took each vertex, looked at its 64 nearest neighbours and
     took the first one whose normal opposed it. Wrong, and it returned
     confident, plausible numbers: the mesh has ~0.2% of object between vertices
     and the wall is several percent thick, so 64 neighbours never reach the far
     face at all. It was measuring local creases, and read walls of 0.27% on
     objects whose volume-to-area ratio says 4%.

  2. The second version cast rays, but approximately -- marching inward and
     stopping at the first FACE CENTROID that came within a step. On the coarse
     training meshes a triangle's centroid can sit far from where the ray
     actually crosses it, so true hits were missed and later, wrong surfaces
     were taken instead. It read 6.84% against 2.10% from volume-over-area: a
     factor of 3.3, which this file's own rule says means neither is believable.

What is measured now:

  wall (ray)   exact Moller-Trumbore ray-triangle intersection. From a point on
               the surface, fire along -normal into the solid; the first
               triangle actually crossed is the far face of the wall, and that
               distance IS the wall. No approximation, so no centroid-offset
               error. Candidate triangles are gathered with a KD-tree march;
               only the candidate GATHERING is approximate, and it is
               deliberately generous.

  wall (2V/A)  twice volume over area -- the mean thickness of a closed shell.
               But a fragment is not a closed shell: it also has BREAK faces,
               and counting those in the denominator makes the wall look
               thinner than it is. The break faces are removed first, using
               TORA's own overlap rule, so this is 2V / (A - A_break).

Ray origins are restricted the same way. A ray fired from a break face travels
ALONG the break and returns the width of the fragment, not the wall.

The env has neither embree nor rtree, so trimesh cannot cast rays here, and
installing into the training environment for a diagnostic is not worth the risk
of disturbing the thing under investigation. Hence the hand-rolled caster.

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
PROBE_PTS = 20000      # points per fragment used to decide which faces are break
N_RAYS = 900           # ray origins per fragment
K_CAND = 8             # candidate triangles gathered per march step
RAY_CHUNK = 100        # rays intersected at once, to bound memory
FACING_BACK = -0.3     # dot(ray normal, hit normal) below this = far wall


def _moller_trumbore(orig, direc, tri):
    """Exact ray-triangle intersection, vectorised. Returns (t, hit)."""
    e1 = tri[:, 1] - tri[:, 0]
    e2 = tri[:, 2] - tri[:, 0]
    pv = np.cross(direc, e2)
    det = np.einsum("ij,ij->i", e1, pv)
    ok = np.abs(det) > 1e-14
    inv = np.zeros_like(det)
    np.divide(1.0, det, out=inv, where=ok)
    tv = orig - tri[:, 0]
    u = np.einsum("ij,ij->i", tv, pv) * inv
    qv = np.cross(tv, e1)
    v = np.einsum("ij,ij->i", direc, qv) * inv
    t = np.einsum("ij,ij->i", e2, qv) * inv
    hit = ok & (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9)
    return t, hit


def wall_thickness(mesh, rng, origin_faces=None):
    """Median distance from the surface to the far face of the wall.

    `origin_faces` is a boolean mask over faces saying which may be used as ray
    origins; break faces are excluded by the caller because a ray fired along a
    break returns the fragment's width instead of its wall.
    """
    nf = len(mesh.faces)
    if nf < 50:
        return None
    size = float(np.linalg.norm(mesh.extents))
    step = float(np.sqrt(mesh.area / nf))
    if step <= 0:
        return None
    nsteps = int(min(500, max(20, (0.6 * size) / step)))

    cent = np.asarray(mesh.triangles_center)
    fn = np.asarray(mesh.face_normals)
    tris = np.asarray(mesh.triangles)
    tree = cKDTree(cent)

    # area-weighted origins, so a densely tessellated patch cannot dominate
    weights = np.asarray(mesh.area_faces).astype(np.float64)
    if origin_faces is not None:
        weights = np.where(origin_faces, weights, 0.0)
    if weights.sum() <= 0:
        return None
    weights /= weights.sum()
    n_rays = int(min(N_RAYS, max(200, nf // 4)))
    src = rng.choice(nf, size=n_rays, p=weights)
    bary = rng.dirichlet((1.0, 1.0, 1.0), size=n_rays)
    pts = np.einsum("ij,ijk->ik", bary, tris[src])
    nrm = fn[src]

    ts = np.arange(1, nsteps + 1, dtype=np.float64) * step
    eps = 1e-5 * size
    out = []
    for a in range(0, n_rays, RAY_CHUNK):
        b = min(a + RAY_CHUNK, n_rays)
        o, d, s = pts[a:b], -nrm[a:b], src[a:b]
        m = len(o)
        probe = o[:, None, :] + d[:, None, :] * ts[None, :, None]
        _, cand = tree.query(probe.reshape(-1, 3), k=K_CAND, workers=-1)
        cand = cand.reshape(m, -1)
        ray = np.repeat(np.arange(m), cand.shape[1])
        flat = cand.reshape(-1)
        t, hit = _moller_trumbore(o[ray], d[ray], tris[flat])
        hit &= (t > eps) & (flat != s[ray])
        hit &= np.einsum("ij,ij->i", nrm[a:b][ray], fn[flat]) < FACING_BACK
        # candidates are ray-major with a fixed width, so the per-ray minimum
        # is a reshape and a min. np.minimum.at does the same thing about two
        # orders of magnitude slower and dominated the runtime.
        out.append(np.where(hit, t, np.inf).reshape(m, -1).min(axis=1))
    best = np.concatenate(out)
    best = best[np.isfinite(best)]
    if len(best) < 20:
        return None
    return float(np.median(best))


def break_faces(meshes, thr):
    """Which faces of each fragment lie on a break, by TORA's own overlap rule.

    A face is a break face if its centroid sits within one sampling cell of
    another fragment's surface -- `has_contact = distances <= overlap_threshold`
    from point_cloud_encoder.py, applied to faces instead of sampled points.
    """
    clouds = [np.asarray(trimesh.sample.sample_surface(m, PROBE_PTS)[0])
              for m in meshes]
    trees = [cKDTree(c) for c in clouds]
    masks = []
    for i, m in enumerate(meshes):
        cent = np.asarray(m.triangles_center)
        best = np.full(len(cent), np.inf)
        for j, t in enumerate(trees):
            if j != i:
                best = np.minimum(best, t.query(cent, workers=-1)[0])
        masks.append(best <= thr)
    return masks


def shell_thickness(meshes, masks):
    """2V / (A - A_break): mean wall thickness of the shell, break faces removed.

    Plain 2V/A treats the break as if it were wall and reads far too thin.
    """
    vol = float(sum(abs(m.volume) for m in meshes))
    area = 0.0
    for m, brk in zip(meshes, masks):
        af = np.asarray(m.area_faces)
        area += float(af[~brk].sum())
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
                masks = break_faces(meshes, spacing)
                walls = [w for w in (wall_thickness(m, rng, ~brk)
                                     for m, brk in zip(meshes, masks))
                         if w is not None]
                shell = shell_thickness(meshes, masks)
                brk_pct = 100.0 * float(np.mean([m.mean() for m in masks]))
                del meshes, masks
                gc.collect()
                if not walls or shell is None:
                    continue
                wall = float(np.median(walls))
                rows[lvl].append((100 * wall / size, 100 * shell / size,
                                  100 * spacing / size, wall / spacing,
                                  brk_pct))
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
    print("  level              n  wall ray %  wall 2V/A %  spacing %  cells"
          "  break faces %")
    print("  ---------------- ---  ----------  -----------  ---------  -----"
          "  -------------")
    for lvl in sorted(rows):
        a = np.array(rows[lvl])
        print("  " + str(lvl).ljust(16) + " " + str(len(a)).rjust(3) + "  " +
              format(np.median(a[:, 0]), "10.2f") + "  " +
              format(np.median(a[:, 1]), "11.2f") + "  " +
              format(np.median(a[:, 2]), "9.2f") + "  " +
              format(np.median(a[:, 3]), "5.2f") + "  " +
              format(np.median(a[:, 4]), "13.1f"))
    print("")
    print("  The two wall columns are independent routes to the same number.")
    print("  If they disagree by more than about a factor of two, neither")
    print("  should be believed -- that is how the last two versions of this")
    print("  script were caught.")
    print("")
    print("  cells below 1: one sampled point straddles the whole wall, so the")
    print("  break face never gets a row of points of its own.")


def selftest():
    """Measure shells whose wall thickness we set ourselves.

    Two versions of this script returned confident wrong numbers before anyone
    thought to check the instrument against a known answer. This is that check,
    and it is a flag rather than a paragraph so it can be re-run:

        python scripts/measure_wall_vs_sampling.py --selftest

    The 1%-of-object case matters most: its wall is THINNER than one mean face
    edge, which is the regime the vessels are in and the regime the marching
    version got wrong.
    """
    rng = np.random.default_rng(0)
    ok = True
    print("  true wall   measured   error")
    print("  ---------   --------   -----")
    for radius, thick in ((1.0, 0.05), (1.0, 0.02), (1.0, 0.15)):
        outer = trimesh.creation.icosphere(subdivisions=4, radius=radius)
        inner = trimesh.creation.icosphere(subdivisions=4,
                                           radius=radius - thick)
        inner.invert()
        shell = trimesh.util.concatenate([outer, inner])
        shell.merge_vertices()
        got = wall_thickness(shell, rng)
        if got is None:
            print("  " + format(100 * thick / (2 * radius), "8.2f") +
                  "%   returned None")
            ok = False
            continue
        err = 100.0 * (got - thick) / thick
        print("  " + format(100 * thick / (2 * radius), "8.2f") + "%   " +
              format(100 * got / (2 * radius), "7.2f") + "%   " +
              format(err, "+5.1f") + "%")
        ok = ok and abs(err) < 3.0
    print("")
    print("  PASS" if ok else "  FAIL")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--limit", type=int, default=8)
    ap.add_argument("--only", default=None,
                    choices=["bbad_vessels", "erosion_sweep"])
    ap.add_argument("--selftest", action="store_true",
                    help="measure shells of known wall thickness and stop")
    a = ap.parse_args()
    if a.selftest:
        raise SystemExit(selftest())
    root = Path(a.root)
    for name in ("bbad_vessels", "erosion_sweep"):
        if a.only and a.only != name:
            continue
        run(root / ("dataset/" + name + ".hdf5"), name, a.limit)


if __name__ == "__main__":
    main()
