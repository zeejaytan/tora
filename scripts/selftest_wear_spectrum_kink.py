import sys
import numpy as np
from scipy.ndimage import gaussian_filter
from scipy.spatial import cKDTree
sys.path.insert(0, "scripts")
from selftest_wear_spectrum_exponent import fbm_surface, EXTENT, N
from wear_fracture_spectrum import probe_faces

LADDER = [0.80, 1.60, 3.20, 6.40]
REPAIR = {0.80: 0.0049, 1.60: 0.0197, 3.20: 0.0685, 6.40: 0.2091}
rng = np.random.default_rng(0)
grid = EXTENT / N
step = max(1, int(round(0.267 / grid)))
z0 = fbm_surface(0.5)


def cloud(z):
    g = np.linspace(-EXTENT / 2, EXTENT / 2, N)[::step]
    X, Y = np.meshgrid(g, g, indexing="ij")
    p = np.column_stack([X.ravel(), Y.ravel(), z[::step, ::step].ravel()])
    _, idx = cKDTree(p).query(p, k=9, workers=-1)
    nb = p[idx] - p[idx].mean(axis=1, keepdims=True)
    ev = np.linalg.eigh(np.einsum("nki,nkj->nij", nb, nb))[1][:, :, 0]
    ev *= np.sign(ev[:, 2])[:, None]
    return p, ev


def report(label, tex):
    r = np.log(np.array(LADDER))
    t = np.log(np.array(tex))
    p = np.polyfit(r, t, 1)
    resid = t - np.polyval(p, r)
    r2 = 1.0 - np.sum(resid ** 2) / np.sum((t - t.mean()) ** 2)
    seg = np.diff(t) / np.diff(r)
    print(label.ljust(30) + "slope " + format(p[0], "6.3f") +
          "  R2 " + format(r2, ".4f") + "  segments " +
          "  ".join(format(x, ".2f") for x in seg))


print("ladder mm: " + ", ".join(format(r, ".2f") for r in LADDER))
print("")
report("RePAIR, published", [REPAIR[r] for r in LADDER])
print("")
for sig in [0.0, 0.10, 0.20, 0.30, 0.50, 0.80]:
    z = z0 if sig <= 0 else gaussian_filter(z0, sig / grid, mode="wrap")
    p, ev = cloud(z)
    tex = [probe_faces([(p, ev)], R, 2000, rng)["texture"] for R in LADDER]
    report("known fresh H=0.5, sigma " + format(sig, ".2f"), tex)
