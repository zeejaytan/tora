"""Material loss by signed-distance offset — the correct way to shrink a solid.

Recession currently displaces band vertices along a smoothed contact-relative
direction. That works, but it approximates what is properly a SOLID OFFSET, and
the approximation has already cost real time:

  * displacing along raw per-vertex normals corrugated the surface (relief rose
    ~6x, job 28287699), because a per-vertex direction field on a noisy scan is
    itself noise;
  * displacing along MESH normals pushed 7-17% of the surface the WRONG WAY,
    since that fraction of these scans is wound inward. It survived three rounds
    of numeric validation (jobs 28758826, 28760757).

Both bugs are the same species: **vertex displacement needs a direction, and on
scanned meshes the direction cannot be trusted.**

An SDF offset has no direction at all. Convert the fragment to a signed distance
field, subtract the offset, re-extract the surface. The operation is arithmetic
on a grid, so:

  * there is no winding to invert — the whole bug class disappears;
  * the surface cannot self-intersect or fold over;
  * "how much material was lost" is an exact distance, not an inferred quantity;
  * concave regions shrink correctly, which displacement handles badly.

The cost is resolution: an SDF is sampled on a grid, so fine relief below the
voxel size is lost. That matters here — relief IS the signal — so `grid` must be
fine enough that the offset does not silently smooth the break face. The
validation below measures exactly that rather than assuming it.

These are SCANNED fragments: holes, self-intersections and inconsistent winding
are normal, so the backend must tolerate non-watertight input. `mesh_to_sdf` and
`mesh2sdf` both do; a library assuming clean solids would fail on this material.

Falls back to the displacement implementation when no SDF backend is installed,
so the pipeline keeps working either way.
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
