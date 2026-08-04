"""Material loss by signed-distance offset.

Convert the fragment to a distance field, move the level set, re-extract the
surface. The motivation: both recession bugs were the same species -- vertex
displacement needs a DIRECTION, and on scanned meshes the direction cannot be
trusted (raw normals corrugated the surface; mesh normals pushed 7-17% of it the
wrong way and survived three validation rounds). A field offset has no direction.

**SIGN CONVENTION — the bug this module itself shipped with.** `mesh2sdf` uses
NEGATIVE inside. The first version raised the level to shrink, which only shrinks
when inside is POSITIVE, so it GREW every fragment instead (limb3 volume
0.000329 -> 0.000412, blue_pot 0.000633 -> 0.000797). That produced joins
CLOSING (limb3 x0.73), which was then read as evidence the METHOD was unsuitable
and it was rejected outright — for a defect in this file.

It was caught only because someone asked whether a visual check had been done.
It had not: the rejection rested on numbers alone, days after visual
confirmation was made mandatory for exactly this kind of operation. The lesson is
not about signed distance fields. The convention is now MEASURED at runtime
rather than assumed.

OPEN QUESTION, still being tested: whether grid sampling destroys the fracture
relief. These meshes carry detail at ~0.002-0.005 of object size and a 256 grid
has ~0.004 voxels, so the texture sits at grid scale. Relief is the signal this
whole investigation rests on (0.92 fresh vs 0.71 worn break surfaces), so if it
does not survive, displacement stays -- but that verdict now has to be reached
with the offset actually shrinking.

Backend tolerates non-watertight input, because these are scanned fragments where
holes, self-intersections and inconsistent winding are normal.
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

    try:
        from skimage.measure import marching_cubes
    except Exception as e:
        raise RuntimeError(f"marching cubes unavailable: {e}")

    # MEASURE the sign convention; do not assume it. Assuming positive-inside is
    # what made this module grow fragments instead of shrinking them.
    g = sdf.shape[0]
    c = g // 2
    core = float(np.nanmedian(sdf[c - 2:c + 3, c - 2:c + 3, c - 2:c + 3]))
    corner = float(np.nanmedian(sdf[:4, :4, :4]))
    inside_negative = core < corner
    # shrink = move the level set toward the interior, whichever sign that is
    level = -dn if inside_negative else dn

    lo, hi = float(np.nanmin(sdf)), float(np.nanmax(sdf))
    if not (lo < level < hi):
        # offset larger than the fragment's own thickness would erase it
        raise ValueError(f"offset {distance} exceeds the fragment (sdf range "
                         f"{lo:.4f}..{hi:.4f} normalised, level {level:.4f})")

    nv, nf, _, _ = marching_cubes(sdf, level=level)
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
