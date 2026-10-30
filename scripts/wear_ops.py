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
from sherd_worn.wear import (  # noqa: E402
    _band_mask,
    _smoothed_normals,
    _local_mean,
    _proud_height,
    _outward_directions,
    _wall_estimate,
    blunt_asperities,
    wear_context,
    recede_surface,
    _chip_dish,
    _chip_boolean,
    _boundary_loops,
    _seal_chip_scars,
    _seal_once,
    recede_and_chip,
    band_limit,
    apply_wear,
)


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
