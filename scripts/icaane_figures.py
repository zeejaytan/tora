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
  fig5  the ranker's top five as the conservator saw them blind (rank1..5.ply), with an
        arrow on each sherd turned more than 90 degrees from home
  rabati a contact sheet of Rabati per-sherd meshes (--rabati-glob), to choose the sherd
        whose break replaces the juglet's in Fig 2; then --rabati-mesh draws that Fig 2

Review of 2026-10-22 (ICAANE paper thread): Figs 3-5 are drawn mouth up, the
archaeological convention (the earlier renders had the juglet neck down); Fig 5 marks the
turned sherd, which at print size was invisible; Fig 2 can take a Rabati sherd.

THE RENDERER is a point splat with a depth buffer: each surface is sampled densely by
area, projected orthographically, the nearest sample wins each pixel, and it is shaded by
its face normal. No GPU and no extra package. Orthographic, so the scale bar holds
everywhere in the panel.

Every geometric claim is checked, not assumed, and printed: the reference's longest side
against the juglet's 65 mm; the genuine attempt scoring 9 of 9 right way round; the
attempt frame matching the reference frame. A failed check stops the figure.

Usage (Spartan, CPU node; scripts/hpc/icaane_figures.slurm):
  python scripts/icaane_figures.py --bundles .../rank_u17/juglet_32107634/bundles --key .../key/idmap.json \
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


def tilt(R, deg):
    """Rotate a camera basis about its own right axis (look down onto the piece)."""
    t = np.radians(deg)
    r = np.array([[1, 0, 0], [0, np.cos(t), -np.sin(t)], [0, np.sin(t), np.cos(t)]])
    return r @ R


def upright(R, H, neck):
    """Mouth up, as pottery is drawn: flip the camera's up if the neck sherd sits below
    the vessel's centre (frame() picks the long axis with an arbitrary sign)."""
    if (H[neck].mean(0) - np.concatenate(H).mean(0)) @ R[1] < 0:
        R = R * np.array([[-1], [-1], [1]])
    return R


def turn_deg(h, p):
    """How far a placed sherd is turned from home, in degrees (one-to-one points)."""
    r, _ = kabsch(h, p)
    return float(np.degrees(np.arccos(np.clip((np.trace(r) - 1) / 2, -1, 1))))


def render(meshes, greys, R, mm_per_px, light=(-0.45, 0.6, 0.66), pad_mm=3.0, seed=0,
           with_frame=False):
    """meshes: list of (V, F) in mm. Returns a float image in [0, 1] (1 = white), and with
    with_frame also a function taking points (mm) to pixel (x, y) in that image."""
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
    if with_frame:
        def to_px(Q):
            Q = np.atleast_2d(Q) @ R.T
            return np.stack([(Q[:, 0] - lo[0]) / mm_per_px, (hi[1] - Q[:, 1]) / mm_per_px], 1)
        return img, to_px
    return img


def scale_bar(ax, img, mm_per_px, mm=10.0):
    H, W = img.shape
    L = mm / mm_per_px
    x0, y0 = W - L - 0.04 * W, H - 0.05 * H
    ax.plot([x0, x0 + L], [y0, y0], color="black", lw=2, solid_capstyle="butt")
    ax.text(x0 + L / 2, y0 - 0.02 * H, f"{mm:g} mm", ha="center", va="bottom", fontsize=7)


def panel_row(path, imgs, titles, mm_per_px, height_cm, marks=None):
    # pad every panel to one height, so all are drawn at one scale (job 33142284 fitted
    # each to its own box, and the juglet panel of Fig 2 came out at two-thirds scale)
    h = max(i.shape[0] for i in imgs)
    tops = [h - i.shape[0] for i in imgs]
    imgs = [np.vstack([np.ones((h - i.shape[0], i.shape[1])), i]) for i in imgs]
    fig, axs = plt.subplots(1, len(imgs), figsize=(WIDTH_CM * CM, height_cm * CM),
                            gridspec_kw=dict(width_ratios=[i.shape[1] for i in imgs]))
    axs = np.atleast_1d(axs)
    for k, (ax, im, t) in enumerate(zip(axs, imgs, titles)):
        ax.imshow(im, cmap="gray", vmin=0, vmax=1, interpolation="lanczos")
        ax.set_title(t, fontsize=7.5)
        ax.axis("off")
        scale_bar(ax, im, mm_per_px)
        for (x, y) in (marks[k] if marks else []):
            # black arrow with a white edge, from the upper left, so it reads in greyscale
            L = 0.22 * im.shape[1]
            ax.annotate("", xy=(x, y + tops[k]), xytext=(x - L, y + tops[k] - L),
                        arrowprops=dict(arrowstyle="-|>", color="black", lw=1.6,
                                        mutation_scale=10, shrinkB=2))
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


