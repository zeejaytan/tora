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
    """Per-object medians of the reported quantities.

    The first run came back with a median mating angle of 90 degrees, which is
    what you get from NO orientation agreement at all -- and it was bimodal by
    object: bottles near 160 degrees, bowls and vases near 87. Ninety degrees is
    also exactly what a 50/50 mixture of two populations produces, so the median
    is reported alongside the split that would explain it:

      mate>135   the two normals point away from each other. A true mating pair
                 -- one point on each side of the break face.
      mate<45    the two normals point the SAME way. Not a break at all: two
                 points on the OUTER (or inner) wall, one either side of the
                 join, where the vessel surface simply continues.

    If the second population is large, then most of what TORA's own overlap rule
    flags as contact is wall continuing across a join, not fracture surface --
    which would mean the wall is thin compared to the 5000-point spacing.
    """
    spacings, mates, roughs, hi_f, lo_f, hi_n = [], [], [], [], [], 0
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
        ang = np.degrees(np.arccos(np.clip(dots, -1, 1)))
        mates.append(np.median(ang))
        hi_f.append(100.0 * np.mean(ang > 135))
        lo_f.append(100.0 * np.mean(ang < 45))
        hi_n += int((ang > 135).sum())

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
            float(np.median(mates)), float(np.median(roughs)),
            float(np.median(hi_f)), float(np.median(lo_f)), hi_n)


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
                                  st[4], st[5], st[6]))
                print("    " + tag.ljust(40) + " contact " +
                      format(st[0], "5.1f") + "%  mate " +
                      format(st[2], "6.1f") + " deg  >135 " +
                      format(st[4], "5.1f") + "%  <45 " +
                      format(st[5], "5.1f") + "%  break pts " +
                      str(st[6]).rjust(4) + "/5000", flush=True)
            except Exception as e:                        # noqa: BLE001
                print("  skip " + str(obj) + "/" + str(lvl) + ": " + str(e),
                      flush=True)
    h.close()
    if not rows:
        return
    print("")
    print("  level             n  contact%  face-sp%  mate  rough  mate>135%"
          "  mate<45%  break pts")
    print("  ---------------- --  --------  --------  ----  -----  ---------"
          "  --------  ---------")
    for lvl in sorted(rows):
        a = np.array(rows[lvl])
        print("  " + str(lvl).ljust(16) + " " + str(len(a)).rjust(2) + "  " +
              format(np.median(a[:, 0]), "8.1f") + "  " +
              format(np.median(a[:, 1]), "8.3f") + "  " +
              format(np.median(a[:, 2]), "4.0f") + "  " +
              format(np.median(a[:, 3]), "5.1f") + "  " +
              format(np.median(a[:, 4]), "9.1f") + "  " +
              format(np.median(a[:, 5]), "8.1f") + "  " +
              format(np.median(a[:, 6]), "9.0f"))
    print("")
    print("  break pts = points of the 5000 whose nearest neighbour on another")
    print("  fragment faces the opposite way, i.e. genuinely across a fracture.")
    print("  The rest of the contact set is wall continuing across the join.")


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
