"""Can a strip long enough for the ISO filter rules be laid on these break faces?

WHY THIS EXISTS. Round 1 of the wear-ruler grilling settled that the measuring
patch is a STRIP along the break ribbon rather than a disc, because the
Juglet's 1.79 mm wall (job 30385552) cannot hold the 2.88 mm disc its own
0.29-0.48 mm point spacing demands. That is the shape. It does not give the
SIZE, and the size is not free either -- surface-roughness metrology fixes it
with two rules, both of which are ratios to things we have already measured:

  1. ISO 3274 / ISO 16610-21: the sampling interval must not exceed one fifth
     of the filter cutoff, or the Gaussian weighting function itself is
     undersampled and the filter is not the filter it claims to be. For us the
     sampling interval IS the point spacing, so

         cutoff  lambda_c >= 5 x point spacing

  2. ISO 21920 / ISO 4288: an evaluation length is five section lengths, and a
     section length is one cutoff. So

         strip length >= 5 x lambda_c  =  25 x point spacing

On the Juglet's 0.48 mm spacing that is lambda_c >= 2.4 mm and a strip at least
12 mm long. THAT NUMBER IS AN ASSERTION UNTIL MEASURED: a 65 mm juglet's break
ribbons may simply not run 12 mm unbroken, and if they do not, either the
cutoff has to come down (below what the spacing supports) or the evaluation
length rule has to be broken deliberately and said out loud.

WHAT IT MEASURES. Per break face, in millimetres: the point spacing, and the
longest strip that actually fits. "Fits" is tested where the strip would sit,
not inferred from an area: at each sampled centre the neighbours are projected
into the plane perpendicular to that point's normal -- the local surface frame
-- and the two in-surface principal extents are the run ALONG the break and
the width ACROSS the wall. A strip of length L fits at that centre if the
along-break extent reaches L while the across-wall extent stays inside the
wall. The frame is the one already used by
`check_mating_face_is_a_ribbon.py:70-102`; taking the direction from the
ribbon's own bounds is safe because the elongation comes from where the clay
ENDS, not from the surface texture being measured, so it cannot be biased by
the wear.

Break-face selection is `wear_fracture_spectrum.mating_faces` (near another
sherd AND facing it), whose recall was measured at 99.5-99.8%. Faces are never
pooled -- two mating faces are two surfaces ~0.1 mm apart pointing opposite
ways, and pooling them once made the instrument blind to the roughness it
existed to measure.

Read at e000 only: this is about how the objects are SAMPLED, not about wear.
"""

import argparse
import json
from pathlib import Path

import h5py
import numpy as np
import trimesh
from scipy.spatial import cKDTree

from wear_fracture_spectrum import load_sherds, mating_faces, raw_scales

# The two ISO ratios, kept as names so a change is visible in the log.
SPACING_PER_CUTOFF = 5.0    # ISO 3274: sampling interval <= lambda_c / 5
CUTOFFS_PER_LENGTH = 5.0    # ISO 21920/4288: evaluation = 5 section lengths

# Strip lengths to test, mm. Spans the 12 mm the Juglet's spacing implies.
LENGTHS = [4.0, 6.0, 8.0, 12.0, 16.0, 24.0]
N_CENTRES = 300             # sampled strip positions per face
MIN_NB = 40                 # a centre with fewer neighbours is not measured
JUGLET_SPACING = (0.29, 0.48)


def local_frame_extents(pts, nrms, tree, centre_idx, r):
    """In-surface (along, across) extents of the neighbourhood, in file units.

    Neighbours are projected onto the plane perpendicular to the centre
    point's own normal, so both numbers are extents WITHIN the surface. The
    2nd-98th percentile spread is used rather than min-max: a single stray
    point must not lengthen a ribbon.
    """
    nb = tree.query_ball_point(pts[centre_idx], r)
    if len(nb) < MIN_NB:
        return None
    d = pts[nb] - pts[centre_idx]
    n = nrms[centre_idx]
    a = np.array([0.0, 1.0, 0.0]) if abs(n[0]) > 0.9 else np.array([1.0, 0.0, 0.0])
    e1 = np.cross(n, a)
    e1 /= np.linalg.norm(e1) + 1e-12
    e2 = np.cross(n, e1)
    p2 = np.column_stack([d @ e1, d @ e2])
    _w, u = np.linalg.eigh(p2.T @ p2)
    pr = p2 @ u[:, ::-1]
    lo, hi = np.percentile(pr, [2, 98], axis=0)
    ext = np.abs(hi - lo)
    return float(ext[0]), float(ext[1])


