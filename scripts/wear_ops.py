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

WEAR IS ALSO SCALE-SELECTIVE, and this is the correction of 2026-08-10. A break
face carries two different things at two different scales: the TEETH that
interlock on a fresh break (sub-millimetre) and the CURVE of the face itself
(centimetre). Wear blunts the teeth and leaves the curve — which is why a worn
sherd can still be reassembled by hand, and why the curve, not the teeth, is
what a model should be taught to read on real material.

Measured on blue_pot before and after (same mesh, so no density confound), the
mollification this replaced did the opposite at BOTH ends: it ADDED fine
structure (0.073 -> 0.090) and REMOVED 14% of the curve (1.723 -> 1.483). Its
kernel sits at 5% of the object, above the curve scale, so it was low-passing
the feature that had to survive. `blunt_asperities` is the replacement and
`apply_wear(mode=...)` selects between them.

The acceptance test for any future change is the same measurement, on one
object: fine-scale structure must FALL with wear level while coarse-scale
structure holds, and the joins must open. `validate_wear_spectrum.py`.

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
from itertools import chain
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


def _local_mean(pts, query, radius, max_ref: int = 60000, seed: int = 0):
    """The surface as it would be if everything finer than `radius` were gone.

    Averaging the neighbours within a radius is a low-pass filter whose cutoff
    IS that radius: structure smaller than it averages away, structure larger
    survives untouched. That is the whole basis of scale-selective wear, and it
    is why the cutoff is an explicit parameter rather than a tuning constant.

    The reference set is subsampled -- an envelope is a smooth surface, and 60k
    points describe it as well as 500k. The per-point mean is accumulated with
    `reduceat` rather than a Python loop: on a 24k-vertex toy the loop version
    did not finish in two minutes, and the real meshes are twenty times larger.
    """
    rng = np.random.default_rng(seed)
    ref = pts
    if len(ref) > max_ref:
        ref = ref[rng.choice(len(ref), max_ref, replace=False)]

    # Thin the reference until a ball holds about `per_ball` points. Without
    # this the cost is set by the mesh's sampling density rather than by the
    # cutoff: at a 4% radius on a densely scanned pot each ball holds ~800
    # points, so a 100k-vertex band would materialise 80M indices. A uniform
    # subsample leaves the mean unbiased -- an envelope needs coverage, not
    # every point.
    per_ball = 80
    tree = cKDTree(ref)
    probe = ref[rng.choice(len(ref), min(200, len(ref)), replace=False)]
    occ = float(np.mean([len(x) for x in
                         tree.query_ball_point(probe, radius, workers=-1)]))
    if occ > per_ball * 1.5 and len(ref) > 2000:
        keep = max(2000, int(len(ref) * per_ball / max(occ, 1.0)))
        ref = ref[rng.choice(len(ref), keep, replace=False)]
        tree = cKDTree(ref)

    nb = tree.query_ball_point(query, radius, workers=-1, return_sorted=False)

    lens = np.fromiter((len(x) for x in nb), dtype=np.int64, count=len(nb))
    out = query.copy()
    ok = np.where(lens >= 4)[0]
    if not len(ok):
        return out
    lo = lens[ok]
    flat = np.fromiter(chain.from_iterable(nb[i] for i in ok),
                       dtype=np.int64, count=int(lo.sum()))
    starts = np.zeros(len(lo), dtype=np.int64)
    np.cumsum(lo[:-1], out=starts[1:])
    out[ok] = np.add.reduceat(ref[flat], starts, axis=0) / lo[:, None]
    return out


