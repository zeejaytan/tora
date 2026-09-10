"""How long a profile can be traced along these break ribbons, in millimetres.

WHY THIS EXISTS. Round 1 of the wear-ruler grilling settled that the measuring
patch is a STRIP along the break ribbon rather than a disc, because the
Juglet's 1.79 mm wall (job 30385552) cannot hold the 2.88 mm disc its own
0.29-0.48 mm point spacing demands. That is the shape. It does not give the
SIZE, and the size is not free either -- surface-roughness metrology fixes it
with two rules, both of which are ratios to things we have already measured:

  1. ISO 3274 / ISO 16610-21: the sampling interval must not exceed one fifth
     of the filter cutoff, or the Gaussian weighting function is itself
     undersampled and the filter is not the filter it claims to be. For us the
     sampling interval IS the point spacing, so

         cutoff  lambda_c >= 5 x point spacing

  2. ISO 21920 / ISO 4288: an evaluation length is five section lengths, and a
     section length is one cutoff. So

         profile length >= 5 x lambda_c  =  25 x point spacing

That is arithmetic. Whether the break ribbons on a 65 mm vessel actually run
that far is a measurement, and it is the one this script makes.

VERSION 2 -- V1 (JOB 30386369) WAS BROKEN AND ITS NUMBERS MUST NOT BE QUOTED.
V1 asked, at each candidate position, whether the break ran at least L mm as
seen from inside a ball of radius L/2. A ball of radius L/2 is L across, so
the spread of points inside it can never exceed L, and the 2-98 percentile
trims it to about 0.88 L. Every object read 0.0% at every length and the
"available run" column tracked 0.88 x L exactly. The test could not pass.

It was also wrong in concept, which is why this is a rewrite rather than a
patched radius. A break ribbon on a curved vessel CURVES. A straight 12 mm
ruler laid on it runs off the wall even where the ribbon is 30 mm long, so a
straight-chord extent understates the ribbon and confounds ribbon length with
vessel curvature. What ISO 21920 traces is a profile FOLLOWING the surface.

WHAT V2 MEASURES. Per break face, in millimetres:

  * point spacing -- the step size of the measurement, median nearest-neighbour
    distance, measured BEFORE any thinning;

  * traceable profile length -- the arc length of continuous ribbon, got by
    walking the break-face points as a graph (each point joined to its near
    neighbours) and taking the longest shortest-path through the largest
    connected piece, by the standard two-sweep method. This follows the curve,
    so it is the length of profile a filter could actually be run over. It is
    conservative on a closed loop: a break running right around a sherd's
    perimeter reports about half its circumference, because that is the
    furthest you can get from any starting point;

  * ribbon width -- the across-wall extent, from the local in-surface frame
    (project neighbours into the plane perpendicular to the point's normal;
    the narrow principal direction is across the wall). This must come back at
    or below the measured wall thickness, and that is the control: the same
    measurement on points whose normals face AWAY from the neighbouring sherd
    -- the pot's outer skin, not a ribbon -- must NOT be bounded. The frame is
    the one already in check_mating_face_is_a_ribbon.py:70-102, and taking the
    direction from the ribbon's own bounds is safe because the elongation comes
    from where the clay ENDS, not from the surface texture being measured, so
    it cannot be biased by the wear.

Break-face selection is wear_fracture_spectrum.mating_faces (near another
sherd AND facing it), whose recall was measured at 99.5-99.8%. Faces are never
pooled -- two mating faces are two surfaces about 0.1 mm apart pointing
opposite ways, and pooling them once made the instrument blind to the
roughness it existed to measure.

Read at e000 only: this is about how the objects are SAMPLED, not about wear.
"""

import argparse
import json
from pathlib import Path

import h5py
import numpy as np
import trimesh
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components, dijkstra
from scipy.spatial import cKDTree

from wear_fracture_spectrum import load_sherds, mating_faces, raw_scales

# The two ISO ratios, kept as named constants so a change is visible in the log.
SPACING_PER_CUTOFF = 5.0    # ISO 3274: sampling interval <= lambda_c / 5
CUTOFFS_PER_LENGTH = 5.0    # ISO 21920/4288: evaluation = 5 section lengths

