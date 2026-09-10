"""Does our simulated wear produce the surface REAL eroded fracture has? (O7)

Gate A measured real eroded archaeological fracture on 20 RePAIR fresco
fragments and got a number: with each fragment's own curvature removed by a
fitted quadric, texture rises as R^1.71 from 0.4 to 6.4 mm. A real FRACTURE
surface is self-affine with a roughness exponent of 0.4-0.8 across metals,
ceramics and rocks; R^1.7 is what a smooth surface with mild residual shape
gives. So there is a dimensionless fingerprint separating fresh fracture from
worn archaeological fracture, and it had low scatter -- one straight log-log
line, consistent across all 20 fragments.

WHY THIS IS ANSWERABLE WHEN THE PAIRED COMPARISON IS NOT. `intent/O7` strikes
both captures: you cannot get a pot's break face as it was BEFORE burial, so
"is the wear on this face simulated correctly" is dead. This asks an ENDPOINT
question instead. Do the surfaces our operator produces land where real worn
archaeological surfaces land, and away from where fresh fracture lands? No
before-state, no pairing, no second pot.

  CAN establish: whether simulated wear moves a real ceramic break face's
       roughness-scaling exponent off the fresh-fracture value and toward the
       value real eroded archaeological fracture actually shows.

  CANNOT establish: that the wear on any particular sherd is right. And it
       inherits Gate A's own limit -- whether the ground removed the texture
       from the frescoes or photogrammetry never recorded it is not separable.
       So the claim this supports is "our simulated wear matches real SCANNED
       worn fracture", which is the honest target for training data anyway,
       because the file is what a model sees.

============================================================================
VERSION 2, after job 30352180 measured the wall instead of the break
============================================================================

Version 1 selected the break face as everything within 2% of object size of
another sherd, and read Gate A's radii unchanged. It returned exponents of
1.06-1.81 on FRESH ceramic, median 1.35, where real fracture is 0.4-0.8 -- with
`galli_pot` at 1.69 and `plate` at 1.81 already at or above RePAIR's WORN value
before any wear was applied. `scripts/diagnose_wear_spectrum_band.py` found the
cause, and it was the ruler, not the model:

  - **A pot wall is 4.5 mm.** Gate A's largest patch is 12.8 mm across, so on
    these sherds it is 2.9x the wall it is supposed to sit inside. On a RePAIR
    plaque, 23.5 mm thick, the same patch is 0.55x the wall and fits.
  - **At R = 6.40 mm, 64% of every patch had wrapped onto another surface** and
    100% of patches were contaminated. The residual there was 1.1 mm -- a
    quarter of the wall thickness. That is the vessel's shape and the sharp
    edge where break meets wall, not the texture of the break.
  - **The exponent moved with the selection**, 0.76 to 1.28 as the band was
    narrowed, which a measurement of the break face would not do.

Rendered per point and unbinned in `residual_<tag>.png`: at 6.40 mm the
residual is not spread over a face, it runs in a line along the arris.

Three things change here, and each is a correction with a reason:

  1. **The break face is found by MATING DIRECTION, not by distance alone.**
     Two break faces pressed together point AT each other. So a vertex is on the
     break if it is near another sherd *and* its own normal points toward that
     sherd (dot with the direction to the mean of its 8 nearest other-sherd
     points above MATING_DOT). A vertex on the outer or inner wall beside the
     join is equally near, but its normal points across that direction, not
     along it. This is the same cue `measure_faces_as_network_sees.py` already
     uses to separate a true mating pair from wall continuing across a join,
     and it assumes nothing about the sherd's shape -- unlike Gate A's global
     slab-plane fit, which is undefined on a curved sherd.

  2. **Radii a 4.5 mm wall can actually hold: 0.40 to 1.60 mm.** The floor is
     Gate A's own rule that the finest readable scale is about three times the
     point spacing, and our break-face spacing is 0.13-0.36 mm. The ceiling is
     the wall. **This does not cost the reference**: RePAIR's log-log line is
     straight, so refitting its published texture over 0.4-1.6 mm alone gives
     **1.73**, against 1.70 over 1.6-6.4 and 1.75 over the whole range. The
     window is narrower -- a factor of 4 instead of 16 -- so a slope from it is
     less well determined, and that is stated with the result rather than
     hidden.

  3. **Every radius carries its own validity gate, and a failed gate is not
     fitted.** Reported per radius: the off-face fraction of each patch (share
     of its points facing more than 60 degrees away from the probe point) and
     the patch aspect ratio (a narrow band makes slivers, and a 6-parameter
     quadric fitted to a sliver is unconstrained across the short direction --
     which is the way THIS correction could produce its own artefact). A radius
     is fitted only if off-face stays under OFF_FACE_MAX and aspect under
     ASPECT_MAX. If too few radii pass, the answer is "this material cannot
     support the measurement", which is a real result and is reported as one.

CALIBRATED AGAINST KNOWN ANSWERS BEFORE ANY POT WAS MEASURED. Two synthetic
self-tests, `scripts/selftest_wear_spectrum_mating.py` and
`scripts/selftest_wear_spectrum_exponent.py`, put surfaces of known roughness through this exact code path:

  - A perfectly flat break between two 4.5 mm slabs reads texture **0.00000**
    at every radius, as a plane must. (Pooled, as version 1 did it, the same
    surface read 0.0497 -- see `mating_faces`.)
  - White noise of standard deviation 0.02 mm reads **0.01594**, against the
    analytic mean absolute deviation of 0.798 * sigma = **0.01596**, and flat
    across radii, i.e. exponent 0 -- correct, because white noise has no
    scaling. The arithmetic is exact.
  - Fractional-Brownian break faces of known Hurst exponent H recover as:
    H = 0.2 -> **0.358**, H = 0.5 -> **0.585**, H = 0.8 -> **0.864**.

So the instrument is a ruler, with two properties that have to travel with
every number it prints:

  1. **It reads about +0.1 high at the fresh end** (+0.16 at H = 0.2, +0.06 at
     H = 0.8), because the fitted quadric absorbs some long-wavelength
     roughness. A pot reading 0.76 is therefore consistent with a true
     exponent near 0.65. The bias is toward the fresh band being read as
     rougher-scaling than it is, i.e. toward the worn conclusion, so it does
     not flatter the hypothesis being tested.
  2. **It cannot produce a reading near 1.7 from a fracture surface at all.**
     The roughest self-affine input possible, H = 0.8, came back 0.864.
     Anything above about 0.9 is not fracture texture -- it is a smooth
     surface with shape leaking into the fit. That is an INDEPENDENT
     confirmation that version 1's readings of 1.06-1.81 on fresh ceramic were
     the vessel's shape and not its break texture, arrived at without using
     the wall-thickness argument at all.

     It also sharpens what RePAIR's 1.73 means. A worn archaeological face
     reads above the self-affine ceiling because erosion has removed the
     fracture texture and left mild residual form -- which is what Gate A
     concluded. The honest caution is that "smoothed by burial" and "shape
     leaking into the fit" both read high, and only Gate A's patch-to-slab
     ratio of 0.55x and its straight unkinked line over a 16x span argue
     against the second. A crease gives a kink; RePAIR has none.

PREDICTION, RECORDED BEFORE THE V2 NUMBERS. Version 1's own predictions are
kept below because one of them was already refuted and that has to stay
visible.

  v2-1. Fresh (e000) faces should now read in or near 0.4-0.8. The one probe
        already taken points that way: `pink_bowl` fresh read **0.76** on a
        0.5%-of-size band, inside the fresh-fracture range, against 1.25 on
        the contaminated 2% band. If e000 still reads above 1.2 after the
        correction, then either the correction is insufficient or our scans do
        not resolve fresh fracture, and this route closes.
  v2-2. Wear should raise the exponent toward 1.73.
  v2-3. It probably does not reach it. `erode_fracture_band` saturates from
        e075 on for every pot in this corpus (the knn=48 kernel stops
        widening), and achieved wear plateaus above the Juglet's roughness on
        half of them (`narrow_bottle4` 0.244 vs Juglet 0.171).

  v1-1. REFUTED. Version 1 predicted e000 would read 0.4-0.8 and it read
        1.06-1.81 -- for the instrument reason above, not because our fresh
        ceramic is smooth.
  v1-2. UNTESTED by v1: the direction of change split between pots, which is
        what a contaminated statistic does.

A CONFOUND THAT REMAINS. The wear operator acts at a fixed FRACTION of object
size, but this axis is absolute millimetres, so the same rung is a different
physical abrasion per pot: roughly 0.40-0.67 mm on `blue_pot` against
1.0-1.67 mm on `plate`. Pots are therefore never pooled -- each is read up its
own ladder, which is this corpus's standing rule anyway (agreement between
attempts correlates with fragment count at r = -0.87).

ABSOLUTE MILLIMETRES. The ladder geometry is normalised to max|v| = 0.5, and
erosion is a physical process, so each pot is rescaled to real scan units
before measuring: scale = raw_max|v| / 0.5 from `fractura_real.hdf5`, computed
in-script rather than hand-copied. That is exact because the normalisation was
one uniform factor applied once, before erosion, and it is verified per pot
against the raw bounding-box diagonal (worst drift on the full ladder: 0.43%).

Usage:
  python scripts/wear_fracture_spectrum.py \
      --erosion dataset/erosion_ceramics.hdf5 \
      --raw     dataset/fractura_real.hdf5 \
      --out-dir artifacts/wear_spectrum
"""