def _outward_directions(v, idx, obj_scale, k_fit: int = 24,
                        smooth_k: int = 16):
    """Which way is OUT of the sherd, decided by where the material is.

    Every previous wear operation took this from the mesh winding, and the
    winding is exactly what cannot be trusted on these scans -- 7-15% of band
    normals are wound inward, and each time, wear ran backwards there.

    The replacement asks a question winding cannot corrupt: material lies on the
    INSIDE. Fit a plane to the local neighbourhood, which fixes the normal up to
    sign, then count the piece's own surface points on each side within a radius
    of the wall thickness. The side carrying less of the sherd is outside.
    Works on a thin wall (the far wall sits inward) and on a solid (the bulk
    sits inward) without being told which it is dealing with.

    This also replaces the direction taken from the nearest point on the
    NEIGHBOURING fragment, which turned out to be unusable for the case it was
    written for. Two mating break faces are the same surface, so the nearest
    point on the other fragment is the vertex itself: the difference vector is
    zero, or tangential noise, and after smoothing it cancels. On a synthetic
    pair with an exactly shared interface it produced no displacement at all.
    """
    q = v[idx]
    tree = cKDTree(v)

    # local plane fit -> normal up to sign
    _, nb = tree.query(q, k=min(k_fit, len(v)), workers=-1)
    P = v[nb] - q[:, None, :]
    C = np.einsum("nki,nkj->nij", P, P)
    n = np.linalg.eigh(C)[1][:, :, 0]              # smallest-variance direction

    # Which side holds the material? The centre of mass of the piece's own
    # surface near the vertex lies INWARD, so the normal pointing away from it
    # is outward.
    #
    # AT WHICH RADIUS, though. This is the whole difficulty, and it is the
    # conservator's thickness spectrum again: on an eggshell sherd the far wall
    # is a fraction of a percent away, on a solid bone there is no wall at all
    # and the nearest material asymmetry is the bulk of the piece, tens of
    # percent away. Two fixed radii were tried and each failed on the case the
    # other handled -- too small and the neighbourhood is just the break face,
    # symmetric, so the sign falls out of rounding noise (41% of vertices sent
    # the wrong way on the synthetic pair); too large and a genuinely thin wall
    # is swamped by the sherd's overall curvature.
    #
    # So the radius is not chosen in advance. The test runs at a ladder of
    # radii and each vertex takes its answer from the radius where the material
    # is most decisively one-sided, measured as offset relative to the radius
    # itself so the scales are comparable. Nothing needs to know whether it is
    # looking at a wall or a solid.
    best = np.zeros(len(q))
    sign = np.ones(len(q))
    for rf in (0.01, 0.02, 0.04, 0.08, 0.16, 0.32):
        proj = np.einsum("ni,ni->n", _local_mean(v, q, rf * obj_scale) - q, n)
        conf = np.abs(proj) / (rf * obj_scale)
        take = conf > best
        best[take] = conf[take]
        sign[take] = -np.sign(proj[take])          # away from the material
    n *= np.where(sign == 0, 1.0, sign)[:, None]

    # smooth the field, aligning signs first so opposing normals do not cancel
    if len(idx) > smooth_k:
        _, nn = cKDTree(q).query(q, k=min(smooth_k, len(q)), workers=-1)
        ref = n[nn]
        ref *= np.sign(np.einsum("nki,ni->nk", ref, n))[:, :, None]
        n = ref.mean(axis=1)
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    return n / np.maximum(ln, 1e-12)


def _wall_estimate(v, f, idx, sample: int = 4000, ref_pts: int = 20000,
                   seed: int = 0):
    """How thick the sherd is at the break, from the surface facing back at it.

    Returns 0 when there is no facing-back surface within reach, which is the
    honest answer for a solid: a bone has no wall, and the conservator's point
    about the thickness spectrum is that an estimator must be allowed to say so
    rather than return the nearest number it can find.

    The reference set is thinned to a KNOWN density first. Querying the k
    nearest vertices of a full scan cannot reach the far wall -- they all sit on
    the near surface -- which is exactly how the estimator this replaces ended
    up reporting mesh spacing as though it were thickness.
    """
    rng = np.random.default_rng(seed)
    sel = idx if len(idx) <= sample else rng.choice(idx, sample, replace=False)
    try:
        m = trimesh.Trimesh(vertices=v, faces=f, process=False)
        vn = np.asarray(m.vertex_normals, dtype=np.float64)
    except Exception:
        return 0.0
    ref_i = (np.arange(len(v)) if len(v) <= ref_pts
             else rng.choice(len(v), ref_pts, replace=False))
    d, nb = cKDTree(v[ref_i]).query(v[sel], k=min(64, len(ref_i)), workers=-1)
    facing = (vn[ref_i][nb] * vn[sel][:, None, :]).sum(axis=-1) < -0.5
    d = np.where(facing, d, np.inf)
    thick = d.min(axis=1)
    thick = thick[np.isfinite(thick)]
    return float(np.median(thick)) if len(thick) >= 20 else 0.0


