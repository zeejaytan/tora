"""Material loss by signed-distance offset — IMPLEMENTED, TESTED, AND REJECTED.

**Do not adopt this without re-reading the numbers below.** It is kept because
the negative result is worth more than the code: it records that the
mathematically correct method is the wrong one here, and why.

The motivation was sound. Both recession bugs were the same species -- vertex
displacement needs a DIRECTION, and on scanned meshes the direction cannot be
trusted (raw normals corrugated the surface; mesh normals pushed 7-17% of it the
wrong way and survived three validation rounds). An SDF offset has no direction
at all, so the whole bug class disappears by construction.

MEASURED (job on 2026-08-01, validate_sdf_offset.py):

    blue_pot   original relief 0.225
               displacement    gap x1.38   relief 0.269
               SDF grid 128    gap x1.17   relief 0.108
               SDF grid 256    gap x1.13   relief 0.133

    limb3      original relief 0.319
               displacement    gap x1.09   relief 0.530
               SDF grid 128    gap x0.73   relief 0.119
               SDF grid 256    gap x0.85   relief 0.151

The offset HALVES the surface relief, and on limb3 it CLOSES joins rather than
opening them. Relief is the signal this entire investigation rests on -- 0.92 on
fresh break surfaces versus 0.71 on worn ones is what made the wear-training work
-- so an operation that smooths the break face defeats the purpose, however clean
its mathematics.

The cause is inherent, not a tuning failure: an SDF is sampled on a grid, so
detail finer than a voxel is lost. Preserving this relief needs 512^3 or 1024^3,
and memory scales as the cube.

CONCLUSION: the approximation beats the correct method here. Displacement stays.
Revisit only with a sparse or adaptive SDF that can carry fine detail without
a dense grid.
"""

import numpy as np
import trimesh


def _backend():
    """Pick an SDF backend that tolerates imperfect scanned meshes."""
    try:
        import mesh_to_sdf  # noqa: F401
        return "mesh_to_sdf"
    except Exception:
        pass
    try:
        import mesh2sdf  # noqa: F401
        return "mesh2sdf"
    except Exception:
        pass
    return None


def available() -> bool:
    return _backend() is not None


def offset_mesh(verts: np.ndarray, faces: np.ndarray, distance: float,
                grid: int = 256, pad: float = 0.08):
    """Shrink a fragment by `distance` (world units) via a signed-distance field.

    Positive `distance` removes material. Returns (verts, faces); topology
    changes, because the surface is re-extracted.

    Raises RuntimeError if no SDF backend is installed — callers should check
    `available()` and fall back rather than silently producing unworn geometry.
    """
    be = _backend()
    if be is None:
        raise RuntimeError("no SDF backend (pip install mesh-to-sdf or mesh2sdf)")

    v = np.asarray(verts, dtype=np.float64)
    f = np.asarray(faces, dtype=np.int64)
    centre = 0.5 * (v.max(0) + v.min(0))
    extent = float((v.max(0) - v.min(0)).max())
    if extent <= 0:
        return v.copy(), f.copy()

    # normalise into a cube with padding, so the offset surface stays inside the
    # grid; an offset that touches the boundary would be clipped, not shrunk.
    s = (1.0 - pad) * 2.0 / extent
    vn = (v - centre) * s
    dn = distance * s

    if be == "mesh2sdf":
        import mesh2sdf
        sdf = mesh2sdf.compute(vn, f, size=grid, fix=True, level=2.0 / grid,
                               return_mesh=False)
    else:
        from mesh_to_sdf import mesh_to_voxels
        sdf = mesh_to_voxels(trimesh.Trimesh(vertices=vn, faces=f, process=False),
                             grid, pad=False, sign_method="depth")

    # Shrink: the surface is the zero level set, so raising the level moves it
    # inward by that distance. No direction is involved -- this is the point.
    try:
        from skimage.measure import marching_cubes
    except Exception as e:
        raise RuntimeError(f"marching cubes unavailable: {e}")

    lo, hi = float(np.nanmin(sdf)), float(np.nanmax(sdf))
    if not (lo < dn < hi):
        # offset larger than the fragment's own thickness would erase it
        raise ValueError(f"offset {distance} exceeds the fragment (sdf range "
                         f"{lo:.4f}..{hi:.4f} normalised)")

    nv, nf, _, _ = marching_cubes(sdf, level=dn)
    # marching_cubes returns voxel indices; map back to the original frame
    nv = nv / (grid - 1) * 2.0 - 1.0
    nv = nv / s + centre
    return np.asarray(nv, dtype=np.float64), np.asarray(nf, dtype=np.int64)


def offset_pieces(pieces, distance_frac: float = 0.0015, grid: int = 256,
                  verbose: bool = False):
    """Apply an SDF offset to every fragment, scaled by object size.

    Returns (pieces, ok). `ok` is False if any fragment fell back to unmodified
    geometry, so a caller can refuse to build a dataset on a partial result
    rather than shipping some worn and some pristine fragments.
    """
    allv = np.concatenate([v for v, _ in pieces], axis=0)
    scale = float(np.linalg.norm(allv.max(0) - allv.min(0))) + 1e-9
    d = distance_frac * scale

    out, ok = [], True
    for i, (v, f) in enumerate(pieces):
        try:
            nv, nf = offset_mesh(v, f, d, grid=grid)
            out.append((nv, nf))
            if verbose:
                print(f"      fragment {i}: {len(v)} -> {len(nv)} verts", flush=True)
        except Exception as e:
            if verbose:
                print(f"      fragment {i}: offset FAILED ({e}) — kept original",
                      flush=True)
            out.append((v.copy(), f.copy()))
            ok = False
    return out, ok