import argparse
import json
import sys
from pathlib import Path

import h5py
import numpy as np
import trimesh
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from repair_fracture_spectrum import RADII_MM, spectrum_mm  # noqa: E402,F401

import matplotlib                                            # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt                              # noqa: E402

# Gate A, docs/notes/GATE_A_RESULT.md -- 20 Pompeii fresco fragments, real
# archaeological fracture eroded for two thousand years.
REPAIR_TEXTURE = {0.40: 0.0018, 0.80: 0.0049, 1.60: 0.0197,
                  3.20: 0.0685, 6.40: 0.2091}
REPAIR_EXPONENT_FULL = 1.75      # 0.4 - 6.4 mm, as published (quoted 1.71)
REPAIR_EXPONENT_WINDOW = 1.73    # 0.4 - 1.6 mm, the window a pot wall holds
# self-affine roughness exponent of a real fracture surface, across metals,
# ceramics and rocks -- the fresh end of the axis.
FRESH_FRACTURE_BAND = (0.4, 0.8)
# measured recovery of known Hurst exponents through this code path, from
# selftest_exponent.py: truth -> reading. Used only to state the bias in the
# read-out; no number is silently corrected by it.
CALIBRATION = {0.2: 0.358, 0.5: 0.585, 0.8: 0.864}
# above this a reading is no longer fracture texture: the roughest possible
# self-affine surface (H = 0.8) reads 0.864 through this instrument.
SELF_AFFINE_CEILING = 0.9
# SECOND AXIS: how much the local log-log slope falls between the smallest and
# largest patch. A capture that lost fine detail is smooth only at small
# scales, so its local slope collapses as patches grow; a surface eroded
# through and through is equally smooth at every scale and its slope holds.
# Measured on RePAIR's published table over 0.8-6.4 mm, and on known-fresh
# H = 0.5 surfaces smoothed until they read the same slope
# (scripts/selftest_wear_spectrum_kink.py):
#   RePAIR, slope 1.80          decline 0.40
#   fresh + 0.50 mm smoothing, slope 1.60   decline 1.52
#   fresh + 0.80 mm smoothing, slope 2.00   decline 1.62
# So a high slope with a SMALL decline is genuine erosion, and a high slope
# with a LARGE decline is lost resolution. This is the discriminator Gate A's
# straight-line argument was reaching for, made into a number.
REPAIR_DECLINE = 0.40
DECLINE_ARTEFACT = 1.5