def kabsch(a, b):
    """Rotation r and shift t with a @ r.T + t closest to b (point i matches point i)."""
    ca, cb = a.mean(0), b.mean(0)
    u, _, vt = np.linalg.svd((a - ca).T @ (b - cb))
    d = np.sign(np.linalg.det(vt.T @ u.T))
    r = vt.T @ np.diag([1, 1, d]) @ u.T
    return r, cb - r @ ca


def load_reference(hdf5, obj):
    """The juglet's scans as they sit in the reference reassembly (the key side), in mm."""
    import h5py
    with h5py.File(hdf5, "r") as f:
        g = f[obj]["pieces"]
        scans = [(g[str(i)]["vertices"][:].astype(float), g[str(i)]["faces"][:].astype(np.int64))
                 for i in range(len(g))]
    side = float(np.ptp(np.concatenate([v for v, _ in scans]), 0).max())
    s = POT_MM / side
    print(f"reference: {len(scans)} sherds from {obj}, longest side {side:.4f} -> {POT_MM:g} mm")
    return [v * s for v, _ in scans]


def load_sherds(bundles, H):
    """The ranker's neutral sherds (each centred and turned at random, in mm). Their
    vertices are the reference scans' vertices in the same order, so each one maps onto
    its home exactly; that is checked here."""
    z = np.load(bundles / "sherds.npz")
    k = int(z["k"])
    V = [z[f"v{j}"].astype(float) for j in range(k)]
    F = [z[f"f{j}"].astype(np.int64) for j in range(k)]
    if k != len(H) or any(len(v) != len(h) for v, h in zip(V, H)):
        sys.exit("CHECK FAILED: sherds.npz and the reference scans differ in vertex counts")
    res = []
    for v, h in zip(V, H):
        r, t = kabsch(v, h)
        res.append(float(np.abs(v @ r.T + t - h).max()))
    print(f"neutral sherds onto their homes: worst vertex {max(res):.3f} mm")
    if max(res) > 0.1:
        sys.exit("CHECK FAILED: a neutral sherd does not map onto its home; vertex order differs")
    return V, F


def attempt_file(bundles, aid):
    """The ranker writes sherds.npz beside a bundles/ folder of one npz per attempt."""
    for p in (bundles / "bundles" / f"{aid}.npz", bundles / f"{aid}.npz"):
        if p.exists():
            return p
    sys.exit(f"attempt {aid} not found under {bundles}")


def anchor_of(H, F):
    """The largest sherd by area: the one each method holds in its true place."""
    def area(v, f):
        return float(0.5 * np.linalg.norm(np.cross(v[f[:, 1]] - v[f[:, 0]],
                                                   v[f[:, 2]] - v[f[:, 0]]), axis=1).sum())
    return int(np.argmax([area(h, f) for h, f in zip(H, F)]))


def home_frame(P, H, anchor):
    """Undo the ranker's random move of the whole attempt: put its anchor back home."""
    r, t = kabsch(P[anchor], H[anchor])
    return [p @ r.T + t for p in P]


def placed(V, bundle, H, anchor):
    b = np.load(bundle)
    P = [v @ R.T + t for v, R, t in zip(V, b["R"].astype(float), b["t"].astype(float))]
    return home_frame(P, H, anchor)


def right_way(H, P):
    """Per sherd: median offset from its own home points under 4.6 mm (one-to-one points)."""
    return [float(np.median(np.linalg.norm(p - h, axis=1))) < SEAT_MM for h, p in zip(H, P)]


# ---------------------------------------------------------------- figures

def fig3(V, F, out, mpp):
    """V here is the reference: the sherds in their home places."""
    allv = np.concatenate(V)
    neck = anchor_of(V, F)
    R = upright(frame(allv), V, neck)
    print(f"fig3: neck sherd (largest) {neck}; drawn mouth up")
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


