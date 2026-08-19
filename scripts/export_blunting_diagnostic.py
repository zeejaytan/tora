"""Export the sherd itself, painted with what the blunting did and where.

Asked for by the conservator, 2026-08-13: a picture is hard to read, show the
model. So this writes geometry that can be opened, turned over and inspected in
Blender or MeshLab, rather than a plot of it.

THE QUESTION IT IS BUILT TO ANSWER. The plate blunts less than the other three
objects. My first explanation -- that its texture is coarser than the cutoff
reaches -- was refuted by measurement: the plate has the MOST fine-scale relief
of the four (0.020% of object at the 0.4% scale, against blue_pot's 0.013%) and
the largest share of its relief within reach of the cut. What the render did
show is that its break face is a narrow RIBBON, about 3% of the object wide,
with relief concentrated along the two long edges -- the conservator's eggshell
case, where the fracture is a ribbon rather than a face.

The hypothesis now under test: near the edge of a ribbon the local envelope is
ONE-SIDED, because a point's neighbours all lie inward. The height a vertex
appears to stand proud of that envelope is then biased, and blunting removes
less than it should. On a broad face that region is a thin rim and hardly
matters; on a 3%-wide ribbon it is most of the surface. If true, the model
systematically under-wears thin-walled material, which is the archaeologically
common case and matters well beyond this one object.

WHAT IS EXPORTED, as separate named objects in one file so they can be shown
and hidden independently:

  1_fresh          the untouched fragment, neutral grey
  2_removal        how much material blunting took, per vertex
  3_available      how much there WAS to take (height above the envelope)
  4_efficiency     removal / available -- dark means blunting under-performed
  5_edge_zone      green = within one cutoff of the break-face edge

Put 4 and 5 side by side. If the dark regions of 4 coincide with the green of 5,
the hypothesis holds. Panels 2 and 3 separate the two ways low removal can
arise: nothing there to remove, or something there that was missed.

AND A MEASUREMENT, because a viewpoint can flatter or hide a pattern and this
one is about a thin band seen edge-on. Efficiency is tabulated against distance
from the ribbon edge, in units of the cutoff. That number does not care where
the camera is.

Usage:
  python scripts/export_blunting_diagnostic.py --src dataset/real_heldout_norm.hdf5 \
      --dataset real_heldout_norm --object plate --out artifacts/plate_diag.glb
"""

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np
import trimesh
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wear_ops import (_band_mask, _outward_directions,  # noqa: E402
                      _proud_height, blunt_asperities)

import matplotlib
matplotlib.use("Agg")
from matplotlib import cm  # noqa: E402


def load(path, dsname, obj):
    with h5py.File(path, "r") as h:
        grp = h[dsname][obj]
        g = grp["pieces"] if "pieces" in grp else grp
        keys = sorted(g.keys(), key=lambda s: int(s) if s.isdigit() else s)
        return [(np.asarray(g[k]["vertices"][:], dtype=np.float64),
                 np.asarray(g[k]["faces"][:], dtype=np.int64)) for k in keys]


def paint(v, f, values, cmap="inferno", vmin=None, vmax=None, grey=False):
    """A copy of the mesh with per-vertex colour from `values`."""
    m = trimesh.Trimesh(vertices=v.copy(), faces=f.copy(), process=False)
    if grey:
        cols = np.tile(np.array([170, 170, 170, 255], np.uint8), (len(v), 1))
    else:
        lo = float(np.nanmin(values)) if vmin is None else vmin
        hi = float(np.nanmax(values)) if vmax is None else vmax
        t = np.clip((values - lo) / max(hi - lo, 1e-12), 0, 1)
        cols = (np.asarray(cm.get_cmap(cmap)(t)) * 255).astype(np.uint8)
    m.visual = trimesh.visual.ColorVisuals(mesh=m, vertex_colors=cols)
    return m