# radii a 4.5 mm wall can hold, floor set by 3x the 0.13-0.36 mm spacing
RADII_V2 = [0.40, 0.55, 0.80, 1.10, 1.60]
# version 1's fitting band, kept ONLY so the contaminated job 30352180 stays
# reproducible by diagnose_wear_spectrum_band.py. A 6.40 mm patch is 2.9x a pot
# wall; do not fit here.
COMMON_BAND = (1.60, 6.40)
BAND_FRAC = 0.02        # how near another sherd a break-face vertex must be
MATING_DOT = 0.50       # normal must point this much toward the other sherd
MATING_K = 8            # smooth the direction over this many other-sherd pts
OFF_FACE_DEG = 60.0
OFF_FACE_MAX = 0.15     # a radius above this is measuring more than one face
ASPECT_MAX = 4.0        # above this the patch is a sliver and the fit is loose
SPACING_RULE = 3.0      # finest readable scale ~ 3x point spacing (Gate A)
RUNGS = ["e000", "e025", "e050", "e075", "e100"]


def raw_scales(raw_path, raw_group="ceramics"):
    """max|v| / 0.5 per pot, and the raw diagonal to verify the rescale."""
    scale_of, diag_of = {}, {}
    with h5py.File(raw_path, "r") as fr:
        if raw_group not in fr:
            raise SystemExit("no group '" + raw_group + "' in " + raw_path +
                             "; top level: " + str(list(fr.keys())))
        for pot in sorted(fr[raw_group].keys()):
            g = fr[raw_group][pot]["pieces"]
            allv = np.concatenate(
                [np.asarray(g[k]["vertices"][:], dtype=np.float64)
                 for k in sorted(g.keys())], axis=0)
            scale_of[pot] = float(np.abs(allv).max()) / 0.5
            diag_of[pot] = float(np.linalg.norm(allv.max(0) - allv.min(0)))
            del allv
    return scale_of, diag_of


def load_sherds(h5, group, tag, max_pts, rng):
    """Points and their own triangle-derived normals, one entry per sherd."""
    g = h5[group][tag]["pieces"]
    out = []
    for k in sorted(g.keys(), key=lambda s: (len(s), s)):
        v = np.asarray(g[k]["vertices"][:], dtype=np.float64)
        f = np.asarray(g[k]["faces"][:], dtype=np.int64)
        m = trimesh.Trimesh(vertices=v, faces=f, process=False)
        n = np.asarray(m.vertex_normals, dtype=np.float64)
        del m
        if len(v) > max_pts:
            sel = rng.choice(len(v), max_pts, replace=False)
            v, n = v[sel], n[sel]
        out.append((v, n))
    return out


