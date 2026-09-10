"""Can the instrument recover a KNOWN roughness exponent?

This is the calibration that decides whether any number it prints means
anything. A self-affine surface with Hurst exponent H has texture growing as
R^H by definition, so we build fractional-Brownian break faces at H = 0.2,
0.5 and 0.8 -- spanning fresh fracture (0.4-0.8) and RePAIR's worn 1.73 is
above the range a true self-affine surface can even reach, which is itself
worth knowing -- and check what comes back.

If the recovered slope tracks H, the instrument is a ruler. If it does not,
nothing measured with it can be quoted, including 0.76.
"""
import sys
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, "scripts")
from wear_fracture_spectrum import probe_faces, RADII_V2, fit_exponent

rng = np.random.default_rng(0)
N = 900                      # grid points across a 40 x 40 mm face
EXTENT = 40.0
AMP = 0.05                   # roughness amplitude in mm at the 1 mm scale


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


print("radii mm: " + ", ".join(format(r, ".2f") for r in RADII_V2))
print("")
for H in [0.2, 0.5, 0.8]:
    z = fbm_surface(H)
    g = np.linspace(-EXTENT / 2, EXTENT / 2, N)
    X, Y = np.meshgrid(g, g, indexing="ij")
    pts = np.column_stack([X.ravel(), Y.ravel(), z.ravel()])
    # normals from local plane fits, the same way a mesh would supply them
    tree = cKDTree(pts)
    _, idx = tree.query(pts, k=9, workers=-1)
    nb = pts[idx] - pts[idx].mean(axis=1, keepdims=True)
    cov = np.einsum("nki,nkj->nij", nb, nb)
    ev = np.linalg.eigh(cov)[1][:, :, 0]
    ev *= np.sign(ev[:, 2])[:, None]

    keep = rng.choice(len(pts), 120000, replace=False)
    faces = [(pts[keep], ev[keep])]
    tex = []
    for R in RADII_V2:
        st = probe_faces(faces, R, 6000, rng)
        tex.append(None if st is None else st["texture"])
        print("  H=" + format(H, ".1f") + "  R " + format(R, "5.2f") +
              ("  no probes" if st is None else
               "  texture " + format(st["texture"], ".5f") +
               "  off-face " + format(100 * st["off_face"], "4.1f") + "%" +
               "  aspect " + format(st["aspect"], ".2f")))
    e, n = fit_exponent(RADII_V2, tex)
    print("  H=" + format(H, ".1f") + "  ->  RECOVERED EXPONENT " +
          format(e, ".3f") + "   (truth " + format(H, ".2f") + ", " +
          str(n) + " radii)")
    print("")
