"""What does a SMOOTHED fracture surface read? The branch that closes or opens O7.

The density self-test refuted sampling as the cause of fresh ceramic reading
1.51: decimating a known H = 0.5 surface to our scans' 0.267 mm spacing still
recovered 0.651. But decimation is not what a scanner does. Decimation keeps the
roughness amplitude at the points it keeps; a scanner LOW-PASS FILTERS, so
detail finer than its resolution is not sampled sparsely, it is gone, replaced
by a smooth interpolation with the object's residual form still in it.

That distinction decides the whole question, so it gets its own test.

  If a low-pass-filtered H = 0.5 surface reads near 1.5, then a high exponent
  means "this surface has no recorded texture at these scales" -- and it means
  that whether the texture was worn away by burial or never captured by the
  instrument. Our 1.51 and RePAIR's 1.73 would then be THE SAME READING for two
  different reasons, the fingerprint would not discriminate wear at all, and the
  distributional route in intent/O7 closes on this corpus.

  If instead smoothing has to be severe before the reading climbs that high,
  then a fresh pot at 1.51 is saying something about the surface, and the
  question is which of wear and capture put it there.

This is the test that can refute the instrument rather than the model, which is
why it is run before any pot number is quoted.

Usage:
  python scripts/selftest_wear_spectrum_smoothing.py
"""

import sys

import numpy as np
from scipy.ndimage import gaussian_filter
from scipy.spatial import cKDTree

sys.path.insert(0, "scripts")
from wear_fracture_spectrum import (RADII_V2, SELF_AFFINE_CEILING,  # noqa: E402
                                    fit_exponent, probe_faces)
from selftest_wear_spectrum_exponent import (EXTENT, N,  # noqa: E402
                                             fbm_surface)

# how much of the fine detail a capture removes, as the Gaussian sigma of the
# smoothing in millimetres. 0.00 is the raw synthetic surface.
SIGMAS_MM = [0.0, 0.05, 0.10, 0.20, 0.30, 0.50, 0.80]
SPACING_MM = 0.267           # our pots' measured break-face point spacing
TRUTH = 0.5                  # a mid fresh-fracture surface


def read_surface(z, step, rng):
    g = np.linspace(-EXTENT / 2, EXTENT / 2, N)[::step]
    X, Y = np.meshgrid(g, g, indexing="ij")
    pts = np.column_stack([X.ravel(), Y.ravel(), z[::step, ::step].ravel()])
    tree = cKDTree(pts)
    _, idx = tree.query(pts, k=9, workers=-1)
    nb = pts[idx] - pts[idx].mean(axis=1, keepdims=True)
    cov = np.einsum("nki,nkj->nij", nb, nb)
    ev = np.linalg.eigh(cov)[1][:, :, 0]
    ev *= np.sign(ev[:, 2])[:, None]
    keep = rng.choice(len(pts), min(120000, len(pts)), replace=False)
    faces = [(pts[keep], ev[keep])]
    tex = []
    for R in RADII_V2:
        st = probe_faces(faces, R, 6000, rng)
        tex.append(None if st is None else st["texture"])
    e, n = fit_exponent(RADII_V2, tex)
    return e, n, tex


def main():
    rng = np.random.default_rng(0)
    grid = EXTENT / N
    step = max(1, int(round(SPACING_MM / grid)))
    z0 = fbm_surface(TRUTH)

    print("A known fresh-fracture surface (Hurst " + format(TRUTH, ".1f") +
          "), sampled at our pots'")
    print("spacing of " + format(step * grid, ".3f") +
          " mm, then progressively smoothed the way a capture")
    print("smooths. Radii mm: " +
          ", ".join(format(r, ".2f") for r in RADII_V2))
    print("")
    print("smoothing".ljust(12) + "roughness".rjust(11) +
          "  exponent   what the reading would mean")
    print("sigma mm".ljust(12) + "left (mm)".rjust(11) +
          "  read back")
    print("-" * 74)

    for sig in SIGMAS_MM:
        z = z0 if sig <= 0 else gaussian_filter(z0, sig / grid, mode="wrap")
        e, n, tex = read_surface(z, step, rng)
        rough = float(np.std(z))
        note = ("fresh fracture" if e <= 0.9 else
                "READS AS SMOOTHED -- indistinguishable from worn")
        print(format(sig, ".2f").ljust(12) + format(rough, ".4f").rjust(11) +
              format(e, "11.3f") + "   " + note)

    print("")
    print("=" * 74)
    print("WHAT THIS DECIDES")
    print("=" * 74)
    print("Our fresh pots read 1.51 and RePAIR's worn frescoes read 1.73.")
    print("The smoothing sigma at which this known-fresh surface first crosses")
    print(format(SELF_AFFINE_CEILING, ".1f") + " is the amount of detail loss "
          "that would fake a worn reading.")
    print("Compare it to our point spacing of " + format(SPACING_MM, ".3f") +
          " mm: a capture cannot record")
    print("anything finer than about twice its spacing, so detail below "
          "~" + format(2 * SPACING_MM, ".2f") + " mm")
    print("is absent from our meshes whatever the pot's real surface does.")


if __name__ == "__main__":
    main()
