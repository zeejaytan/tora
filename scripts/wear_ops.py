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


def recede_and_chip(pieces, recession_frac: float = 0.004, chip_count: int = 6,
                    chip_frac: float = 0.010, seed: int = 0, verbose: bool = False):
    """Material LOSS done properly: recede the fracture edge and chip the points.

    Conservator's description of what burial actually does to a sherd:
      * the fracture edge RECEDES — material is lost from the break, so worn
        sherds no longer meet tightly and gaps open at the joins;
      * small CHIPS form on the pointy ends, which are the most exposed and
        fragile parts of a fragment. Localised and modest, not a uniform shrink.

    The earlier attempt (`material_loss` in `wear_piece_set`) tried to fake this
    by displacing vertices inward along their normals. That is not what loss is,
    and it failed accordingly — relief blew up ~6x because per-vertex
    displacement on noisy normals corrugates the surface instead of removing
    material (calibration job 28287699).

    This REMOVES GEOMETRY instead: faces near the fracture rim, and small patches
    at sharp protrusions, are deleted. That is topologically what abrasion does,
    and it cannot corrugate a surface because it never moves a vertex.

    Returns a list of (verts, faces) — topology changes, so faces come back too.
    """
    rng = np.random.default_rng(seed)
    allv = np.concatenate([v for v, _ in pieces], axis=0)
    scale = float(np.linalg.norm(allv.max(0) - allv.min(0))) + 1e-9
    out = []

    for i, (v, f) in enumerate(pieces):
        hard, feather = _band_mask(pieces, i, v)
        keep = np.ones(len(f), bool)

        # --- edge recession: drop faces at the rim of the break surface ---
        # the rim is where the break face meets the original surface: partially
        # feathered, not deep inside the contact band.
        rim_v = (feather > 0.15) & (feather < 0.98)
        if rim_v.any() and recession_frac > 0:
            rim_pts = v[rim_v]
            tree = cKDTree(rim_pts)
            fc = v[f].mean(axis=1)                      # face centroids
            d, _ = tree.query(fc)
            keep &= d > (recession_frac * scale)

        # --- chipping: remove small patches at sharp, exposed protrusions ---
        if chip_count > 0 and chip_frac > 0:
            try:
                m = trimesh.Trimesh(vertices=v, faces=f, process=False)
                sharp = np.asarray(m.vertex_defects)     # angle deficit: high = pointy
            except Exception:
                sharp = np.zeros(len(v))
            cand = np.where(hard & (sharp > np.percentile(sharp[hard], 90))
                            if hard.any() else np.zeros(len(v), bool))[0]
            if len(cand) > 0:
                picks = rng.choice(cand, size=min(chip_count, len(cand)), replace=False)
                fc = v[f].mean(axis=1)
                ftree = cKDTree(fc)
                for p in picks:
                    r = chip_frac * scale * rng.uniform(0.5, 1.5)
                    keep[ftree.query_ball_point(v[p], r)] = False

        nf = f[keep]
        if len(nf) < 16:                                 # never delete a piece
            out.append((v.copy(), f.copy()))
            continue
        m = trimesh.Trimesh(vertices=v, faces=nf, process=False)
        m.remove_unreferenced_vertices()
        if verbose:
            print(f"      piece {i}: faces {len(f)} -> {len(m.faces)} "
                  f"({100 * (1 - len(m.faces) / len(f)):.1f}% removed)", flush=True)
        out.append((np.asarray(m.vertices, dtype=np.float64),
                    np.asarray(m.faces, dtype=np.int64)))
    return out


def wear_to_target(pieces, target_relief: float, *, kernel_frac_max: float = 0.05,
                   lo: float = 0.0, hi: float = 1.0, iters: int = 5, verbose: bool = False):
    """Wear each object until it REACHES a target roughness, not by a fixed amount.

    This is the fix the calibration pointed to (job 28287699). A fixed strength
    wears different pots by wildly different amounts: at the same setting
    `blue_pot` reached relief 0.110 while `limb3` only reached 0.171, and the
    training-set mean of 0.183 hid that spread. Half the training material never
    reached the condition we actually care about.

    Raising the kernel does NOT fix this — the mollifier SATURATES (0.1707 ->
    0.1789 -> 0.1820 as the kernel grows), the same plateau GARF hit in Exp 7/7b.
    So the lever is per-object strength, targeted.

    Binary-searches mollification strength so each object lands near
    `target_relief` (lower = more worn). Returns (verts, achieved_relief).
    """
    from fracture_mesh_ops import piece_relief_stats

    def relief_of(vs):
        return float(np.mean([piece_relief_stats(v, f)["relief_p90"]
                              for v, (_, f) in zip(vs, pieces)]))

    best_v = [v.copy() for v, _ in pieces]
    best_r = relief_of(best_v)
    if best_r <= target_relief:
        return best_v, best_r          # already at least this worn

    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        v = erode_fracture_band(pieces, strength=max(mid, 1e-6),
                                kernel_frac_max=kernel_frac_max)
        r = relief_of(v)
        if verbose:
            print(f"      strength {mid:.3f} -> relief {r:.4f}", flush=True)
        if abs(r - target_relief) < abs(best_r - target_relief):
            best_v, best_r = v, r
        if r > target_relief:
            lo = mid                   # not worn enough -> wear harder
        else:
            hi = mid
    return best_v, best_r


def wear_piece_set(pieces, strength: float, *, kernel_frac_max: float = 0.05,
                   material_loss: float = 0.0, edge_round: float = 0.0):
    """Apply mollification + material loss + edge rounding. Returns new vertex arrays.

    Args:
        pieces: list of (verts, faces) in the ASSEMBLED pose.
        strength: mollification strength (0 = none).
        kernel_frac_max: mollification radius as a fraction of piece scale.
            Raise this to push wear PAST the Juglet's real level.
        material_loss: **BROKEN — DO NOT USE FOR TRAINING.** Calibration job
            28287699 showed this drives relief to 1.03-1.07, i.e. ~6x ROUGHER,
            when it should be smoother. Values near 1.0 mean neighbouring
            normals are near-perpendicular: mangled geometry, not an abraded
            pot. Cause: displacing each vertex along ITS OWN normal on a
            million-vertex scan with noisy normals adds high-frequency noise
            instead of removing material. Real material loss needs solid-body
            erosion (offsetting the whole surface, e.g. via a signed-distance
            field), not per-vertex nudging. Kept only so the failure is on
            record and not re-attempted this way.
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
