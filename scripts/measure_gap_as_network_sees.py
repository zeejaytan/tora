"""Measure the join gap on the point cloud TORA actually receives, not the mesh.

Every earlier gap measurement here used mesh vertices. The network never sees
mesh vertices. `TORADataset._sample_points` Poisson-samples 5000 points across
the whole object, allocated by area, and computes its own resolution as

    overlap_thr = sqrt(2 * total_area / num_points_to_sample)

which is the spacing between neighbouring sampled points -- TORA's own scale for
"these two points are on top of each other".

That matters because the two datasets have very different mesh densities
(Breaking Bad ~0.20% of object between vertices, our scans ~0.07%), so a gap
measured in mesh vertices is measured with a different ruler on each set. After
resampling to a fixed 5000 points, the ruler is the same.

The number that decides the argument is therefore

    join gap / overlap_thr

  well below 1   the two faces are inside one sampling cell: at the resolution
                 the network sees, they are touching, and "which fragment is my
                 neighbour" is answerable by proximity alone
  well above 1   the gap is resolved, proximity is ambiguous, and the shape of
                 the break has to be read

This replicates the dataset's allocation and sampler exactly rather than
approximating them.
"""

import argparse
import gc
from collections import defaultdict
from pathlib import Path

import h5py
import numpy as np
import trimesh
from scipy.spatial import cKDTree

from tora.data.transform import sample_points_poisson

from compare_wear_severity import object_size, split_tag

NUM_POINTS = 5000
MIN_PER_PART = 20


def load_meshes(grp):
    pg = grp["pieces"]
    keys = sorted(pg.keys(), key=lambda s: int(s) if s.isdigit() else s)
    out = []
    for k in keys:
        v = np.asarray(pg[k]["vertices"][:], dtype=np.float64)
        if "faces" not in pg[k]:
            return None
        f = np.asarray(pg[k]["faces"][:])
        out.append(trimesh.Trimesh(vertices=v, faces=f, process=False))
    return out


def sample_like_tora(meshes, sampler="poisson"):
    """Verbatim from TORADataset._sample_points (dataset.py:236-256)."""
    areas = np.array([m.area for m in meshes])
    total_area = areas.sum()
    remaining = NUM_POINTS - MIN_PER_PART * len(meshes)
    counts = (MIN_PER_PART
              + (remaining * (areas / total_area)).astype(int)).tolist()
    counts[int(np.argmax(counts))] += NUM_POINTS - sum(counts)
    pcs = []
    for mesh, cnt in zip(meshes, counts):
        if sampler == "poisson":
            pts, _ = sample_points_poisson(mesh, cnt)
            if len(pts) < cnt:
                extra, _ = trimesh.sample.sample_surface(mesh, cnt - len(pts))
                pts = np.vstack((pts, extra))
        else:
            # pcu's Poisson-disk sampler is O(faces) in memory and was killed
            # on 1M-face scans. Uniform area sampling has the same spacing
            # SCALE but clumps more, so nearest-neighbour distances come out
            # slightly smaller. Fine for comparing two sets, provided BOTH are
            # sampled the same way -- which is the whole point of this script.
            pts, _ = trimesh.sample.sample_surface(mesh, cnt)
        pcs.append(pts[:cnt])
    overlap_thr = float(np.sqrt(2 * total_area / NUM_POINTS + 1e-4))
    return pcs, overlap_thr


def joint_gap(parts):
    trees = [cKDTree(s) for s in parts]
    out = []
    for i, s in enumerate(parts):
        best = np.full(len(s), np.inf)
        for j, t in enumerate(trees):
            if i != j:
                best = np.minimum(best, t.query(s, workers=-1)[0])
        out.append(float(np.percentile(best, 10)))
    return float(np.mean(out))


def run(src, dataset, limit, sampler):
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

    print(f"\n{'='*78}\n{dataset}  ({len(usable)} objects)\n{'='*78}", flush=True)
    rows = defaultdict(list)
    for obj in usable:
        for lvl, tag in groups[obj].items():
            try:
                meshes = load_meshes(dg[tag])
                if meshes is None or len(meshes) < 2:
                    continue
                # The real scans carry ~1.1M vertices per object. Holding
                # several at once got this killed on the login node with no
                # message and no table -- which reads as "no data" rather than
                # "ran out of memory". Free each one before the next.
                size = object_size([np.asarray(m.vertices) for m in meshes])
                pcs, thr = sample_like_tora(meshes, sampler)
                del meshes
                gc.collect()
                g = joint_gap(pcs)
                del pcs
                rows[lvl].append((100 * g / size, 100 * thr / size, g / thr))
                print(f"    {tag:44s} gap/spacing = {g / thr:.3f}", flush=True)
            except Exception as e:                        # noqa: BLE001
                print(f"  skip {obj}/{lvl}: {e}", flush=True)
    print(f"\n  {'level':<16} {'n':>3}  {'gap %':>8} {'TORA spacing %':>15}"
          f"  {'gap / spacing':>14}")
    print(f"  {'-'*16} {'-'*3}  {'-'*8} {'-'*15}  {'-'*14}")
    for lvl in sorted(rows):
        a = np.array(rows[lvl])
        print(f"  {lvl:<16} {len(a):>3}  {np.median(a[:,0]):>8.4f} "
              f"{np.median(a[:,1]):>15.4f}  {np.median(a[:,2]):>14.3f}")
    h.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/data/gpfs/projects/punim2657/TORA")
    ap.add_argument("--limit", type=int, default=12)
    ap.add_argument("--only", default=None,
                    choices=["bbad_vessels", "erosion_sweep"])
    ap.add_argument("--sampler", choices=["poisson", "uniform"],
                    default="uniform")
    a = ap.parse_args()
    root = Path(a.root)
    print(f"sampler: {a.sampler}")
    for name in ("bbad_vessels", "erosion_sweep"):
        if a.only and a.only != name:
            continue
        run(root / f"dataset/{name}.hdf5", name, a.limit, a.sampler)
    print("\n  gap / spacing is the number that matters. Below 1 the two faces")
    print("  sit inside one sampling cell: at the resolution the network is")
    print("  given, they are touching.")


if __name__ == "__main__":
    main()
