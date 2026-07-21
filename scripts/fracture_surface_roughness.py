"""Quantify fracture-surface roughness: synthetic vs. real fracture, matched category.

Mesh-only, no GPU, no `tora` package dependency (just h5py/numpy/scipy) — the
companion geometric probe to `overlap_head_probe.py`. Where that script asks
"does TORA's encoder perceive the difference," this one asks "is there a
measurable geometric difference to perceive."

For each object: loads all part meshes from the Fractura HDF5, finds the
cross-part contact/fracture band (mesh vertices within a small distance of a
different part's surface), then measures local surface roughness on that band
as the angular standard deviation between each band vertex's normal and its
neighbors' normals within a FIXED PHYSICAL RADIUS (a fraction of the object's
bounding-box diagonal). A first version of this script used a fixed
neighbor-COUNT (k-NN) instead of a fixed radius, which is confounded by mesh
density: these Fractura meshes differ in raw vertex density by 100-200x
between real photogrammetry/CT scans (~450k vertices/part) and synthetic
fracture meshes (~2-4k vertices/part), so k-NN neighborhoods spanned very
different physical scales on each side. This version fixes that by querying a
fixed physical radius and additionally equalizing point density via
`_subsample_to_density` before scoring.

Usage:
  python scripts/fracture_surface_roughness.py \\
    --hdf5 /path/to/dataset/bone_synthetic.hdf5 --dataset-name pig \\
    --min-parts 2 --max-parts 12

  python scripts/fracture_surface_roughness.py \\
    --hdf5 /path/to/dataset/fractura_real.hdf5 --dataset-name bones \\
    --min-parts 2 --max-parts 12
"""

import argparse

import h5py
import numpy as np
import trimesh
from scipy.spatial import cKDTree


def load_parts(h5file: h5py.File, name: str):
    """Load per-part vertices and vertex normals.

    These Fractura HDF5s store `vertices`/`faces`/`shared_faces` but no
    precomputed `normals` dataset, so normals are reconstructed from face
    connectivity via trimesh (matches what `_load_mesh_from_h5` in
    `tora/data/dataset.py` effectively gets when its own `normals` lookup
    misses and it falls back to `trimesh.Trimesh(..., vertex_normals=None)`,
    whose `.vertex_normals` are computed lazily from faces on first access).
    """
    group = h5file[name]
    if "pieces" in group:
        group = group["pieces"]
    parts = sorted(group.keys())
    verts, norms = [], []
    for p in parts:
        sub = group[p]
        v = np.asarray(sub["vertices"][:], dtype=np.float64)
        f = np.asarray(sub["faces"][:], dtype=np.int64) if "faces" in sub else None
        if f is not None and len(f) > 0:
            mesh = trimesh.Trimesh(vertices=v, faces=f, process=False)
            n = np.asarray(mesh.vertex_normals, dtype=np.float64)
        else:
            n = None
        verts.append(v)
        norms.append(n)
    return verts, norms


def _subsample_to_density(verts, norms, max_total_points: int, rng: np.random.Generator):
    """Uniformly subsample each part so the WHOLE object has ~max_total_points.

    Real (photogrammetry/CT) scans and synthetic fracture meshes differ in
    raw vertex density by 100-200x (e.g. ~450k vs ~2-4k vertices per part in
    this dataset) — a k-NN or fixed-radius neighborhood on the raw meshes
    would sample a very different physical scale on each side purely from
    density, confounding any roughness comparison. Matching point density
    first removes that confound before the geometric measurement.
    """
    total = sum(len(v) for v in verts)
    if total <= max_total_points:
        return verts, norms
    keep_frac = max_total_points / total
    out_v, out_n = [], []
    for v, n in zip(verts, norms):
        k = max(4, int(round(len(v) * keep_frac)))
        idx = rng.choice(len(v), size=min(k, len(v)), replace=False)
        out_v.append(v[idx])
        out_n.append(n[idx])
    return out_v, out_n


