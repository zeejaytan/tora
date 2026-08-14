"""Does one fracture face lose less material than the others? Measure per face.

Conservator, looking at the exported sherd, 2026-08-14: one of the fracture
edges appears to have less material removed than the other two.

That is a claim about a specific face, and nothing shown so far can settle it --
the sections were three cuts through ONE face, not a comparison between faces.
So this splits the break region by WHICH neighbouring fragment each part mates
with, which is what makes one fracture face distinct from another, and reports
each separately.

It also exports the faces in distinct colours. If the conservator and this
script disagree about which edge is which, every number below is about the
wrong thing, and there is no way to notice that from a table.

Reported per face, because the interesting quantity is a ratio and either half
of it can move on its own:

  available    how much relief there was to remove
  removed      how much came off
  efficiency   the share of it that came off -- LOW means blunting failed here,
               as opposed to there being nothing to take
  edge         median distance to the boundary of the break region, in cutoffs.
               Blunting is known to fail within about one cutoff of a boundary
               (7-9% efficiency against 93-99% well inside), so a face that is
               mostly near its own edge will lose less however well the model
               works elsewhere.

Usage:
  python scripts/removal_per_face.py --src dataset/real_heldout_norm.hdf5 \
      --dataset real_heldout_norm --object plate --out artifacts/plate_faces.glb
"""

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np
import trimesh
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wear_ops import (_band_mask, _local_mean, _outward_directions,  # noqa: E402
                      blunt_asperities)

import matplotlib  # noqa: E402

FACE_COLOURS = np.array([
    [214, 39, 40, 255], [31, 119, 180, 255], [44, 160, 44, 255],
    [255, 127, 14, 255], [148, 103, 189, 255], [140, 86, 75, 255],
    [227, 119, 194, 255], [127, 127, 127, 255],
], dtype=np.uint8)


def load(path, dsname, obj):
    with h5py.File(path, "r") as h:
        grp = h[dsname][obj]
        g = grp["pieces"] if "pieces" in grp else grp
        keys = sorted(g.keys(), key=lambda s: int(s) if s.isdigit() else s)
        return [(np.asarray(g[k]["vertices"][:], dtype=np.float64),
                 np.asarray(g[k]["faces"][:], dtype=np.int64)) for k in keys]


def region_edge(faces, in_region):
    e = faces[:, [0, 1, 1, 2, 2, 0]].reshape(-1, 2)
    a, b = e[:, 0], e[:, 1]
    cross = in_region[a] != in_region[b]
    out = np.zeros(len(in_region), bool)
    out[a[cross]] = True
    out[b[cross]] = True
    return out & in_region


def paint(v, f, cols):
    m = trimesh.Trimesh(vertices=v, faces=f, process=False)
    m.visual = trimesh.visual.ColorVisuals(mesh=m, vertex_colors=cols)
    return m


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", required=True)
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--object", required=True)
    ap.add_argument("--piece", type=int, default=-1)
    ap.add_argument("--cut", type=float, default=0.005)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    pieces = load(args.src, args.dataset, args.object)
    masks = [_band_mask(pieces, i, pieces[i][0]) for i in range(len(pieces))]
    i = (args.piece if args.piece >= 0
         else int(np.argmax([(m[1] > 0.02).sum() for m in masks])))
    worn = blunt_asperities(pieces, cut_frac=args.cut, strength=1.0, passes=3,
                            masks=masks)

    v0, f0 = pieces[i]
    v1 = worn[i][0]
    allv = np.concatenate([v for v, _ in pieces], axis=0)
    size = float(np.linalg.norm(allv.max(0) - allv.min(0)))
    R = args.cut * size
    band = masks[i][1] > 0.02
    idx = np.where(band)[0]

    # which neighbour does each part of the break region mate with? That is
    # what separates one fracture face from another.
    best = np.full(len(idx), np.inf)
    owner = np.full(len(idx), -1)
    for j, (w, _) in enumerate(pieces):
        if j == i:
            continue
        ref = w if len(w) <= 80000 else w[::max(1, len(w) // 80000)]
        d, _ = cKDTree(ref).query(v0[idx], workers=-1)
        take = d < best
        best[take], owner[take] = d[take], j

    nrm = _outward_directions(v0, idx, size)
    env0 = _local_mean(v0[idx], v0[idx], R)
    available = np.maximum(((v0[idx] - env0) * nrm).sum(axis=1), 0.0)
    removed = np.maximum(-((v1[idx] - v0[idx]) * nrm).sum(axis=1), 0.0)
    edge_v = region_edge(f0, band)
    d_edge, _ = cKDTree(v0[edge_v]).query(v0[idx], workers=-1)

    print(f"{args.object}: fragment {i} of {len(pieces)}, {len(idx)} break-region "
          f"vertices of {len(v0)}; object size {size:.4f}; "
          f"cutoff {100 * args.cut:.1f}%")
    print(f"\n  Break region split by which fragment it mates with:")
    print(f"  {'face':<22s} {'verts':>8s} {'% of region':>12s} "
          f"{'available':>11s} {'removed':>10s} {'efficiency':>11s} {'edge':>8s}")
    print("  " + "-" * 88)

    order = sorted(set(owner.tolist()))
    rows = []
    for j in order:
        m = owner == j
        if m.sum() < 50:
            continue
        eff = (removed[m].sum() / available[m].sum() * 100
               if available[m].sum() > 0 else float("nan"))
        rows.append((j, int(m.sum()), eff))
        print(f"  {'mates fragment ' + str(j):<22s} {int(m.sum()):>8d} "
              f"{100 * m.mean():>11.1f}% "
              f"{100 * available[m].mean() / size:>10.4f}% "
              f"{100 * removed[m].mean() / size:>9.4f}% "
              f"{eff:>10.1f}% "
              f"{np.median(d_edge[m]) / R:>7.1f}")
    print("\n  available/removed are % of object size, averaged per vertex.")
    print("  edge = median distance to the break-region boundary, in cutoffs.")
    if len(rows) > 1:
        lo = min(rows, key=lambda r: r[2])
        hi = max(rows, key=lambda r: r[2])
        print(f"\n  Lowest efficiency: fragment {lo[0]} at {lo[2]:.1f}%; "
              f"highest: fragment {hi[0]} at {hi[2]:.1f}%. "
              f"Ratio {hi[2] / max(lo[2], 1e-9):.1f}x.")

    # colour the faces so we can agree on which edge is which
    cols = np.tile(np.array([200, 200, 200, 255], np.uint8), (len(v0), 1))
    for n, j in enumerate(order):
        cols[idx[owner == j]] = FACE_COLOURS[n % len(FACE_COLOURS)]
    scene = trimesh.Scene()
    scene.add_geometry(paint(v0.copy(), f0, cols), node_name="1_faces_by_colour")

    rem_pct = np.zeros(len(v0))
    rem_pct[idx] = removed / size * 100
    t = np.clip(rem_pct / max(float(np.percentile(rem_pct[idx], 99)), 1e-9), 0, 1)
    hot = (np.asarray(matplotlib.colormaps["inferno"](t)) * 255).astype(np.uint8)
    vv = v0.copy()
    vv[:, 0] += float(v0.max(0)[0] - v0.min(0)[0]) * 1.25
    scene.add_geometry(paint(vv, f0, hot), node_name="2_material_removed")

    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    scene.export(outp)
    print(f"\nwrote {outp}")
    print("  1_faces_by_colour: each fracture face in its own colour, grey is")
    print("  not break region. 2_material_removed sits beside it. Check the")
    print("  colours match the faces you mean before trusting the table.")


if __name__ == "__main__":
    main()
