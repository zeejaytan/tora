"""Look at the U10 training files: the renders the audit's numbers need -- ticket 02.

Everything is drawn from the finished files, never from CSC's own outputs, so what is
seen is what TORA will be given. Three figures:

  u10_look_juglet.png    a ceiling training breakage, put back together from the file,
                         beside the Juglet from juglet_gt.hdf5, both in the units TORA
                         reads (max |coord| 0.5) on the same axes. Same size is the claim.
  u10_look_forms.png     three ceiling vessels and one of each generic form, same axes.
  u10_look_sections.png  cuts through the vessel's axis, each sherd its own colour, black
                         where the cut crosses a break face. Top: whole pot at 10 mm.
                         Bottom: a 7 mm window of wall with a 0.5 mm bar, which resolves a
                         wall of 1.6-2.5 mm and a gap or overlap at a join of 0.1 mm. The
                         vessels are the thinnest-walled and the thickest-walled in the
                         audit report, and the sherd the audit read as thickest -- the
                         handle, where a lump would show if there were one.

    python scripts/render_u10_trainset.py --report <audit report.json> --juglet <juglet_gt.hdf5> \
        --outdir <dir> <u10_ceiling.hdf5> <u10_generic.hdf5>
"""
import argparse
import json
from pathlib import Path

import h5py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import trimesh  # noqa: E402
from matplotlib.collections import LineCollection  # noqa: E402
from scipy.spatial import cKDTree  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402

LIGHT = np.array([0.4, -0.6, 0.7]) / np.linalg.norm([0.4, -0.6, 0.7])


def pieces(group):
    g = group["pieces"] if "pieces" in group else group
    return [(np.asarray(g[k]["vertices"][:], float), np.asarray(g[k]["faces"][:], np.int64))
            for k in sorted(g.keys())]


def upright(P):
    """For a pot of unknown orientation: the axis is the direction whose spread differs
    most from the other two (a wheel-made shape spreads alike across its axis)."""
    allV = np.concatenate([V for V, _ in P])
    c = allV.mean(0)
    w, U = np.linalg.eigh(np.cov((allV - c).T))
    k = int(np.argmax([abs(w[i] - np.mean(np.delete(w, i))) for i in range(3)]))
    ax = U[:, k]
    e1 = U[:, (k + 1) % 3]
    R = np.stack([e1, np.cross(ax, e1), ax])
    return [((V - c) @ R.T, F) for V, F in P]


def shade(ax, P, title, lim=0.55):
    polys, cols = [], []
    for i, (V, F) in enumerate(P):
        t = V[F]
        n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
        n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
        base = np.array(plt.cm.tab20(i % 20)[:3])
        cols.append(np.clip(base[None] * (0.35 + 0.65 * np.abs(n @ LIGHT))[:, None], 0, 1))
        polys.append(t)
    ax.add_collection3d(Poly3DCollection(np.concatenate(polys), facecolors=np.concatenate(cols),
                                         edgecolors="none", linewidths=0))
    for f in (ax.set_xlim, ax.set_ylim, ax.set_zlim):
        f(-lim, lim)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=15, azim=-60)
    ax.set_title(title, fontsize=8)
    ax.tick_params(labelsize=5)


def axis_xy(P):
    """Centre of the base: the lowest fifth of the pot is round even where a handle is not."""
    allV = np.concatenate([V for V, _ in P])
    low = allV[allV[:, 2] < np.quantile(allV[:, 2], 0.2)]
    return low[:, :2].mean(0)