# Profile lengths of interest, mm. 12 mm is what the Juglet's spacing implies.
LENGTHS = [4.0, 6.0, 8.0, 12.0, 16.0, 24.0]

GRAPH_MAX_PTS = 30000       # face points kept for the walk (voxel-thinned)
EDGE_SPACINGS = 3.0         # join points closer than this x the thinned spacing
FRAME_R_WALLS = 1.2         # local-frame radius, as a multiple of the wall
N_CENTRES = 400             # sampled positions for the width measurement
MIN_NB = 30
JUGLET_SPACING = (0.29, 0.48)


def median_spacing(pts, rng, n=4000):
    """Median nearest-neighbour distance -- the step size of the measurement."""
    idx = rng.choice(len(pts), min(n, len(pts)), replace=False)
    d, _ = cKDTree(pts).query(pts[idx], k=2, workers=-1)
    return float(np.median(d[:, 1]))


def voxel_thin(pts, voxel):
    """One point per voxel, so a graph edge length means one thing."""
    key = np.floor(pts / voxel).astype(np.int64)
    _u, first = np.unique(key, axis=0, return_index=True)
    return pts[np.sort(first)]


def traceable_length(pts, spacing, scale):
    """Arc length of the longest continuous run of ribbon, in mm.

    Walks the face as a graph and takes the longest shortest-path (graph
    diameter) of its largest connected piece, by the two-sweep method: the
    furthest point from an arbitrary start, then the furthest point from
    there. This follows the surface, so a curving ribbon is not penalised for
    curving, and a ribbon interrupted by a hole in the scan is not credited
    across the hole.
    """
    voxel = max(spacing * 1.5, 1e-12)
    thin = pts
    while len(thin) > GRAPH_MAX_PTS:
        thin = voxel_thin(pts, voxel)
        if len(thin) > GRAPH_MAX_PTS:
            voxel *= 1.3
    if len(thin) < 50:
        return float("nan"), 0, float("nan")

    d2, _ = cKDTree(thin).query(thin, k=2, workers=-1)
    sp_thin = float(np.median(d2[:, 1]))
    tree = cKDTree(thin)
    pairs = tree.query_pairs(EDGE_SPACINGS * sp_thin, output_type="ndarray")
    if len(pairs) == 0:
        return float("nan"), 0, float("nan")
    w = np.linalg.norm(thin[pairs[:, 0]] - thin[pairs[:, 1]], axis=1)
    n = len(thin)
    g = coo_matrix((np.concatenate([w, w]),
                    (np.concatenate([pairs[:, 0], pairs[:, 1]]),
                     np.concatenate([pairs[:, 1], pairs[:, 0]]))),
                   shape=(n, n)).tocsr()

    ncomp, lab = connected_components(g, directed=False)
    big = int(np.argmax(np.bincount(lab)))
    keep = np.flatnonzero(lab == big)
    sub = g[keep][:, keep]

    d0 = dijkstra(sub, indices=0)
    a = int(np.argmax(np.where(np.isfinite(d0), d0, -1.0)))
    d1 = dijkstra(sub, indices=a)
    diam = float(np.max(np.where(np.isfinite(d1), d1, -1.0)))
    return diam * scale, int(ncomp), float(len(keep)) / n


def ribbon_width(pts, nrms, wall_mm, scale, rng):
    """Median across-wall extent from the local in-surface frame, in mm."""
    r = (FRAME_R_WALLS * (wall_mm if wall_mm else 3.0)) / scale
    tree = cKDTree(pts)
    idx = rng.choice(len(pts), min(N_CENTRES, len(pts)), replace=False)
    narrow = []
    for i in idx:
        nb = tree.query_ball_point(pts[i], r)
        if len(nb) < MIN_NB:
            continue
        d = pts[nb] - pts[i]
        nvec = nrms[i]
        aux = np.array([0.0, 1.0, 0.0]) if abs(nvec[0]) > 0.9 \
            else np.array([1.0, 0.0, 0.0])
        e1 = np.cross(nvec, aux)
        e1 /= np.linalg.norm(e1) + 1e-12
        e2 = np.cross(nvec, e1)
        p2 = np.column_stack([d @ e1, d @ e2])
        _w, u = np.linalg.eigh(p2.T @ p2)
        pr = p2 @ u[:, ::-1]
        lo, hi = np.percentile(pr, [2, 98], axis=0)
        narrow.append(float(abs(hi[1] - lo[1])))
    return (float(np.median(narrow)) * scale) if narrow else float("nan")


