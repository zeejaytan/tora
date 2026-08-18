"""Gate A: what does REAL eroded fracture look like, at what scale?

The wear model has never been checked against real worn material. The Juglet
cannot do it -- its scan records nothing finer than about 0.5% of object size
and our blunting acts at 0.3-0.5%, so there is no overlap. RePAIR's fresco
fragments are scanned at 0.05-0.2 mm, which is far finer, and there are
thousands of them.

WHAT THIS CAN AND CANNOT ESTABLISH, stated before any number is produced,
because the temptation to over-read it will be strong.

  CAN: what scales real eroded fracture actually carries structure at, in
       millimetres, on real archaeological material eroded for two thousand
       years. And whether our simulated wear produces a spectrum of the same
       SHAPE.

  CANNOT: prove our wear is correct. That needs a fresh and a worn scan of the
       same object, which nobody has published. A fresco fragment has no fresh
       counterpart any more than the Juglet does.

So a match here is supporting evidence, and a MISMATCH is the valuable outcome:
a concrete, physical discrepancy to fix, which is more than the wear model has
ever had.

THE CONSERVATOR'S CONSTRAINT, which shapes what is measured: these are fresco
plaques, not sherds, and the painted surface does much of the matching work in
the original benchmark. We are interested ONLY in how the worn fracture joins.
So the painted face is discarded and only the broken perimeter is measured.

FINDING THE FRACTURE. A plaque is a thin slab: two large faces, painted front
and rough back, and a broken ribbon around the perimeter. The slab's plane comes
from the point cloud, and a vertex belongs to the fracture if its surface faces
sideways rather than out through a flat face. That classification is RENDERED
before any spectrum is trusted -- measuring the painted front by mistake would
produce clean, plausible, meaningless numbers.

Relief is the normal deviation from the local mean, never the total distance:
the sideways component is two to three times larger at fine scales and no
erosion can remove it.

Usage:
  python scripts/repair_fracture_spectrum.py \
      --dir /path/to/OPEN_DISCOVERY/pieces --out-dir artifacts/
"""

import argparse
from pathlib import Path

import numpy as np
import trimesh
from scipy.spatial import cKDTree

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wear_ops import _local_mean  # noqa: E402

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# absolute scales in millimetres: erosion is a physical process, so this is the
# honest axis. Percentages of object size were what made every earlier
# comparison ambiguous.
RADII_MM = [0.10, 0.20, 0.40, 0.80, 1.60, 3.20, 6.40]


def load_merged(path):
    """Vertices with duplicates merged, and the faces reindexed onto them.

    RePAIR's OBJs store one vertex per face corner because of the texture
    coordinates, so the raw arrays hold about three times the geometry in exact
    duplicates. A nearest-neighbour spacing computed on them reads 0.000 mm -- a
    measurement of the file format rather than the object.
    """
    m = trimesh.load(path, process=False, skip_materials=True, force="mesh")
    v = np.asarray(m.vertices, dtype=np.float64)
    f = np.asarray(m.faces, dtype=np.int64)
    key = np.round(v, 6)
    uniq, inv = np.unique(key, axis=0, return_inverse=True)
    return uniq, inv[f]


def fracture_mask(v, f):
    """True for vertices on the broken perimeter, False on the flat faces."""
    m = trimesh.Trimesh(vertices=v, faces=f, process=False)
    try:
        vn = np.asarray(m.vertex_normals, dtype=np.float64)
    except Exception:
        return np.zeros(len(v), bool), np.array([0.0, 0.0, 1.0])
    c = v.mean(axis=0)
    P = v - c
    # a slab's thinnest direction is the plane normal
    plane_n = np.linalg.svd(P.T @ P)[0][:, 2]
    facing = np.abs(vn @ plane_n)
    return facing < 0.45, plane_n


