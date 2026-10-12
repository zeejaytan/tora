"""Synthetic ring for the overlap gate (U17 Revision 6 check): 8 sherds, 100 mm across, 6 mm wall,
written as bundles (correct, pressed, pressed_hard, half_over, across) for overlap_measure.py.

Usage: python scripts/overlap_synthetic.py OUTDIR && python scripts/overlap_measure.py --bundles OUTDIR --out ov.json
"""
import sys, json
from pathlib import Path
import numpy as np
O = Path(sys.argv[1]); (O / "bundles").mkdir(parents=True, exist_ok=True)
R0, H, W = 50.0, 60.0, 6.0          # radius, height, wall (mm); pot ~ 100 mm
def shell(a0, a1, h0, h1, na=24, nh=16):
    """closed wall segment between angles a0..a1 and heights h0..h1"""
    A = np.linspace(a0, a1, na); Z = np.linspace(h0, h1, nh)
    v, idx = [], {}
    for s, r in enumerate((R0, R0 - W)):
        for i, a in enumerate(A):
            for j, z in enumerate(Z):
                idx[s, i, j] = len(v); v.append((r * np.cos(a), r * np.sin(a), z))
    f = []
    def q(a, b, c, d, flip):
        f.extend([(a, b, c), (a, c, d)] if not flip else [(a, c, b), (a, d, c)])
    for i in range(na - 1):
        for j in range(nh - 1):
            q(idx[0, i, j], idx[0, i + 1, j], idx[0, i + 1, j + 1], idx[0, i, j + 1], False)
            q(idx[1, i, j], idx[1, i + 1, j], idx[1, i + 1, j + 1], idx[1, i, j + 1], True)
    for i in range(na - 1):   # bottom/top
        q(idx[0, i, 0], idx[1, i, 0], idx[1, i + 1, 0], idx[0, i + 1, 0], False)
        q(idx[0, i, nh-1], idx[0, i + 1, nh-1], idx[1, i + 1, nh-1], idx[1, i, nh-1], False)
    for j in range(nh - 1):   # the two break faces
        q(idx[0, 0, j], idx[0, 0, j + 1], idx[1, 0, j + 1], idx[1, 0, j], False)
        q(idx[0, na-1, j], idx[1, na-1, j], idx[1, na-1, j + 1], idx[0, na-1, j + 1], False)
    v, f = np.array(v), np.array(f)
    vol = np.einsum("ij,ij->i", v[f[:, 0]], np.cross(v[f[:, 1]], v[f[:, 2]])).sum() / 6
    if vol < 0: f = f[:, ::-1]
    return v, f
K = 8; step = 2 * np.pi / K
sh = [shell(k * step, (k + 1) * step, 0, H) for k in range(K)]
z = {"k": K, "pot_mm": 100.0}
for j, (v, f) in enumerate(sh): z[f"v{j}"], z[f"f{j}"] = v, f
np.savez(O / "sherds.npz", **z)
I = np.eye(3)
def rotz(a): c, s = np.cos(a), np.sin(a); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
def save(name, R, t): np.savez(O / "bundles" / f"{name}.npz", R=np.array(R, np.float32), t=np.array(t, np.float32))
Rs, ts = [I] * K, [np.zeros(3)] * K
save("correct", Rs, ts)
# every join pressed: each sherd rotated 1.5% of its span toward its neighbour (~0.6 mm at the rim)
save("pressed", [rotz(0.015 * step * (1 if k % 2 else -1)) for k in range(K)], ts)
# long deep seam press: each sherd rotated 0.04 rad toward neighbour (~2 mm), all along the 60 mm seam
save("pressed_hard", [rotz(0.04 * (1 if k % 2 else -1)) for k in range(K)], ts)
# sherd 0 slid half over sherd 1 (rotated half a span)
save("half_over", [rotz(0.5 * step)] + [I] * (K - 1), ts)
# sherd 0 lifted and laid inward across the pot to cross sherd 4's wall
R0m = rotz(np.pi * 0.9); save("across", [R0m] + [I] * (K - 1), [np.array([0, 0, 10.0])] + [np.zeros(3)] * (K - 1))