def wall_of(v, f):
    m = trimesh.Trimesh(vertices=v, faces=f, process=False)
    return (2.0 * abs(float(m.volume)) / float(m.area)) if m.area > 0 else None


def measure_face(pts, nrms, wall_mm, scale, rng):
    sp_units = median_spacing(pts, rng)
    run, ncomp, frac = traceable_length(pts, sp_units, scale)
    return dict(spacing_mm=sp_units * scale, n_pts=int(len(pts)),
                run_mm=run, n_components=ncomp, largest_frac=frac,
                width_mm=ribbon_width(pts, nrms, wall_mm, scale, rng))


def report(title, faces, wall_mm):
    print("")
    print("=" * 78)
    print(title)
    print("=" * 78)
    if not faces:
        print("  no break faces selected")
        return
    sp = [f["spacing_mm"] for f in faces]
    runs = [f["run_mm"] for f in faces if np.isfinite(f["run_mm"])]
    wid = [f["width_mm"] for f in faces if np.isfinite(f["width_mm"])]
    m = float(np.median(sp))
    lam = SPACING_PER_CUTOFF * m
    need = CUTOFFS_PER_LENGTH * lam
    print("  point spacing, median over faces     " + format(m, ".3f") +
          " mm   (range " + format(min(sp), ".3f") + " - " +
          format(max(sp), ".3f") + ")")
    print("  -> ISO 3274 floor on the cutoff      lambda_c >= " +
          format(lam, ".2f") + " mm")
    print("  -> ISO 21920 floor on profile length          >= " +
          format(need, ".2f") + " mm")
    print("")
    if runs:
        nearest = min(LENGTHS, key=lambda x: abs(x - need))
        print("  traceable profile length, following the ribbon:")
        print("    median over faces " + format(float(np.median(runs)), "7.2f") +
              " mm     shortest face " + format(min(runs), "7.2f") +
              "     longest " + format(max(runs), "7.2f"))
        for L in LENGTHS:
            k = sum(1 for r in runs if r >= L)
            flag = "   <-- nearest to this object's ISO floor" \
                if L == nearest else ""
            print("    faces with >= " + format(L, "5.1f") +
                  " mm traceable:  " + str(k) + " of " + str(len(runs)) +
                  "   (" + format(100.0 * k / len(runs), "5.1f") + "%)" + flag)
        print("    this object's own ISO floor (" + format(need, ".2f") +
              " mm) is met by " + str(sum(1 for r in runs if r >= need)) +
              " of " + str(len(runs)) + " faces")
    if wid:
        print("")
        print("  ribbon width across the wall, median over faces  " +
              format(float(np.median(wid)), ".2f") + " mm   (wall " +
              (format(wall_mm, ".2f") if wall_mm else "n/a") +
              " mm)  CONTROL: must not exceed the wall")
    fr = [f["largest_frac"] for f in faces if np.isfinite(f["largest_frac"])]
    if fr:
        print("  largest connected piece holds " +
              format(100.0 * float(np.median(fr)), ".1f") +
              "% of the face's points (median)")


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
                   per, wall_mm)
            result[pot] = dict(wall_mm=wall_mm, faces=per)

    if a.juglet:
        # The fragments sit in their ground-truth pose in this file, so the
        # union of ALL of them is the vessel. A single fragment is smaller than
        # the pot it came from, so a per-fragment extent cannot set the scale.
        # Same convention as measure_sherd_scale.juglet_union_extent.
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
                diag = float(np.linalg.norm(
                    allv.max(axis=0) - allv.min(axis=0)))
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
                       per, wall_mm)
                result["juglet_" + tag] = dict(wall_mm=wall_mm, faces=per)

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dict(objects=result, lengths_mm=LENGTHS,
                                   spacing_per_cutoff=SPACING_PER_CUTOFF,
                                   cutoffs_per_length=CUTOFFS_PER_LENGTH,
                                   juglet_spacing_mm=JUGLET_SPACING,
                                   method="geodesic graph diameter, v2",
                                   units="millimetres"), indent=2))
    print("")
    print("wrote " + str(out))


if __name__ == "__main__":
    main()