def face_spacing(pts, rng, n=4000):
    """Median nearest-neighbour distance -- the step size of the measurement."""
    idx = rng.choice(len(pts), min(n, len(pts)), replace=False)
    d, _ = cKDTree(pts).query(pts[idx], k=2, workers=-1)
    return float(np.median(d[:, 1]))


def wall_of(v, f):
    m = trimesh.Trimesh(vertices=v, faces=f, process=False)
    return (2.0 * abs(float(m.volume)) / float(m.area)) if m.area > 0 else None


def measure_face(pts, nrms, wall_mm, scale, rng):
    """Longest strip that fits, and the fraction of positions where it fits."""
    spacing = face_spacing(pts, rng) * scale
    tree = cKDTree(pts)
    idx = rng.choice(len(pts), min(N_CENTRES, len(pts)), replace=False)
    fits, along_at = {}, {}
    for L in LENGTHS:
        r = 0.5 * L / scale           # half-length, back in file units
        ok, along = 0, []
        for i in idx:
            e = local_frame_extents(pts, nrms, tree, i, r)
            if e is None:
                continue
            lg, nr = e[0] * scale, e[1] * scale
            along.append(lg)
            # the strip must run the full length along the break, and must not
            # have wandered off the ribbon across it
            if lg >= L and (wall_mm is None or nr <= wall_mm * 1.15):
                ok += 1
        n_meas = max(len(along), 1)
        fits[L] = ok / n_meas
        along_at[L] = float(np.median(along)) if along else float("nan")
    return dict(spacing_mm=spacing, n_pts=int(len(pts)),
                fits=fits, median_along_mm=along_at)


