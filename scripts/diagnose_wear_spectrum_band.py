"""Is the break-face spectrum on a POT measuring the break, or the wall? (O7)

Job 30352180 put our simulated worn break faces on Gate A's fingerprint and got
answers that do not look like break faces. Fresh (e000) ceramic read **1.06 to
1.81**, median 1.35, where a real fracture surface should read 0.4-0.8 and where
real ERODED archaeological fracture reads 1.71. Two pots (`galli_pot` 1.69,
`plate` 1.81) already sat at or above the worn value before any wear was
applied, and the direction of change under wear disagreed between pots: up on
`galli_pot` and `plate`, flat on `blue_pot`, down on four others.

That pattern is what a contaminated measurement looks like, and there is a
specific geometric reason to expect one here.

THE SUSPICION, STATED SO IT CAN BE REFUTED. Gate A's largest patch has radius
6.4 mm -- 12.8 mm across. A RePAIR fresco plaque is **23 mm thick** (16-40,
`docs/notes/REPAIR_AS_TRAINING_SOURCE.md`), so its fracture ribbon is 16-40 mm
wide and a 12.8 mm patch sits inside it. A pot wall is a few millimetres. If our
break ribbon is narrower than the patch, then no patch at the large radii can
stay on the break: each one runs off the fracture, over the sharp arris where
break meets wall, and onto the vessel surface. **A quadric absorbs curvature but
it cannot absorb a crease.** A crease inside the patch leaves a residual that
grows roughly like the patch size, which is exactly the 1.7-2.0 signature the
run reported -- and exactly the trap Gate A already fell into once, when
measuring against the local mean returned 1.75 that turned out to be the
plaque's own outline.

If that is what happened, the honest conclusion is category 2 -- **the
measurement was broken** -- and not "our wear does not resemble real wear". The
two lead to opposite decisions, so this has to be settled before the numbers are
read.

WHAT WOULD REFUTE THE SUSPICION. If wall thickness is comfortably above 12.8 mm,
if the exponent barely moves when the band is narrowed 8x, and if patches at
6.4 mm are mostly single-surface, then the contamination is minor and the run's
numbers stand -- meaning our simulated wear genuinely fails to move this
statistic. That is a real and reportable negative, and this script is written to
be able to return it.

FOUR MEASUREMENTS, each able to contradict the others.

  1. WALL THICKNESS, per sherd, as 2V/A -- the same instrument and the same
     correction already applied to the RePAIR plaques. `is_watertight` is
     printed beside it, because 2V/A on a non-watertight scan is meaningless and
     a silent bad number here would invalidate everything below.

  2. BAND-WIDTH SWEEP. The exponent recomputed with the contact band at 0.25%,
     0.5%, 1% and 2% of object size. A measurement of the break face should be
     roughly indifferent to this. A measurement of the wall should collapse as
     the band narrows toward the fracture.

  3. OFF-FACE FRACTION, per radius. For every probe patch, the share of its
     points whose surface normal is more than 60 degrees away from the probe
     point's own. Zero means one continuous surface; a large value means the
     patch has wrapped around an edge onto another face. This is the direct
     measurement of the suspicion, at each of Gate A's radii, so it says where
     the axis stops being readable rather than only whether it does.

  4. THE RESIDUAL FIELD ITSELF, rendered per point and unbinned, at 1.6 and
     6.4 mm. Four successive proxy views of wear in this workspace each answered
     the wrong question convincingly (`docs/lessons.md`); the rule that came out
     of it is that when a proxy keeps failing you render the measured quantity.
     The residual IS the measured quantity. If the contamination is real the
     large-radius residual will be concentrated in a line along the arris rather
     than spread over the face.

The quadric fit here is copied from `spectrum_mm` rather than imported, because
the aggregate function returns one number per radius and this needs the
per-probe values behind it. The arithmetic is line-for-line the same and a
regression check against `spectrum_mm` is printed, so a divergence is visible.

Usage:
  python scripts/diagnose_wear_spectrum_band.py \
      --erosion dataset/erosion_ceramics.hdf5 \
      --raw     dataset/fractura_real.hdf5 \
      --out-dir artifacts/wear_spectrum_diag \
      --pots blue_pot,pink_bowl,galli_pot,plate --rungs e000,e100
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
from repair_fracture_spectrum import RADII_MM, spectrum_mm      # noqa: E402
from wear_fracture_spectrum import (COMMON_BAND, contact_bands,  # noqa: E402
                                    fit_exponent, raw_scales)

import matplotlib                                                # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                  # noqa: E402

BAND_SWEEP = [0.0025, 0.005, 0.01, 0.02]
OFF_FACE_DEG = 60.0
GATE_A_PATCH_MM = 2 * RADII_MM[-1]      # 12.8 mm across, the largest patch
REPAIR_SLAB_MM = 23.46                  # median, REPAIR_AS_TRAINING_SOURCE.md


def load_sherds(h5, group, tag):
    """Vertices, faces and vertex normals per sherd, full resolution.

    Not subsampled: wall thickness is a volume/area ratio and needs the mesh,
    and normals must come from the triangles rather than from a point cloud.
    """
    g = h5[group][tag]["pieces"]
    out = []
    for k in sorted(g.keys(), key=lambda s: (len(s), s)):
        v = np.asarray(g[k]["vertices"][:], dtype=np.float64)
        f = np.asarray(g[k]["faces"][:], dtype=np.int64)
        out.append((v, f))
    return out


def wall_thickness(v, f):
    """2V / A: mean thickness of a thin shell. Same instrument as the plaques.

    The break ribbon is left in the denominator here (unlike the RePAIR
    measurement, which could subtract it) because there is no break label on
    these real pots -- `shared_faces` is -1 everywhere. Leaving it in biases the
    answer THIN, which is the conservative direction for this argument: it makes
    the wall look less able to hold a patch, so it cannot manufacture the
    conclusion being tested.
    """
    m = trimesh.Trimesh(vertices=v, faces=f, process=False)
    a = float(m.area)
    if a <= 0:
        return None, False
    return 2.0 * abs(float(m.volume)) / a, bool(m.is_watertight)


def quadric_probe(pts, nrms, R, max_probe=6000, seed=0):
    """Per-probe residual and off-face fraction at one radius.

    The residual arithmetic is `spectrum_mm`'s, line for line. The off-face
    fraction is the new part: the share of the patch lying on a surface pointing
    more than OFF_FACE_DEG away from the probe point's own.
    """
    rng = np.random.default_rng(seed)
    tree = cKDTree(pts)
    probe_i = (np.arange(len(pts)) if len(pts) <= max_probe
               else rng.choice(len(pts), max_probe, replace=False))
    idx = tree.query_ball_point(pts[probe_i], R, workers=-1,
                               return_sorted=False)
    cos_thr = np.cos(np.deg2rad(OFF_FACE_DEG))

    res, off, keep = [], [], []
    for n, nb in zip(probe_i, idx):
        if len(nb) < 12:
            continue
        nb = np.asarray(nb)
        sel = nb if len(nb) <= 400 else rng.choice(nb, 400, replace=False)
        q = pts[sel]
        c = q.mean(axis=0)
        Q = q - c
        u = np.linalg.eigh(Q.T @ Q)[1]
        a, b, nrm = u[:, 2], u[:, 1], u[:, 0]
        x, y, z = Q @ a, Q @ b, Q @ nrm
        A = np.column_stack([np.ones_like(x), x, y, x * x, x * y, y * y])
        try:
            coef, *_ = np.linalg.lstsq(A, z, rcond=None)
        except np.linalg.LinAlgError:
            continue
        res.append(float(np.abs(z - A @ coef).mean()))
        off.append(float(np.mean(nrms[sel] @ nrms[n] < cos_thr)))
        keep.append(int(n))
    return (np.array(res), np.array(off), np.array(keep, dtype=np.int64))


def render_residual_field(band, nrms, out, tag):
    """The measured quantity itself, per point, unbinned, at two radii.

    Left column is the residual the exponent is computed from; right column is
    the off-face fraction. If the large-radius residual lines up with the
    off-face stripe, the exponent at that radius is an edge statistic.
    """
    fig, axes = plt.subplots(2, 2, figsize=(11, 9))
    for row, R in enumerate([1.60, 6.40]):
        res, off, keep = quadric_probe(band, nrms, R, max_probe=6000)
        if len(keep) == 0:
            continue
        p = band[keep]
        for col, (val, name, cm) in enumerate([
                (res, "quadric residual (mm)", "magma"),
                (off, "off-face fraction of patch", "viridis")]):
            ax = axes[row, col]
            order = np.argsort(val)
            s = ax.scatter(p[order, 0], p[order, 1], c=val[order], s=2.2,
                           cmap=cm, linewidths=0)
            ax.set_title(tag + "   R = " + format(R, ".2f") + " mm\n" + name +
                         "   median " + format(float(np.median(val)), ".4f"),
                         fontsize=9)
            ax.set_aspect("equal")
            ax.axis("off")
            fig.colorbar(s, ax=ax, fraction=0.045)
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
    ap.add_argument("--pots", default="blue_pot,pink_bowl,galli_pot,plate")
    ap.add_argument("--rungs", default="e000,e100")
    ap.add_argument("--max-band-pts", type=int, default=60000)
    ap.add_argument("--max-sherd-pts", type=int, default=250000)
    ap.add_argument("--max-probe", type=int, default=6000)
    a = ap.parse_args()

    outd = Path(a.out_dir)
    outd.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(0)
    scale_of, rawdiag_of = raw_scales(a.raw, a.raw_group)
    pots = [p for p in a.pots.split(",") if p]
    rungs = [r for r in a.rungs.split(",") if r]

    rows = []
    with h5py.File(a.erosion, "r") as fe:
        for pot in pots:
            for rung in rungs:
                tag = pot + "_" + rung
                if tag not in fe[a.group]:
                    print("  " + tag + ": absent, skipped")
                    continue
                s = scale_of[pot]
                sherds = [(v * s, f) for v, f in
                          load_sherds(fe, a.group, tag)]
                allv = np.concatenate([v for v, _ in sherds], axis=0)
                diag = float(np.linalg.norm(allv.max(0) - allv.min(0)))

                # --- 1. wall thickness, per sherd -------------------------
                th, wt = [], []
                for v, f in sherds:
                    t, w = wall_thickness(v, f)
                    if t is not None:
                        th.append(t)
                        wt.append(w)
                t_med = float(np.median(th)) if th else float("nan")
                print("")
                print("=" * 74)
                print(tag + "   diag " + format(diag, ".1f") + " mm")
                print("=" * 74)
                print("  wall thickness 2V/A per sherd, median " +
                      format(t_med, ".2f") + " mm   " +
                      "watertight " + str(sum(wt)) + "/" + str(len(wt)))
                print("    per sherd: " +
                      ", ".join(format(x, ".1f") for x in sorted(th)))
                print("  Gate A's largest patch is " +
                      format(GATE_A_PATCH_MM, ".1f") +
                      " mm across; a RePAIR plaque is " +
                      format(REPAIR_SLAB_MM, ".1f") + " mm thick.")
                print("    patch / wall = " +
                      format(GATE_A_PATCH_MM / max(t_med, 1e-9), ".1f") +
                      "x   (RePAIR: " +
                      format(GATE_A_PATCH_MM / REPAIR_SLAB_MM, ".2f") + "x)")

                # normals from the full mesh, then ONE consistent subsample
                # per sherd so points and normals never drift out of step.
                # Full resolution is needed for 2V/A above but not here: the
                # cross-sherd nearest-neighbour queries are the expensive part
                # and 250k points already resolve a 0.2 mm spacing.
                pieces, npieces = [], []
                for (v, f) in sherds:
                    m = trimesh.Trimesh(vertices=v, faces=f, process=False)
                    vn = np.asarray(m.vertex_normals, dtype=np.float64)
                    if len(v) > a.max_sherd_pts:
                        sel = rng.choice(len(v), a.max_sherd_pts, False)
                        pieces.append(v[sel])
                        npieces.append(vn[sel])
                    else:
                        pieces.append(v)
                        npieces.append(vn)
                    del m, vn

                # --- 2. band-width sweep ----------------------------------
                print("  band-width sweep, exponent over " +
                      format(COMMON_BAND[0], ".1f") + "-" +
                      format(COMMON_BAND[1], ".1f") + " mm:")
                sweep = {}
                for bf in BAND_SWEEP:
                    bands = contact_bands(pieces, diag, band_frac=bf,
                                          min_pts=200)
                    if not bands:
                        print("    " + format(100 * bf, "5.2f") +
                              "%  no band")
                        continue
                    bb = np.concatenate(bands, axis=0)
                    if len(bb) > a.max_band_pts:
                        bb = bb[rng.choice(len(bb), a.max_band_pts, False)]
                    tex = spectrum_mm(bb, RADII_MM, max_probe=a.max_probe)
                    e, n = fit_exponent(RADII_MM, [float(x) for x in tex],
                                        *COMMON_BAND)
                    sweep[bf] = dict(exponent=e, n_radii=n, pts=int(len(bb)),
                                     width_mm=bf * diag)
                    print("    " + format(100 * bf, "5.2f") + "% of size = " +
                          format(bf * diag, "5.2f") + " mm wide   " +
                          str(len(bb)).rjust(6) + " pts   exponent " +
                          format(e, "5.2f"))

                # --- 3. off-face fraction per radius ----------------------
                # on the widest band, i.e. the one job 30352180 used. Selected
                # by index so each point keeps its own sherd's normal.
                bp, bn = [], []
                for i, v in enumerate(pieces):
                    best = None
                    for j, w in enumerate(pieces):
                        if i == j:
                            continue
                        d, _ = cKDTree(w).query(v, workers=-1)
                        best = d if best is None else np.minimum(best, d)
                    if best is None:
                        continue
                    sel = best < 0.02 * diag
                    if sel.sum() >= 400:
                        bp.append(v[sel])
                        bn.append(npieces[i][sel])
                if not bp:
                    print("  no contact band at 2%, skipped")
                    continue
                band = np.concatenate(bp, axis=0)
                nrms = np.concatenate(bn, axis=0)
                if len(band) > a.max_band_pts:
                    pick = rng.choice(len(band), a.max_band_pts, False)
                    band, nrms = band[pick], nrms[pick]

                print("  off-face fraction of each patch (mean over probes), "
                      "and share of patches >15% off-face:")
                offrow = {}
                for R in RADII_MM:
                    res, off, keep = quadric_probe(band, nrms, R,
                                                   max_probe=a.max_probe)
                    if len(off) < 50:
                        print("    R " + format(R, "5.2f") +
                              " mm   too few patches")
                        continue
                    offrow[R] = dict(off_mean=float(off.mean()),
                                     off_median=float(np.median(off)),
                                     frac_contaminated=float((off > 0.15).mean()),
                                     residual_mean=float(res.mean()),
                                     n_probes=int(len(off)))
                    print("    R " + format(R, "5.2f") + " mm   off-face " +
                          format(100 * off.mean(), "5.1f") + "%   " +
                          "patches >15% off-face " +
                          format(100 * (off > 0.15).mean(), "5.1f") + "%   " +
                          "residual " + format(res.mean(), ".4f") + " mm")

                # regression check: our per-probe mean must equal spectrum_mm
                chk = spectrum_mm(band, RADII_MM, max_probe=a.max_probe)
                mine = [offrow.get(R, {}).get("residual_mean", float("nan"))
                        for R in RADII_MM]
                worst = np.nanmax([abs(x - y) / max(abs(y), 1e-12)
                                   for x, y in zip(mine, chk)])
                print("  regression vs spectrum_mm: worst relative "
                      "difference " + format(100 * worst, ".2f") + "%  " +
                      ("(same arithmetic)" if worst < 0.05
                       else "(DIVERGED - do not trust the diagnostic)"))

                rows.append(dict(tag=tag, pot=pot, rung=rung, diag_mm=diag,
                                 wall_2VA_mm=t_med, wall_per_sherd=th,
                                 watertight=int(sum(wt)), n_sherds=len(th),
                                 band_sweep={str(k): v
                                             for k, v in sweep.items()},
                                 off_face={str(k): v
                                           for k, v in offrow.items()},
                                 regression_worst_rel=float(worst)))

                # --- 4. the residual field itself -------------------------
                render_residual_field(band, nrms,
                                      outd / ("residual_" + tag + ".png"), tag)
                del sherds, pieces, npieces, allv, band, nrms

    (outd / "wear_spectrum_diag.json").write_text(
        json.dumps(dict(band_sweep=BAND_SWEEP, off_face_deg=OFF_FACE_DEG,
                        gate_a_patch_mm=GATE_A_PATCH_MM,
                        repair_slab_mm=REPAIR_SLAB_MM, rows=rows), indent=2),
        encoding="utf-8")

    # ---- the verdict, as a table -----------------------------------------
    print("")
    print("=" * 74)
    print("DOES THE NUMBER DEPEND ON THE SELECTION? (it should not, if it is "
          "the break)")
    print("=" * 74)
    print("tag".ljust(22) + "wall mm" +
          "".join(("  " + format(100 * b, ".2f") + "%").rjust(9)
                  for b in BAND_SWEEP) + "   off-face @6.4mm")
    for r in rows:
        line = r["tag"].ljust(22) + format(r["wall_2VA_mm"], "7.2f")
        for b in BAND_SWEEP:
            s = r["band_sweep"].get(str(b))
            line += (format(s["exponent"], "9.2f") if s else "-".rjust(9))
        o = r["off_face"].get("6.4")
        line += ("   " + format(100 * o["off_mean"], ".1f") + "%"
                 if o else "   -")
        print(line)
    print("")
    print("wrote " + str(outd) + "/wear_spectrum_diag.json and the residual "
          "field renders")


if __name__ == "__main__":
    main()
