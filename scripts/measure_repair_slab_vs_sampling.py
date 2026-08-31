"""Can TORA's sampling see a RePAIR fracture at all?

THE QUESTION THIS ANSWERS, AND WHY IT IS THE DECIDING ONE.

The proposal is to distil "how two worn fractured pieces join" out of RePAIR and
carry it into a pottery model through a LoRA adapter. That only makes sense if
the join is inside what the network actually reads. TORA reads 5000 points per
object with normals, area-weighted -- so its cell is

    spacing = sqrt(2 * total_area / 5000)

and a fracture is a RIBBON around the perimeter of a thin plaque. If fewer than
about one cell fits through the plaque's thickness, one sampled point straddles
the whole slab and the fracture ribbon never gets a row of points of its own.
The adapter would then be trained on the plaque's OUTLINE, which is fresco
shape, not on how the break mates -- which is the pollution the question worries
about, arriving through the front door.

This is the same instrument, and the same threshold, already applied to the
training vessels (`measure_wall_vs_sampling.py`, job 29764781): median 0.78
cells there, against 152-177 degree mating angles for the objects above 4 cells
and 83-96 for those below 1.

WHAT IS AND IS NOT KNOWN ABOUT THE OBJECT SIZE. The open-discovery subset on
Spartan is loose fragments with no assembly grouping, so "how many pieces share
the 5000 points" is not fixed by the data. It is therefore swept (2, 5, 10, 20
fragments) rather than assumed. The ribbon area fraction does not depend on that
choice and is reported on its own.

The fracture classification is Gate A's, which was rendered and checked before
its spectrum was believed (`repair_fracture_classification.png`). The slab
thickness is measured two independent ways so a bad one is visible:
  - percentile of the point cloud along the slab normal (shape only)
  - 2V/A with the fracture ribbon removed from the denominator (volume/area)

Usage:
  python scripts/measure_repair_slab_vs_sampling.py \
      --dir /data/gpfs/projects/punim2657/TORA/repair/OPEN_DISCOVERY/pieces \
      --limit 0 --render artifacts/repair_slab_vs_sampling.png
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parent))
from repair_fracture_spectrum import fracture_mask, load_merged  # noqa: E402

import matplotlib                                                # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                  # noqa: E402

NUM_POINTS = 5000          # TORA's per-object budget; see point_cloud_encoder
PIECE_COUNTS = [2, 5, 10, 20]
THICK_LO, THICK_HI = 2.0, 98.0   # percentiles, so one stray vertex cannot set it


def slab_thickness(v, plane_n):
    """Plaque thickness from the spread along its own thinnest direction."""
    t = v @ plane_n
    return float(np.percentile(t, THICK_HI) - np.percentile(t, THICK_LO))


def thickness_2VA(mesh, frac_area):
    """2V / (A - A_fracture): mean thickness of a slab, ribbon not counted.

    A plaque is a shell whose two big faces bound the volume; the perimeter
    ribbon is the edge, and leaving it in the denominator biases the answer
    thin. Same correction as the vessel wall measurement.
    """
    a = float(mesh.area) - frac_area
    if a <= 0:
        return None
    return 2.0 * abs(float(mesh.volume)) / a


def measure_one(path):
    v, f = load_merged(path)
    if len(v) < 500 or len(f) < 500:
        return None
    frac, plane_n = fracture_mask(v, f)
    m = trimesh.Trimesh(vertices=v, faces=f, process=False)

    # a face is fracture if all three of its corners are
    fface = frac[f].all(axis=1)
    areas = m.area_faces
    frac_area = float(areas[fface].sum())
    total_area = float(areas.sum())
    if total_area <= 0:
        return None

    thick = slab_thickness(v, plane_n)
    t2va = thickness_2VA(m, frac_area)
    ext = np.sort(np.ptp(v, axis=0))          # thinnest, middle, longest
    return {
        "name": Path(path).stem,
        "thick_mm": thick,
        "thick_2VA_mm": -1.0 if t2va is None else t2va,
        "area_mm2": total_area,
        "ribbon_pct": 100.0 * frac_area / total_area,
        "face_mm": float(ext[2]),          # longest extent, the plaque's span
        "verts": len(v),
    }


def report(rows):
    if not rows:
        print("nothing measured")
        return
    thick = np.array([r["thick_mm"] for r in rows])
    t2va = np.array([r["thick_2VA_mm"] for r in rows])
    area = np.array([r["area_mm2"] for r in rows])
    ribbon = np.array([r["ribbon_pct"] for r in rows])
    face = np.array([r["face_mm"] for r in rows])

    print("")
    print("=" * 72)
    print("THE PLAQUES  (n = " + str(len(rows)) + ")")
    print("=" * 72)
    print("  slab thickness, cloud     median " +
          format(float(np.median(thick)), "6.2f") + " mm   " +
          format(float(np.percentile(thick, 10)), ".2f") + " - " +
          format(float(np.percentile(thick, 90)), ".2f"))
    ok = t2va > 0
    if ok.any():
        print("  slab thickness, 2V/A      median " +
              format(float(np.median(t2va[ok])), "6.2f") + " mm")
    print("  longest span              median " +
          format(float(np.median(face)), "6.2f") + " mm")
    print("  fracture ribbon           median " +
          format(float(np.median(ribbon)), "6.2f") + " % of surface area")
    print("  aspect (span / thickness) median " +
          format(float(np.median(face / np.maximum(thick, 1e-9))), "6.2f"))

    print("")
    print("=" * 72)
    print("CELLS THROUGH THE SLAB AT TORA'S 5000-POINT BUDGET")
    print("=" * 72)
    print("  pieces   spacing mm   cells   points on ribbon   verdict")
    med_area = float(np.median(area))
    med_thick = float(np.median(thick))
    med_ribbon = float(np.median(ribbon))
    for n in PIECE_COUNTS:
        total = med_area * n
        spacing = float(np.sqrt(2.0 * total / NUM_POINTS))
        cells = med_thick / spacing
        on_ribbon = NUM_POINTS * med_ribbon / 100.0
        verdict = ("one point spans the slab" if cells < 1.0 else
                   "a thin row" if cells < 2.0 else "a proper break face")
        print("  " + str(n).rjust(6) + "   " + format(spacing, "10.3f") +
              "   " + format(cells, "5.2f") + "   " +
              format(on_ribbon, "16.0f") + "   " + verdict)
    print("")
    print("  Points on the ribbon is per OBJECT, shared over all its pieces;")
    print("  divide by the piece count for points per fragment edge.")


def render(rows, paths, out):
    """Draw the slab against the sampling cell it has to be seen through.

    A number saying '0.6 cells' is easy to nod at. The picture is a cross
    section with the cell drawn to scale on top of it, which is not.
    """
    n = min(6, len(paths))
    if n == 0:
        return
    idx = np.linspace(0, len(paths) - 1, n).astype(int)
    med_area = float(np.median([r["area_mm2"] for r in rows]))
    spacing = float(np.sqrt(2.0 * med_area * 5 / NUM_POINTS))   # 5-piece object

    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    for ax, i in zip(axes.ravel(), idx):
        v, f = load_merged(paths[i])
        frac, plane_n = fracture_mask(v, f)
        c = v.mean(axis=0)
        P = v - c
        u = np.linalg.svd(P.T @ P)[0]
        x = P @ u[:, 0]                 # longest in-plane direction
        z = P @ plane_n                 # across the slab
        band = np.abs(P @ u[:, 1]) < 0.02 * np.ptp(P @ u[:, 1]) + 1e-9
        ax.scatter(x[band & ~frac], z[band & ~frac], s=1, c="#bbbbbb",
                   label="flat face")
        ax.scatter(x[band & frac], z[band & frac], s=3, c="#c0392b",
                   label="fracture")
        # the sampling cell, drawn to the same scale
        x0 = float(np.percentile(x, 5))
        z0 = float(np.percentile(z, 50))
        ax.add_patch(plt.Rectangle((x0, z0 - spacing / 2), spacing, spacing,
                                   fill=False, ec="#2c3e50", lw=1.8))
        ax.set_title(Path(paths[i]).stem + "  thick " +
                     format(rows[i]["thick_mm"], ".1f") + " mm", fontsize=9)
        ax.set_aspect("equal")
        ax.set_xlabel("mm")
    axes.ravel()[0].legend(fontsize=7, loc="upper right")
    fig.suptitle("RePAIR plaque cross sections, with TORA's 5000-point "
                 "sampling cell (" + format(spacing, ".1f") +
                 " mm) drawn to scale", fontsize=11)
    fig.tight_layout()
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=130)
    print("wrote " + out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--limit", type=int, default=0, help="0 = every fragment")
    ap.add_argument("--render", default="")
    ap.add_argument("--out", default="")
    a = ap.parse_args()

    objs = sorted(Path(a.dir).glob("*.obj"))
    if a.limit:
        objs = objs[:a.limit]
    print("measuring " + str(len(objs)) + " RePAIR fragments", flush=True)

    rows, kept = [], []
    for i, p in enumerate(objs):
        try:
            r = measure_one(p)
        except Exception as e:                                # noqa: BLE001
            print("  skip " + p.stem + ": " + str(e), flush=True)
            continue
        if r is None:
            continue
        rows.append(r)
        kept.append(p)
        if i % 10 == 0:
            print("  " + str(i) + "/" + str(len(objs)) + "  " +
                  r["name"] + "  thick " + format(r["thick_mm"], "6.2f") +
                  " mm  ribbon " + format(r["ribbon_pct"], "5.1f") + "%",
                  flush=True)

    report(rows)
    if a.out and rows:
        keys = list(rows[0].keys())
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        with open(a.out, "w", encoding="utf-8", newline="") as fh:
            fh.write(",".join(keys) + "\n")
            for r in rows:
                fh.write(",".join(str(r[k]) for k in keys) + "\n")
        print("wrote " + a.out)
    if a.render:
        render(rows, kept, a.render)


if __name__ == "__main__":
    main()