def blunt_asperities(pieces, cut_frac: float = 0.004, strength: float = 1.0,
                     passes: int = 2, exposure: float = 0.5, masks=None,
                     seed: int = 0):
    """Blunt the TEETH and leave the CURVE — wear as one-sided peak truncation.

    Replaces mollification as the micro-scale term, for three faults the scale
    spectrum exposed on 2026-08-10 (blue_pot, same mesh before and after, so the
    comparison is free of the mesh-density confound that invalidated the
    cross-object one):

      1. IT MOVED MATERIAL BOTH WAYS. Averaging a vertex toward its neighbours
         pushes roughly half of them OUTWARD, into the space the neighbouring
         sherd occupies. Abrasion cannot add material. Truncation only removes,
         so joins open monotonically and the inward-normal class of bug cannot
         recur.

      2. IT ATE THE CURVE. At the heavy setting coarse-scale structure fell
         1.723 -> 1.483, a 14% loss of exactly the feature that must survive.
         The mollifier's kernel is 5% of the object, which is ABOVE the curve
         scale; it was low-passing the thing it was supposed to preserve.

      3. IT FILLED VALLEYS AS READILY AS IT CUT PEAKS. An abrasive contacts the
         high points first: real wear truncates asperity tips and leaves the
         troughs. Symmetric averaging produces a surface that is smooth by
         statistic and wrong by shape.

    Conservator's framing, which this implements literally (2026-08-10): "it
    blunts the teeth and preserves the curve".

    Method. Each band vertex is compared with the local envelope at the cutoff
    radius -- the surface with everything finer than the cutoff removed. The
    part of the vertex standing PROUD of that envelope, measured along the
    direction away from the neighbouring fragment, is the asperity; a fraction
    of it is removed. Material below the envelope is never touched, so nothing
    moves toward the neighbour and no valley is filled.

    Structure coarser than the cutoff lives in the envelope itself and is
    invisible to the operation, which is what makes the curve safe by
    construction rather than by choosing a gentle dose.

    Wear is also UNEVEN, and the unevenness carries information: exposed
    protrusions abrade faster than sheltered hollows, which is why chips form at
    the pointy ends. The rate is scaled by how far the neighbourhood stands
    proud at a coarser scale, so a worn face ends up blunter where it was
    exposed -- a texture no uniform operation can produce.

    Args:
        cut_frac: cutoff radius as a fraction of object size, and the knob that
            sets SEVERITY -- heavier wear blunts larger asperities. It must stay
            well below the curve, and "well below" is quantitative here: a
            disc-mean envelope rolls off slowly, so a cutoff at 1% still passes
            41% of a 3.2% feature into the residual and would truncate it. At
            0.4% that falls to 5%. Hence the default: the cutoff sits at the
            finest scale the spectrum probes, and the curve is untouched.
        strength: fraction of the sub-cutoff relief removed, 0-1. At 1.0 the
            face lands exactly on its own envelope.
        passes: refinement iterations. The budget is fixed from the untouched
            surface, so extra passes converge on that target rather than cutting
            deeper -- unlike repeated mollification, which reversed after pass
            2-3 and started adding artefacts.
        exposure: how strongly the rate follows local exposure. 0 = uniform.
    """
    allv = np.concatenate([v for v, _ in pieces], axis=0)
    scale = float(np.linalg.norm(allv.max(0) - allv.min(0))) + 1e-9
    R = cut_frac * scale
    out = []

    for i, (v, f) in enumerate(pieces):
        hard, feather = masks[i] if masks is not None else _band_mask(pieces, i, v)
        band = feather > 0.02
        if not band.any() or strength <= 0 or passes < 1:
            out.append((v.copy(), f.copy()))
            continue

        v = v.copy()
        idx = np.where(band)[0]
        away = _outward_directions(v, idx, scale)

        # How exposed each vertex is, measured once on the untouched shape: how
        # far its neighbourhood stands proud of a coarser envelope. Positive on
        # a bump, negative in a hollow.
        expo = np.ones(len(idx))
        if exposure > 0:
            coarse = _local_mean(v[idx], v[idx], 4.0 * R, seed=seed)
            hm = ((v[idx] - coarse) * away).sum(axis=1)
            s = float(np.std(hm)) + 1e-12
            expo = np.clip(1.0 + exposure * (hm / s), 0.3, 1.8)

        # A BUDGET, fixed from the untouched surface: no vertex may be cut below
        # the envelope it started above. Without it the operation runs away --
        # each pass recomputes the envelope on an already-lowered surface, so
        # the envelope descends and there is always more to cut. Measured on the
        # synthetic pair, three passes at full strength drove the teeth to
        # amplitude x-0.17: the peaks had been cut so deep they became troughs.
        # Wear blunts an asperity; it does not carve a mirror image of it.
        #
        # It also puts severity on the right knob. More wear means blunting
        # reaches LARGER asperities -- raise `cut_frac` -- not that the same
        # small ones get cut deeper. That is the module's own framing of wear as
        # loss moving up the scales, applied to the micro term.
        # The FRACTION removed is capped at 1, not just the passes. Exposure
        # reaches 1.8, so an exposed peak was being given a budget of 1.8x its
        # own height above the envelope -- and spent it. Measured on real
        # scans: peaks ended at -49.5% of their starting height, i.e. cut clean
        # through the envelope and left as pits, while hollows sat untouched at
        # 100%. One-sidedness was working perfectly and the magnitude was not.
        # Pits are fresh fine-scale relief, which is why the teeth were still
        # creeping UP at the finest scale on an abrasion-only run.
        env0 = _local_mean(v[idx], v[idx], R, seed=seed)
        frac = np.clip(strength * feather[idx] * expo, 0.0, 1.0)
        budget = frac * np.maximum(((v[idx] - env0) * away).sum(axis=1), 0.0)
        removed = np.zeros(len(idx))
        for _ in range(max(1, int(passes))):
            env = _local_mean(v[idx], v[idx], R, seed=seed)
            h = ((v[idx] - env) * away).sum(axis=1)
            step = np.clip(np.maximum(h, 0.0), 0.0, budget - removed)
            if not np.any(step > 0):
                break
            v[idx] -= away * step[:, None]
            removed += step
        out.append((v, f.copy()))
    return out


