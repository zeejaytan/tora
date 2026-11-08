"""A copy of the Juglet with the scan flaw at the sherd 0 / sherd 7 join trimmed off.

pr-workspace U20 ticket 12. The conservator ruled (2026-11-08) that a ~1.5 mm tip of sherd 0
sitting up to 1 mm inside sherd 7's wall is an imperfection from the scanning. Their idea: a
model trained on clean breaks will not let one sherd sit inside another, so the flaw pushes it
to turn sherd 7 (and 4, which joins 7) the way the re-seat solver did; rough training, which
lets sherds sit slightly inside each other, gets round it. The test runs the existing models on
this copy.

Only sherd 0 changes, and only at the spot; the hand pose is kept (no sherd moves). Every face of
sherd 0 with a vertex inside sherd 7 (generalised winding number, the ruler's own test) within
RADIUS of the spot is removed, and then any face left hanging by one edge, so the tip becomes a
small open hole instead of a clash. Pushing the tip out onto sherd 7's surface was tried first
and either left it 0.64 mm in or folded faces over, so it is trimmed instead.

    python scripts/make_juglet_tipfix.py juglet_gt.hdf5 out/juglet_gt.hdf5 [--json out.json]
"""

import argparse
import json
import shutil
import sys

import h5py
import numpy as np
import trimesh



