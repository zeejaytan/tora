"""Screen the whole training corpus for objects TORA cannot see a break face on.

Two failure modes, one screen. Both were found on eight objects; this asks
whether they hold across all 371.

FAILURE 1 -- THE WALL IS THINNER THAN THE SAMPLING CELL.
TORA samples 5000 points per object, so its cells are sqrt(2*area/5000) across.
A fracture is a ribbon through the wall. If fewer than about one cell fits
through the wall, a single sampled point straddles the whole thickness and the
break face never gets a row of points of its own -- the network is matching
sherds on their outer profile, not on how they broke. Measured on eight
training vessels, the median gets 0.78 cells (`measure_wall_vs_sampling.py`,
job 29764781), and the objects above 4 cells mate at 152-177 degrees against
83-96 for the objects below 1.

FAILURE 2 -- THE "VESSEL" IS SOLID.
Three of those eight read 10-15% of object thick, which is not a wall, it is a
body. Sections confirm it by eye: one filled outline crossed by fracture
planes, no cavity (`render_object_sections.py` -> `artifacts/object_sections.png`).
A solid's fracture is a broad face through the body; a sherd's is a ribbon
through a shell. Training on the first to reassemble the second teaches the
wrong thing, and `GATE_B_DECISION.md` currently records these objects as hollow
because it used a probe that could only reach ~2% of object.

THE SOLIDITY MEASURE, AND WHY IT IS NOT THE ONE IN THE FIGURE.
The figure first tried counting loops per cut, which cannot work: the objects
are already broken, so every sherd contributes a closed loop whether the vessel
is hollow or not. It then tried shapely `polygons_full`, which returned nothing
on a fragmented section. What works is a scanline:

  cut the assembled object with a plane, take the raw segments, and for each
  scanline count crossings and pair them off by the even-odd rule.

Coincident fracture segments appear twice, once from each side, so they flip
parity twice and leave the interior correctly interior -- which is exactly why
this survives fragmentation when the polygon routines do not. Averaged over
three orthogonal cuts so no single slab direction can lie; the Plate in the
earlier hollowness figure looked filled purely because of its slab axis.

    fill = material length / outer extent, per scanline

A solid reads ~1. A shell of thickness t on a body of radius r reads ~2t/r.

Usage:
  python scripts/screen_vessel_corpus.py --root . --limit 0 \
      --out artifacts/corpus_screen.csv
"""

import argparse
import gc
from collections import defaultdict
from pathlib import Path

import h5py
import numpy as np
import trimesh

from compare_wear_severity import object_size, split_tag
from measure_gap_as_network_sees import load_meshes
from measure_wall_vs_sampling import (NUM_POINTS, break_faces,
                                      shell_thickness, wall_thickness)

N_SCANLINES = 240      # scanlines per cut; the fill is a length ratio, not a count
MIN_CROSS = 2          # a scanline needs at least one in/out pair to say anything


def _fill_one_cut(mesh, axis):
    """Fraction of the outline that is material, on one plane through the centre."""
    origin = mesh.bounds.mean(axis=0)
    normal = np.zeros(3)
    normal[axis] = 1.0
    try:
        segs = trimesh.intersections.mesh_plane(mesh, plane_normal=normal,
                                                plane_origin=origin)
    except Exception:                                     # noqa: BLE001
        return None
    if segs is None or len(segs) == 0:
        return None

    # drop the cut axis: the remaining two columns are the plane's own coords
    keep = [i for i in range(3) if i != axis]
    a = segs[:, 0, :][:, keep]
    b = segs[:, 1, :][:, keep]

    y0, y1 = a[:, 1], b[:, 1]
    lo, hi = np.minimum(y0, y1), np.maximum(y0, y1)
    ys = np.linspace(float(lo.min()), float(hi.max()), N_SCANLINES + 2)[1:-1]

    inside = outer = 0.0
    for y in ys:
        # segments this scanline actually crosses, half-open so a shared
        # endpoint is counted once rather than twice
        m = (lo <= y) & (hi > y)
        if m.sum() < MIN_CROSS:
            continue
        ay, by = y0[m], y1[m]
        ax, bx = a[m, 0], b[m, 0]
        t = (y - ay) / np.where(np.abs(by - ay) < 1e-30, 1e-30, by - ay)
        xs = np.sort(ax + t * (bx - ax))
        if len(xs) % 2:
            continue                                      # numerically ragged line
        inside += float((xs[1::2] - xs[0::2]).sum())
        outer += float(xs[-1] - xs[0])
    if outer <= 0:
        return None
    return inside / outer


