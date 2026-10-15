"""Draft figures 2-5 of the ICAANE 2027 paper, as greyscale shaded renders with scale bars.

Asked for by the conservator (2026-10-15, ICAANE paper thread, "do 1"): the paper's
figures must read in greyscale, carry a scale bar and print at 13 cm wide (photographs at
300 dpi). The existing pictures are diagnostic point clouds coloured by right and wrong,
which give the answer away and fail the greyscale rule. This draws the same geometry as
shaded surfaces, one grey per sherd, with a dark line where two sherds meet.

  fig2  a simulated break (Breaking Bad) beside a real worn break (a juglet sherd), same
        scale, raking light, three views each -- a draft to choose the view from
  fig3  the juglet's nine sherds laid apart, and the reference reassembly
  fig4  GARF's best clean-trained attempt beside the full reassembly from rough training
        (rough 1x, seed 42, job 31835635, presentation 1, attempt 19); sherds placed the
        right way round light, the rest dark
  fig5  the ranker's top five as the conservator saw them blind (rank1..5.ply)

THE RENDERER is a point splat with a depth buffer: each surface is sampled densely by
area, projected orthographically, the nearest sample wins each pixel, and it is shaded by
its face normal. No GPU and no extra package. Orthographic, so the scale bar holds
everywhere in the panel.

Every geometric claim is checked, not assumed, and printed: the reference's longest side
against the juglet's 65 mm; the genuine attempt scoring 9 of 9 right way round; the
attempt frame matching the reference frame. A failed check stops the figure.

Usage (Spartan, CPU node; scripts/hpc/icaane_figures.slurm):
  python scripts/icaane_figures.py --bundles .../rank_u17/juglet_32107634 \
      --top5 .../rank_u17/jug_top5 --bbad dataset/breaking_bad_vol.hdf5 --out DIR
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))

POT_MM = 65.0          # the juglet's longest side (juglet-sfs ticket 01 scale)
SEAT_MM = 4.6          # right way round: median point offset under this (Section 3)
CM = 1 / 2.54
WIDTH_CM = 13.0        # print area width
DPI = 300
GENUINE = ("noise_d100_ds1_juglet_gt_31835635", 19)


# ---------------------------------------------------------------- geometry

def area_sample(V, F, n_per_mm2, rng):
    """Points on a mesh, area-weighted, with their face normals."""
    a, b, c = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    cr = np.cross(b - a, c - a)
    ar = 0.5 * np.linalg.norm(cr, axis=1)
    nrm = cr / np.maximum(2 * ar[:, None], 1e-12)
    n = int(max(1000, ar.sum() * n_per_mm2))
    f = rng.choice(len(F), n, p=ar / ar.sum())
    u, v = rng.random(n), rng.random(n)
    flip = u + v > 1
    u[flip], v[flip] = 1 - u[flip], 1 - v[flip]
    P = a[f] + u[:, None] * (b[f] - a[f]) + v[:, None] * (c[f] - a[f])
    return P, nrm[f]


def frame(P):
    """Camera basis from a point set: rows = (right, up, towards viewer); up = long axis."""
    c = P.mean(0)
    e = np.linalg.svd(P - c, full_matrices=False)[2]
    up, right = e[0], e[1]
    return np.stack([right, up, np.cross(right, up)])


def turn(R, deg):
    """Rotate a camera basis about its own up axis."""
    t = np.radians(deg)
    r = np.array([[np.cos(t), 0, np.sin(t)], [0, 1, 0], [-np.sin(t), 0, np.cos(t)]])
    return r @ R


def render(meshes, greys, R, mm_per_px, light=(-0.45, 0.6, 0.66), pad_mm=3.0, seed=0):
    """meshes: list of (V, F) in mm. Returns a float image in [0, 1] (1 = white)."""
    rng = np.random.default_rng(seed)
    dens = 6.0 / mm_per_px ** 2          # about six samples per pixel
    Ps, Ns, Is = [], [], []
    for j, (V, F) in enumerate(meshes):
        P, N = area_sample(V, F, dens, rng)
        Ps.append(P @ R.T)
        Ns.append(N @ R.T)
        Is.append(np.full(len(P), j))
    P, N, I = np.concatenate(Ps), np.concatenate(Ns), np.concatenate(Is)
    lo = P[:, :2].min(0) - pad_mm
    hi = P[:, :2].max(0) + pad_mm
    W, H = (np.ceil((hi - lo) / mm_per_px)).astype(int)
    x = ((P[:, 0] - lo[0]) / mm_per_px).astype(int)
    y = ((hi[1] - P[:, 1]) / mm_per_px).astype(int)
    pix = y * W + x
    order = np.lexsort((-P[:, 2], pix))          # nearest first within each pixel
    pix_s = pix[order]
    first = np.r_[True, pix_s[1:] != pix_s[:-1]]
    win = order[first]
    l = np.asarray(light, float)
    l /= np.linalg.norm(l)
    shade = 0.22 + 0.78 * np.abs(N[win] @ l)     # two-sided: some meshes face inward
    alb = np.asarray(greys, float)[I[win]]
    img = np.ones(W * H)
    ids = np.full(W * H, -1)
    dep = np.full(W * H, -np.inf)
    img[pix[win]] = shade * alb
    ids[pix[win]] = I[win]
    dep[pix[win]] = P[win, 2]
    img, ids, dep = img.reshape(H, W), ids.reshape(H, W), dep.reshape(H, W)
    # a pixel that missed the near surface shows the far one through it: if at least
    # three of its four neighbours are more than 1 mm nearer, take the nearest of them
    for _ in range(2):
        nbs = [(np.roll(dep, s, a), np.roll(img, s, a), np.roll(ids, s, a))
               for s, a in ((1, 0), (-1, 0), (1, 1), (-1, 1))]
        nearer = sum((d > dep + 1.0).astype(int) for d, _, _ in nbs)
        best = np.argmax(np.stack([d for d, _, _ in nbs]), 0)
        fix = nearer >= 3
        for k, (d, im, i) in enumerate(nbs):
            m = fix & (best == k)
            dep[m], img[m], ids[m] = d[m], im[m], i[m]
    # one-pixel holes between samples: fill from the nearest covered neighbour
    hole = ids < 0
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        nb_ids = np.roll(ids, (dy, dx), (0, 1))
        nb_img = np.roll(img, (dy, dx), (0, 1))
        inner = hole & (nb_ids >= 0) & (np.roll(ids, (-dy, -dx), (0, 1)) >= 0)
        img[inner], ids[inner] = nb_img[inner], nb_ids[inner]
        hole = ids < 0
    # dark line where two sherds meet, and round the outline
    edge = np.zeros_like(hole)
    for dy, dx in ((0, 1), (1, 0)):
        nb = np.roll(ids, (dy, dx), (0, 1))
        edge |= (nb != ids)
    img[edge & ((ids >= 0) | (np.roll(ids, (1, 1), (0, 1)) >= 0))] = 0.1
    return img


def scale_bar(ax, img, mm_per_px, mm=10.0):
    H, W = img.shape
    L = mm / mm_per_px
    x0, y0 = W - L - 0.04 * W, H - 0.05 * H
    ax.plot([x0, x0 + L], [y0, y0], color="black", lw=2, solid_capstyle="butt")
    ax.text(x0 + L / 2, y0 - 0.02 * H, f"{mm:g} mm", ha="center", va="bottom", fontsize=7)


def panel_row(path, imgs, titles, mm_per_px, height_cm):
    fig, axs = plt.subplots(1, len(imgs), figsize=(WIDTH_CM * CM, height_cm * CM),
                            gridspec_kw=dict(width_ratios=[i.shape[1] for i in imgs]))
    axs = np.atleast_1d(axs)
    for ax, im, t in zip(axs, imgs, titles):
        ax.imshow(im, cmap="gray", vmin=0, vmax=1, interpolation="lanczos")
        ax.set_title(t, fontsize=7.5)
        ax.axis("off")
        scale_bar(ax, im, mm_per_px)
    fig.tight_layout(pad=0.3)
    fig.savefig(path, dpi=DPI)
    plt.close(fig)
    print(f"-> {path}")


# ---------------------------------------------------------------- data

def read_ply(path):
    """Binary PLY as written by u17_top5_export.py: xyz float, rgb uchar, triangle faces."""
    raw = Path(path).read_bytes()
    end = raw.index(b"end_header\n") + len(b"end_header\n")
    head = raw[:end].decode().split("\n")
    nv = int(next(h for h in head if h.startswith("element vertex")).split()[-1])
    nf = int(next(h for h in head if h.startswith("element face")).split()[-1])
    vt = np.frombuffer(raw, [("x", "<f4"), ("y", "<f4"), ("z", "<f4"),
                             ("r", "u1"), ("g", "u1"), ("b", "u1")], nv, end)
    ft = np.frombuffer(raw, [("n", "u1"), ("i", "<i4", 3)], nf, end + vt.nbytes)
    V = np.stack([vt["x"], vt["y"], vt["z"]], 1).astype(float)
    C = np.stack([vt["r"], vt["g"], vt["b"]], 1)
    return V, ft["i"].astype(np.int64), C


def split_by_colour(V, F, C):
    """One mesh per sherd: the export gives every sherd its own fixed colour."""
    key = C[:, 0].astype(int) * 65536 + C[:, 1].astype(int) * 256 + C[:, 2]
    out = []
    for k in np.unique(key):
        m = key[F[:, 0]] == k
        out.append((V, F[m]))
    return out


def load_sherds(bundles):
    z = np.load(bundles / "sherds.npz")
    k = int(z["k"])
    V = [z[f"v{j}"].astype(float) for j in range(k)]
    F = [z[f"f{j}"].astype(np.int64) for j in range(k)]
    side = float(np.ptp(np.concatenate(V), 0).max())
    print(f"reference: {k} sherds, longest side {side:.2f} (units of sherds.npz)")
    if abs(side - POT_MM) > 0.05 * POT_MM:
        s = POT_MM / side
        print(f"  not {POT_MM:g} mm: scaling by {s:.4f} to millimetres")
        V = [v * s for v in V]
    return V, F


def placed(V, bundle):
    b = np.load(bundle)
    return [v @ R.T + t for v, R, t in zip(V, b["R"].astype(float), b["t"].astype(float))]


def right_way(V, P):
    """Per sherd: median offset from its own home points under 4.6 mm (one-to-one points)."""
    return [float(np.median(np.linalg.norm(p - v, axis=1))) < SEAT_MM for v, p in zip(V, P)]


# ---------------------------------------------------------------- figures

def fig3(V, F, out, mpp):
    allv = np.concatenate(V)
    R = frame(allv)
    c = allv.mean(0)
    greys = np.linspace(0.62, 0.95, len(V))
    apart = []
    for v, f in zip(V, F):
        d = v.mean(0) - c
        apart.append((v + 0.9 * d, f))       # laid apart along the line from the centre
    ref = list(zip(V, F))
    panel_row(out / "icaanefig_fig3_juglet.png",
              [render(apart, greys, R, mpp), render(ref, greys, R, mpp)],
              ["(a) the nine sherds", "(b) the reference reassembly"], mpp, 7.5)


def fig4(V, F, bundles, out, mpp):
    idmap = json.loads((bundles / "key" / "idmap.json").read_text())
    gen = [a for a, m in idmap.items()
           if GENUINE[0] in str(m["run"]) and int(m["attempt"]) == GENUINE[1]]
    if len(gen) != 1:
        sys.exit(f"genuine attempt {GENUINE} found {len(gen)} times in the key")
    Pg = placed(V, bundles / "bundles" / f"{gen[0]}.npz")
    rg = right_way(V, Pg)
    print(f"genuine {GENUINE}: right way round {sum(rg)}/9")
    if sum(rg) != len(V):
        sys.exit("CHECK FAILED: the genuine attempt does not score 9 of 9 here, so the "
                 "attempt frame is not the reference frame; no figure drawn")
    best = None
    for a, m in idmap.items():
        run = str(m["run"])
        if "_fresh_" not in run or "juglet" not in run:
            continue
        P = placed(V, bundles / "bundles" / f"{a}.npz")
        r = right_way(V, P)
        off = float(np.mean([np.median(np.linalg.norm(p - v, axis=1)) for v, p in zip(V, P)]))
        key = (sum(r), -off)
        if best is None or key > best[0]:
            best = (key, a, run, int(m["attempt"]), P, r)
    (_, a, run, t, Pc, rc) = best
    print(f"best clean attempt: {run} #{t}: right way round {sum(rc)}/9")
    R = frame(np.concatenate(V))
    imgs, titles = [], []
    for P, r, name in ((Pc, rc, "clean"), (Pg, rg, "rough")):
        greys = [0.92 if ok else 0.45 for ok in r]
        meshes = list(zip(P, F))
        imgs += [render(meshes, greys, R, mpp), render(meshes, greys, turn(R, 90), mpp)]
        titles += [f"{name}: {sum(r)} of 9", f"{name}, turned 90°"]
    panel_row(out / "icaanefig_fig4_clean_vs_full.png", imgs, titles, mpp, 6.0)
    (out / "icaanefig_fig4_attempts.json").write_text(json.dumps(dict(
        clean=dict(run=run, attempt=t, right_way=sum(rc)),
        genuine=dict(run=GENUINE[0], attempt=GENUINE[1], right_way=sum(rg))), indent=2))


def fig5(V, top5, out, mpp):
    R = frame(np.concatenate(V))      # the reference's own frame, the same for all five
    imgs = []
    for n in range(1, 6):
        Vr, Fr, C = read_ply(top5 / f"rank{n}.ply")
        sh = split_by_colour(Vr, Fr, C)
        greys = np.linspace(0.62, 0.95, len(sh))
        imgs.append(render(sh, greys, R, mpp))
        print(f"rank {n}: {len(sh)} sherds, box {np.ptp(Vr, 0).round(1)} mm")
    panel_row(out / "icaanefig_fig5_top5.png", imgs, [f"{n}" for n in range(1, 6)], mpp, 4.5)


def bbad_fragment(path):
    """The largest piece of a several-piece break of a Breaking Bad vase, in mm at the
    juglet's 65 mm, with faces if the file holds them."""
    import h5py
    h = h5py.File(path, "r")
    root = h["everyday"] if "everyday" in h else h
    for cat in ("Vase", "Bottle", "Mug", "Cup", "Bowl"):
        if cat not in root:
            continue
        obj = root[cat][sorted(root[cat].keys())[0]]
        for fr in sorted(obj.keys()):
            if len(obj[fr].keys()) >= 4:
                parts = [obj[fr][k] for k in sorted(obj[fr].keys())]
                allv = np.concatenate([np.asarray(p["vertices"] if "vertices" in p else p)
                                       for p in parts])
                s = POT_MM / float(np.ptp(allv, 0).max())
                big = max(parts, key=lambda p: len(p["vertices"] if "vertices" in p else p))
                v = np.asarray(big["vertices"] if "vertices" in big else big, float) * s
                f = np.asarray(big["faces"], np.int64) if "faces" in big else None
                print(f"Breaking Bad: {cat}/{obj.name.split('/')[-1]}/{fr}, "
                      f"{len(parts)} pieces, largest {len(v)} vertices, faces: {f is not None}")
                return v, f
    sys.exit("no several-piece vessel break found in the Breaking Bad file")


