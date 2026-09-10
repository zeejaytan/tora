"""Purity and recall of break-face selection, on a pot whose truth we built.

The dataset has no break-face label. All three routes to one are closed, and
each was checked rather than assumed:
  - `shared_faces` is -1 for every triangle of every piece (the field exists,
    it was never filled);
  - `full_mesh` is not the intact vessel. Every sherd vertex lies on it at
    0.00 mm in all percentiles, and blue_pot's full_mesh has 1,043,149 vertices
    against 608,207 across its five sherds -- a pre-break mesh would have
    FEWER, since breaking duplicates every break-face vertex. It contains the
    break faces, so it cannot label them;
  - the cut did not duplicate vertices either. Nearest-neighbour distance from
    each sherd to the others has NO mass below 1e-4 of object size on any of
    blue_pot's five sherds. The pieces were independently remeshed.

So the truth is built here instead, on geometry carrying the confound that
matters: a thin-walled curved vessel with a WAVY break, so the join line on the
outer surface wanders the way a real one does. A flat cut would let any
selection through and prove nothing.

  wall 4.5 mm on a 20 mm radius, 0.2 mm point spacing, mating gap 0.10 mm,
  cut waviness 3 mm at ~15 mm wavelength, break roughness at known Hurst H.

Every point is labelled by construction: outer surface, inner surface, rim, or
break face. That makes purity and recall exact, and it is what the real data
cannot give.

WHAT THIS IS FOR. The selection in `wear_fracture_spectrum.py` keeps points
within 2% of object diagonal of another sherd -- 2.7 mm on blue_pot -- and
facing it. But the real mating gap measured on blue_pot's own sherds is
0.07-0.13 mm. The band is 20-40x wider than any true contact, so it can admit
wall while still passing every gate the instrument owns. This measures how much
it actually admits, and whether a gap tied to point spacing plus an
ANTIPARALLEL partner normal does better. A break face has its twin 0.1 mm away
pointing back at it; a patch of outer wall near the join has its neighbour's
outer wall alongside, pointing the SAME way. That difference survives curvature
and needs no viewpoint.

Usage:
  python scripts/selftest_wear_spectrum_pot.py
  python scripts/selftest_wear_spectrum_pot.py 0.8
  python scripts/selftest_wear_spectrum_pot.py 0.5 0.0   # flat cut
"""

import sys

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, "scripts")
from wear_fracture_spectrum import (BAND_FRAC, MATING_DOT,  # noqa: E402
                                    MATING_K, RADII_V2, fit_exponent,
                                    probe_faces, slope_decline)

R_OUT = 20.0
WALL = 4.5
HEIGHT = 30.0
STEP = 0.20
GAP = 0.10
WAVE_AMP = 3.0
WAVE_LEN = 15.0
ROUGH_AMP = 0.05
TIGHT_SPACINGS = 3.0      # candidate gap gate, in point spacings
ANTI_DOT = -0.70          # candidate partner-normal gate


def rough_field(H, seed=0, n=1024, extent=64.0):
    """Fractional-Brownian height field, interpolated on demand.

    n MATTERS AND THE FIRST VERSION HAD IT WRONG. At n = 256 over 64 mm the
    field has 0.25 mm cells while the pot is sampled at 0.20 mm, so the
    surface was smooth below the sampling scale BY CONSTRUCTION -- the exact
    band-limited condition already shown to read falsely high
    (`selftest_wear_spectrum_smoothing.py`: a known H = 0.5 blurred to 0.10 mm
    reads 0.979). It inflated the flat-cut reading to 1.099 for truth 0.5.
    At n = 1024 the cells are 0.0625 mm, 3.2x finer than the sampling, so the
    roughness is real at every radius probed.
    """
    r = np.random.default_rng(seed)
    k = np.fft.fftfreq(n, d=extent / n)
    KX, KZ = np.meshgrid(k, k, indexing="ij")
    K = np.sqrt(KX ** 2 + KZ ** 2)
    K[0, 0] = 1.0
    amp = K ** (-(H + 1.0))
    amp[0, 0] = 0.0
    ph = r.normal(size=(n, n)) + 1j * r.normal(size=(n, n))
    z = np.real(np.fft.ifft2(amp * ph))
    z *= ROUGH_AMP / np.std(z)
    g = np.linspace(-extent / 2, extent / 2, n)

    def f(x, y):
        ix = np.clip(np.searchsorted(g, x) - 1, 0, n - 2)
        iy = np.clip(np.searchsorted(g, y) - 1, 0, n - 2)
        tx = (x - g[ix]) / (g[1] - g[0])
        ty = (y - g[iy]) / (g[1] - g[0])
        return ((1 - tx) * (1 - ty) * z[ix, iy] +
                tx * (1 - ty) * z[ix + 1, iy] +
                (1 - tx) * ty * z[ix, iy + 1] +
                tx * ty * z[ix + 1, iy + 1])
    return f