def section(P, mm, az):
    """Cut every sherd with the plane through the pot's axis at azimuth `az`, in mm."""
    c = np.r_[axis_xy(P), 0.0]
    e_h = np.array([np.cos(az), np.sin(az), 0.0])
    normal = np.array([-np.sin(az), np.cos(az), 0.0])
    e_v = np.array([0.0, 0.0, 1.0])
    trees = [trimesh.Trimesh(V, F, process=False) for V, F in P]
    kd = [cKDTree(V) for V, _ in P]
    out = []
    for i, (m, (V, F)) in enumerate(zip(trees, P)):
        on = np.zeros(len(V), bool)
        for j, t in enumerate(kd):
            if j != i:
                d, _ = t.query(V, distance_upper_bound=1e-4 / mm)
                on |= np.isfinite(d)
        brk = on[F].all(1)
        lines, fi = trimesh.intersections.mesh_plane(m, normal, c, return_faces=True)
        if len(lines) == 0:
            out.append((np.zeros((0, 2, 2)), np.zeros(0, bool)))
            continue
        d = (lines - c) * mm
        out.append((np.stack([d @ e_h, d @ e_v], -1), brk[fi]))
    return out


def draw_cut(ax, cuts, win=None, bar=10.0, title=""):
    for i, (seg, b) in enumerate(cuts):
        ax.add_collection(LineCollection(seg[~b], colors=[plt.cm.tab20(i % 20)], linewidths=1.2))
        ax.add_collection(LineCollection(seg[b], colors="k", linewidths=0.9))
    ax.set_aspect("equal")
    if win:
        ax.set_xlim(*win[0])
        ax.set_ylim(*win[1])
    else:
        ax.autoscale_view()
    (x0, x1), (y0, y1) = ax.get_xlim(), ax.get_ylim()
    xs, ys = x0 + 0.06 * (x1 - x0), y0 + 0.06 * (y1 - y0)
    ax.plot([xs, xs + bar], [ys, ys], color="k", lw=3, solid_capstyle="butt")
    ax.text(xs + bar / 2, ys + 0.03 * (y1 - y0), f"{bar:g} mm", ha="center", fontsize=7)
    ax.set_title(title, fontsize=8)
    ax.tick_params(labelsize=6)


def wall_window(cuts, half=3.5):
    """A window on the outer wall at mid-height of the cut, positive side."""
    pts = np.concatenate([s.reshape(-1, 2) for s, _ in cuts if len(s)])
    right = pts[pts[:, 0] > 0]
    zmid = np.median(right[:, 1])
    band = right[np.abs(right[:, 1] - zmid) < 2.0]
    x = band[:, 0].max() if len(band) else right[:, 0].max()
    return ((x - 2 * half + 1.0, x + 1.0), (zmid - half, zmid + half))