def contact_bands(pieces, diag, band_frac=BAND_FRAC, min_pts=400):
    """Kept from version 1 so the contaminated result stays reproducible.

    Distance to another sherd alone. This is what job 30352180 used, and it
    takes the vessel wall beside the join along with the break face. Use
    `mating_faces` instead; `diagnose_wear_spectrum_band.py` imports this one
    to reproduce the fault.
    """
    bands = []
    for i, a in enumerate(pieces):
        best = None
        for j, b in enumerate(pieces):
            if i == j:
                continue
            d, _ = cKDTree(b).query(a, workers=-1)
            best = d if best is None else np.minimum(best, d)
        if best is None:
            continue
        band = a[best < band_frac * diag]
        if len(band) >= min_pts:
            bands.append(band)
    return bands


def mating_faces(sherds, diag, band_frac=BAND_FRAC, dot_min=MATING_DOT,
                 min_pts=400):
    """Break-face points: near another sherd AND facing it. ONE ENTRY PER SHERD.

    Two mating break faces point at each other; the wall beside the join is
    just as near but points across. Also returns what fraction of the
    merely-near set survived -- the discard is the size of version 1's
    contamination, reported rather than assumed.

    THE FACES MUST NOT BE POOLED, and version 1 pooled them. Two mating faces
    are two surfaces about 0.1 mm apart pointing in opposite directions, so a
    patch containing both has a quadric residual of half the gap between them
    at every radius. A synthetic self-test (`scripts/selftest_wear_spectrum_mating.py`) read texture
    0.0497 mm at R = 0.40 and 0.0493 at R = 6.40 on a PERFECTLY FLAT pair --
    no scaling at all, and identical on a deliberately roughened pair. Pooled,
    this instrument is blind to the roughness it exists to measure. On the real
    pots that defect was masked by the larger wall contamination; it would have
    surfaced the moment the wall was excluded. So each sherd's break face is
    probed on its own and the results averaged across sherds.
    """
    out, kept, near = [], 0, 0
    for i, (v, n) in enumerate(sherds):
        others = np.concatenate([w for j, (w, _) in enumerate(sherds)
                                 if j != i], axis=0)
        tree = cKDTree(others)
        k = min(MATING_K, len(others))
        d, idx = tree.query(v, k=k, workers=-1)
        d1 = d[:, 0] if k > 1 else d
        target = others[idx].mean(axis=1) if k > 1 else others[idx]
        u = target - v
        u /= np.linalg.norm(u, axis=1, keepdims=True) + 1e-12
        is_near = d1 < band_frac * diag
        faces_it = np.sum(n * u, axis=1) > dot_min
        sel = is_near & faces_it
        near += int(is_near.sum())
        kept += int(sel.sum())
        if sel.sum() >= min_pts:
            out.append((v[sel], n[sel]))
        del others, tree
    return out, near, kept


def probe_radius(pts, nrms, R, max_probe, rng):
    """Residual, off-face fraction and patch aspect at one radius.

    The residual arithmetic is `spectrum_mm`'s, line for line -- same local
    frame, same quadric, same mean absolute deviation. The two diagnostics are
    the new part, and they are what say whether the residual means anything:

      off-face   share of the patch pointing more than OFF_FACE_DEG away from
                 the probe point. Above zero the patch spans more than one
                 surface and the quadric is absorbing an edge, not curvature.
      aspect     sqrt of the ratio of the patch's two in-surface eigenvalues.
                 A narrow band makes slivers; a 6-parameter quadric on a sliver
                 is unconstrained across the short direction. This is how the
                 v2 correction could invent its own artefact, so it is measured.
    """
    tree = cKDTree(pts)
    probe_i = (np.arange(len(pts)) if len(pts) <= max_probe
               else rng.choice(len(pts), max_probe, replace=False))
    idx = tree.query_ball_point(pts[probe_i], R, workers=-1,
                                return_sorted=False)
    cos_thr = np.cos(np.deg2rad(OFF_FACE_DEG))

    res, off, asp = [], [], []
    for n, nb in zip(probe_i, idx):
        if len(nb) < 12:
            continue
        nb = np.asarray(nb)
        sel = nb if len(nb) <= 400 else rng.choice(nb, 400, replace=False)
        q = pts[sel]
        Q = q - q.mean(axis=0)
        w, u = np.linalg.eigh(Q.T @ Q)
        a, b, nrm = u[:, 2], u[:, 1], u[:, 0]
        x, y, z = Q @ a, Q @ b, Q @ nrm
        A = np.column_stack([np.ones_like(x), x, y, x * x, x * y, y * y])
        try:
            coef, *_ = np.linalg.lstsq(A, z, rcond=None)
        except np.linalg.LinAlgError:
            continue
        res.append(float(np.abs(z - A @ coef).mean()))
        off.append(float(np.mean(nrms[sel] @ nrms[n] < cos_thr)))
        asp.append(float(np.sqrt(max(w[2], 1e-18) / max(w[1], 1e-18))))
    if len(res) < 50:
        return None
    return dict(texture=float(np.mean(res)), off_face=float(np.mean(off)),
                aspect=float(np.median(asp)), n_probes=len(res))