def band_limit(pieces, spacing_frac: float = 0.005):
    """Blur away detail no real scan resolves. This models the SCANNER, not wear.

    Conservator's flag, 2026-08-10: fine fracture detail on a scanned real object
    is unreliable, so an assembly cannot honestly rest on it. That cuts both
    ways. Our simulated FRESH breaks carry crisp teeth at a scale no scan of a
    real sherd ever delivers, so a model trained on them learns to read detail
    that will not be there at inference -- a domain gap pointing the wrong way,
    and one no amount of wear simulation fixes because it is present before any
    wear is applied.

    Deliberately TWO-SIDED, unlike `blunt_asperities`. Wear removes material;
    a measurement limit does not. It blurs symmetrically, because that is what
    finite resolution does.

    Default spacing is the Juglet's own mesh spacing (0.535% of object size),
    the one measured figure available for real scanned material here.
    """
    allv = np.concatenate([v for v, _ in pieces], axis=0)
    scale = float(np.linalg.norm(allv.max(0) - allv.min(0))) + 1e-9
    R = spacing_frac * scale
    out = []
    for v, f in pieces:
        out.append((_local_mean(v, v.copy(), R), f.copy()))
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
        # Retreat direction, revised 2026-08-10. It used to be "away from the
        # nearest point on another fragment", which was itself a fix for mesh
        # normals being wound inward on 7-15% of the band. That fix has a hole
        # in it: two mating break faces are the SAME surface, so on closely
        # sampled fragments the nearest point on the neighbour is the vertex
        # itself. The difference vector is then zero or tangential noise, and
        # smoothing cancels what is left. On a synthetic pair with an exactly
        # shared interface it produced no displacement at all -- recession would
        # have been silently doing nothing.
        #
        # `_outward_directions` asks where the sherd's own material is instead,
        # which needs neither the winding nor the neighbour.
        idx = np.where(band)[0]
        away = _outward_directions(v, idx, scale, smooth_k=normal_k)

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
        # ONE cap for the whole piece, from a real wall estimate.
        #
        # It used to be 0.35 x the distance to the 48th nearest vertex, per
        # vertex, and that is a sampling-density figure wearing a geometry
        # label: on blue_pot the 48th neighbour sits 0.32% of the object away,
        # so the cap came out at 0.11% and BOUND every displacement -- the
        # requested recession never applied, and what did apply varied from
        # vertex to vertex with the local mesh density.
        #
        # A displacement that varies across a surface IS relief. That is the
        # whole mechanism, and it is measured: recession alone added 18% at the
        # teeth scales and took 10% off the curve, on a term whose only job is
        # to retreat the face by a thin uniform layer. A constant offset along
        # a smooth normal field adds no structure at any scale, which is what
        # this restores.
        #
        # Same error class as the other three found today: an estimator reading
        # how finely the mesh was sampled rather than how thick the sherd is.
        wall = _wall_estimate(v, f, idx)
        cap = np.full(len(idx), 0.6 * wall if wall > 0 else np.inf)

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

        # MINUS. `_outward_directions` points away from the sherd's own
        # material, i.e. out of the solid and therefore TOWARD the neighbouring
        # fragment. Recession is material lost from the break face, so the face
        # must retreat INTO the sherd, against that direction.
        #
        # The old direction vector pointed the other way -- away from the
        # neighbour, hence into the sherd -- so swapping the direction field
        # silently inverted this term. It reintroduced, in the same function,
        # the exact defect that was found by rendering the join in 2026-08:
        # recession pushing surfaces toward their neighbour.
        #
        # Caught by isolating the terms rather than by inspection. Blunting
        # alone opened blue_pot's joins 0.891% -> 0.905%; adding recession took
        # that straight back to 0.891%, i.e. the term whose entire purpose is to
        # open joins was closing them, and it raised coarse structure 10.2% by
        # bulging the face outward as it went.
        amount = np.minimum((recession_frac * scale) * mag, cap)
        disp = np.zeros_like(v)
        disp[idx] = -away * amount[:, None]
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

        # Never dish deeper than the sherd is thick. At the larger chip sizes
        # the plate dropped to 5 of 6 sherds sealed -- the chip had gone clean
        # through. A chip removes a flake from a surface; it does not perforate
        # a pot. Local thickness comes from the nearest surface facing the other
        # way, the same estimator that gave coherent walls in the survey.
        depth = depth_ratio * r
        opp = np.where(vn[idx] @ vn[centre_idx] < -0.5)[0]
        if len(opp):
            wall = float(np.min(np.linalg.norm(v[idx][opp] - v[centre_idx], axis=1)))
            depth = min(depth, 0.6 * wall)

        dist = np.linalg.norm(v[idx] - v[centre_idx], axis=1)
        w = np.clip(1.0 - (dist / r) ** 2, 0.0, 1.0) ** 2   # 1 at centre, 0 at rim
        v[idx] += into * depth * w[:, None]
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
                    chip_method: str = "dish"):
    # DISH BY DEFAULT since 2026-08-12, for two independent reasons.
    #
    # GARF trains on `shared_faces` labels, which name the faces of the
    # original mesh. A boolean subtraction rebuilds the mesh, so those labels
    # no longer refer to anything and the fine-tune would be training on
    # mislabelled geometry. That alone settles it for the GARF work.
    #
    # It also makes wear MEASURABLE. Boolean chipping changes the vertex set,
    # so before and after cannot be compared vertex for vertex, and the
    # validation falls back to picking break-face points by distance -- which
    # re-derives them from the worn geometry and shrinks the measured window as
    # the dose rises. That is what made chipped runs report joins CLOSING on
    # coxae and vert9 while the same settings opened them on every run where
    # topology was preserved.
    #
    # Boolean remains reachable and is still the more faithful account of what
    # a flake detaching does. It is not the default because a chip we cannot
    # measure and cannot label is worth less than one we can.
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
               recession: float = 0.0, chip_count: int = 4,
               chip_size: float = 0.003, seed: int = 0,
               mode: str = "blunt", blunt_cut: float = 0.004,
               scan_spacing: float = 0.0):
    """Simulate archaeological wear on an assembled set of fragments.

    MODE, added 2026-08-10, and the default CHANGED with it:

      "blunt"   the micro term is one-sided peak truncation at a cutoff between
                the teeth and the curve (`blunt_asperities`). This is the model
                that matches what wear physically does.
      "legacy"  the micro term is symmetric mollification. Kept so results built
                before this date can be reproduced. It moves material both ways
                and removes 14% of the curve at the heavy setting; do not use it
                for new datasets.

    Datasets built either side of this change are NOT comparable, and anything
    trained on "legacy" data was trained on break faces whose coarse shape had
    been partly filtered away.

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

    if smoothing and smoothing > 0 and mode == "blunt":
        # Blunt the teeth, leave the curve. `smoothing` is reused as the dose so
        # every existing call site keeps working, but it now means "fraction of
        # each asperity removed per pass" rather than a mollification strength.
        cur = blunt_asperities(cur, cut_frac=blunt_cut, strength=smoothing,
                               passes=max(1, int(smoothing_passes)), seed=seed)

    elif smoothing and smoothing > 0:
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

    # The scanner comes last, because it is not part of the object's history --
    # it is how the object was measured. Off by default: turning it on changes
    # the fresh control too, which is the point, but it must be a deliberate
    # choice rather than something that quietly appears in one dataset.
    if scan_spacing and scan_spacing > 0:
        cur = band_limit(cur, spacing_frac=scan_spacing)

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
# RECESSION IS RETIRED, 2026-08-12, on a measured dose response rather than a
# judgement. It is kept in the code and reachable, but no canonical condition
# uses it.
#
# Recession alone, curve at the 6.4% scale, against the join opening it buys:
#
#     dose     blue_pot curve   plate curve   join opening
#     0.02%        -1.0%           -2.0%          +1.1%
#     0.05%        -2.5%           -5.3%          +2.9%
#     0.10%        -5.3%          -11.6%          +5.8%
#     0.20%       -11.7%          -26.3%         +12.4%
#
# The cost is linear in the dose, so a setting below tolerance does exist. It
# is not worth having: BLUNTING ALONE opens the joins by more than any safe
# recession dose -- blue_pot +4.4%, plate +6.4%, against +1.1% and +1.5% at the
# largest recession that keeps the curve within 4% -- and it does so while
# leaving the curve intact and blunting the teeth, which recession does not.
# Recession also ADDS fine relief (+11% at 0.4% on blue_pot), the opposite of
# what abrasion does.
#
# Severity therefore rides entirely on the blunting CUTOFF, which is this
# module's own framing of wear as loss moving up the scales. That is a smaller
# model than before and a better-evidenced one. What it gives up: recession was
# the only term that could open a join by a large amount, so if real worn
# sherds turn out to sit much looser than blunting produces, this needs
# revisiting with a term that retreats the face WITHOUT tapering across it --
# the taper is the suspected mechanism, since it lays a ramp across the contact
# band at exactly the scale the curve is measured at.
WEAR_CONDITIONS = [
    # name             smoothing  cutoff   chips  chip size
    ("fresh",          dict(smoothing=0.0, recession=0.0, blunt_cut=0.003,
                            chip_count=0, chip_size=0.0)),
    ("abraded_light",  dict(smoothing=0.5, recession=0.0, blunt_cut=0.003,
                            chip_count=0, chip_size=0.0)),
    ("abraded_heavy",  dict(smoothing=1.0, recession=0.0, blunt_cut=0.005,
                            chip_count=0, chip_size=0.0)),
    ("loss_dominant",  dict(smoothing=0.5, recession=0.0, blunt_cut=0.003,
                            chip_count=4, chip_size=0.0030)),
    ("worn_moderate",  dict(smoothing=0.8, recession=0.0, blunt_cut=0.004,
                            chip_count=3, chip_size=0.0025)),
    ("worn_heavy",     dict(smoothing=1.0, recession=0.0, blunt_cut=0.005,
                            chip_count=4, chip_size=0.0022)),
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


# HOW BIG A CHIP SHOULD BE
#
# Conservator's calibration after inspecting the chip-size series (2026-08-07):
# "current-double is fine, very large is very rare, but large can happen."
#
# So chips ARE a minor effect on real sherds, which settles a question the
# numbers had raised but could not answer: at the default setting a chip removes
# 0.254% of a sherd against 0.252% for no chips at all, i.e. nothing. That looked
# like a bug. It is not — it is what ordinary chipping does. Material loss on a
# worn sherd comes from abrasion and edge recession; chips are a garnish.
#
# The tail is real though, and a dataset that never shows a large chip would
# leave the model surprised by one. Weights follow the verdict directly: common
# through "double", occasional at "large", rare at "very large".
#
# Sizes are radii as a fraction of object size. Measured loss on blue_pot, whole
# object: 0.254% at current, 0.260% double, 0.562% large, 1.105% very large,
# against 0.252% with no chips.
CHIP_LEVELS = [
    # name          count  size     weight
    ("current",     3,     0.0022,  3.0),
    ("double",      3,     0.0045,  3.0),
    ("quadruple",   4,     0.0090,  2.0),
    ("large",       5,     0.0180,  1.0),
    ("very_large",  6,     0.0300,  0.25),
]


def sample_chip_level(rng):
    """Draw a chip size following the conservator's distribution.

    Returns (name, dict) ready to merge into an apply_wear call. Use when
    building a dataset; iterating CHIP_LEVELS uniformly would make large chips
    five times more common than they are.
    """
    w = np.array([c[3] for c in CHIP_LEVELS], dtype=float)
    w /= w.sum()
    i = int(rng.choice(len(CHIP_LEVELS), p=w))
    name, count, size, _ = CHIP_LEVELS[i]
    return name, dict(chip_count=count, chip_size=size)


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
