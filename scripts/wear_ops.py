"""Archaeological wear, modelled as material loss at three scales.

WEAR IS MATERIAL LOSS. Smoothing is not a separate phenomenon — it is loss of
the sharp edges. What differs between these operations is the SCALE of what goes:

    micro   asperities on the break face   -> reads as smoothing
    meso    the mating surface as a whole  -> reads as a receding edge
    macro   chunks at exposed points       -> reads as chipping

Consequences that matter for building a dataset:

  * Loss at ANY scale opens the joins, so worn sherds no longer meet tightly.
    That is the effect no earlier training data had — fragments always still
    mated perfectly, merely with smoother faces — and it changes the assembly
    problem rather than just its appearance.

  * Asperity-scale loss SATURATES. Beyond a point more smoothing removes nothing
    further (galli_pot stalls at relief 0.288, plate at 0.234, against a 0.15
    target), the same plateau GARF hit in Exp 7/7b. Wear does not stop there; it
    continues at a larger scale. `wear_to_loss` does exactly that.

  * ORDER follows the sherd's history: chip, then smooth, then recede. A sherd
    chips in antiquity and is then abraded for centuries, so its chip boundaries
    end up rounded. Chipping last leaves fresh sharp edges, which are themselves
    relief — that drove measured roughness ABOVE the untouched sherd
    (galli_pot 0.457 -> 0.681) until the order was corrected.

Ground-truth poses are never touched — geometry-only edits — so scoring stays
valid and any dataset built here remains scoreable.

PLANNED (decided 2026-08-01, after current testing): replace recession with
genuine mesh offsetting via trimesh or libigl signed-distance fields. The current
vertex displacement approximates what is properly a solid offset; a real offset
would handle self-intersection, remove the need for direction smoothing, and
eliminate the whole class of normal-winding bugs documented in
docs/notes/WEAR_SIMULATION.md. Validate any replacement against this
implementation before switching -- every downstream dataset depends on it.

No purpose-built tool for this exists: fracture-modes (behind Breaking Bad)
breaks objects rather than wearing them, terrain-erosion libraries target
landscapes, and the nearest archaeological work (Deep Aramaic) targets
inscriptions with no released library. See docs/notes/WEAR_SIMULATION.md.

Entry points:
    apply_wear      one object, explicit doses
    wear_to_loss    wear until the joins have opened by a target amount
    wear_to_target  wear until the surface reaches a target roughness
    WEAR_CONDITIONS canonical conditions for building a dataset
"""

import sys
from pathlib import Path

import numpy as np
import trimesh
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fracture_mesh_ops import erode_fracture_band  # noqa: E402


def _band_mask(pieces, idx, verts, band_tau_frac=0.02, feather_mult=3.0,
               ref_pts: int = 80000, seed: int = 0):
    """Vertices of piece `idx` on/near the contact band with any other piece.

    This is the pipeline's real hot spot — profiling (job 28740054) showed a
    single nearest-neighbour query over ~460k vertices costs 11.4s, and this
    runs once per fragment per other-fragment. Two things make it affordable:

      * the reference set is SUBSAMPLED. We only need each vertex's distance to
        another fragment's SURFACE, and 80k points describe that surface just as
        well as 500k for a tolerance measured in percent of object scale. Tree
        size drops ~6x.
      * `workers=-1` actually applies here. An earlier attempt patched
        `scipy.spatial.cKDTree` globally and gained nothing (x1.0), because this
        module binds `cKDTree` at import time — the patch only ever reached
        GARF's mollifier, which is ~12s of an 843s run.
    """
    rng = np.random.default_rng(seed)
    allv = np.concatenate([v for v, _ in pieces], axis=0)
    scale = float(np.linalg.norm(allv.max(0) - allv.min(0))) + 1e-9
    tau = band_tau_frac * scale

    best = np.full(len(verts), np.inf)
    found = False
    for j, (v, _) in enumerate(pieces):
        if j == idx:
            continue
        ref = v if len(v) <= ref_pts else v[rng.choice(len(v), ref_pts, replace=False)]
        d, _ = cKDTree(ref).query(verts, workers=-1)
        best = np.minimum(best, d)
        found = True
    if not found:
        return np.zeros(len(verts), bool), np.zeros(len(verts))

    hard = best < tau
    feather = np.clip(1.0 - (best - tau) / (tau * (feather_mult - 1) + 1e-12), 0.0, 1.0)
    feather[hard] = 1.0
    return hard, feather


def _smoothed_normals(v, f, mask, k: int = 16):
    """Outward vertex normals, averaged over neighbours to remove scan noise.

    This is the fix for the corrugation failure. Displacing along RAW per-vertex
    normals on a million-point scan adds high-frequency noise — measured relief
    blew up ~6x (job 28287699). Averaging the normal field first makes the
    displacement smooth, so the surface retreats instead of crumpling.

    Only computed for `mask` vertices (the fracture band), which is a small
    fraction of the mesh — smoothing all of a 1M-vertex scan is needlessly slow.
    """
    m = trimesh.Trimesh(vertices=v, faces=f, process=False)
    try:
        vn = np.asarray(m.vertex_normals, dtype=np.float64)
    except Exception:
        return np.zeros_like(v)
    idx = np.where(mask)[0]
    if len(idx) == 0:
        return np.zeros_like(v)
    tree = cKDTree(v)
    _, nb = tree.query(v[idx], k=min(k, len(v)), workers=-1)
    sm = vn[nb].mean(axis=1)
    n = np.linalg.norm(sm, axis=1, keepdims=True)
    out = np.zeros_like(v)
    out[idx] = sm / np.maximum(n, 1e-12)
    return out