def repair_reference(radii):
    """RePAIR's own slope and decline, computed on OUR radii, not borrowed.

    The published table has five points at 0.4, 0.8, 1.6, 3.2 and 6.4 mm. Its
    local log-log slope is not constant -- 1.44 then 2.01 then 1.80 then 1.61 --
    so a slope quoted over one span is not the reference for another, and a
    DECLINE quoted over 0.8-6.4 mm is certainly not the reference for 0.4-1.6,
    where RePAIR's slope actually rises. Both reference numbers are therefore
    interpolated in log-log onto whatever ladder is in use, so ours and theirs
    are read over the same span with the same arithmetic.
    """
    rr = np.array(sorted(REPAIR_TEXTURE))
    tt = np.array([REPAIR_TEXTURE[r] for r in rr])
    lo, hi = min(radii), max(radii)
    inside = [r for r in radii if rr[0] - 1e-9 <= r <= rr[-1] + 1e-9]
    if len(inside) < 2:
        return float("nan"), float("nan"), 0
    t = np.exp(np.interp(np.log(inside), np.log(rr), np.log(tt)))
    slope, _ = fit_exponent(inside, list(t))
    return slope, slope_decline(inside, list(t)), len(inside)


def slope_decline(radii, texture):
    """Local log-log slope at the smallest span, minus at the largest.

    Positive and large means the surface is smooth at fine scales but rough at
    coarse ones -- the signature of detail the capture never recorded. Near
    zero means it is equally smooth at every scale, which is what erosion
    through the whole surface does. See REPAIR_DECLINE.
    """
    pairs = [(r, t) for r, t in zip(radii, texture)
             if t is not None and np.isfinite(t) and t > 0]
    if len(pairs) < 3:
        return float("nan")
    r = np.log(np.array([p[0] for p in pairs]))
    t = np.log(np.array([p[1] for p in pairs]))
    seg = np.diff(t) / np.diff(r)
    return float(seg[0] - seg[-1])


def probe_faces(faces, R, max_probe, rng):
    """One radius, across every sherd's break face separately.

    Each face is probed on its own -- see `mating_faces` on why pooling them
    destroys the measurement -- and the sherds are then averaged, weighted by
    how many probes each contributed, so a large sherd is not out-voted by a
    small one. The per-sherd spread is carried out too: if the sherds of one
    pot disagree wildly at a radius, that radius is not measuring a property
    of the material.
    """
    per = [probe_radius(f, n, R, max_probe, rng) for f, n in faces]
    per = [x for x in per if x is not None]
    if not per:
        return None
    w = np.array([x["n_probes"] for x in per], dtype=np.float64)
    w /= w.sum()
    tex = np.array([x["texture"] for x in per])
    return dict(texture=float(tex @ w),
                texture_spread=float(np.std(tex)),
                off_face=float(np.array([x["off_face"] for x in per]) @ w),
                aspect=float(np.median([x["aspect"] for x in per])),
                n_probes=int(sum(x["n_probes"] for x in per)),
                n_sherds=len(per))


def fit_exponent(radii, texture, lo=None, hi=None):
    """log-log slope of texture against patch radius, over [lo, hi]."""
    lo = -np.inf if lo is None else lo
    hi = np.inf if hi is None else hi
    pairs = [(r, t) for r, t in zip(radii, texture)
             if lo - 1e-9 <= r <= hi + 1e-9 and t is not None
             and np.isfinite(t) and t > 0]
    if len(pairs) < 2:
        return float("nan"), len(pairs)
    r = np.array([p[0] for p in pairs])
    t = np.array([p[1] for p in pairs])
    return float(np.polyfit(np.log(r), np.log(t), 1)[0]), len(pairs)


def render_faces(shown, out):
    """LOOK AT THE SELECTION BEFORE BELIEVING THE NUMBERS (mandatory here).

    Grey is every vertex merely NEAR another sherd -- version 1's selection.
    Red is what also faces the other sherd -- version 2's. The difference
    between the two is the contamination that produced job 30352180's numbers,
    so this view is the correction itself rather than an illustration of it.
    """
    fig, axes = plt.subplots(1, len(shown), figsize=(3.4 * len(shown), 3.7))
    axes = np.atleast_1d(axes)
    for ax, (tag, near, face) in zip(axes, shown):
        rng = np.random.default_rng(0)
        a = near[rng.choice(len(near), min(25000, len(near)), False)]
        b = face[rng.choice(len(face), min(12000, len(face)), False)]
        ax.scatter(a[:, 0], a[:, 1], s=0.5, c="0.78", linewidths=0)
        ax.scatter(b[:, 0], b[:, 1], s=0.6, c="crimson", linewidths=0)
        ax.set_title(tag + "\ngrey = near a sherd, red = also facing it",
                     fontsize=8)
        ax.set_aspect("equal")
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    plt.close(fig)
    print("wrote " + str(out))