def wave(x, z):
    """Large-scale waviness of the cut: a real break is not a plane."""
    return WAVE_AMP * (np.sin(2 * np.pi * x / WAVE_LEN) *
                       np.cos(2 * np.pi * z / (1.7 * WAVE_LEN)))


def shell(sign, rough):
    """One piece: outer, inner, rims, and its two break sheets. Labelled."""
    pts, nrm, lab = [], [], []

    # outer and inner surfaces, kept on this piece's side of the wavy cut
    for r, s_out in ((R_OUT, 1.0), (R_OUT - WALL, -1.0)):
        nth = max(8, int(round(2 * np.pi * r / STEP)))
        th = np.linspace(0, 2 * np.pi, nth, endpoint=False)
        zz = np.arange(0.0, HEIGHT, STEP)
        T, Z = np.meshgrid(th, zz, indexing="ij")
        x, y = r * np.cos(T), r * np.sin(T)
        keep = (y - (wave(x, Z) + rough(x, Z))) * sign > GAP / 2
        p = np.column_stack([x[keep], y[keep], Z[keep]])
        n = np.column_stack([np.cos(T[keep]), np.sin(T[keep]),
                             np.zeros(keep.sum())]) * s_out
        pts.append(p)
        nrm.append(n)
        lab.append(np.full(len(p), 1 if s_out > 0 else 2))

    # rims at z = 0 and z = HEIGHT
    for z0, s_z in ((0.0, -1.0), (HEIGHT, 1.0)):
        rr = np.arange(R_OUT - WALL, R_OUT, STEP)
        for r in rr:
            nth = max(8, int(round(2 * np.pi * r / STEP)))
            th = np.linspace(0, 2 * np.pi, nth, endpoint=False)
            x, y = r * np.cos(th), r * np.sin(th)
            zc = np.full_like(x, z0)
            keep = (y - (wave(x, zc) + rough(x, zc))) * sign > GAP / 2
            p = np.column_stack([x[keep], y[keep], np.full(keep.sum(), z0)])
            pts.append(p)
            nrm.append(np.column_stack([np.zeros(keep.sum()),
                                        np.zeros(keep.sum()),
                                        np.full(keep.sum(), s_z)]))
            lab.append(np.full(len(p), 3))

    # THE BREAK SHEET. Two mating faces are ONE surface pulled apart, so both
    # pieces must be built from the same height field S and the same normals,
    # this piece's face being S pushed GAP/2 along its own outward normal.
    #
    # THE FIRST VERSION DID NOT DO THAT AND IT MANUFACTURED A FINDING. It set
    # Y = W + sign * (GAP/2 + h) and n = [gx, -sign, gz]: the roughness and the
    # normal's y component were MIRRORED about the wave, so the two faces were
    # reflections of each other rather than the same surface. Reflections are
    # only antiparallel where the cut is flat. With the wave's gradient
    # reaching 1.26, n_A . n_B = (|g|^2 - 1)/(|g|^2 + 1) = +0.23 -- the two
    # faces of a single break read as facing the SAME way. That silently turned
    # the `tight gap + antiparallel` gate into a flatness filter: its recall
    # fell 69% -> 10% on a wavy cut and the 10% it kept were the near-flat
    # patches, which is why it appeared to be immune to the meander and to
    # recover the flat-cut exponent. It was not immune; it had discarded every
    # part of the break that meanders. The tangential terms carried the wrong
    # sign as well (+gx where the surface normal needs -gx), so the frame every
    # quadric was fitted in was tilted the wrong way on any sloped patch.
    #
    # Here n_A . n_B = -1 exactly and the faces sit GAP apart along the normal,
    # which is what a break that has come apart actually looks like.
    xs = np.arange(-R_OUT, R_OUT, STEP)
    zs = np.arange(0.0, HEIGHT, STEP)
    X, Z = np.meshgrid(xs, zs, indexing="ij")
    S = wave(X, Z) + rough(X, Z)
    sx, sz = np.gradient(S, STEP, STEP)
    N = np.stack([-sx, np.ones_like(S), -sz], axis=-1)
    N /= np.linalg.norm(N, axis=-1, keepdims=True)
    # This piece keeps the wall where (y - S) * sign > GAP/2, so its face sits
    # on the +sign side of the cut and its OUTWARD normal points back across
    # the gap at its partner: -sign, not +sign. Getting that backwards makes
    # both faces point away from each other, and `dot > MATING_DOT` then
    # selects nothing at all -- which is how it was caught.
    P = np.stack([X, S, Z], axis=-1) + sign * N * (GAP / 2)
    rad = np.sqrt(P[..., 0] ** 2 + P[..., 1] ** 2)
    keep = (rad >= R_OUT - WALL) & (rad <= R_OUT)
    n = -sign * N[keep]
    pts.append(P[keep])
    nrm.append(n)
    lab.append(np.full(int(keep.sum()), 4))

    return (np.concatenate(pts), np.concatenate(nrm), np.concatenate(lab))