def report(title, faces, spacings):
    print("")
    print("=" * 78)
    print(title)
    print("=" * 78)
    if not faces:
        print("  no break faces selected")
        return
    sp = float(np.median(spacings))
    lam = SPACING_PER_CUTOFF * sp
    need = CUTOFFS_PER_LENGTH * lam
    print("  point spacing, median over faces   " + format(sp, ".3f") + " mm"
          "   (range " + format(min(spacings), ".3f") + " - " +
          format(max(spacings), ".3f") + ")")
    print("  -> ISO 3274 floor on the cutoff    lambda_c >= " +
          format(lam, ".2f") + " mm   (5 x spacing)")
    print("  -> ISO 21920 floor on strip length        >= " +
          format(need, ".2f") + " mm   (5 x lambda_c)")
    print("")
    print("  fraction of strip positions where a strip of each length fits")
    print("  inside the ribbon (median over faces):")
    for L in LENGTHS:
        fr = [f["fits"][L] for f in faces]
        al = [f["median_along_mm"][L] for f in faces
              if np.isfinite(f["median_along_mm"][L])]
        flag = "  <-- the length this object's spacing demands" \
            if abs(L - min(LENGTHS, key=lambda x: abs(x - need))) < 1e-9 else ""
        print("    L = " + format(L, "5.1f") + " mm   fits at " +
              format(100.0 * float(np.median(fr)), "5.1f") + "% of positions"
              "   (median run available " +
              (format(float(np.median(al)), "5.2f") if al else "  n/a") +
              " mm)" + flag)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--erosion", required=True)
    p.add_argument("--erosion-group", default="erosion_ceramics")
    p.add_argument("--rung", default="e000")
    p.add_argument("--raw", required=True)
    p.add_argument("--raw-group", default="ceramics")
    p.add_argument("--juglet")
    p.add_argument("--juglet-group", default="juglet_gt")
    p.add_argument("--juglet-mm", type=float, default=65.0)
    p.add_argument("--max-pts", type=int, default=200000)
    p.add_argument("--out", default="artifacts/strip_feasibility.json")
    a = p.parse_args()

    rng = np.random.default_rng(0)
    scales, _diags = raw_scales(a.raw, a.raw_group)
    result = {}

    with h5py.File(a.erosion, "r") as h:
        tags = [t for t in sorted(h[a.erosion_group].keys())
                if t.endswith("_" + a.rung)]
        for tag in tags:
            pot = tag.replace("_" + a.rung, "")
            sc = scales.get(pot)
            if sc is None:
                print("WARNING no rescale for " + pot + " -- skipped")
                continue
            g = h[a.erosion_group][tag]["pieces"]
            walls = []
            for k in sorted(g.keys(), key=lambda s: (len(s), s)):
                w = wall_of(np.asarray(g[k]["vertices"][:], dtype=np.float64),
                            np.asarray(g[k]["faces"][:], dtype=np.int64))
                if w is not None:
                    walls.append(w * sc)
            wall_mm = float(np.median(walls)) if walls else None
            sherds = load_sherds(h, a.erosion_group, tag, a.max_pts, rng)
            if len(sherds) < 2:
                print(pot + ": " + str(len(sherds)) +
                      " sherd(s) -- no mating partner, skipped")
                continue
            allv = np.concatenate([v for v, _ in sherds], axis=0)
            diag = float(np.linalg.norm(allv.max(axis=0) - allv.min(axis=0)))
            faces, near, kept = mating_faces(sherds, diag)
            print("")
            print(pot + "   " + str(len(faces)) + " break faces, wall " +
                  (format(wall_mm, ".2f") if wall_mm else "n/a") + " mm, "
                  "selection kept " + str(kept) + " of " + str(near) + " near")
            per = [measure_face(v, n, wall_mm, sc, rng) for v, n in faces]
            report(pot + " at " + a.rung + ", real scan millimetres",
                   per, [f["spacing_mm"] for f in per])
            result[pot] = dict(wall_mm=wall_mm, faces=per)

    if a.juglet:
        # The fragments sit in their ground-truth pose in this file, so the
        # union of ALL of them is the vessel. A single fragment is smaller
        # than the pot it came from, so a per-fragment extent cannot set the
        # scale. Same convention as measure_sherd_scale.juglet_union_extent.
        with h5py.File(a.juglet, "r") as h:
            lo = np.full(3, np.inf)
            hi = np.full(3, -np.inf)
            for tag in sorted(h[a.juglet_group].keys()):
                if "pieces" not in h[a.juglet_group][tag]:
                    continue
                for k in h[a.juglet_group][tag]["pieces"].keys():
                    v = np.asarray(
                        h[a.juglet_group][tag]["pieces"][k]["vertices"][:],
                        dtype=np.float64)
                    lo = np.minimum(lo, v.min(axis=0))
                    hi = np.maximum(hi, v.max(axis=0))
            union = float((hi - lo).max()) if np.isfinite(lo).all() else 0.0
            jf = (a.juglet_mm / union) if union > 0 else 1.0
            print("")
            print("juglet assembled longest side " + format(union, ".4f") +
                  " file units, taken as " + format(a.juglet_mm, ".1f") +
                  " mm  ->  x" + format(jf, ".4f"))

            for tag in sorted(h[a.juglet_group].keys()):
                if "pieces" not in h[a.juglet_group][tag]:
                    continue
                g = h[a.juglet_group][tag]["pieces"]
                walls = []
                for k in sorted(g.keys(), key=lambda s: (len(s), s)):
                    w = wall_of(
                        np.asarray(g[k]["vertices"][:], dtype=np.float64),
                        np.asarray(g[k]["faces"][:], dtype=np.int64))
                    if w is not None:
                        walls.append(w * jf)
                wall_mm = float(np.median(walls)) if walls else None
                sherds = load_sherds(h, a.juglet_group, tag, a.max_pts, rng)
                if len(sherds) < 2:
                    print("JUGLET " + tag + ": " + str(len(sherds)) +
                          " sherd(s) -- no mating partner, skipped")
                    continue
                allv = np.concatenate([v for v, _ in sherds], axis=0)
                diag = float(np.linalg.norm(allv.max(axis=0) - allv.min(axis=0)))
                faces, near, kept = mating_faces(sherds, diag)
                print("")
                print("JUGLET " + tag + "   " + str(len(faces)) +
                      " break faces, wall " +
                      (format(wall_mm, ".2f") if wall_mm else "n/a") +
                      " mm, selection kept " + str(kept) + " of " +
                      str(near) + " near")
                per = [measure_face(v, n, wall_mm, jf, rng) for v, n in faces]
                report("JUGLET " + tag + " -- THE REFERENCE, scaled to " +
                       format(a.juglet_mm, ".1f") + " mm vessel",
                       per, [f["spacing_mm"] for f in per])
                result["juglet_" + tag] = dict(wall_mm=wall_mm, faces=per)

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dict(objects=result, lengths_mm=LENGTHS,
                                   spacing_per_cutoff=SPACING_PER_CUTOFF,
                                   cutoffs_per_length=CUTOFFS_PER_LENGTH,
                                   juglet_spacing_mm=JUGLET_SPACING,
                                   units="millimetres"), indent=2))
    print("")
    print("wrote " + str(out))


if __name__ == "__main__":
    main()
