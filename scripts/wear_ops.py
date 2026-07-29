"""Deeper, more realistic archaeological wear than smoothing alone.

The wear-trained checkpoint works (+0.235 seating on abraded pots, p=0.008) and
produced the first Juglet output showing genuine vessel form. Two limits bound
how far that route went, and this addresses both:

1. **The Juglet is worn past our training range.** Its measured surface relief
   is 0.171; the harshest level we simulated reached only 0.183 (higher =
   sharper = less worn). We trained up to *almost* this pot's condition.

2. **Smoothing is only part of what burial does.** The existing mollifier
   rounds fracture relief. Real abrasion also *removes material*, so worn sherds
   no longer meet tightly — there are gaps at the joins. That changes the
   assembly problem itself, not just the surface texture, and nothing in the
   current simulation reproduces it.

`wear_piece_set` applies, in order:
  * mollification (GARF's validated `erode_fracture_band`, unmodified) at a
    configurable kernel so wear can be pushed past the Juglet's real level;
  * **material loss** — band vertices pulled inward along their local normals,
    opening the gaps that abrasion actually creates;
  * **edge rounding** — extra smoothing where the break face meets the original
    surface, which is the first thing to soften on a buried sherd.

Ground-truth poses are never touched: this edits vertex positions only, so
scoring stays valid, exactly as the base mollifier does.
"""

import sys
from pathlib import Path

import numpy as np
import trimesh
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fracture_mesh_ops import erode_fracture_band  # noqa: E402


def _band_mask(pieces, idx, verts, band_tau_frac=0.02, feather_mult=3.0):
    """Vertices of piece `idx` on/near the contact band with any other piece."""
    allv = np.concatenate([v for v, _ in pieces], axis=0)
    scale = float(np.linalg.norm(allv.max(0) - allv.min(0))) + 1e-9
    tau = band_tau_frac * scale
    others = [cKDTree(v) for j, (v, _) in enumerate(pieces) if j != idx]
    if not others:
        return np.zeros(len(verts), bool), np.zeros(len(verts))
    best = np.full(len(verts), np.inf)
    for t in others:
        d, _ = t.query(verts)
        best = np.minimum(best, d)
    hard = best < tau
    feather = np.clip(1.0 - (best - tau) / (tau * (feather_mult - 1) + 1e-12), 0.0, 1.0)
    feather[hard] = 1.0
    return hard, feather


def wear_piece_set(pieces, strength: float, *, kernel_frac_max: float = 0.05,
                   material_loss: float = 0.0, edge_round: float = 0.0):
    """Apply mollification + material loss + edge rounding. Returns new vertex arrays.

    Args:
        pieces: list of (verts, faces) in the ASSEMBLED pose.
        strength: mollification strength (0 = none).
        kernel_frac_max: mollification radius as a fraction of piece scale.
            Raise this to push wear PAST the Juglet's real level.
        material_loss: inward displacement of band vertices, as a fraction of
            object scale. This is what opens gaps between worn sherds.
        edge_round: extra smoothing applied at the break/original-surface edge.
    """
    if strength > 0:
        verts = erode_fracture_band(pieces, strength=strength,
                                    kernel_frac_max=kernel_frac_max)
    else:
        verts = [v.copy() for v, _ in pieces]

    if material_loss <= 0 and edge_round <= 0:
        return verts

    allv = np.concatenate(verts, axis=0)
    scale = float(np.linalg.norm(allv.max(0) - allv.min(0))) + 1e-9
    cur = [(verts[i], pieces[i][1]) for i in range(len(pieces))]

    out = []
    for i, (v, f) in enumerate(cur):
        v = v.copy()
        hard, feather = _band_mask(cur, i, v)
        if hard.sum() == 0:
            out.append(v)
            continue

        m = trimesh.Trimesh(vertices=v, faces=f, process=False)
        try:
            vn = np.asarray(m.vertex_normals, dtype=np.float64)
        except Exception:
            vn = np.zeros_like(v)

        # material loss: pull the worn band inward along its own normal, which
        # is what abrasion does -- it takes material away, so the faces no
        # longer meet exactly.
        if material_loss > 0:
            d = (material_loss * scale) * feather[:, None]
            v = v - vn * d

        # edge rounding: soften the transition where the break meets the
        # original surface, by pulling those vertices toward their neighbours'
        # mean position.
        if edge_round > 0:
            edge = (feather > 0.05) & (feather < 0.95)
            if edge.sum() > 0:
                tree = cKDTree(v)
                k = min(12, len(v))
                _, nb = tree.query(v[edge], k=k)
                target = v[nb].mean(axis=1)
                v[edge] = v[edge] * (1 - edge_round) + target * edge_round
        out.append(v)
    return out
