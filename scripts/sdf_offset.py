"""Material loss by signed-distance offset — WORKS, but not what this needs.

Convert the fragment to a distance field, move the level set, re-extract. No
direction is involved, so the winding bugs that plagued vertex displacement
cannot occur.

**HISTORY, because both my verdicts on this were wrong.**

First verdict (reject): "it halves the relief and closes joins". That rested on a
SIGN CONVENTION bug in this file -- mesh2sdf is NEGATIVE-inside, and raising the
level to shrink only shrinks when inside is POSITIVE, so it GREW every fragment
(limb3 volume 0.000329 -> 0.000412). The relief loss and closing joins were both
artefacts of reconstructing a grown surface. Caught only because the conservator
asked whether a visual check had been done. It had not.

Second measurement, sign fixed (volumes now shrink correctly):

    blue_pot   original relief 0.218
               displacement    gap x1.38   relief 0.263
               SDF grid 256    gap x1.08   relief 0.208

    limb3      original relief 0.314
               displacement    gap x1.09   relief 0.522
               SDF grid 256    gap x0.95   relief 0.223

**Relief is largely preserved at grid 256** -- 0.208 against 0.218 on blue_pot.
The "grid sampling destroys the texture" reasoning was mostly wrong; it was the
grown surface.

**The real reason not to use it here is different and is not a defect.** An SDF
offset shrinks the WHOLE fragment uniformly. Displacement targets only the
contact band, so every bit of removed material goes into opening the join --
which is why it achieves x1.38 where a uniform shrink of the same distance gets
x1.08. Most of the SDF's material loss happens on outer surfaces that have
nothing to do with the join.

That also makes targeted loss the more physical choice for pottery: a fresh
break face is newly exposed and unprotected, while the vessel's outer surface is
finished or glazed and wears far more slowly. Uniform shrinkage models neither.

VERDICT: displacement stays -- because it concentrates loss where wear actually
concentrates, not because the SDF is broken. Revisit if a future use needs
whole-fragment loss (chemical dissolution, say) rather than break-face wear,
where a uniform offset would be the correct model.
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