def recede_surface(pieces, recession_frac: float = 0.0015, normal_k: int = 16, masks=None):
    """Retreat the MATING SURFACE so worn sherds no longer meet tightly.

    Why the surface and not the rim: two fragments touch across the WHOLE break
    face, so trimming only its outline leaves the middle still meeting perfectly.
    Validation showed exactly that — `blue_pot`, whose fragments have broad
    contact areas, saw its joints *close* slightly (x0.8) while `limb3` opened
    (x2.6). Receding the surface itself fixes that.

    Displaces band vertices inward along a SMOOTHED normal field, weighted by
    how deep in the contact band they sit. Vertices are moved, not deleted, so
    the sherd stays a closed surface; the piece simply becomes slightly thinner
    at the break, which is what opens the join.
    """
    allv = np.concatenate([v for v, _ in pieces], axis=0)
    scale = float(np.linalg.norm(allv.max(0) - allv.min(0))) + 1e-9
    out = []
    for i, (v, f) in enumerate(pieces):
        hard, feather = masks[i] if masks is not None else _band_mask(pieces, i, v)
        band = feather > 0.02
        if not band.any() or recession_frac <= 0:
            out.append((v.copy(), f.copy()))
            continue

        # Retreat direction comes from the CONTACT, not from mesh normals.
        #
        # Using mesh normals was a real bug, found by visualising the join
        # (jobs 28758826 / 28760757). These scans have 7-15% of their band
        # normals wound INWARD, and wherever that happened recession pushed the
        # surface TOWARD the neighbouring fragment. The damage tracked the defect
        # exactly: blue_pot at 14.5% inverted normals went backwards (x0.95),
        # vert9 at 12.2% barely moved, coxae at 7.1% behaved correctly. Small
        # recessions looked worst because the wrongly-moved patches are the
        # closest points, so they dominate the measurement.
        #
        # Moving away from the nearest point on another fragment is correct by
        # construction, whatever the winding: material is lost AT the contact, so
        # the surface retreats FROM the contact.
        idx = np.where(band)[0]
        nearest = None
        best = np.full(len(idx), np.inf)
        for j, (w, _) in enumerate(pieces):
            if j == i:
                continue
            ref = w if len(w) <= 80000 else w[::max(1, len(w) // 80000)]
            d_, k_ = cKDTree(ref).query(v[idx], workers=-1)
            upd = d_ < best
            if upd.any():
                pts = ref[k_[upd]]
                if nearest is None:
                    nearest = np.zeros((len(idx), 3))
                nearest[upd] = pts
                best[upd] = d_[upd]
        if nearest is None:
            out.append((v.copy(), f.copy()))
            continue

        away = v[idx] - nearest
        n = np.linalg.norm(away, axis=1, keepdims=True)
        away = np.divide(away, np.maximum(n, 1e-12))

        # Smooth the direction field, for the reason the original normals were
        # smoothed: an unsmoothed per-vertex direction corrugates the surface
        # instead of retreating it (relief blew up ~6x, job 28287699).
        if len(idx) > 8:
            _, nb = cKDTree(v[idx]).query(v[idx], k=min(normal_k, len(idx)), workers=-1)
            away = away[nb].mean(axis=1)
            n = np.linalg.norm(away, axis=1, keepdims=True)
            away = np.divide(away, np.maximum(n, 1e-12))

        # CAP the displacement by local feature size, or the surface folds.
        #
        # Vertex displacement cannot move a concave region inward further than
        # its radius of curvature: past that the surface passes through itself
        # and leaves spikes, which register as relief. This is the failure that
        # SDF offsetting exists to avoid ("without causing the mesh to fold over
        # itself").
        #
        # It is why worn_heavy (recession 0.0025) measured ROUGHER than the
        # untouched sherd on 4 of 6 pots while worn_moderate (0.0010) passed
        # everywhere -- and why loss_dominant, with MORE chipping and LESS
        # smoothing, still came out smoother than worn_heavy. Chips were never
        # the cause; three hypotheses were spent on them before the render made
        # the folded geometry visible.
        #
        # Local feature size is estimated as the distance to the nearest surface
        # point that is not an immediate neighbour -- for a thin sherd that is
        # the opposite wall, for a concave dimple it is the curvature scale.
        if len(idx) > 8:
            k_probe = min(48, len(v))
            dprobe, _ = cKDTree(v).query(v[idx], k=k_probe, workers=-1)
            # skip the immediate ring; the far end of the local neighbourhood
            # approximates the free space available to move into
            local_feature = dprobe[:, -1]
            cap = 0.35 * local_feature
        else:
            cap = np.full(len(idx), np.inf)

        # Smooth the displacement MAGNITUDE as well as its direction. The
        # feather weight varies per vertex, so an unsmoothed magnitude field
        # sculpts new undulation into the surface -- the displacement gradient
        # becomes relief. That is why worn_heavy (recession 0.0025) measured
        # rougher than the untouched sherd on 4 of 6 pots while worn_moderate
        # (0.0010) passed everywhere: the same effect, scaled up.
        mag = feather[idx]
        if len(idx) > 8:
            _, nbm = cKDTree(v[idx]).query(v[idx], k=min(normal_k, len(idx)),
                                           workers=-1)
            mag = mag[nbm].mean(axis=1)

        amount = np.minimum((recession_frac * scale) * mag, cap)
        disp = np.zeros_like(v)
        disp[idx] = away * amount[:, None]
        out.append((v + disp, f.copy()))
    return out


def _chip_dish(v, f, sites, depth_ratio: float = 0.45):
    """A chip scar as a dish pressed into the surface — no topology change.

    Chipping used to DELETE faces, which is why the conservator found holes: a
    deleted patch is a perforation, and nothing closed it. Capping the rim
    afterwards was tried and does not work either. A cap is a fan of triangles
    to one apex, and on a rim that wraps a corner it bulges however the apex is
    placed — measured at +0.12% volume on a 6% slab and +0.18% on a 3.5% one,
    i.e. a chip that ADDED material. A boolean subtraction would be the clean
    answer but neither this machine nor the cluster has a backend for it.

    Displacing instead of deleting settles all of it at once. Topology never
    changes, so a sealed sherd stays sealed by construction rather than by
    repair; pressing the surface inward genuinely removes volume; and the result
    is a concave scar, which is what a chip leaves.

    This is NOT the earlier displacement approach that corrugated surfaces (job
    28287699, relief up ~6x). That moved every band vertex along its own raw
    normal on a noisy million-point scan. Here one direction serves a whole chip
    and the falloff is smooth, so the patch cannot corrugate — it can only dish.

    The direction is verified against the solid rather than trusted. These scans
    have 7-15% of normals wound inward, and a flipped direction would raise a
    blister where a chip belongs — the same defect, in a new place, that took
    three rounds of numeric validation to catch last time.
    """
    if not sites:
        return v
    v = v.copy()
    m = trimesh.Trimesh(vertices=v, faces=f, process=False)
    try:
        vn = np.asarray(m.vertex_normals, dtype=np.float64)
    except Exception:
        return v
    tree = cKDTree(v)

    for centre_idx, r in sites:
        idx = np.asarray(tree.query_ball_point(v[centre_idx], r), dtype=np.int64)
        if len(idx) < 8:
            continue
        d = vn[idx].mean(axis=0)
        n = float(np.linalg.norm(d))
        if n < 1e-12:
            continue
        into = -d / n

        probe = v[centre_idx] + into * (0.25 * r)
        try:
            cp, _, fid = trimesh.proximity.closest_point(m, probe[None, :])
            if float(((probe - cp[0]) * m.face_normals[fid[0]]).sum()) > 0:
                into = -into           # normals were wound the wrong way here
        except Exception:
            pass

        dist = np.linalg.norm(v[idx] - v[centre_idx], axis=1)
        w = np.clip(1.0 - (dist / r) ** 2, 0.0, 1.0) ** 2   # 1 at centre, 0 at rim
        v[idx] += into * (depth_ratio * r) * w[:, None]
    return v


def _chip_boolean(v, f, sites, seed: int = 0, flatten: float = 0.55,
                  bite: float = 0.15):
    """A chip as a genuine subtraction — the flake is cut away, not pressed in.

    Available since manifold3d was installed (2026-08-07). Preferred over the
    dish when it succeeds, because it is what a chip physically IS: a piece
    detaches and leaves a scar with a defined edge, rather than the surface
    sagging inward. The dish is a good approximation; this is the thing itself.

    The cutter is a jittered, flattened blob rather than a sphere. A sphere
    subtracts a drilled pocket, which reads as machining; real flake scars are
    shallow and irregular, wider across the surface than they are deep.

    Falls back to the dish on failure and says so. Boolean operations on scan
    meshes are not reliable in the way they are on clean solids -- a mesh that
    is not properly manifold can produce garbage or nothing at all -- so this
    must never be the only path.
    """
    rng = np.random.default_rng(seed)
    m = trimesh.Trimesh(vertices=v, faces=f, process=False)
    try:
        vn = np.asarray(m.vertex_normals, dtype=np.float64)
    except Exception:
        return None

    cutters = []
    for centre_idx, r in sites:
        n = vn[centre_idx]
        ln = float(np.linalg.norm(n))
        if ln < 1e-12:
            continue
        n = n / ln

        s = trimesh.creation.icosphere(subdivisions=2, radius=r)
        sv = np.asarray(s.vertices, dtype=np.float64)
        sv *= (1.0 + rng.uniform(-0.28, 0.28, len(sv)))[:, None]   # irregular

        # flatten along the surface normal: a scallop, not a bore hole
        basis = np.eye(3) - (1.0 - flatten) * np.outer(n, n)
        sv = sv @ basis.T

        # How deep the cut goes: the flattening has already scaled the cutter
        # to `flatten * r` along the normal, so offsetting the centre by
        # `bite * r` leaves a penetration of (flatten - bite) * r. Getting this
        # wrong is easy and quiet -- at bite 0.45 the cut grazed the surface and
        # removed 0.013% where the dish removed 0.294%, which would have read as
        # "boolean chipping barely wears anything" rather than as a mis-set
        # offset.
        s = trimesh.Trimesh(vertices=sv + v[centre_idx] + n * (r * bite),
                            faces=s.faces, process=False)
        cutters.append(s)

    if not cutters:
        return None
    try:
        out = trimesh.boolean.difference([m] + cutters)
    except Exception:
        return None
    if out is None or len(out.faces) < 16:
        return None
    ov = np.asarray(out.vertices, dtype=np.float64)
    of = np.asarray(out.faces, dtype=np.int64)
    # a subtraction must not add material; if it did, the operation misbehaved
    try:
        if abs(out.volume) > abs(m.volume) * 1.0001:
            return None
    except Exception:
        pass
    return ov, of


def _boundary_loops(faces):
    """Ordered vertex loops around every opening in a mesh.

    A boundary edge belongs to exactly one face. Walking those edges gives the
    rim of each hole, in order, which is what a cap has to be built on.
    """
    e = np.sort(faces[:, [0, 1, 1, 2, 2, 0]].reshape(-1, 2), axis=1)
    uniq, cnt = np.unique(e, axis=0, return_counts=True)
    bedges = uniq[cnt == 1]
    if not len(bedges):
        return []

    adj = {}
    for a, b in bedges:
        adj.setdefault(int(a), []).append(int(b))
        adj.setdefault(int(b), []).append(int(a))

    seen, loops = set(), []
    for start in adj:
        if start in seen:
            continue
        loop, cur, prev = [start], start, None
        seen.add(start)
        while True:
            nxt = next((c for c in adj[cur] if c != prev and c not in seen), None)
            if nxt is None:
                break
            loop.append(nxt)
            seen.add(nxt)
            prev, cur = cur, nxt
        if len(loop) >= 3:
            loops.append(np.asarray(loop, dtype=np.int64))
    return loops


def _seal_chip_scars(mv, mf, pre_boundary_pts, orig_mesh=None,
                     concavity: float = 0.35,
                     verbose: bool = False, max_passes: int = 4):
    """Seal repeatedly until nothing is left open.

    One pass is not enough on thin walls. A chip there can punch clean through,
    and the rims of the resulting opening meet at pinch points -- vertices where
    more than two boundary edges join. The loop walk terminates early at such a
    vertex and its closing edge never gets capped. Measured on a 3.5% slab: one
    pass took 1125 open edges down to 13 rather than to zero, while a 6% slab
    (no through-punching) sealed completely first time.

    Re-deriving the boundary after each pass turns the leftovers into ordinary
    loops, because the caps already added remove the junctions that broke the
    walk. Bounded, and it reports if it ever fails to converge.
    """
    total_sealed = total_left = 0
    for _ in range(max_passes):
        mv, mf, sealed, left = _seal_once(mv, mf, pre_boundary_pts, orig_mesh,
                                          concavity, verbose)
        total_sealed += sealed
        total_left = left
        if sealed == 0:
            break
    return mv, mf, total_sealed, total_left


def _seal_once(mv, mf, pre_boundary_pts, orig_mesh=None,
               concavity: float = 0.35, verbose: bool = False):
    """Close the openings our own face deletion made, leaving a concave scar.

    Conservator's finding, 2026-08-07: the wear model punches holes. Both
    material-loss effects work by deleting faces and nothing ever closed the
    boundary, so every sherd came out open at every wear level when the scans
    had arrived sealed. Confirmed by count -- holes equalled chips x sherds
    exactly, and the largest reached 18.6% of the object's width.

    A real chip does not perforate a sherd. It detaches a flake and leaves a
    fresh concave scar, and the sherd is still a solid object afterwards. So the
    rim is capped with a shallow dish pushed INWARD, not a flat lid (which would
    read as a machined facet) and not an outward bulge (which would add material
    that wear just removed).

    Pre-existing openings are left alone. Some scans arrive with holes -- one of
    four narrow_bottle3 sherds did -- and silently repairing the scanner's gaps
    would change the source geometry while claiming only to simulate wear. Rims
    are matched by POSITION against the untouched mesh, because deleting faces
    renumbers the vertices.
    """
    loops = _boundary_loops(mf)
    if not loops:
        return mv, mf, 0, 0

    pre_tree = cKDTree(pre_boundary_pts) if len(pre_boundary_pts) else None
    scale = float(np.linalg.norm(mv.max(0) - mv.min(0))) + 1e-12

    m = trimesh.Trimesh(vertices=mv, faces=mf, process=False)
    try:
        vn = np.asarray(m.vertex_normals)
    except Exception:
        vn = np.zeros_like(mv)

    new_v, new_f = [mv], [mf]
    n_next = len(mv)
    sealed = skipped = 0

    for loop in loops:
        pts = mv[loop]
        if pre_tree is not None:
            d, _ = pre_tree.query(pts)
            if (d < 1e-9 * scale + 1e-12).mean() > 0.5:
                skipped += 1          # the scanner's hole, not ours
                continue

        centre = pts.mean(axis=0)
        radius = float(np.linalg.norm(pts - centre, axis=1).mean())
        if radius <= 0:
            continue

        outward = vn[loop].mean(axis=0)
        n = float(np.linalg.norm(outward))
        if n < 1e-12:
            u, s, vt = np.linalg.svd(pts - centre, full_matrices=False)
            outward = vt[2]
            n = 1.0
        outward = outward / n

        # Which way is INTO the sherd?
        #
        # Dishing along -outward is right for an ordinary chip, whose rim lies
        # on the surface with material behind it. It is wrong when the chip has
        # punched clean through a thin wall: there are then two rims facing
        # opposite ways, and dishing both inward builds a lens of NEW volume.
        # Measured before this check: a 6% slab GAINED 0.12% and a 3.5% slab
        # 0.18% — a chip that added material.
        #
        # So the candidate apex is tested against the untouched solid rather
        # than assumed. The test is local (nearest surface point and its normal)
        # so it survives the scans that are not watertight, which a containment
        # test would not.
        apex = centre - outward * (concavity * radius)
        if orig_mesh is not None:
            try:
                cp, _, fid = trimesh.proximity.closest_point(
                    orig_mesh, np.vstack([apex, centre + outward * (concavity * radius)]))
                fn0 = orig_mesh.face_normals[fid]
                inside = ((np.vstack([apex, centre + outward * (concavity * radius)])
                           - cp) * fn0).sum(axis=1) < 0
                if not inside[0] and inside[1]:
                    apex = centre + outward * (concavity * radius)
                elif not inside[0] and not inside[1]:
                    # punched through: neither side has material behind it, so
                    # a flat cap is the honest close. It adds no volume and
                    # keeps the sherd solid.
                    apex = centre
            except Exception:
                pass
        ai = n_next
        n_next += 1
        new_v.append(apex[None, :])

        k = len(loop)
        tri = np.empty((k, 3), dtype=np.int64)
        tri[:, 0] = loop
        tri[:, 1] = np.roll(loop, -1)
        tri[:, 2] = ai
        new_f.append(tri)
        sealed += 1

    if sealed == 0:
        return mv, mf, 0, skipped

    out_v = np.concatenate(new_v, axis=0)
    out_f = np.concatenate(new_f, axis=0)
    # the fan is built from an unordered walk, so winding is not guaranteed;
    # let trimesh make it consistent rather than trusting the traversal
    try:
        mm = trimesh.Trimesh(vertices=out_v, faces=out_f, process=False)
        mm.fix_normals()
        out_v = np.asarray(mm.vertices, dtype=np.float64)
        out_f = np.asarray(mm.faces, dtype=np.int64)
    except Exception:
        pass
    if verbose:
        print(f"        sealed {sealed} chip scar(s), left {skipped} "
              f"pre-existing opening(s) alone", flush=True)
    return out_v, out_f, sealed, skipped


def recede_and_chip(pieces, recession_frac: float = 0.004, chip_count: int = 6,
                    chip_frac: float = 0.010, seed: int = 0, verbose: bool = False,
                    masks=None, seal_scars: bool = True,
                    chip_method: str = "auto"):
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
        hard, feather = masks[i] if masks is not None else _band_mask(pieces, i, v)
        keep = np.ones(len(f), bool)

        # Rims this mesh ALREADY had, recorded by position: deleting faces
        # renumbers the vertices, so indices cannot be carried across.
        e0 = np.sort(f[:, [0, 1, 1, 2, 2, 0]].reshape(-1, 2), axis=1)
        u0, c0 = np.unique(e0, axis=0, return_counts=True)
        pre_boundary = (v[np.unique(u0[c0 == 1])] if (c0 == 1).any()
                        else np.empty((0, 3)))

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
            # Never chip a scan artifact. A hole's rim is sharp, so it scores
            # high on the same "pointy and exposed" test real protrusions do --
            # and a chip landing there moved the rim, which defeated the check
            # meant to leave pre-existing openings alone. narrow_bottle3 went
            # from 2/4 sealed to 4/4, i.e. the scanner's gaps were quietly
            # repaired and counted as wear.
            on_boundary = np.zeros(len(v), bool)
            if (c0 == 1).any():
                on_boundary[np.unique(u0[c0 == 1])] = True
            cand = np.where(hard & ~on_boundary
                            & (sharp > np.percentile(sharp[hard], 90))
                            if hard.any() else np.zeros(len(v), bool))[0]
            if len(cand) > 0:
                picks = rng.choice(cand, size=min(chip_count, len(cand)), replace=False)
                sites = [(int(p), chip_frac * scale * rng.uniform(0.5, 1.5))
                         for p in picks]
                # Cut the flake away if a boolean engine is available; press a
                # dish in if it is not, or if the cut fails. Never punch a hole.
                cut = (_chip_boolean(v, f, sites, seed=seed)
                       if chip_method in ("boolean", "auto") else None)
                if cut is not None:
                    v, f = cut
                    keep = np.ones(len(f), bool)
                elif chip_method == "boolean":
                    raise RuntimeError("boolean chipping requested but failed")
                else:
                    v = _chip_dish(v, f, sites)

        deleted_any = not bool(keep.all())
        nf = f[keep]
        if len(nf) < 16:                                 # never delete a piece
            out.append((v.copy(), f.copy()))
            continue
        m = trimesh.Trimesh(vertices=v, faces=nf, process=False)
        m.remove_unreferenced_vertices()

        # Round the chip boundaries. Deleting faces leaves a SHARP open edge,
        # and sharp edges are relief -- which is why chipped arms measured
        # rougher than the untouched sherd even after reordering (limb3 0.319 ->
        # 0.619, job 28763465). Reordering let the mollifier round chips that
        # fall inside the contact band; it never reached the rest.
        #
        # A chip that happened in antiquity has had its edge worn round for
        # centuries, so rounding it here is the physics, not a cosmetic fix.
        try:
            mv = np.asarray(m.vertices, dtype=np.float64)
            mf = np.asarray(m.faces, dtype=np.int64)
            e = np.sort(mf[:, [0, 1, 1, 2, 2, 0]].reshape(-1, 2), axis=1)
            uniq, cnt = np.unique(e, axis=0, return_counts=True)
            border = np.unique(uniq[cnt == 1])            # edges used once = a hole rim
            if len(border) > 3:
                ring = set(border.tolist())
                # include one ring of neighbours so the rounding is not a cliff
                for a, b in uniq[cnt == 1]:
                    ring.add(int(a)); ring.add(int(b))
                idx = np.fromiter(ring, dtype=np.int64)
                nb_tree = cKDTree(mv)
                _, nb = nb_tree.query(mv[idx], k=min(12, len(mv)), workers=-1)
                for _ in range(3):                        # a few gentle passes
                    mv[idx] = 0.5 * mv[idx] + 0.5 * mv[nb].mean(axis=1)
                m = trimesh.Trimesh(vertices=mv, faces=mf, process=False)
        except Exception:
            pass
        ov = np.asarray(m.vertices, dtype=np.float64)
        of = np.asarray(m.faces, dtype=np.int64)

        # Close what we opened. The rims of the ORIGINAL mesh are passed in by
        # position so a scanner's pre-existing hole is not quietly repaired and
        # counted as wear.
        # Seal only if faces were actually deleted. The dish and the boolean cut
        # both leave topology sound on their own, so running the sealer over
        # them can only touch openings that were already there -- which is how
        # the scanner's holes got repaired. Nothing of ours to close, so do not
        # go looking.
        if seal_scars and deleted_any:
            ov, of, n_sealed, n_left = _seal_chip_scars(
                ov, of, pre_boundary,
                orig_mesh=trimesh.Trimesh(vertices=v, faces=f, process=False))
        else:
            n_sealed = n_left = 0

        if verbose:
            print(f"      piece {i}: faces {len(f)} -> {len(of)} "
                  f"({100 * (1 - len(of) / len(f)):.1f}% removed), "
                  f"sealed {n_sealed} scar(s), left {n_left} pre-existing",
                  flush=True)
        out.append((ov, of))
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


# ---------------------------------------------------------------------------
# The wear model, as one call
# ---------------------------------------------------------------------------

def apply_wear(pieces, *, smoothing: float = 1.0, smoothing_kernel: float = 0.05,
               smoothing_passes: int = 1,
               recession: float = 0.0015, chip_count: int = 4,
               chip_size: float = 0.003, seed: int = 0):
    """Simulate archaeological wear on an assembled set of fragments.

    Three independent, physically-named effects, applied in the order burial
    causes them. All edit geometry only — assembled poses and the ground-truth
    answer are never touched, so scoring stays valid.

      smoothing  Rounds the fracture relief. NOTE this SATURATES: raising the
                 kernel past ~0.05 buys almost nothing (limb3 relief 0.1707 ->
                 0.1789 -> 0.1820 as kernel goes 0.05 -> 0.12), the same plateau
                 GARF hit in Exp 7/7b. Use `wear_to_target` if you need a
                 specific roughness per object rather than a fixed dose.

      recession  Retreats the mating SURFACE, so fragments no longer meet
                 tightly and gaps open at the joins. This is the effect no
                 earlier training data had — fragments always still mated
                 perfectly, merely with smoother faces — and it changes the
                 assembly problem rather than just its appearance.

      chipping   Removes small chunks at the sharpest, most exposed points of
                 the break, which is where sherds actually chip. Deliberately
                 small and local, not a uniform shrink.

    Args:
        pieces: list of (verts, faces) in the ASSEMBLED pose.
        smoothing: mollification strength, 0 to disable.
        smoothing_kernel: mollification radius as a fraction of piece scale.
        recession: inward retreat of the mating surface, as a fraction of object
            scale. Small — 0.0015 is a realistic default; 0.01 would be extreme.
        chip_count: number of chips per fragment.
        chip_size: chip radius as a fraction of object scale.
        seed: RNG seed for chip placement.

    Returns:
        list of (verts, faces). Topology changes when chipping is enabled.
    """
    cur = [(np.asarray(v, dtype=np.float64), np.asarray(f, dtype=np.int64))
           for v, f in pieces]

    # ORDER MATTERS, and it follows the physical history of the sherd.
    #
    # Chipping comes FIRST. A sherd chips in antiquity and is then abraded for
    # centuries, so its chip boundaries end up rounded like everything else.
    # Chipping last leaves fresh, sharp-edged deletions, and validation job
    # 28749619 showed exactly that: chipped arms came out ROUGHER than the
    # untouched sherd (galli_pot 0.457 -> 0.681, plate 0.332 -> 0.541) because
    # sharp chip boundaries are themselves relief. Chipping first lets the
    # smoothing pass round them, as burial does.
    if chip_count and chip_count > 0 and chip_size > 0:
        masks = [_band_mask(cur, i, cur[i][0]) for i in range(len(cur))]
        cur = recede_and_chip(cur, recession_frac=0.0,
                              chip_count=chip_count, chip_frac=chip_size,
                              seed=seed, masks=masks)

    if smoothing and smoothing > 0:
        # REPEATED passes reach smoother surfaces than one deep pass, and this
        # matters: smoothness is the axis that destroys the interlocking
        # information, so it is the axis training data must span.
        #
        # Single-pass smoothing saturates -- galli_pot stalls at 0.288, plate at
        # 0.234, against the Juglet's 0.171. Raising the KERNEL does not help
        # (0.05 -> 0.12 gave 0.1707, 0.1789, 0.1820: no gain, slightly worse).
        # Repeating at a fixed small kernel does, and is closer to how abrasion
        # actually works -- many cycles, not one deep cut:
        #
        #   galli_pot  0.461 -> 0.276 -> 0.220 -> 0.213 -> 0.226 -> 0.231 -> 0.264
        #   plate      0.341 -> 0.241 -> 0.209 -> 0.214 -> 0.229 -> 0.227 -> 0.233
        #   limb3      0.314 -> 0.171 -> 0.154 -> 0.159 -> 0.166 -> 0.161 -> 0.204
        #
        # Note it REVERSES after pass 2-3: repeated resampling of an already
        # averaged surface starts adding numerical artefacts, the same
        # "more is worse" pattern as the kernel sweep. Hence the cap.
        #
        # Residual limit, worth stating: limb3 gets past the Juglet (0.154) but
        # naturally-rough ceramics do not -- galli_pot bottoms at 0.213 and plate
        # at 0.209. Some objects cannot be simulated as smooth as the real target.
        passes = max(1, min(int(smoothing_passes), 3))
        for _ in range(passes):
            sm = erode_fracture_band(cur, strength=smoothing,
                                     kernel_frac_max=smoothing_kernel)
            cur = [(sm[i], cur[i][1]) for i in range(len(cur))]

    # Recession last: it is the net loss of material from the mating face, and
    # must not be undone by a later smoothing pass. Its mask is recomputed
    # because chipping changed the vertex arrays.
    if recession and recession > 0:
        cur = recede_surface(cur, recession_frac=recession)

    return cur


# ---------------------------------------------------------------------------
# Dataset wear conditions
# ---------------------------------------------------------------------------

# Surface abrasion and material loss are INDEPENDENT axes, and a dataset should
# sample them independently. The first validation set failed to: all three of its
# "levels" used identical smoothing and varied only material loss, so they were
# material-loss levels wearing a wear-level label. That is also why measured
# roughness came out non-monotonic — chipping ADDS roughness (ragged edges) while
# smoothing removes it, so at heavy settings the added roughness won and `limb3`
# ended up rougher (0.380) than the untouched sherd (0.315).
#
# Real assemblages contain both kinds independently: sherds abraded smooth but
# intact, and sherds with crisp breaks that have chipped. Training data should
# too, or the model cannot learn which cue to trust.
#
# `smoothing` is a DOSE, not an outcome — the same dose wears different pots by
# very different amounts (blue_pot reached relief 0.110 where limb3 reached only
# 0.171). Use `wear_to_target` when a specific roughness is required across a set.
#
# Chip size is deliberately restrained. Full-set validation (job 28742114) showed
# that chipping at 0.0040 with 6 chips OVERWHELMS the smoothing it is combined
# with: galli_pot's relief went 0.471 -> 0.726 and plate's 0.339 -> 0.606, i.e.
# "heavy wear" produced ROUGHER break faces than the untouched sherd. Ragged chip
# boundaries are themselves relief. Chips must stay small enough to read as
# missing material rather than as added texture.
WEAR_CONDITIONS = [
    # name             smoothing  recession  chips  chip size
    ("fresh",          dict(smoothing=0.0, recession=0.0,    chip_count=0, chip_size=0.0)),
    ("abraded_light",  dict(smoothing=0.5, recession=0.0,    chip_count=0, chip_size=0.0)),
    ("abraded_heavy",  dict(smoothing=1.0, recession=0.0,    chip_count=0, chip_size=0.0)),
    ("loss_dominant",  dict(smoothing=0.3, recession=0.0015, chip_count=4, chip_size=0.0030)),
    ("worn_moderate",  dict(smoothing=0.7, recession=0.0010, chip_count=3, chip_size=0.0025)),
    ("worn_heavy",     dict(smoothing=1.0, recession=0.0025, chip_count=4, chip_size=0.0022)),
]


# HOW OFTEN EACH CONDITION SHOULD APPEAR IN A DATASET
#
# Conservator's calibration after inspecting exported sherds (2026-08-05):
# "in real archaeological sense, most wear falls between light and moderate."
#
# This matters more than it sounds. A dataset that over-represents severe wear
# teaches the model to expect damage that is rare, at the cost of accuracy on the
# material actually excavated. Sampling should follow the archaeological
# distribution, not sweep the parameter range uniformly.
#
# Weights are relative, for sampling when a dataset is built. `fresh` is retained
# because assemblages contain recent breaks and protected sherds; the heavy tail
# is retained but rare, because it exists and the model should not be surprised
# by it.
#
# Note the Juglet sits BEYOND this range (relief 0.171 against ~0.22-0.31 for
# untouched real pots here). If most archaeological wear really is light-moderate,
# the Juglet is an unusually hard case rather than a typical one — which would
# mean a tool trained on this distribution could serve most material well while
# still struggling with that particular pot.
WEAR_SAMPLING_WEIGHTS = {
    "fresh":          1.0,
    "abraded_light":  3.0,
    "abraded_heavy":  1.0,
    "loss_dominant":  2.0,
    "worn_moderate":  3.0,
    "worn_heavy":     1.0,
}


def sample_wear_condition(rng):
    """Draw a wear condition following the archaeological distribution.

    Use this when building a dataset, rather than iterating WEAR_CONDITIONS
    uniformly — see WEAR_SAMPLING_WEIGHTS for why.
    """
    conds = wear_conditions()
    w = np.array([WEAR_SAMPLING_WEIGHTS.get(n, 1.0) for n, _ in conds], dtype=float)
    w /= w.sum()
    i = int(rng.choice(len(conds), p=w))
    return conds[i]


def wear_conditions(names=None):
    """The canonical wear conditions for building a dataset.

    Returns [(name, kwargs)] suitable for `apply_wear`. Covers both axes
    separately (`abraded_*` = smoothing only, `loss_only` = material loss only)
    and together (`worn_*`), plus an untouched control.
    """
    if names is None:
        return list(WEAR_CONDITIONS)
    want = {n.strip() for n in names.split(",")} if isinstance(names, str) else set(names)
    return [(n, kw) for n, kw in WEAR_CONDITIONS if n in want]


# ---------------------------------------------------------------------------
# Wear as loss: one phenomenon at three scales
# ---------------------------------------------------------------------------
#
# Conservator's framing, adopted 2026-08-01 and better than the two-axis model
# it replaces: WEAR IS MATERIAL LOSS. Smoothing is not a separate effect — it is
# loss of the sharp edges. What differs between the three operations here is the
# SCALE of what goes:
#
#   micro   asperities on the break face      -> reads as smoothing
#   meso    the mating surface as a whole     -> reads as a receding edge
#   macro   chunks at exposed points          -> reads as chipping
#
# This retro-explains a result I had wrongly called a bad test. Validation job
# 28749619 flagged "abrasion opened the join without material loss" on nine arms,
# and I dismissed the check as encoding a wrong assumption. Under this framing it
# is not surprising at all: smoothing IS loss, so of course the pieces stop
# meeting. Only the two-axis model made it look anomalous.
#
# Practical consequence: when asperity-scale loss saturates — as it does on
# naturally-rough pots (galli_pot stalls at relief 0.288, plate at 0.234, against
# a 0.15 target) — wear does not stop. It continues at the next scale up. That is
# what `wear_to_loss` does.


def wear_to_loss(pieces, target_gap_ratio: float = 1.30, *,
                 smoothing: float = 1.0, smoothing_kernel: float = 0.05,
                 chip_count: int = 4, chip_size: float = 0.0022,
                 lo: float = 0.0, hi: float = 0.010, iters: int = 5,
                 seed: int = 0, verbose: bool = False):
    """Wear an object until its joins have opened by `target_gap_ratio`.

    Wear is expressed as LOSS, measured where it matters for reassembly: how far
    the fragments have stopped meeting. Smoothing and chipping are applied first
    (asperity- and chunk-scale loss), then surface recession is searched to reach
    the target — so an object whose surface will not smooth any further still
    reaches the intended degree of wear, via loss at a larger scale.

    Returns (pieces, achieved_gap_ratio).
    """
    from scipy.spatial import cKDTree as _KD

    def gap(ps, max_pts=40000):
        rng = np.random.default_rng(0)
        subs = [v if len(v) <= max_pts else v[rng.choice(len(v), max_pts, replace=False)]
                for v, _ in ps]
        trees = [_KD(s) for s in subs]
        out = []
        for i, s in enumerate(subs):
            best = np.full(len(s), np.inf)
            for j, t in enumerate(trees):
                if i != j:
                    d, _ = t.query(s, workers=-1)
                    best = np.minimum(best, d)
            out.append(float(np.percentile(best, 10)))
        return float(np.mean(out))

    g0 = gap(pieces)
    base = apply_wear(pieces, smoothing=smoothing, smoothing_kernel=smoothing_kernel,
                      recession=0.0, chip_count=chip_count, chip_size=chip_size,
                      seed=seed)
    best, best_r = base, gap(base) / max(g0, 1e-12)
    if verbose:
        print(f"      after micro+macro loss: gap x{best_r:.2f}", flush=True)
    if best_r >= target_gap_ratio:
        return best, best_r

    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        cand = recede_surface(base, recession_frac=max(mid, 1e-9))
        r = gap(cand) / max(g0, 1e-12)
        if verbose:
            print(f"      recession {mid:.5f} -> gap x{r:.2f}", flush=True)
        if abs(r - target_gap_ratio) < abs(best_r - target_gap_ratio):
            best, best_r = cand, r
        if r < target_gap_ratio:
            lo = mid
        else:
            hi = mid
    return best, best_r