def boundary_of_region(faces, in_region):
    """Vertices of the region that touch a vertex outside it -- the ribbon edge.

    Taken along MESH EDGES, not by proximity in space. The two long edges of a
    thin ribbon are close together in space, so a distance-based rule would
    label the whole ribbon as edge and the test would confirm itself.
    """
    e = faces[:, [0, 1, 1, 2, 2, 0]].reshape(-1, 2)
    a, b = e[:, 0], e[:, 1]
    cross = in_region[a] != in_region[b]
    edge_v = np.zeros(len(in_region), bool)
    edge_v[a[cross]] = True
    edge_v[b[cross]] = True
    return edge_v & in_region


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", required=True)
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--object", required=True)
    ap.add_argument("--piece", type=int, default=-1)
    ap.add_argument("--cut", type=float, default=0.005)
    ap.add_argument("--strength", type=float, default=1.0)
    ap.add_argument("--passes", type=int, default=3)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    pieces = load(args.src, args.dataset, args.object)
    masks = [_band_mask(pieces, i, pieces[i][0]) for i in range(len(pieces))]
    i = (args.piece if args.piece >= 0
         else int(np.argmax([(m[1] > 0.02).sum() for m in masks])))

    worn = blunt_asperities(pieces, cut_frac=args.cut, strength=args.strength,
                            passes=args.passes, masks=masks)
    v0, f0 = pieces[i]
    v1 = worn[i][0]
    allv = np.concatenate([v for v, _ in pieces], axis=0)
    size = float(np.linalg.norm(allv.max(0) - allv.min(0)))
    R = args.cut * size

    band = masks[i][1] > 0.02
    idx = np.where(band)[0]
    print(f"{args.object}: fragment {i} of {len(pieces)}, "
          f"{len(idx)} band vertices of {len(v0)}, object size {size:.4f}")

    out = _outward_directions(v0, idx, size)
    # THE SAME RULER THE MODEL USES. This measured `available` against the mean
    # of the neighbours while blunting had moved to a fitted plane, and the two
    # disagree exactly where the fix matters -- the mean is dragged inward at a
    # boundary and under-reports how proud a point is. The efficiency column
    # then read 122% and 132%, more material removed than was available, which
    # is impossible and is the signature of a ruler that moved.
    available = np.maximum(_proud_height(v0, idx, out, R), 0.0)
    removed = -((v1[idx] - v0[idx]) * out).sum(axis=1)
    removed = np.maximum(removed, 0.0)

    # how far each band vertex is from the edge of the break-face region
    edge_v = boundary_of_region(f0, band)
    if edge_v.any():
        dist_edge, _ = cKDTree(v0[edge_v]).query(v0[idx], workers=-1)
    else:
        dist_edge = np.full(len(idx), np.inf)
    print(f"  break-face region: {int(band.sum())} vertices, "
          f"{int(edge_v.sum())} on its edge; "
          f"median distance to edge {100 * np.median(dist_edge) / size:.2f}% "
          f"of object = {np.median(dist_edge) / R:.1f} cutoffs")

    # ---- the measurement a viewpoint cannot distort ----------------------
    eff = np.where(available > 1e-12, removed / np.maximum(available, 1e-12),
                   np.nan)
    # THE FEATHER, reported beside the efficiency. blunt_asperities scales its
    # budget by strength * feather * exposure, and `feather` is the taper that
    # fades wear out beyond the contact band -- 1 on the true fracture face,
    # falling to 0.02 at the region boundary this table measures distance from.
    # If efficiency simply tracks it, the "under-worn rim" is the taper working
    # as designed on surface that is NOT fracture face, not a defect.
    feather_v = masks[i][1][idx]
    print("\n  Did blunting under-perform near the ribbon edge?")
    print(f"  {'distance from edge':<22s} {'verts':>8s} {'available':>11s} "
          f"{'removed':>9s} {'efficiency':>11s} {'feather':>9s}")
    bins = [(0, 0.5), (0.5, 1.0), (1.0, 2.0), (2.0, 4.0), (4.0, np.inf)]
    for lo, hi in bins:
        m = (dist_edge >= lo * R) & (dist_edge < hi * R)
        if m.sum() < 20:
            continue
        e = eff[m]
        e = e[np.isfinite(e)]
        label = (f"{lo:g}-{hi:g} cutoffs" if np.isfinite(hi)
                 else f"more than {lo:g} cutoffs")
        print(f"  {label:<22s} {int(m.sum()):>8d} "
              f"{100 * available[m].mean() / size:>10.4f}% "
              f"{100 * removed[m].mean() / size:>8.4f}% "
              f"{100 * e.mean() if len(e) else float('nan'):>10.1f}% "
              f"{feather_v[m].mean():>9.3f}")
    print("  Efficiency is the share of what was there that actually came off.")
    print("  Compare it with FEATHER. If they track each other, the low numbers")
    print("  near the edge are the deliberate taper on non-fracture surface and")
    print("  there is nothing to fix.")
    print("  Falling toward the edge supports the one-sided-envelope idea;")
    print("  flat across the bins refutes it and the cause is elsewhere.")

    # ---- the geometry, for looking at ------------------------------------
    def full(vals, fill=np.nan):
        a = np.full(len(v0), fill, dtype=np.float64)
        a[idx] = vals
        return a

    scene = trimesh.Scene()
    scene.add_geometry(paint(v0, f0, None, grey=True), node_name="1_fresh")
    scene.add_geometry(
        paint(v0, f0, np.nan_to_num(full(removed / size * 100)),
              vmin=0.0, vmax=float(np.percentile(removed / size * 100, 99))),
        node_name="2_removal")
    scene.add_geometry(
        paint(v0, f0, np.nan_to_num(full(available / size * 100)),
              vmin=0.0, vmax=float(np.percentile(available / size * 100, 99))),
        node_name="3_available")
    scene.add_geometry(
        paint(v0, f0, np.nan_to_num(full(eff), 0.0), cmap="viridis",
              vmin=0.0, vmax=1.0),
        node_name="4_efficiency")
    zone = full((dist_edge < R).astype(float), 0.0)
    scene.add_geometry(paint(v0, f0, zone, cmap="summer", vmin=0.0, vmax=1.0),
                       node_name="5_edge_zone")

    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    scene.export(outp)
    print(f"\nwrote {outp}")
    print("  Five copies of the same fragment, as named objects. Show 4 and 5")
    print("  together: if the dark parts of 4_efficiency sit where 5_edge_zone")
    print("  is green, blunting is failing at the edge of the ribbon.")
    print("  2 and 3 separate the two reasons removal can be low -- nothing")
    print("  there to take, or something there that was missed.")


if __name__ == "__main__":
    main()