def select(sherds, diag, mode, spacing):
    """Boolean mask per sherd for one selection rule."""
    out = []
    for i, (v, n, _l) in enumerate(sherds):
        others = np.concatenate([w for j, (w, _, _) in enumerate(sherds)
                                 if j != i])
        onrm = np.concatenate([m for j, (_, m, _) in enumerate(sherds)
                               if j != i])
        tree = cKDTree(others)
        k = min(MATING_K, len(others))
        d, idx = tree.query(v, k=k, workers=-1)
        d1 = d[:, 0] if k > 1 else d
        near1 = idx[:, 0] if k > 1 else idx
        target = others[idx].mean(axis=1) if k > 1 else others[idx]
        u = target - v
        u /= np.linalg.norm(u, axis=1, keepdims=True) + 1e-12
        dot = np.sum(n * u, axis=1)
        if mode == "near":
            m = d1 < BAND_FRAC * diag
        elif mode == "mating":
            m = (d1 < BAND_FRAC * diag) & (dot > MATING_DOT)
        else:
            partner = np.sum(n * onrm[near1], axis=1)
            m = ((d1 < TIGHT_SPACINGS * spacing) & (dot > MATING_DOT)
                 & (partner < ANTI_DOT))
        out.append(m)
        del others, onrm, tree
    return out


def score(sherds, masks):
    tp = sum(int(((l == 4) & m).sum()) for (_, _, l), m in zip(sherds, masks))
    sel = sum(int(m.sum()) for m in masks)
    tot = sum(int((l == 4).sum()) for (_, _, l) in sherds)
    return (100.0 * tp / sel if sel else float("nan"),
            100.0 * tp / tot if tot else float("nan"), sel)


def spectrum(faces, rng):
    tex = []
    for R in RADII_V2:
        st = probe_faces(faces, R, 6000, rng)
        tex.append(None if st is None else st["texture"])
    e, n = fit_exponent(RADII_V2, tex)
    return e, slope_decline(RADII_V2, tex), n