def fig4(V, H, F, bundles, key, out, mpp):
    idmap = json.loads(key.read_text())
    gen = [a for a, m in idmap.items()
           if GENUINE[0] in str(m["run"]) and int(m["attempt"]) == GENUINE[1]]
    if len(gen) != 1:
        sys.exit(f"genuine attempt {GENUINE} found {len(gen)} times in the key")
    anc = anchor_of(H, F)
    Pg = placed(V, attempt_file(bundles, gen[0]), H, anc)
    rg = right_way(H, Pg)
    print(f"genuine {GENUINE}: right way round {sum(rg)}/9")
    if sum(rg) != len(V):
        sys.exit("CHECK FAILED: the genuine attempt does not score 9 of 9 here, so the "
                 "attempt frame is not the reference frame; no figure drawn")
    best = None
    for a, m in idmap.items():
        run = str(m["run"])
        if "_fresh_" not in run or "juglet" not in run:
            continue
        P = placed(V, attempt_file(bundles, a), H, anc)
        r = right_way(H, P)
        off = float(np.mean([np.median(np.linalg.norm(p - h, axis=1)) for h, p in zip(H, P)]))
        key = (sum(r), -off)
        if best is None or key > best[0]:
            best = (key, a, run, int(m["attempt"]), P, r)
    (_, a, run, t, Pc, rc) = best
    print(f"best clean attempt: {run} #{t}: right way round {sum(rc)}/9")
    R = upright(frame(np.concatenate(H)), H, anc)
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


def fig5(H, F, top5, out, mpp):
    """rank<N>.ply holds the nine placed sherds one after another, in sherds.npz order."""
    anc = anchor_of(H, F)
    R = upright(frame(np.concatenate(H)), H, anc)   # the reference's frame, the same for all five
    cuts = np.cumsum([0] + [len(h) for h in H])
    greys = np.linspace(0.62, 0.95, len(H))
    imgs, marks = [], []
    for n in range(1, 6):
        Vr, _, _ = read_ply(top5 / f"rank{n}.ply")
        if len(Vr) != cuts[-1]:
            sys.exit(f"CHECK FAILED: rank{n}.ply has {len(Vr)} vertices, sherds {cuts[-1]}")
        P = home_frame([Vr[a:b] for a, b in zip(cuts[:-1], cuts[1:])], H, anc)
        r = right_way(H, P)
        img, to_px = render(list(zip(P, F)), greys, R, mpp, with_frame=True)
        imgs.append(img)
        deg = [turn_deg(h, p) for h, p in zip(H, P)]
        turned = [i for i, d in enumerate(deg) if d > 90]
        marks.append([tuple(to_px(P[i].mean(0))[0]) for i in turned])
        print(f"rank {n}: right way round {sum(r)}/9 (key side, for the record only); "
              f"turns {', '.join(f'{d:.0f}' for d in deg)} deg; arrow on {turned}")
    panel_row(out / "icaanefig_fig5_top5.png", imgs, [f"{n}" for n in range(1, 6)], mpp, 4.5,
              marks=marks)


def bbad_fragment(path, target_mm, vessel_mm=POT_MM, thin=False, n_obj=30):
    """A piece of a several-piece break of a Breaking Bad vessel, scaled so the vessel is
    vessel_mm (Breaking Bad models have no real size), choosing the piece whose longest side
    is nearest the real sherd's: the largest piece was nearly the whole vase (job 33141486),
    which shows no break face. With thin (the conservator, 2026-10-22: "pick a thin sherd"),
    the search runs over up to n_obj vessels per category and takes the piece that is thinnest
    for its size: smallest ratio of its least to its greatest extent along its own principal
    axes (the most wall-like), plus half its relative size difference from the real sherd."""
    import h5py
    h = h5py.File(path, "r")
    root = h["everyday"] if "everyday" in h else h

    def verts(p):
        return np.asarray(p["vertices"] if "vertices" in p else p, float)

    def wall(v, f):
        """Mean wall thickness of a closed shell: twice its volume over its area."""
        a, b, c = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
        vol = abs(np.einsum("ij,ij->i", a, np.cross(b, c)).sum()) / 6
        area = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1).sum()
        return 2 * vol / max(area, 1e-12)

    def extents(v):
        c = v - v.mean(0)
        return np.sort(np.ptp(c @ np.linalg.svd(c, full_matrices=False)[2].T, 0))

    best = None
    # thin: curved wall pieces of closed forms only; a bowl base is a flat slab that reads
    # as a straight line when its break is turned to the viewer (job 33674664, conservator)
    for cat in (("Vase", "Bottle", "Jar") if thin else ("Vase", "Bottle", "Mug", "Cup", "Bowl")):
        if cat not in root:
            continue
        for name in sorted(root[cat].keys())[: (n_obj if thin else 1)]:
            obj = root[cat][name]
            for fr in sorted(obj.keys()):
                parts = [obj[fr][k] for k in sorted(obj[fr].keys())]
                if len(parts) < 6 or any("faces" not in p for p in parts if hasattr(p, "keys")):
                    continue
                s = vessel_mm / float(np.ptp(np.concatenate([verts(p) for p in parts]), 0).max())
                for p in parts:
                    e = extents(verts(p) * s)
                    gap = abs(e[-1] - target_mm) / target_mm
                    if thin:
                        if "faces" not in p or e[0] / e[-1] < 0.09:
                            continue          # flat, or no surface to measure
                        th = wall(verts(p) * s, np.asarray(p["faces"], np.int64))
                        score = th / e[-1] + 0.5 * gap + (0 if len(verts(p)) >= 1000 else 1)
                    else:
                        score = abs(e[-1] - target_mm)
                    if best is None or score < best[0]:
                        best = (score, cat, name, fr, len(parts), p, s, e)
                if not thin:
                    break
            if best is not None and not thin:
                break
        if best is not None and not thin:
            break
    if best is None:
        sys.exit("no several-piece vessel break found in the Breaking Bad file")
    _, cat, name, fr, n, p, s, e = best
    v = verts(p) * s
    f = np.asarray(p["faces"], np.int64) if "faces" in p else None
    print(f"Breaking Bad: {cat}/{name}/{fr}, {n} pieces, vessel scaled to {vessel_mm:g} mm; "
          f"piece {e[-1]:.1f} x {e[1]:.1f} x {e[0]:.1f} mm (thinness {e[0] / e[-1]:.2f}; "
          f"wall {wall(verts(p) * s, np.asarray(p['faces'], np.int64)) if 'faces' in p else float('nan'):.1f} mm; "
          f"real sherd {target_mm:.1f} mm), {len(v)} vertices, faces: {f is not None}")
    return v, f