def fill_fraction(mesh):
    """Median fill over three orthogonal cuts, so a slab direction cannot lie."""
    vals = [v for v in (_fill_one_cut(mesh, ax) for ax in range(3))
            if v is not None]
    if not vals:
        return None
    return float(np.median(vals))


def screen(src, dataset, level, limit, out_csv):
    if not Path(src).exists():
        print("missing " + str(src))
        return
    rng = np.random.default_rng(0)
    h = h5py.File(src, "r")
    dg = h[dataset]

    groups = defaultdict(dict)
    for tag in dg.keys():
        obj, lvl = split_tag(tag)
        if obj is not None:
            groups[obj][lvl] = tag
    usable = sorted(o for o, v in groups.items() if level in v)
    if limit and len(usable) > limit:
        usable = usable[::max(1, len(usable) // limit)][:limit]

    print("screening " + str(len(usable)) + " objects at level " + level,
          flush=True)
    rows = []
    for n, obj in enumerate(usable):
        tag = groups[obj][level]
        try:
            meshes = load_meshes(dg[tag])
            if meshes is None or len(meshes) < 2:
                continue
            size = object_size([np.asarray(m.vertices) for m in meshes])
            total_area = float(sum(m.area for m in meshes))
            spacing = float(np.sqrt(2 * total_area / NUM_POINTS + 1e-4))
            masks = break_faces(meshes, spacing)
            walls = [w for w in (wall_thickness(m, rng, ~brk)
                                 for m, brk in zip(meshes, masks))
                     if w is not None]
            shell = shell_thickness(meshes, masks)
            brk_pct = 100.0 * float(np.mean([m.mean() for m in masks]))
            fill = fill_fraction(trimesh.util.concatenate(meshes))
            npieces = len(meshes)
            del meshes, masks
            gc.collect()
            if not walls or shell is None:
                continue
            wall = float(np.median(walls))
            rows.append({
                "object": obj,
                "pieces": npieces,
                "wall_ray_pct": 100 * wall / size,
                "wall_2VA_pct": 100 * shell / size,
                "spacing_pct": 100 * spacing / size,
                "cells": wall / spacing,
                "break_faces_pct": brk_pct,
                "fill": -1.0 if fill is None else fill,
            })
            if n % 10 == 0:
                print("  " + str(n) + "/" + str(len(usable)) + "  " +
                      obj.ljust(34) + " cells " +
                      format(wall / spacing, "5.2f") + "  fill " +
                      ("  n/a" if fill is None else format(fill, "5.2f")),
                      flush=True)
        except Exception as e:                            # noqa: BLE001
            print("  skip " + str(obj) + ": " + str(e), flush=True)
    h.close()

    if not rows:
        print("nothing measured")
        return
    keys = list(rows[0].keys())
    Path(out_csv).parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        f.write(",".join(keys) + "\n")
        for r in rows:
            f.write(",".join(str(r[k]) for k in keys) + "\n")
    print("")
    print("wrote " + out_csv + "  (" + str(len(rows)) + " objects)")
    report(rows)


def report(rows):
    cells = np.array([r["cells"] for r in rows])
    fill = np.array([r["fill"] for r in rows])
    wall = np.array([r["wall_ray_pct"] for r in rows])
    ok_fill = fill >= 0

    print("")
    print("=" * 70)
    print("HOW MANY SAMPLING CELLS FIT THROUGH THE WALL")
    print("=" * 70)
    for lo, hi, what in [(0.0, 0.5, "under half a cell -- no break face at all"),
                         (0.5, 1.0, "under one cell -- one point spans the wall"),
                         (1.0, 2.0, "1-2 cells -- a thin row of break points"),
                         (2.0, 4.0, "2-4 cells"),
                         (4.0, 1e9, "over 4 cells -- a proper break face")]:
        m = (cells >= lo) & (cells < hi)
        print("  " + what.ljust(46) + str(int(m.sum())).rjust(4) + "  " +
              format(100.0 * m.mean(), "5.1f") + "%")
    print("  median cells " + format(float(np.median(cells)), ".2f"))

    print("")
    print("=" * 70)
    print("SOLID OR HOLLOW  (fill = material / outline, 3 cuts)")
    print("=" * 70)
    if ok_fill.sum() == 0:
        print("  fill measurement returned nothing -- do not report solidity")
    else:
        f = fill[ok_fill]
        for lo, hi, what in [(0.0, 0.25, "thin shell"),
                             (0.25, 0.50, "thick shell"),
                             (0.50, 0.80, "mostly filled"),
                             (0.80, 1.01, "SOLID -- not a vessel")]:
            m = (f >= lo) & (f < hi)
            print("  " + what.ljust(46) + str(int(m.sum())).rjust(4) + "  " +
                  format(100.0 * m.mean(), "5.1f") + "%")
        print("  median fill " + format(float(np.median(f)), ".2f") +
              "   n = " + str(int(ok_fill.sum())))

    print("")
    print("=" * 70)
    print("WHAT A SCREEN WOULD KEEP")
    print("=" * 70)
    keep = (cells >= 1.0)
    if ok_fill.sum():
        keep = keep & (fill < 0.5)
    print("  cells >= 1 and not solid: " + str(int(keep.sum())) + " of " +
          str(len(rows)) + "  (" + format(100.0 * keep.mean(), ".1f") + "%)")
    if keep.sum():
        print("  their median wall " + format(float(np.median(wall[keep])), ".2f") +
              "% of object, median cells " +
              format(float(np.median(cells[keep])), ".2f"))
    print("")
    print("  A screen that keeps almost nothing is not a screen, it is a")
    print("  verdict on the corpus. Read the counts before applying it.")


def selftest():
    """Fill fraction against shapes whose answer is known by construction."""
    ok = True
    solid = trimesh.creation.icosphere(subdivisions=4, radius=1.0)
    f = fill_fraction(solid)
    print("  solid sphere            fill " + format(f, ".3f") + "  expect ~1.00")
    ok &= abs(f - 1.0) < 0.03

    for t in (0.05, 0.15):
        outer = trimesh.creation.icosphere(subdivisions=4, radius=1.0)
        inner = trimesh.creation.icosphere(subdivisions=4, radius=1.0 - t)
        inner.invert()
        shell = trimesh.util.concatenate([outer, inner])
        f = fill_fraction(shell)
        # The fill is summed over the whole cut, so it is an AREA ratio, not the
        # value on the centre line. For a disc of radius r with a hole of
        # r - t that is 1 - (1 - t/r)^2 = 2t/r - (t/r)^2, which is the ~2t/r of
        # the docstring and NOT t. Getting this wrong once made a correct
        # instrument look broken.
        want = 2 * t - t * t
        print("  shell t=" + format(t, ".2f") + "              fill " +
              format(f, ".3f") + "  expect ~" + format(want, ".3f"))
        ok &= abs(f - want) < 0.03
    print("  selftest " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--src", default="dataset/bbad_vessels.hdf5")
    ap.add_argument("--dataset", default="bbad_vessels")
    ap.add_argument("--level", default="fresh")
    ap.add_argument("--limit", type=int, default=0, help="0 = every object")
    ap.add_argument("--out", default="artifacts/corpus_screen.csv")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        raise SystemExit(selftest())
    screen(str(Path(a.root) / a.src), a.dataset, a.level, a.limit, a.out)


if __name__ == "__main__":
    main()