def fig2(V, F, bbad, out, mpp):
    vb, fb = bbad_fragment(bbad)
    if fb is None:
        print("fig2 skipped: the Breaking Bad file holds vertices only; a mesh source is needed")
        return
    j = int(np.argmax([len(f) for f in F[1:]])) + 1    # largest sherd that is not the anchor
    rake = (-0.92, 0.25, 0.3)
    imgs, titles = [], []
    for (v, f), name in (((vb, fb), "simulated"), ((V[j], F[j]), f"juglet sherd {j}")):
        R0 = frame(v)
        for d in (0, 60, 120):
            imgs.append(render([(v, f)], [0.9], turn(R0, d), mpp, light=rake))
            titles.append(f"{name}, {d}°")
    half = len(imgs) // 2
    panel_row(out / "icaanefig_fig2_simulated_views.png", imgs[:half], titles[:half], mpp, 4.5)
    panel_row(out / "icaanefig_fig2_juglet_views.png", imgs[half:], titles[half:], mpp, 4.5)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bundles", type=Path, required=True)
    ap.add_argument("--top5", type=Path, required=True)
    ap.add_argument("--bbad", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--only", default="2345")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    V, F = load_sherds(a.bundles)
    mpp = 0.08   # mm per pixel: a 65 mm juglet spans about 800 px, ample at 300 dpi
    if "3" in a.only:
        fig3(V, F, a.out, mpp)
    if "4" in a.only:
        fig4(V, F, a.bundles, a.out, mpp)
    if "5" in a.only:
        fig5(V, a.top5, a.out, mpp)
    if "2" in a.only:
        fig2(V, F, a.bbad, a.out, 0.04)
    return 0


if __name__ == "__main__":
    sys.exit(main())