def fig2(V, F, bbad, out, mpp):
    j = int(np.argmax([len(f) for f in F[1:]])) + 1    # largest sherd that is not the anchor
    vb, fb = bbad_fragment(bbad, float(np.ptp(V[j], 0).max()))
    if fb is None:
        print("fig2 skipped: the Breaking Bad file holds vertices only; a mesh source is needed")
        return
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


def load_any_mesh(path):
    import trimesh
    m = trimesh.load(path, force="mesh", process=False)
    return np.asarray(m.vertices, float), np.asarray(m.faces, np.int64)


def rabati_sheet(globs, out, mpp=0.15):
    """One raking view of each Rabati per-sherd mesh found, titled with its file and its
    longest side in file units, to choose Fig 2's sherd by eye. Units are printed, not
    assumed: a mesh is in mm only where scale_apply.py has run for its capture."""
    import glob
    paths = sorted({p for g in globs for p in glob.glob(g, recursive=True)})[:24]
    if not paths:
        print("rabati: no meshes matched", globs)
        return
    rows = []
    for p in paths:
        v, f = load_any_mesh(p)
        side = float(np.ptp(v, 0).max())
        scale = next((s for s in Path(p).parents if (s / "scale" / "SCALE.txt").exists()), None)
        print(f"rabati: {p}: {len(v)} vertices, {len(f)} faces, longest side {side:.3f} units; "
              f"scale/SCALE.txt {'at ' + str(scale) if scale else 'not found'}")
        s = 40.0 / side            # each drawn about 40 units wide, for choosing only
        img = render([(v * s, f)], [0.9], frame(v * s), mpp, light=(-0.92, 0.25, 0.3))
        rows.append((img, f"{Path(p).parent.parent.name}/{Path(p).name}  {side:.1f}"))
    n = len(rows)
    cols = 4
    fig, axs = plt.subplots((n + cols - 1) // cols, cols, figsize=(18 * CM, 4.5 * CM * ((n + cols - 1) // cols)))
    for ax in np.atleast_1d(axs).ravel():
        ax.axis("off")
    for ax, (img, t) in zip(np.atleast_1d(axs).ravel(), rows):
        ax.imshow(img, cmap="gray", vmin=0, vmax=1)
        ax.set_title(t, fontsize=6)
    fig.tight_layout(pad=0.3)
    fig.savefig(out / "icaanefig_rabati_sheet.png", dpi=150)
    plt.close(fig)
    print(f"-> {out / 'icaanefig_rabati_sheet.png'} (not to scale: for choosing only)")


VESSEL_MM = 250.0  # simulated vessel size for the Rabati comparison
BASE_MM = 190.0   # the turntable base's long side, 13 x 19 cm (MILo AGENTS.md: scale
                  # captures without SCALE.txt from the base)


def fig2_rabati(mesh, mm_per_unit, bbad, out, mpp, base=None):
    """Fig 2 with a Rabati sherd's break in place of the juglet's, both at one scale. With
    base (the 13 x 19 cm turntable base, split out of the same model) the scale is read
    from the base's long side instead of mm_per_unit."""
    if base is not None:
        vb0, _ = load_any_mesh(base)
        ext = np.sort(np.ptp((vb0 - vb0.mean(0)) @ np.linalg.svd(vb0 - vb0.mean(0), full_matrices=False)[2].T, 0))
        mm_per_unit = BASE_MM / ext[-1]
        print(f"base {base}: sides {ext[-1]:.4f} x {ext[-2]:.4f} units (ratio {ext[-2] / ext[-1]:.3f}, "
              f"13/19 = {13 / 19:.3f}) -> {mm_per_unit:.2f} mm per unit")
        if abs(ext[-2] / ext[-1] - 13 / 19) > 0.05:
            sys.exit("CHECK FAILED: the base's sides are not in the 13:19 ratio; not the base")
    v, f = load_any_mesh(mesh)
    v = v * mm_per_unit
    side = float(np.ptp(v, 0).max())
    print(f"rabati sherd {mesh}: longest side {side:.1f} mm at {mm_per_unit} mm per unit")
    # A Rabati sherd (79 mm) is larger than the whole juglet, so the simulated vessel is
    # scaled to a mid-sized Caucasus coarse-ware vessel (15-40 cm, CSC AGENTS.md) rather
    # than to the juglet; the caption says so (job 33674098 picked the whole 65 mm vase).
    vb, fb = bbad_fragment(bbad, side, vessel_mm=VESSEL_MM, thin=True)
    rake = (-0.92, 0.25, 0.3)
    # face on, then three-quarter views (turned 60 and 300 degrees and tipped 25 degrees),
    # which show the break face together with the curve of the wall
    views = (0, 60, 300)
    imgs, titles = [], []
    for (vv, ff), name in (((vb, fb), "simulated"), ((v, f), "Rabati")):
        R0 = frame(vv)
        for d in views:
            imgs.append(render([(vv, ff)], [0.9], tilt(turn(R0, d), 25 if d else 0), mpp, light=rake))
            titles.append(f"{d}°")
    n = len(views)
    panel_row(out / "icaanefig_fig2_rabati_views.png", imgs[n:], titles[n:], mpp, 4.5)
    panel_row(out / "icaanefig_fig2_simulated_views.png", imgs[:n], titles[:n], mpp, 4.5)
    for a, da in enumerate(views):
        for b, db in enumerate(views):
            if da and db:
                panel_row(out / f"icaanefig_fig2_breaks_s{da}_r{db}.png", [imgs[a], imgs[n + b]],
                          ["(a) simulated", "(b) real, worn (Rabati)"], mpp, 6.0)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bundles", type=Path, required=True)
    ap.add_argument("--key", type=Path, required=True, help="the ranker's key/idmap.json")
    ap.add_argument("--hdf5", type=Path, required=True, help="dataset/juglet_gt.hdf5")
    ap.add_argument("--object", default="juglet_gt/Juglet-000")
    ap.add_argument("--top5", type=Path, required=True)
    ap.add_argument("--bbad", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--only", default="2345")
    ap.add_argument("--rabati-glob", nargs="*", default=[],
                    help="Rabati per-sherd meshes for the contact sheet (only 'r')")
    ap.add_argument("--rabati-mesh", type=Path, help="the chosen Rabati sherd (only 'R')")
    ap.add_argument("--rabati-mm-per-unit", type=float, default=1.0)
    ap.add_argument("--rabati-base", type=Path, help="the turntable base mesh, to read the scale from")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    H = load_reference(a.hdf5, a.object)
    V, F = load_sherds(a.bundles, H)
    mpp = 0.08   # mm per pixel: a 65 mm juglet spans about 800 px, ample at 300 dpi
    if "3" in a.only:
        fig3(H, F, a.out, mpp)
    if "4" in a.only:
        fig4(V, H, F, a.bundles, a.key, a.out, mpp)
    if "5" in a.only:
        fig5(H, F, a.top5, a.out, mpp)
    if "2" in a.only:
        fig2(H, F, a.bbad, a.out, 0.04)
    if "r" in a.only:
        rabati_sheet(a.rabati_glob, a.out)
    if "R" in a.only and a.rabati_mesh:
        fig2_rabati(a.rabati_mesh, a.rabati_mm_per_unit, a.bbad, a.out, 0.08, a.rabati_base)
    return 0


if __name__ == "__main__":
    sys.exit(main())