def render_spectrum(rows, radii, out):
    fig, ax = plt.subplots(figsize=(6.8, 5.2))
    rr = sorted(REPAIR_TEXTURE)
    for r in rows:
        c = ("#2980b9" if r["rung"] == "e000" else
             "#c0392b" if r["rung"] == "e100" else None)
        if c is None:
            continue
        t = [x if x is not None else np.nan for x in r["texture"]]
        ax.plot(radii, t, "-o", color=c, alpha=0.5, lw=1.1, ms=2.5)
    ax.plot(rr, [REPAIR_TEXTURE[x] for x in rr], "k-o", lw=2.6, ms=5,
            label="RePAIR real eroded fracture  R^" +
                  format(REPAIR_EXPONENT_FULL, ".2f"))
    ax.axvspan(radii[0], radii[-1], color="0.91", zorder=0,
               label="window a 4.5 mm wall holds  (RePAIR here: R^" +
                     format(REPAIR_EXPONENT_WINDOW, ".2f") + ")")
    ax.plot([], [], color="#2980b9", label="ours, fresh (e000)")
    ax.plot([], [], color="#c0392b", label="ours, fully abraded (e100)")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("patch radius (mm)")
    ax.set_ylabel("texture, deviation from fitted quadric (mm)")
    ax.set_title("Break-face texture spectrum, absolute scale, mating faces "
                 "only")
    ax.legend(fontsize=7.5, loc="upper left")
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    plt.close(fig)
    print("wrote " + str(out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--erosion", required=True)
    ap.add_argument("--raw", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--group", default="erosion_ceramics")
    ap.add_argument("--raw-group", default="ceramics")
    ap.add_argument("--face-mode", default="mating", choices=["mating", "band"],
                    help="'band' reproduces job 30352180's contaminated result")
    ap.add_argument("--radii", default=",".join(str(x) for x in RADII_V2))
    ap.add_argument("--max-sherd-pts", type=int, default=250000)
    ap.add_argument("--max-face-pts", type=int, default=80000)
    ap.add_argument("--max-probe", type=int, default=8000)
    ap.add_argument("--pots", default="")
    ap.add_argument("--rungs", default="",
                    help="restrict to these rungs; for smoke tests")
    a = ap.parse_args()

    outd = Path(a.out_dir)
    outd.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(0)
    radii = [float(x) for x in a.radii.split(",") if x]

    scale_of, rawdiag_of = raw_scales(a.raw, a.raw_group)
    print("face mode: " + a.face_mode + "   radii mm: " +
          ", ".join(format(r, ".2f") for r in radii))
    rs, rd, rn = repair_reference(radii)
    print("reference: RePAIR real eroded fracture, interpolated onto these "
          "radii, R^" + format(rs, ".2f") + " with decline " +
          format(rd, ".2f") + " (" + str(rn) + " radii); fresh fracture "
          "0.4-0.8")

    want = [p for p in a.pots.split(",") if p] or None
    want_rungs = [r for r in a.rungs.split(",") if r] or None
    rows, shown = [], []

    with h5py.File(a.erosion, "r") as fe:
        for tag in sorted(fe[a.group].keys()):
            pot, rung = tag.rsplit("_", 1)
            if want and pot not in want:
                continue
            if want_rungs and rung not in want_rungs:
                continue
            if pot not in scale_of:
                print("  " + tag + ": no raw counterpart, skipped")
                continue

            sherds = load_sherds(fe, a.group, tag, a.max_sherd_pts, rng)
            if len(sherds) < 2:
                print("  " + tag + ": fewer than two sherds, skipped")
                continue
            s = scale_of[pot]
            sherds = [(v * s, n) for v, n in sherds]     # -> millimetres
            allv = np.concatenate([v for v, _ in sherds], axis=0)
            diag = float(np.linalg.norm(allv.max(0) - allv.min(0)))
            drift = 100.0 * abs(diag - rawdiag_of[pot]) / rawdiag_of[pot]

            if a.face_mode == "band":
                bands = contact_bands([v for v, _ in sherds], diag)
                if not bands:
                    print("  " + tag + ": no band, skipped")
                    continue
                # v1 shape, reproduced deliberately: one pooled cloud, no
                # normals, so neither gate can fire. This is the contaminated
                # measurement and is only here to be compared against.
                faces = [(np.concatenate(bands, axis=0), None)]
                faces[0] = (faces[0][0], np.zeros_like(faces[0][0]))
                near_n = kept_n = len(faces[0][0])
            else:
                faces, near_n, kept_n = mating_faces(sherds, diag)
                if not faces:
                    print("  " + tag + ": no mating faces found, skipped")
                    continue
            faces = [(f if len(f) <= a.max_face_pts else
                      f[rng.choice(len(f), a.max_face_pts, False)],
                      n if len(n) <= a.max_face_pts else
                      n[rng.choice(len(n), a.max_face_pts, False)])
                     for f, n in faces]
            face_pts = int(sum(len(f) for f, _ in faces))

            sp = []
            for f, _ in faces:
                if len(f) < 4:
                    continue
                d, _i = cKDTree(f).query(f, k=2, workers=-1)
                sp.append(float(np.median(d[:, 1])))
            spacing = float(np.median(sp)) if sp else float("nan")
            finest = SPACING_RULE * spacing

            per_r, tex = {}, []
            for R in radii:
                st = probe_faces(faces, R, a.max_probe, rng)
                per_r[R] = st
                tex.append(None if st is None else st["texture"])

            # a radius is fitted only if the patch was one surface, was not a
            # sliver, and is above the sampling floor
            ok = [R for R in radii
                  if per_r[R] is not None and R >= finest - 1e-9
                  and per_r[R]["off_face"] <= OFF_FACE_MAX
                  and per_r[R]["aspect"] <= ASPECT_MAX]
            e_gated, n_gated = (fit_exponent(radii, tex, min(ok), max(ok))
                                if len(ok) >= 2 else (float("nan"), len(ok)))
            e_all, n_all = fit_exponent(radii, tex)
            decline = slope_decline(radii, tex)

            rows.append(dict(tag=tag, pot=pot, rung=rung, diag_mm=diag,
                             scale_drift_pct=drift, face_pts=face_pts,
                             n_faces=len(faces),
                             near_pts=int(near_n), kept_frac=(
                                 float(kept_n) / max(near_n, 1)),
                             spacing_mm=spacing, finest_valid_mm=finest,
                             radii_mm=radii, texture=tex,
                             per_radius={str(k): v for k, v in per_r.items()},
                             radii_passing_gates=ok,
                             exponent=e_gated, n_gated=n_gated,
                             exponent_ungated=e_all, n_ungated=n_all,
                             slope_decline=decline))
            print("  " + tag.ljust(22) + " diag " + format(diag, "6.1f") +
                  " (drift " + format(drift, ".2f") + "%)  face " +
                  str(face_pts).rjust(6) + " pts on " +
                  str(len(faces)) + " faces, " +
                  format(100 * kept_n / max(near_n, 1), "4.1f") +
                  "% of near  spacing " + format(spacing, ".3f") +
                  "  radii passing " + str(len(ok)) + "/" + str(len(radii)) +
                  "  exponent " + format(e_gated, "5.2f") +
                  " (ungated " + format(e_all, "5.2f") + ")" +
                  "  decline " + format(decline, "5.2f"), flush=True)

            if rung in ("e000", "e100") and len(shown) < 6:
                near_pts = np.concatenate(
                    contact_bands([v for v, _ in sherds], diag), axis=0)
                shown.append((tag, near_pts,
                              np.concatenate([f for f, _ in faces], axis=0)))
            del sherds, allv

    if not rows:
        print("nothing measured")
        return

    if shown and a.face_mode == "mating":
        render_faces(shown, outd / "face_selection.png")
    render_spectrum(rows, radii, outd / "spectrum.png")
    (outd / "wear_spectrum.json").write_text(json.dumps(
        dict(face_mode=a.face_mode, radii_mm=radii,
             repair_exponent_full=REPAIR_EXPONENT_FULL,
             repair_exponent_window=REPAIR_EXPONENT_WINDOW,
             fresh_fracture_band=list(FRESH_FRACTURE_BAND),
             off_face_max=OFF_FACE_MAX, aspect_max=ASPECT_MAX,
             mating_dot=MATING_DOT, band_frac=BAND_FRAC, rows=rows),
        indent=2), encoding="utf-8")

    # ---- the table that answers the question -----------------------------
    pots = sorted({r["pot"] for r in rows})
    print("")
    print("=" * 78)
    print("ROUGHNESS-SCALING EXPONENT, per pot up its own ladder")
    print("  real eroded archaeological fracture, RePAIR n=20, same window "
          "= " + format(REPAIR_EXPONENT_WINDOW, ".2f"))
    print("  fresh fracture, literature                                  "
          "= 0.4 - 0.8")
    print("=" * 78)
    print("pot".ljust(16) + "".join(x.rjust(8) for x in RUNGS) +
          "   spacing   decline")
    for pot in pots:
        line = pot.ljust(16)
        for rg in RUNGS:
            m = [r for r in rows if r["pot"] == pot and r["rung"] == rg]
            line += (format(m[0]["exponent"], "8.2f") if m else "-".rjust(8))
        sp = [r["spacing_mm"] for r in rows if r["pot"] == pot]
        dc = [r["slope_decline"] for r in rows if r["pot"] == pot
              and np.isfinite(r["slope_decline"])]
        line += "   " + format(float(np.median(sp)), ".3f") + " mm"
        line += "   " + (format(float(np.median(dc)), "6.2f") if dc
                         else "     -")
        print(line)

    # ---- the checks that decide whether the table can be read ------------
    print("")
    print("VALIDITY, per radius, median over all " + str(len(rows)) +
          " pot-rungs   (gates: off-face <= " + format(OFF_FACE_MAX, ".2f") +
          ", aspect <= " + format(ASPECT_MAX, ".1f") + ")")
    for R in radii:
        vals = [r["per_radius"][str(R)] for r in rows
                if r["per_radius"].get(str(R))]
        if not vals:
            print("  R " + format(R, "5.2f") + " mm   no probes")
            continue
        of = float(np.median([v["off_face"] for v in vals]))
        asp = float(np.median([v["aspect"] for v in vals]))
        npass = sum(1 for r in rows if R in r["radii_passing_gates"])
        print("  R " + format(R, "5.2f") + " mm   off-face " +
              format(100 * of, "5.1f") + "%   aspect " + format(asp, "5.2f") +
              "   passes on " + str(npass) + "/" + str(len(rows)) +
              " pot-rungs")
    print("")
    print("CALIBRATION of this instrument, from selftest_wear_spectrum_exponent.py:")
    print("  known Hurst exponent  ->  reading:  " + "   ".join(
        format(k, ".1f") + " -> " + format(v, ".2f")
        for k, v in sorted(CALIBRATION.items())))
    print("  it reads about +0.1 high at the fresh end, and CANNOT exceed ~" +
          format(SELF_AFFINE_CEILING, ".1f") + " on a real fracture surface.")
    print("  So a reading above " + format(SELF_AFFINE_CEILING, ".1f") +
          " means smooth-plus-shape, not rough fracture -- either genuine")
    print("  burial smoothing (the RePAIR condition) or shape still leaking "
          "into the fit.")

    e0 = [r["exponent"] for r in rows
          if r["rung"] == "e000" and np.isfinite(r["exponent"])]
    if e0:
        print("")
        print("fresh (e000) exponents: " + format(float(np.min(e0)), ".2f") +
              " - " + format(float(np.max(e0)), ".2f") + ", median " +
              format(float(np.median(e0)), ".2f") +
              "   (real fracture 0.4-0.8, this instrument reads ~+0.1 high)")
        med = float(np.median(e0))
        if med > SELF_AFFINE_CEILING:
            print("  STILL ABOVE THE SELF-AFFINE CEILING. Fresh ceramic "
                  "cannot scale this steeply,")
            print("  so shape is still entering the fit and the wear column "
                  "cannot be read. Either the")
            print("  selection is still contaminated or our scans do not "
                  "resolve fresh fracture at all")
            print("  -- see v2-1 in the docstring. Do not quote the table.")
        else:
            print("  IN RANGE: fresh ceramic reads as fresh fracture, so the "
                  "instrument is on the break")
            print("  face and the wear column above can be read.")

    print("")
    print("=" * 78)
    print("SECOND AXIS: is a high reading erosion, or detail the capture "
          "never recorded?")
    print("=" * 78)
    ref_slope, ref_decline, ref_n = repair_reference(radii)
    print("  RePAIR real eroded fracture, ON THESE RADII: slope " +
          format(ref_slope, ".2f") + "   decline " +
          format(ref_decline, ".2f") + "   (" + str(ref_n) + " radii)")
    print("  RePAIR over its own full 0.8-6.4 mm span:     slope 1.80   "
          "decline " + format(REPAIR_DECLINE, ".2f"))
    print("  known-fresh surface smoothed to read slope 1.60   decline 1.52")
    print("  known-fresh surface smoothed to read slope 2.00   decline 1.62")
    print("")
    print("  A high slope with a SMALL decline is a genuinely eroded "
          "surface: smooth at")
    print("  every scale. A high slope with a decline near " +
          format(DECLINE_ARTEFACT, ".1f") + " is smooth only at fine "
          "scales,")
    print("  which is lost resolution and says nothing about wear.")
    print("")
    for rg in RUNGS:
        d = [r["slope_decline"] for r in rows
             if r["rung"] == rg and np.isfinite(r["slope_decline"])]
        e = [r["exponent_ungated"] for r in rows
             if r["rung"] == rg and np.isfinite(r["exponent_ungated"])]
        if not d or not e:
            continue
        md, me = float(np.median(d)), float(np.median(e))
        verdict = ("erosion-like" if md < 0.8 else
                   "resolution-limited -- NOT a wear signal"
                   if md > DECLINE_ARTEFACT - 0.4 else "ambiguous")
        print("  " + rg + "   slope " + format(me, "5.2f") + "   decline " +
              format(md, "5.2f") + "   " + verdict)
    print("")
    print("  If our rungs sit at a large decline while RePAIR on the same "
          "radii sits at")
    print("  " + format(ref_decline, ".2f") + ", then our break")
    print("  faces and RePAIR's are not the same kind of surface whatever "
          "their slopes")
    print("  look like, and the distributional comparison in intent/O7 "
          "cannot be made on")
    print("  this statistic with this capture. That is a real answer, and it "
          "is about the")
    print("  data we have rather than about the wear model.")
    print("")
    print("wrote " + str(outd) + "/wear_spectrum.json, spectrum.png" +
          (", face_selection.png" if a.face_mode == "mating" else ""))
    print("LOOK AT face_selection.png BEFORE QUOTING ANY NUMBER ABOVE.")


if __name__ == "__main__":
    main()