def spectrum_mm(pts, radii, k=24, max_probe=20000, seed=0):
    """TEXTURE at each absolute radius, in millimetres, with shape removed.

    Deviation from the LOCAL MEAN was the first attempt and it does not measure
    fracture texture on these fragments -- it measures the shape of the plaque.
    A rim curving around a perimeter of radius rho departs from its own chord by
    R^2 / 2*rho, and with rho about 40 mm that predicts 0.51 mm at a 6.4 mm
    radius against 0.49 mm measured. Almost the whole signal was the outline.
    The exponent came out at 1.75, against 2.0 for a perfectly smooth curve and
    0.4-0.8 for a real fracture surface: the curve, not the fracture.

    So the reference is a QUADRIC fitted to each neighbourhood, not its mean.
    A quadric absorbs curvature exactly, by construction, and what is left over
    is texture. This is the same distinction as blunting the teeth while keeping
    the curve, applied to the instrument rather than the model.

    Fitted at a subsample of probe points because a least-squares solve per
    vertex over a hundred thousand vertices and seven radii is not affordable,
    and texture is a statistic -- twenty thousand probes describe it as well as
    all of them.
    """
    rng = np.random.default_rng(seed)
    tree = cKDTree(pts)
    probe_i = (np.arange(len(pts)) if len(pts) <= max_probe
               else rng.choice(len(pts), max_probe, replace=False))

    out = []
    for R in radii:
        idx = tree.query_ball_point(pts[probe_i], R, workers=-1,
                                    return_sorted=False)
        res = []
        for n, nb in zip(probe_i, idx):
            if len(nb) < 12:
                continue
            q = pts[nb] if len(nb) <= 400 else pts[rng.choice(nb, 400, False)]
            c = q.mean(axis=0)
            Q = q - c
            # local frame: two in-surface directions and a normal
            u = np.linalg.eigh(Q.T @ Q)[1]
            a, b, nrm = u[:, 2], u[:, 1], u[:, 0]
            x, y = Q @ a, Q @ b
            z = Q @ nrm
            # z = c0 + c1 x + c2 y + c3 x^2 + c4 xy + c5 y^2
            A = np.column_stack([np.ones_like(x), x, y, x * x, x * y, y * y])
            try:
                coef, *_ = np.linalg.lstsq(A, z, rcond=None)
            except np.linalg.LinAlgError:
                continue
            res.append(float(np.abs(z - A @ coef).mean()))
        out.append(float(np.mean(res)) if len(res) >= 50 else float("nan"))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--max-frags", type=int, default=20)
    ap.add_argument("--max-pts", type=int, default=120000)
    args = ap.parse_args()

    files = sorted(Path(args.dir).glob("*.obj"))[:args.max_frags]
    print(f"{len(files)} fragments")
    rng = np.random.default_rng(0)

    rows, shown = [], []
    for fp in files:
        try:
            v, f = load_merged(fp)
        except Exception as e:
            print(f"  {fp.name}: load failed ({e})")
            continue
        mask, plane_n = fracture_mask(v, f)
        ext = float(np.linalg.norm(v.max(0) - v.min(0)))
        pts = v[mask]
        if len(pts) < 2000:
            print(f"  {fp.name}: only {len(pts)} fracture points, skipped")
            continue
        if len(pts) > args.max_pts:
            pts = pts[rng.choice(len(pts), args.max_pts, replace=False)]
        d, _ = cKDTree(pts).query(pts, k=2, workers=-1)
        sp = float(np.median(d[:, 1]))
        sp_all = spectrum_mm(pts, RADII_MM)
        rows.append((fp.stem, ext, len(v), int(mask.sum()), sp, sp_all))
        if len(shown) < 4:
            shown.append((fp.stem, v, mask, plane_n))
        print(f"  {fp.stem}: extent {ext:.1f} mm, {int(mask.sum())} of {len(v)} "
              f"vertices on the fracture ({100 * mask.mean():.0f}%), "
              f"spacing {sp:.3f} mm")

    if not rows:
        print("nothing measured")
        return

    outd = Path(args.out_dir)
    outd.mkdir(parents=True, exist_ok=True)

    # ---- LOOK AT THE CLASSIFICATION BEFORE BELIEVING THE NUMBERS ----------
    fig, axes = plt.subplots(2, len(shown), figsize=(3.3 * len(shown), 6.6))
    axes = np.atleast_2d(axes)
    for c, (name, v, mask, plane_n) in enumerate(shown):
        e1 = np.cross(plane_n, [0.0, 0.0, 1.0])
        if np.linalg.norm(e1) < 1e-6:
            e1 = np.cross(plane_n, [0.0, 1.0, 0.0])
        e1 /= np.linalg.norm(e1)
        e2 = np.cross(plane_n, e1)
        P = v - v.mean(0)
        for r, (a, b) in enumerate([(e1, e2), (e1, plane_n)]):
            ax = axes[r, c]
            x, y = P @ a, P @ b
            s = slice(None, None, max(1, len(v) // 40000))
            ax.scatter(x[s][~mask[s]], y[s][~mask[s]], s=0.5, linewidths=0,
                       color="#bbbbbb", label="flat face (painted/back)")
            ax.scatter(x[s][mask[s]], y[s][mask[s]], s=0.7, linewidths=0,
                       color="#c1440e", label="FRACTURE")
            ax.set_aspect("equal")
            ax.set_xticks([]); ax.set_yticks([])
            if r == 0:
                ax.set_title(f"{name}\nface-on", fontsize=9)
            else:
                ax.set_title("edge-on", fontsize=9)
            if r == 0 and c == 0:
                ax.legend(fontsize=7, loc="upper right", markerscale=6)
    fig.suptitle(
        "Which surface is the FRACTURE? Orange is what gets measured.\n"
        "Edge-on, the orange should form the rim of the slab and the grey the "
        "two flat faces. If orange covers a flat face, the spectrum below is "
        "measuring the painted front and means nothing.", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(outd / "repair_fracture_classification.png", dpi=140)
    print(f"\nwrote {outd / 'repair_fracture_classification.png'}")

    # ---- the spectrum ----------------------------------------------------
    print(f"\n  TEXTURE ON REAL ERODED FRACTURE, in millimetres (shape removed)")
    print("  " + "{:<22s}".format("fragment")
          + "".join("{:>9s}".format(f"{r:.2f}mm") for r in RADII_MM))
    print("  " + "-" * (22 + 9 * len(RADII_MM)))
    for name, ext, nv, nf, sp, s in rows:
        print("  {:<22s}".format(name[:21])
              + "".join("{:>9.4f}".format(x) for x in s))
    arr = np.array([r[5] for r in rows], dtype=float)
    med_sp = float(np.median([r[4] for r in rows]))
    mean = np.nanmean(arr, axis=0)
    print("  " + "-" * (22 + 9 * len(RADII_MM)))
    print("  {:<22s}".format("MEAN")
          + "".join("{:>9.4f}".format(x) for x in mean))
    print(f"\n  median point spacing {med_sp:.3f} mm -- radii below "
          f"{2 * med_sp:.2f} mm cannot be read")

    fig, ax = plt.subplots(figsize=(7.5, 5.2))
    for name, ext, nv, nf, sp, s in rows:
        ax.plot(RADII_MM, s, "-", lw=0.8, alpha=0.35, color="#888888")
    ax.plot(RADII_MM, mean, "-o", lw=2.2, color="#c1440e", label="mean")
    ax.axvspan(0, 2 * med_sp, color="0.85", zorder=0)
    ax.text(2 * med_sp * 1.1, mean[-1] * 0.1,
            "below the\nscan resolution", fontsize=8, color="0.35")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("scale (mm)")
    ax.set_ylabel("texture (mm), curvature removed")
    ax.set_title("Real eroded fracture: TEXTURE against scale\n"
                 f"{len(rows)} Pompeii fresco fragments, ~2000 years of burial",
                 fontsize=11)
    ax.legend(fontsize=9)
    ax.grid(alpha=0.25, which="both")
    fig.tight_layout()
    fig.savefig(outd / "repair_fracture_spectrum.png", dpi=140)
    print(f"wrote {outd / 'repair_fracture_spectrum.png'}")
    print("\n  READ IT AGAINST WHAT A FRACTURE SHOULD LOOK LIKE. Fracture")
    print("  surfaces are self-affine with a roughness exponent of 0.4-0.8")
    print("  across metals, ceramics and rocks, so texture should rise as")
    print("  R^0.4 to R^0.8. An exponent far above that means the fine")
    print("  roughness is gone and only smooth shape remains -- the erosion")
    print("  signature. An exponent in that band means it is still there.")
    print()
    print("  The previous version of this measurement used deviation from the")
    print("  local MEAN and returned 1.75, which turned out to be the plaque's")
    print("  own outline curvature almost exactly. Fitting a quadric removes")
    print("  that by construction.")


if __name__ == "__main__":
    main()
