"""Can the instrument recover a KNOWN roughness exponent, AT OUR POINT DENSITY?

A self-affine surface with Hurst exponent H has texture growing as R^H by
definition. So building fractional-Brownian break faces of known H and reading
them back through `wear_fracture_spectrum`'s exact code path says whether any
number that script prints is a measurement or a coincidence. Fresh fracture in
metals, ceramics and rocks sits at H = 0.4-0.8; RePAIR's eroded archaeological
fracture reads 1.73, above what a self-affine surface can reach at all, which
is itself part of the answer.

THE DENSITY HALF EXISTS BECAUSE THE FIRST VERSION LACKED IT, and that omission
nearly let a second broken measurement through. On a dense grid the instrument
recovers H well. But a quadric has SIX free parameters, and a small patch at a
coarse spacing holds barely more points than that, so the fit absorbs the
roughness it is meant to leave behind. That is worst at the smallest radii,
which tilts the log-log slope upward -- indistinguishable, from the number
alone, from a genuinely smoothed surface. Our scans have 0.13-0.36 mm spacing
on the break face; the original calibration used 0.044 mm, 5.7x finer, and so
could not have caught this.

Usage:
  python scripts/selftest_wear_spectrum_exponent.py
  python scripts/selftest_wear_spectrum_exponent.py 0.044,0.25
"""

import sys

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, "scripts")
from wear_fracture_spectrum import (RADII_V2, fit_exponent,  # noqa: E402
                                    probe_faces)

N = 900                      # grid points across a 40 x 40 mm face
EXTENT = 40.0
AMP = 0.05                   # roughness amplitude in mm
TRUTHS = [0.2, 0.5, 0.8]
DEFAULT_SPACINGS = [0.044, 0.13, 0.20, 0.25, 0.36]


def fbm_surface(H, n=N, extent=EXTENT, amp=AMP, seed=0):
    """Fourier-synthesis fractional Brownian surface, spectrum ~ k^-(2H+2)."""
    r = np.random.default_rng(seed)
    kx = np.fft.fftfreq(n, d=extent / n)
    KX, KY = np.meshgrid(kx, kx, indexing="ij")
    K = np.sqrt(KX ** 2 + KY ** 2)
    K[0, 0] = 1.0
    amp_k = K ** (-(H + 1.0))
    amp_k[0, 0] = 0.0
    ph = r.normal(size=(n, n)) + 1j * r.normal(size=(n, n))
    z = np.real(np.fft.ifft2(amp_k * ph))
    z *= amp / np.std(z)
    return z


def measure(z, step, rng):
    """Read one decimated surface back through the real code path."""
    g = np.linspace(-EXTENT / 2, EXTENT / 2, N)[::step]
    zz = z[::step, ::step]
    X, Y = np.meshgrid(g, g, indexing="ij")
    pts = np.column_stack([X.ravel(), Y.ravel(), zz.ravel()])

    # normals from local plane fits, the way a mesh would supply them
    tree = cKDTree(pts)
    _, idx = tree.query(pts, k=9, workers=-1)
    nb = pts[idx] - pts[idx].mean(axis=1, keepdims=True)
    cov = np.einsum("nki,nkj->nij", nb, nb)
    ev = np.linalg.eigh(cov)[1][:, :, 0]
    ev *= np.sign(ev[:, 2])[:, None]

    keep = rng.choice(len(pts), min(120000, len(pts)), replace=False)
    faces = [(pts[keep], ev[keep])]

    tex, counts = [], []
    for R in RADII_V2:
        st = probe_faces(faces, R, 6000, rng)
        tex.append(None if st is None else st["texture"])
        counts.append(0 if st is None else st["n_probes"])
    e, n = fit_exponent(RADII_V2, tex)
    return e, n, tex


def main():
    spacings = [float(x) for x in (sys.argv[1].split(",") if len(sys.argv) > 1
                                   else DEFAULT_SPACINGS)]
    rng = np.random.default_rng(0)
    grid = EXTENT / N

    print("radii mm: " + ", ".join(format(r, ".2f") for r in RADII_V2))
    print("")
    print("A quadric has SIX free parameters. Points available to constrain "
          "it in the")
    print("SMALLEST patch (R = " + format(RADII_V2[0], ".2f") + " mm):")
    for sp in spacings:
        step = max(1, int(round(sp / grid)))
        eff = step * grid
        print("  spacing " + format(eff, ".3f") + " mm  ->  ~" +
              str(int(np.pi * RADII_V2[0] ** 2 / eff ** 2)) + " points")
    print("")
    print("Our break-face spacing is 0.13-0.36 mm, typically about 0.25.")
    print("")

    summary, effective = {}, {}
    for H in TRUTHS:
        z = fbm_surface(H)
        for sp in spacings:
            step = max(1, int(round(sp / grid)))
            effective[sp] = step * grid
            e, n, _ = measure(z, step, rng)
            summary[(H, sp)] = e
            print("  H=" + format(H, ".1f") + "  spacing " +
                  format(effective[sp], ".3f") + " mm  ->  RECOVERED " +
                  format(e, ".3f") + "   (truth " + format(H, ".2f") +
                  ", " + str(n) + " radii)")
        print("")

    print("=" * 72)
    print("RECOVERED EXPONENT vs POINT SPACING")
    print("=" * 72)
    print("truth".ljust(8) +
          "".join(format(effective[sp], "9.3f") for sp in spacings))
    for H in TRUTHS:
        print(format(H, ".1f").ljust(8) +
              "".join(format(summary[(H, sp)], "9.3f") for sp in spacings))
    print("")
    print("Read the H = 0.5 row -- a mid fresh-fracture surface. If the "
          "reading climbs")
    print("toward 1.5 as spacing coarsens to our scans' 0.25 mm, then a fresh "
          "pot")
    print("reading 1.51 is a SAMPLING artefact, says nothing about its wear, "
          "and no")
    print("choice of radii can fix it -- only a finer scan, or a fit with "
          "fewer")
    print("parameters, would.")


if __name__ == "__main__":
    main()