def main():
    H = float(sys.argv[1]) if len(sys.argv) > 1 else 0.5
    global WAVE_AMP
    if len(sys.argv) > 2:
        WAVE_AMP = float(sys.argv[2])
    rng = np.random.default_rng(0)
    rough = rough_field(H)

    sherds = [shell(+1.0, rough), shell(-1.0, rough)]
    allv = np.concatenate([v for v, _, _ in sherds])
    diag = float(np.linalg.norm(allv.max(0) - allv.min(0)))
    sp = float(np.median(cKDTree(allv).query(
        allv[rng.choice(len(allv), 20000, replace=False)],
        k=2, workers=-1)[0][:, 1]))

    print("Built pot: outer radius " + format(R_OUT, ".1f") + " mm, wall " +
          format(WALL, ".1f") + " mm, height " + format(HEIGHT, ".1f") +
          " mm, wavy break")
    print("diag " + format(diag, ".1f") + " mm, point spacing " +
          format(sp, ".3f") + " mm, mating gap " + format(GAP, ".2f") +
          " mm, break roughness H = " + format(H, ".1f"))
    print("v1/v2 band = " + format(BAND_FRAC, ".2f") + " x diag = " +
          format(BAND_FRAC * diag, ".2f") + " mm; candidate gate = " +
          format(TIGHT_SPACINGS, ".0f") + " x spacing = " +
          format(TIGHT_SPACINGS * sp, ".2f") + " mm")
    for i, (v, _n, l) in enumerate(sherds):
        print("  sherd " + str(i) + ": " + str(len(v)) + " pts  outer " +
              str(int((l == 1).sum())) + "  inner " +
              str(int((l == 2).sum())) + "  rim " + str(int((l == 3).sum())) +
              "  BREAK " + str(int((l == 4).sum())))
    print("")

    # GATE ON THE GEOMETRY ITSELF, before any selection rule is scored. The
    # first version of `shell` built the two faces as reflections and they were
    # antiparallel only where the cut was flat; that defect is invisible in
    # purity and recall, and it produced a selection rule that looked immune to
    # the meander. So assert what a real break guarantees: the two faces lie
    # GAP apart and point at each other. If this fails, nothing below counts.
    (vA, nA, lA), (vB, nB, lB) = sherds
    bA, bB = vA[lA == 4], vB[lB == 4]
    mA, mB = nA[lA == 4], nB[lB == 4]
    dd, ii = cKDTree(bB).query(bA, k=1, workers=-1)
    pdot = np.sum(mA * mB[ii], axis=1)
    print("break-face geometry check   gap " + format(float(np.median(dd)), ".3f") +
          " mm (built " + format(GAP, ".2f") + "), 95th " +
          format(float(np.percentile(dd, 95)), ".3f") +
          " mm   partner-normal dot median " +
          format(float(np.median(pdot)), ".3f") + ", 95th " +
          format(float(np.percentile(pdot, 95)), ".3f") + " (must be ~ -1)")
    if np.median(pdot) > -0.9 or np.percentile(dd, 95) > 3.0 * GAP:
        print("GEOMETRY INVALID: the two faces are not one surface pulled "
              "apart. Nothing below counts.")
        return
    print("")

    print("selection".ljust(30) + "purity".rjust(9) + "recall".rjust(9) +
          "n_sel".rjust(10) + "exponent".rjust(11) + "decline".rjust(9))
    print("-" * 78)
    truth = [(l == 4) for (_, _, l) in sherds]
    for name, masks in [("TRUTH (break face only)", truth),
                        ("near only (v1)", select(sherds, diag, "near", sp)),
                        ("near + facing (v2)",
                         select(sherds, diag, "mating", sp)),
                        ("tight gap + antiparallel",
                         select(sherds, diag, "tight", sp))]:
        pur, rec, nsel = score(sherds, masks)
        faces = [(v[m], n[m]) for (v, n, _l), m in zip(sherds, masks)
                 if m.sum() >= 400]
        e, dec, _nr = spectrum(faces, rng) if faces else (float("nan"),) * 3
        print(name.ljust(30) + format(pur, "8.1f") + "%" +
              format(rec, "8.1f") + "%" + format(nsel, "10d") +
              format(e, "11.3f") + format(dec, "9.2f"))

    print("")
    print("The exponent on TRUTH is what the instrument would read with a")
    print("perfect selection, at this point spacing, on known H = " +
          format(H, ".1f") + ".")
    print("Any selection whose exponent differs from it is reporting its own")
    print("contamination, not the surface. Purity below ~90% is disqualifying:")
    print("that is the error that voided job 30352180.")


if __name__ == "__main__":
    main()