def winding(q, tri, budget=4_000_000):
    """Generalised winding number (Van Oosterom-Strackee): ~1 inside a closed mesh, ~0 outside.
    Copied from sherd-worn uneven.py (adad0f3), itself the ruler's test, so this job needs no
    sherd-worn install."""
    w = np.empty(len(q))
    step = max(1, budget // len(tri))
    for s in range(0, len(q), step):
        d = tri[None] - q[s:s + step, None, None, :]
        a, b, c = d[:, :, 0], d[:, :, 1], d[:, :, 2]
        la, lb, lc = (np.linalg.norm(x, axis=2) for x in (a, b, c))
        num = np.einsum("mfi,mfi->mf", a, np.cross(b, c))
        den = (la * lb * lc + np.einsum("mfi,mfi->mf", a, b) * lc +
               np.einsum("mfi,mfi->mf", b, c) * la + np.einsum("mfi,mfi->mf", c, a) * lb)
        w[s:s + step] = np.arctan2(num, den).sum(axis=1) / (2.0 * np.pi)
    return w

CENTRE = np.array([-0.110, -0.065, 0.235])   # separate_juglet_overlap --set-aside 0:7 (file units)
RADIUS_MM = 2.5
JUGLET_MM = 65.0
TOL_MM = 0.295      # one scan spacing: what the snug re-seat (ticket 08) also allows


def pieces(h, group):
    tag = sorted(t for t in h[group] if "pieces" in h[group][t])[0]
    g = h[group][tag]["pieces"]
    keys = sorted(g.keys(), key=lambda s: (len(s), s))
    return g, keys


def inside(points, mesh):
    return winding(points, mesh.vertices[mesh.faces]) > 0.5


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--group", default="juglet_gt")
    ap.add_argument("--a", type=int, default=0, help="the sherd whose tip is trimmed")
    ap.add_argument("--b", type=int, default=7, help="the sherd it sits inside")
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    with h5py.File(a.src, "r") as h:
        g, keys = pieces(h, a.group)
        V = [np.asarray(g[k]["vertices"][:], dtype=np.float64) for k in keys]
        F = [np.asarray(g[k]["faces"][:], dtype=np.int64) for k in keys]
    lo = np.min([v.min(0) for v in V], axis=0)
    hi = np.max([v.max(0) for v in V], axis=0)
    jf = JUGLET_MM / float((hi - lo).max())
    r = RADIUS_MM / jf
    va, fa = V[a.a], F[a.a]
    B = trimesh.Trimesh(V[a.b], F[a.b], process=False)

    near = np.where(np.linalg.norm(va - CENTRE, axis=1) < r)[0]
    bad_v = near[inside(va[near], B)]
    depth = B.nearest.on_surface(va[bad_v])[1] * jf if len(bad_v) else np.zeros(0)
    drop = np.isin(fa, bad_v).any(axis=1)
    # faces left hanging: share no edge with any kept face
    for _ in range(3):
        idx = np.where(~drop)[0]
        m = trimesh.Trimesh(va, fa[idx], process=False)
        adj = np.zeros(len(idx), bool)
        adj[m.face_adjacency.reshape(-1)] = True
        if adj.all():
            break
        drop[idx[~adj]] = True
    # and any island the trim cut loose (a few faces next to the hole): keep pieces of >= 1%
    idx = np.where(~drop)[0]
    m = trimesh.Trimesh(va, fa[idx], process=False)
    comps = trimesh.graph.connected_components(m.face_adjacency, nodes=np.arange(len(idx)))
    big = max(len(c) for c in comps)
    for c in comps:
        if len(c) < 0.01 * big:
            drop[idx[c]] = True
    kept = fa[~drop]
    used = np.unique(kept)
    remap = -np.ones(len(va), np.int64)
    remap[used] = np.arange(len(used))
    va2, fa2 = va[used], remap[kept]
    A0 = trimesh.Trimesh(va, fa, process=False)
    A2 = trimesh.Trimesh(va2, fa2, process=False)
    removed_area = float((A0.area - A2.area) * jf * jf)
    gone = np.unique(fa[drop])
    reach = float(np.linalg.norm(va[gone] - CENTRE, axis=1).max() * jf) if len(gone) else 0.0
    def left_in(radius):
        nn = np.where(np.linalg.norm(va2 - CENTRE, axis=1) < radius)[0]
        lf = nn[inside(va2[nn], B)]
        return len(lf), (float(B.nearest.on_surface(va2[lf])[1].max() * jf) if len(lf) else 0.0)
    n_left, left_mm = left_in(r)          # the spot itself: must be clear
    n_ring, ring_mm = left_in(2 * r)      # the join around it, untouched: for scale
    rec = {"src": a.src, "dst": a.dst, "sherds": [keys[a.a], keys[a.b]], "mm_per_unit": jf,
           "radius_mm": RADIUS_MM, "vertices_inside_at_spot": int(len(bad_v)),
           "max_depth_mm": float(depth.max()) if len(depth) else 0.0,
           "faces_removed": int(drop.sum()), "faces_before": int(len(fa)),
           "vertices_removed": int(len(va) - len(va2)),
           "area_removed_mm2": removed_area,
           "area_removed_pct_of_sherd": 100 * removed_area / (A0.area * jf * jf),
           "hole_reach_from_spot_mm": reach,
           "left_inside_spot": n_left, "left_deepest_spot_mm": left_mm,
           "inside_within_5mm_untouched_join": n_ring, "deepest_within_5mm_mm": ring_mm}
    print(json.dumps(rec, indent=1))
    if left_mm > TOL_MM:
        sys.exit(f"tip not cleared: {left_mm:.3f} mm still inside (tolerance {TOL_MM})")

    shutil.copyfile(a.src, a.dst)
    with h5py.File(a.dst, "r+") as h:
        g, _ = pieces(h, a.group)
        sg = g[keys[a.a]]
        vd, fd = sg["vertices"].dtype, sg["faces"].dtype
        del sg["vertices"], sg["faces"]
        sg.create_dataset("vertices", data=va2.astype(vd))
        sg.create_dataset("faces", data=fa2.astype(fd))
        h.attrs["tipfix"] = json.dumps(rec)
    with h5py.File(a.dst, "r") as h:   # read back: only sherd a changed
        g, _ = pieces(h, a.group)
        for i, k in enumerate(keys):
            v = np.asarray(g[k]["vertices"][:], dtype=np.float64)
            f = np.asarray(g[k]["faces"][:], dtype=np.int64)
            wv, wf = (va2, fa2) if i == a.a else (V[i], F[i])
            assert v.shape == wv.shape and np.array_equal(f, wf), f"sherd {k} differs"
            assert np.allclose(v, wv, atol=1e-6 * (hi - lo).max()), f"sherd {k} differs"
    if a.json:
        open(a.json, "w").write(json.dumps(rec, indent=1))
    print("wrote", a.dst)


if __name__ == "__main__":
    main()