def roughness_on_contact_band(
    verts, norms, contact_frac: float = 0.02, radius_frac: float = 0.02,
    max_total_points: int = 15000, seed: int = 0,
):
    """Returns per-object roughness stats, or None if not scoreable.

    Both the contact-band detection and the local-roughness neighborhood use
    a FIXED PHYSICAL RADIUS (a fraction of the object's bounding-box
    diagonal), not a fixed neighbor COUNT — this keeps the measurement at a
    comparable physical scale regardless of mesh resolution. Density is also
    equalized via `_subsample_to_density` first as a second safeguard.
    """
    if any(n is None for n in norms) or len(verts) < 2:
        return None

    rng = np.random.default_rng(seed)
    verts, norms = _subsample_to_density(verts, norms, max_total_points, rng)

    all_pts = np.concatenate(verts, axis=0)
    part_ids = np.concatenate([np.full(len(v), i, dtype=int) for i, v in enumerate(verts)])
    all_norms = np.concatenate(norms, axis=0)
    lens = np.linalg.norm(all_norms, axis=1, keepdims=True)
    all_norms = all_norms / np.clip(lens, 1e-8, None)

    bbox_diag = np.linalg.norm(all_pts.max(axis=0) - all_pts.min(axis=0))
    if bbox_diag <= 0:
        return None
    contact_thr = contact_frac * bbox_diag
    radius = radius_frac * bbox_diag

    tree = cKDTree(all_pts)
    contact_mask = np.zeros(len(all_pts), dtype=bool)
    for i, v in enumerate(verts):
        other_mask = part_ids != i
        if not other_mask.any():
            continue
        other_tree = cKDTree(all_pts[other_mask])
        d, _ = other_tree.query(v, k=1)
        idx_this = np.where(part_ids == i)[0]
        contact_mask[idx_this[d <= contact_thr]] = True

    band_idx = np.where(contact_mask)[0]
    min_band_points = 5
    if len(band_idx) < min_band_points:
        return None

    neighbor_lists = tree.query_ball_point(all_pts[band_idx], r=radius)
    roughness = []
    for row_i, neighbors in enumerate(neighbor_lists):
        center_idx = band_idx[row_i]
        neighbors = [j for j in neighbors if j != center_idx]
        if len(neighbors) < 3:
            continue
        center_n = all_norms[center_idx]
        neighbor_n = all_norms[neighbors]
        cos = np.clip((neighbor_n * center_n).sum(axis=1), -1.0, 1.0)
        ang = np.degrees(np.arccos(cos))
        roughness.append(ang.std())
    roughness = np.asarray(roughness)
    if len(roughness) < min_band_points:
        return None

    return {
        "n_total_verts": len(all_pts),
        "n_band_points": len(band_idx),
        "n_scored_band_points": len(roughness),
        "band_frac": len(band_idx) / len(all_pts),
        "mean_local_normal_std_deg": float(roughness.mean()),
        "median_local_normal_std_deg": float(np.median(roughness)),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hdf5", required=True)
    ap.add_argument("--dataset-name", required=True, help="HDF5 filename stem's dataset, e.g. bones or pig")
    ap.add_argument("--split", default="val")
    ap.add_argument("--min-parts", type=int, default=2)
    ap.add_argument("--max-parts", type=int, default=64)
    ap.add_argument("--max-objects", type=int, default=0, help="0 = no limit")
    ap.add_argument("--contact-frac", type=float, default=0.02, help="contact-band threshold as fraction of bbox diagonal")
    ap.add_argument("--radius-frac", type=float, default=0.02, help="local-roughness neighborhood radius as fraction of bbox diagonal")
    ap.add_argument("--max-total-points", type=int, default=15000, help="subsample whole object to this many vertices before scoring (equalizes mesh density)")
    args = ap.parse_args()

    results = []
    with h5py.File(args.hdf5, "r") as f:
        names = [n.decode() for n in f["data_split"][args.dataset_name][args.split][:]]
        for name in names:
            try:
                group = f[name]
                sub = group["pieces"] if "pieces" in group else group
                n_parts = len(sub.keys())
            except KeyError:
                continue
            if not (args.min_parts <= n_parts <= args.max_parts):
                continue

            verts, norms = load_parts(f, name)
            stats = roughness_on_contact_band(
                verts, norms,
                contact_frac=args.contact_frac,
                radius_frac=args.radius_frac,
                max_total_points=args.max_total_points,
            )
            if stats is None:
                print(f"{name:40s} parts={n_parts:3d}  SKIPPED (no normals / no band / degenerate)")
                continue
            stats["name"] = name
            stats["n_parts"] = n_parts
            results.append(stats)
            print(
                f"{name:40s} parts={n_parts:3d} band_frac={stats['band_frac']*100:5.1f}%  "
                f"mean_normal_std_deg={stats['mean_local_normal_std_deg']:6.2f}  "
                f"median={stats['median_local_normal_std_deg']:6.2f}"
            )
            if args.max_objects and len(results) >= args.max_objects:
                break

    if not results:
        print(f"\n=== {args.dataset_name} ({args.split}): no scoreable objects ===")
        return

    means = [r["mean_local_normal_std_deg"] for r in results]
    medians = [r["median_local_normal_std_deg"] for r in results]
    band_fracs = [r["band_frac"] for r in results]
    print(f"\n=== {args.dataset_name} ({args.split}): n={len(results)} objects ===")
    print(f"  mean of per-object mean_normal_std_deg:   {np.mean(means):.2f} deg")
    print(f"  median of per-object mean_normal_std_deg: {np.median(means):.2f} deg")
    print(f"  mean of per-object median_normal_std_deg: {np.mean(medians):.2f} deg")
    print(f"  mean contact-band fraction of surface:    {np.mean(band_fracs)*100:.2f}%")


if __name__ == "__main__":
    main()
