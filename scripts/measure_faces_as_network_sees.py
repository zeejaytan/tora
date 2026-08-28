"""Does the FRACTURE SURFACE survive TORA's sampling, and does wear change it?

`measure_gap_as_network_sees.py` answered one question: is the join GAP visible
at TORA's 5000-point sampling. It is not, for our training wear. That result
prompted a fair objection: if the sampling is too coarse to see a tenth of a
millimetre, how does TORA match fresh sherds by their fracture surface at all?

The objection is about a different channel, and the code says so. The encoder is
fed six numbers per point, not three:

    tora/modeling/encoder/point_cloud_encoder.py:113
        "feat": torch.cat([part_coords, part_normals], dim=-1)

The normal comes from `mesh.face_normals[fidx]` -- the orientation of the single
triangle the point landed on. That is a SUB-SPACING cue: it reports surface
orientation at triangle scale, which on these meshes is ~0.07-0.20% of object,
some thirty times finer than the 2.9% spacing between the points themselves.

So "TORA cannot see the wear" is proved only for the gap. It is unproven for the
orientation channel, and if the wear IS visible there the earlier conclusion is
wrong. This measures the orientation channel on the exact points TORA receives.

Contact points are flagged by TORA's OWN rule, copied from the encoder:

    point_cloud_encoder.py:  has_contact = (distances <= overlap_threshold)

Reported per level:
  contact %       share of the 5000 points TORA itself flags as contact
  face spacing    median nearest-neighbour distance among one fragment's own
                  contact points -- the resolution at which the break face is
                  actually represented
  mating angle    median angle between a contact point's normal and that of the
                  nearest point on another fragment. Two faces pressed together
                  point away from each other: 180 deg is a perfect mate, 90 deg
                  is no orientation agreement at all. This is the cue that can
                  match a break WITHOUT resolving the gap.
  face roughness  median angle between a contact point's normal and the mean
                  normal of its 8 nearest same-fragment contact neighbours. The
                  texture of the break as the network receives it.
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
from measure_gap_as_network_sees import load_meshes

NUM_POINTS = 5000
MIN_PER_PART = 20


def sample_like_tora(meshes, sampler="poisson"):
    """Replicate TORADataset._sample_points, keeping the face normals."""
    areas = np.array([m.area for m in meshes])
    total_area = areas.sum()
    remaining = NUM_POINTS - MIN_PER_PART * len(meshes)
    counts = (MIN_PER_PART + (remaining * (areas / total_area)).astype(int)).tolist()
    counts[int(np.argmax(counts))] += NUM_POINTS - sum(counts)

    pcs, pns = [], []
    for mesh, cnt in zip(meshes, counts):
        if sampler == "poisson":
            pts, fidx = sample_points_poisson(mesh, cnt)
            if len(pts) < cnt:
                extra, eidx = trimesh.sample.sample_surface(mesh, cnt - len(pts))
                pts = np.vstack((pts, extra))
                fidx = np.concatenate((fidx, eidx))
        else:
            pts, fidx = trimesh.sample.sample_surface(mesh, cnt)
        pcs.append(np.asarray(pts[:cnt]))
        pns.append(np.asarray(mesh.face_normals[fidx[:cnt]]))
    overlap_thr = float(np.sqrt(2 * total_area / NUM_POINTS + 1e-4))
    return pcs, pns, overlap_thr


def face_stats(pcs, pns, thr):
    """Per-object medians of the four reported quantities."""
    spacings, mates, roughs = [], [], []
    n_contact = 0
    for i, (p, n) in enumerate(zip(pcs, pns)):
        others = [(q, m) for j, (q, m) in enumerate(zip(pcs, pns)) if j != i]
        if not others:
            continue
        oq = np.vstack([q for q, _ in others])
        om = np.vstack([m for _, m in others])
        d, idx = cKDTree(oq).query(p, k=1)
        mask = d <= thr
        n_contact += int(mask.sum())
        if mask.sum() < 10:
            continue
        cp, cn = p[mask], n[mask]

        # resolution at which this fragment's own break face is represented
        dd, _ = cKDTree(cp).query(cp, k=2)
        spacings.append(np.median(dd[:, 1]))

        # mating angle against the nearest point on the other fragment
        dots = np.sum(cn * om[idx[mask]], axis=1)
        mates.append(np.median(np.degrees(np.arccos(np.clip(dots, -1, 1)))))

        # texture of the break at the sampling the network gets
        k = min(9, len(cp))
        _, nb = cKDTree(cp).query(cp, k=k)
        mean_n = cn[nb[:, 1:]].mean(axis=1)
        mean_n /= np.linalg.norm(mean_n, axis=1, keepdims=True) + 1e-12
        dots2 = np.sum(cn * mean_n, axis=1)
        roughs.append(np.median(np.degrees(np.arccos(np.clip(dots2, -1, 1)))))

    if not spacings:
        return None
    return (100.0 * n_contact / NUM_POINTS, float(np.median(spacings)),
            float(np.median(mates)), float(np.median(roughs)))


def run(src, dataset, limit, sampler):
    """Grouping and object selection copied from measure_gap_as_network_sees."""
    if not Path(src).exists():
        print("missing " + str(src))
        return
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
                pcs, pns, thr = sample_like_tora(meshes, sampler)
                del meshes
                gc.collect()
                st = face_stats(pcs, pns, thr)
                del pcs, pns
                if st is None:
                    continue
                rows[lvl].append((st[0], 100 * st[1] / size, st[2], st[3],
                                  100 * thr / size))
                print("    " + tag.ljust(40) + " contact " +
                      format(st[0], "5.1f") + "%  face-sp " +
                      format(100 * st[1] / size, "6.3f") + "%  mate " +
                      format(st[2], "6.1f") + " deg  rough " +
                      format(st[3], "5.1f") + " deg", flush=True)
            except Exception as e:                        # noqa: BLE001
                print("  skip " + str(obj) + "/" + str(lvl) + ": " + str(e),
                      flush=True)
    h.close()
    if not rows:
        return
    print("")
    print("  level              n  contact %  face spacing %  mating deg  rough deg")
    print("  ---------------- ---  ---------  --------------  ----------  ---------")
    for lvl in sorted(rows):
        a = np.array(rows[lvl])
        print("  " + str(lvl).ljust(16) + " " + str(len(a)).rjust(3) + "  " +
              format(np.median(a[:, 0]), "9.1f") + "  " +
              format(np.median(a[:, 1]), "14.4f") + "  " +
              format(np.median(a[:, 2]), "10.1f") + "  " +
              format(np.median(a[:, 3]), "9.1f"))
    print("")
    print("  mating deg near 180 = the two faces point away from each other, so")
    print("  the break is matchable from orientation alone, gap unresolved.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--limit", type=int, default=8)
    ap.add_argument("--only", default=None,
                    choices=["bbad_vessels", "erosion_sweep"])
    ap.add_argument("--sampler", default="poisson", choices=["poisson", "uniform"])
    a = ap.parse_args()
    root = Path(a.root)
    print("sampler: " + a.sampler)
    for name in ("bbad_vessels", "erosion_sweep"):
        if a.only and a.only != name:
            continue
        run(root / ("dataset/" + name + ".hdf5"), name, a.limit, a.sampler)


if __name__ == "__main__":
    main()
