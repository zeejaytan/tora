"""Draw the wall in cross-section with TORA's own 5000 points on top of it.

The question this answers: if TORA's sampling is too coarse to resolve a tenth
of a millimetre of recession, how does it match fresh sherds by their fracture
surface at all?

`measure_faces_as_network_sees.py` gave a number that needs looking at. TORA's
own overlap rule flags ~43% of the 5000 points as "contact", but the median
angle between a contact point's normal and its partner's is 89.7 degrees. Two
faces pressed together point AWAY from each other -- 180 degrees. Ninety is what
you get from a 50/50 mixture of 180 (across the fracture) and 0 (along the wall,
which simply continues across the join). And it splits by vessel: bottles near
160 degrees, bowls and vases near 87.

The obvious suspect is wall thickness against sampling spacing, and that is a
thing to look at, not to argue about. Each row is one object:

  left    a thin slab cut through a join, MESH vertices, coloured by fragment.
          This is the wall in cross-section: two lines with the fracture at
          their end.
  right   the same slab, but only what TORA receives -- its 5000-point sample,
          drawn at true relative size, with the mesh behind it in grey.

If the wall is thinner than the point spacing, the right panel cannot show a
break face at all, whatever the left panel contains.

Usage:
  python scripts/render_break_face_sampling.py --out artifacts/break_face.png
"""

import argparse
from pathlib import Path

import h5py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import trimesh
from scipy.spatial import cKDTree

from measure_faces_as_network_sees import sample_like_tora
from measure_gap_as_network_sees import load_meshes
from compare_wear_severity import object_size, split_tag

ROOT = Path("/data/gpfs/projects/punim2657/TORA")

# One thick-walled object (mated at ~165 deg) and two thin-walled ones (~87),
# plus a real scan, so the comparison is not resting on a single case.
CASES = [
    ("dataset/bbad_vessels.hdf5", "bbad_vessels", "Bottle__81bbf3134d1c",
     "fresh", "TRAIN  bottle, fresh   (mated 165 deg)"),
    ("dataset/bbad_vessels.hdf5", "bbad_vessels", "Vase__7545c5b77008",
     "fresh", "TRAIN  vase, fresh   (mated 86 deg)"),
    ("dataset/bbad_vessels.hdf5", "bbad_vessels", "Vase__7545c5b77008",
     "worn_moderate", "TRAIN  vase, worn_moderate"),
    ("dataset/erosion_sweep.hdf5", "erosion_sweep", None,
     "000", "TEST  real scan, unworn"),
]


def find_tag(dg, obj, lvl):
    for tag in sorted(dg.keys()):
        o, l = split_tag(tag)
        if l != lvl:
            continue
        if obj is None or o == obj:
            return tag
    return None


def busiest_join(pcs, thr):
    """The pair of fragments sharing the most contact points."""
    best, n_best = (0, 1), -1
    for i in range(len(pcs)):
        for j in range(i + 1, len(pcs)):
            d, _ = cKDTree(pcs[j]).query(pcs[i], k=1)
            n = int((d <= thr).sum())
            if n > n_best:
                best, n_best = (i, j), n
    return best


def slab_frame(a, b):
    """A 2D frame that looks ALONG the join, so the wall shows its thickness.

    x is the direction between the two fragment centroids (across the break),
    y is the thinnest direction of the contact region (through the wall), and
    the slab is cut normal to the remaining axis.
    """
    c = np.vstack((a, b))
    centre = c.mean(axis=0)
    x = b.mean(axis=0) - a.mean(axis=0)
    x /= np.linalg.norm(x) + 1e-12
    rel = c - centre
    rel = rel - np.outer(rel @ x, x)
    _, _, vt = np.linalg.svd(rel, full_matrices=False)
    y = vt[-1]                       # least spread once the break axis is gone
    y -= (y @ x) * x
    y /= np.linalg.norm(y) + 1e-12
    z = np.cross(x, y)
    return centre, np.column_stack((x, y, z))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--out", default="artifacts/break_face.png")
    ap.add_argument("--slab", type=float, default=0.03,
                    help="slab half-thickness, fraction of object size")
    a = ap.parse_args()
    root = Path(a.root)

    fig, axes = plt.subplots(len(CASES), 2, figsize=(13, 3.4 * len(CASES)))
    for row, (rel, dsname, obj, lvl, title) in enumerate(CASES):
        axL, axR = axes[row]
        path = root / rel
        if not path.exists():
            axL.set_title("missing " + rel)
            continue
        with h5py.File(path, "r") as h:
            dg = h[dsname]
            tag = find_tag(dg, obj, lvl)
            if tag is None:
                axL.set_title("no tag for " + str(obj) + "/" + lvl)
                continue
            meshes = load_meshes(dg[tag])

        size = object_size([np.asarray(m.vertices) for m in meshes])
        verts = [np.asarray(m.vertices) for m in meshes]
        sampler = "poisson" if len(verts[0]) < 200000 else "uniform"
        pcs, pns, thr = sample_like_tora(meshes, sampler)
        del meshes

        i, j = busiest_join(pcs, thr)
        centre, F = slab_frame(pcs[i], pcs[j])
        half = a.slab * size

        def cut(p):
            q = (p - centre) @ F
            return q[np.abs(q[:, 2]) <= half][:, :2] / size * 100.0

        mi, mj = cut(verts[i]), cut(verts[j])
        si, sj = cut(pcs[i]), cut(pcs[j])

        # A point marker sized to the real sampling spacing, so the picture
        # cannot flatter the resolution: one dot = one sampling cell.
        spacing_pct = 100.0 * thr / size

        for ax, show_mesh in ((axL, True), (axR, False)):
            if show_mesh:
                ax.scatter(mi[:, 0], mi[:, 1], s=0.6, c="#1f77b4", lw=0)
                ax.scatter(mj[:, 0], mj[:, 1], s=0.6, c="#d62728", lw=0)
            else:
                ax.scatter(np.r_[mi[:, 0], mj[:, 0]],
                           np.r_[mi[:, 1], mj[:, 1]],
                           s=0.4, c="#cccccc", lw=0, zorder=1)
                ax.scatter(si[:, 0], si[:, 1], s=95, c="#1f77b4",
                           alpha=0.55, lw=0, zorder=2)
                ax.scatter(sj[:, 0], sj[:, 1], s=95, c="#d62728",
                           alpha=0.55, lw=0, zorder=2)
            ax.set_aspect("equal")
            ax.set_xlabel("% of object size")

        allpts = np.vstack((mi, mj)) if len(mi) and len(mj) else np.zeros((1, 2))
        cx, cy = allpts[:, 0].mean(), allpts[:, 1].mean()
        span = 6.0
        for ax in (axL, axR):
            ax.set_xlim(cx - span, cx + span)
            ax.set_ylim(cy - span, cy + span)
        axL.set_title(title + "\nmesh vertices, coloured by fragment",
                      fontsize=9)
        axR.set_title("what TORA receives: 5000 pts, spacing "
                      + format(spacing_pct, ".2f") + "% of object",
                      fontsize=9)

    fig.suptitle("The wall in cross-section, and the sampling TORA gets. "
                 "Dot size is one sampling cell.", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.out, dpi=150)
    print("wrote " + a.out)


if __name__ == "__main__":
    main()
