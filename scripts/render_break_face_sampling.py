"""Draw the wall in cross-section with TORA's own 5000 points on top of it.

The question this answers: if TORA's sampling is too coarse to resolve a tenth
of a millimetre of recession, how does it match fresh sherds by their fracture
surface at all?

`measure_faces_as_network_sees.py` gave a number that needs looking at. TORA's
own overlap rule flags ~43% of the 5000 points as "contact", but the median
angle between a contact point's normal and its partner's is about 90 degrees.
Two faces pressed together point AWAY from each other -- 180 degrees. Ninety is
what a 50/50 mixture of 180 (across the fracture) and 0 (along the wall, which
simply continues across the join) produces, and the split confirms it: only
~23% of contact points are across a fracture, ~18% are wall.

So the picture has to resolve the wall, not the join. The frame is built from
the contact points themselves: a break face is a long thin ribbon, so its
directions of largest, middle and smallest spread are respectively ALONG the
join, THROUGH the wall, and ACROSS the break. Plotting the middle against the
smallest puts the wall thickness on the vertical axis and the break on the
horizontal one -- the section a conservator would cut.

  left    mesh vertices in the slab, coloured by fragment. The wall in section.
  right   what TORA receives: its 5000-point sample, dots drawn at one sampling
          cell across so the picture cannot flatter the resolution. Points whose
          nearest partner on the other fragment faces the OPPOSITE way -- the
          genuine fracture points -- are ringed in black.

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
from scipy.spatial import cKDTree

from measure_faces_as_network_sees import sample_like_tora
from measure_gap_as_network_sees import load_meshes
from compare_wear_severity import object_size

ROOT = Path("/data/gpfs/projects/punim2657/TORA")

# One thick-walled object (mated at ~165 deg) and two thin-walled ones (~87),
# plus a real scan, so the comparison is not resting on a single case.
CASES = [
    ("dataset/bbad_vessels.hdf5", "bbad_vessels", "Bottle__81bbf3134d1c",
     "__fresh", "TRAIN  bottle, fresh   (mates at 165 deg)"),
    ("dataset/bbad_vessels.hdf5", "bbad_vessels", "Vase__7545c5b77008",
     "__fresh", "TRAIN  vase, fresh   (mates at 86 deg)"),
    ("dataset/bbad_vessels.hdf5", "bbad_vessels", "Vase__7545c5b77008",
     "__worn_moderate", "TRAIN  vase, worn_moderate"),
    ("dataset/erosion_sweep.hdf5", "erosion_sweep", None,
     "_e000", "TEST  real scan, unworn"),
]

MAX_V = 250000          # cap on mesh vertices used; the scans carry ~1.1M


def find_tag(dg, obj, lvl_suffix):
    for tag in sorted(dg.keys()):
        if not tag.endswith(lvl_suffix):
            continue
        if obj is None or tag.startswith(obj):
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
    return best, n_best


def section_frame(a, b, thr):
    """A frame that cuts the wall in section, built from the contact ribbon.

    A break face is long along the join, wall-thick through the wall, and
    near-zero across the break. Take the contact points of both fragments and
    order their principal directions by spread: v0 along the join (slab axis),
    v1 through the wall (vertical), v2 across the break (horizontal).
    """
    da, _ = cKDTree(b).query(a, k=1)
    db, _ = cKDTree(a).query(b, k=1)
    band = 4.0 * thr
    c = np.vstack((a[da <= band], b[db <= band]))
    if len(c) < 20:
        c = np.vstack((a, b))
    centre = c.mean(axis=0)
    _, _, vt = np.linalg.svd(c - centre, full_matrices=False)
    v0, v1, v2 = vt[0], vt[1], vt[2]
    # columns: horizontal = across break, vertical = through wall, slab = along
    return centre, np.column_stack((v2, v1, v0))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--out", default="artifacts/break_face.png")
    ap.add_argument("--slab", type=float, default=0.02,
                    help="slab half-thickness, fraction of object size")
    ap.add_argument("--span", type=float, default=4.0,
                    help="half-width of the view, % of object size")
    a = ap.parse_args()
    root = Path(a.root)
    rng = np.random.default_rng(0)

    fig, axes = plt.subplots(len(CASES), 2, figsize=(13, 3.6 * len(CASES)))
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
                axL.set_title("no tag for " + str(obj) + lvl)
                continue
            meshes = load_meshes(dg[tag])

        verts = [np.asarray(m.vertices) for m in meshes]
        size = object_size(verts)
        sampler = "poisson" if max(len(v) for v in verts) < 200000 else "uniform"
        pcs, pns, thr = sample_like_tora(meshes, sampler)
        del meshes

        (i, j), n_contact = busiest_join(pcs, thr)
        vi, vj = verts[i], verts[j]
        if len(vi) > MAX_V:
            vi = vi[rng.choice(len(vi), MAX_V, replace=False)]
        if len(vj) > MAX_V:
            vj = vj[rng.choice(len(vj), MAX_V, replace=False)]
        centre, F = section_frame(pcs[i], pcs[j], thr)
        half = a.slab * size

        def cut(p):
            q = (p - centre) @ F
            keep = np.abs(q[:, 2]) <= half
            return q[keep][:, :2] / size * 100.0, keep

        mi, _ = cut(vi)
        mj, _ = cut(vj)
        si, ki = cut(pcs[i])
        sj, kj = cut(pcs[j])

        # which sampled points sit across a real fracture (normals opposed)
        def opposed(idx_self, idx_other, keep):
            d, nn = cKDTree(pcs[idx_other]).query(pcs[idx_self], k=1)
            ang = np.degrees(np.arccos(np.clip(
                np.sum(pns[idx_self] * pns[idx_other][nn], axis=1), -1, 1)))
            return ((d <= thr) & (ang > 135))[keep]

        oi = opposed(i, j, ki)
        oj = opposed(j, i, kj)

        spacing_pct = 100.0 * thr / size
        # one dot = one sampling cell across, in data units
        dot_pts = (spacing_pct / (2.0 * a.span)) * (5.6 * 72)
        dot_s = max(4.0, dot_pts ** 2 * 0.25)

        axL.scatter(mi[:, 0], mi[:, 1], s=0.5, c="#1f77b4", lw=0)
        axL.scatter(mj[:, 0], mj[:, 1], s=0.5, c="#d62728", lw=0)

        axR.scatter(np.r_[mi[:, 0], mj[:, 0]], np.r_[mi[:, 1], mj[:, 1]],
                    s=0.4, c="#dddddd", lw=0, zorder=1)
        for s, o, col in ((si, oi, "#1f77b4"), (sj, oj, "#d62728")):
            if len(s) == 0:
                continue
            axR.scatter(s[~o, 0], s[~o, 1], s=dot_s, c=col, alpha=0.45,
                        lw=0, zorder=2)
            axR.scatter(s[o, 0], s[o, 1], s=dot_s, c=col, alpha=0.85,
                        lw=1.1, edgecolors="k", zorder=3)

        for ax in (axL, axR):
            ax.set_aspect("equal")
            ax.set_xlim(-a.span, a.span)
            ax.set_ylim(-a.span, a.span)
            ax.set_xlabel("across the break, % of object")
        axL.set_ylabel("through the wall, %")
        axL.set_title(title + "\nmesh vertices, coloured by fragment",
                      fontsize=9)
        axR.set_title("what TORA receives: 5000 pts, spacing "
                      + format(spacing_pct, ".2f") + "% of object; "
                      + str(int(oi.sum() + oj.sum()))
                      + " across the fracture in this slab", fontsize=9)

    fig.suptitle("The wall in cross-section, and the sampling TORA gets. "
                 "One dot = one sampling cell. Ringed = across a fracture.",
                 fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.out, dpi=150)
    print("wrote " + a.out)


if __name__ == "__main__":
    main()