def point_window(xz, half=3.5):
    return ((xz[0] - half, xz[0] + half), (xz[1] - half, xz[1] + half))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--report", required=True)
    ap.add_argument("--juglet", required=True)
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    rep = json.loads(Path(args.report).read_text())

    # every training breakage, by vessel, with the file it lives in
    where, meta = {}, {}
    for path in args.files:
        with h5py.File(path, "r") as f:
            ds = next(iter(f["data_split"]))
            for n in f["data_split"][ds]["train"][:]:
                n = n.decode()
                a = f[n].attrs
                meta[n] = dict(vessel=str(a["vessel"]), form=str(a["form"]),
                               sherds=int(a["sherds"]), mm=float(a["mm_per_unit"]),
                               wall=json.loads(a["recipe"])["wall_mm"])
                where[n] = path

    def load(n):
        with h5py.File(where[n], "r") as f:
            return pieces(f[n])

    def first_of(pred):
        return next(n for n in sorted(meta) if pred(meta[n]))

    with h5py.File(args.juglet, "r") as f:
        ds = next(iter(f["data_split"]))
        jn = f["data_split"][ds]["val"][0].decode()
        jug = upright(pieces(f[jn]))

    # 1. same size as the Juglet
    cn = first_of(lambda m: m["form"] == "ceiling" and 10 <= m["sherds"] <= 30)
    fig = plt.figure(figsize=(12, 6))
    m = meta[cn]
    shade(fig.add_subplot(1, 2, 1, projection="3d"), load(cn),
          f"{cn}\n{m['sherds']} sherds, wall {m['wall']:.2f} mm, 1 unit = {m['mm']:.0f} mm")
    shade(fig.add_subplot(1, 2, 2, projection="3d"), jug,
          f"the Juglet (juglet_gt.hdf5, conservator's reassembly)\n{len(jug)} sherds; "
          "stood upright here by its shape, for the picture only")
    fig.suptitle("Both in the units TORA reads, on the same axes (-0.55 to 0.55)", fontsize=10)
    fig.tight_layout()
    fig.savefig(out / "u10_look_juglet.png", dpi=150)
    plt.close(fig)

    # 2. the forms
    ceil, gen = {}, {}
    for n in sorted(meta):
        m = meta[n]
        if m["form"] == "ceiling":
            ceil.setdefault(m["vessel"], n)
        else:
            gen.setdefault(m["form"], n)
    slots = [(i + 1, n) for i, n in enumerate(list(ceil.values())[:3])] + \
            [(5 + i, n) for i, n in enumerate(gen.values())]
    fig = plt.figure(figsize=(4.2 * 4, 4.2 * 2))
    for slot, n in slots:
        m = meta[n]
        shade(fig.add_subplot(2, 4, slot, projection="3d"), load(n),
              f"{m['form']}: {m['vessel']}\n{m['sherds']} sherds, wall {m['wall']:.2f} mm")
    fig.suptitle("Top: three ceiling training vessels. Bottom: one of each generic form. "
                 "Same axes throughout", fontsize=10)
    fig.tight_layout()
    fig.savefig(out / "u10_look_forms.png", dpi=150)
    plt.close(fig)

    # 3. sections
    vw = rep["facts"]["vessel_walls"]
    thin = min(vw, key=lambda v: vw[v]["median"])
    thick = max(vw, key=lambda v: vw[v]["median"])
    per = {r["name"]: r for r in rep["per_breakage"] if r["name"] in meta}
    hn, hi = max(((n, i) for n, r in per.items() for i, s in enumerate(r["sherds"])
                  if s["wall_mm"] == s["wall_mm"]),
                 key=lambda t: per[t[0]]["sherds"][t[1]]["wall_mm"] / vw[meta[t[0]]["vessel"]]["median"])
    rows = [(first_of(lambda m: m["vessel"] == thin), None, "thinnest-walled vessel"),
            (first_of(lambda m: m["vessel"] == thick), None, "thickest-walled vessel"),
            (hn, hi, "the sherd the audit read thickest against its vessel")]
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    for col, (n, sherd, what) in enumerate(rows):
        P, m = load(n), meta[n]
        if sherd is None:
            az = 0.37
        else:
            cxy = P[sherd][0][:, :2].mean(0) - axis_xy(P)
            az = float(np.arctan2(cxy[1], cxy[0]))
        cuts = section(P, m["mm"], az)
        med = vw[m["vessel"]]["median"]
        head = (f"{what}\n{n}\nbuilt wall {m['wall']:.2f} mm; audit median {med:.2f} mm")
        draw_cut(axes[0, col], cuts, None, 10.0, head)
        if sherd is None:
            win = wall_window(cuts)
            sub = "wall at mid-height"
        else:
            seg = cuts[sherd][0]
            win = point_window(seg.reshape(-1, 2).mean(0)) if len(seg) else wall_window(cuts)
            w = per[n]["sherds"][sherd]["wall_mm"]
            sub = f"sherd {sherd}: audit read {w:.2f} mm, {w / med:.1f} x the vessel's median"
        draw_cut(axes[1, col], cuts, win, 0.5, sub)
    fig.suptitle("Cut through the pot's axis. Colour = sherd; black = where the cut crosses a "
                 "break face. Bottom row: 7 mm windows with a 0.5 mm bar", fontsize=10)
    fig.tight_layout()
    fig.savefig(out / "u10_look_sections.png", dpi=200)
    plt.close(fig)
    print("wrote", *sorted(p.name for p in out.glob("u10_look_*.png")))


if __name__ == "__main__":
    main()
