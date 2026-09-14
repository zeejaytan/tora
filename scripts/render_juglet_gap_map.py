"""Where are the Juglet's missing pieces, and are its worst-placed sherds the ones around them?

Ticket .scratch/juglet-cause/issues/12, secondary check, suggestive only (one object,
eight free sherds). The Juglet is incomplete: one very visible piece and a few small
ones were never recovered (conservator, 2026-08-10). A 3D scatter of `juglet_gt` does
not show where the holes are, because the far wall shows through them. Unrolling the
vessel does: each cell of (angle around the upright axis, height) is coloured by the
sherd whose points fall in it, and a cell inside the body that no sherd reaches is a
hole.

Then, per free sherd: how many hole cells it borders, and how TORA places it over
every draw -- median distance from home after the rigid step, share of draws seated,
share of draws it came out as its own mirror image (`measure_nonrigid_cheating.py`).

Scale: cells are 10 deg around by 1/26 of the height (printed in % of pot size). A
missing chip smaller than about one cell does not show and is not claimed.

The upright axis is the true cloud's z axis through the centre of the lower body. The
neck and handle sit off that axis, so the upper rows are partly empty by shape, not by
loss: holes are counted only below BODY_TOP.

Usage:
  python scripts/render_juglet_gap_map.py \\
      --npz artifacts/jugdraw/jugdraw_baseline_30130049/clouds/juglet_gt_sample00000.npz \\
      --out artifacts/shape12/juglet_gap_map.png
"""

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from measure_nonrigid_cheating import (  # noqa: E402
    SEAT_PCT, load_object, measure_draw, mirror_flags,
)
from readout import unit_box_scale  # noqa: E402

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

NZ, NPHI = 26, 36        # height bands, angle cells (10 deg)
LOWER_BODY = 0.55        # the axis is centred on points below this share of the height
BODY_TOP = 0.75          # above this the neck is off-axis; empty cells there are shape
STEPS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def unroll(gt: np.ndarray, ids: np.ndarray):
    """Grid of the sherd id covering each (height, angle) cell, -1 where none does."""
    g = gt / unit_box_scale(gt)
    z = g[:, 2]
    zlo, zhi = z.min(), z.max()
    low = z < zlo + LOWER_BODY * (zhi - zlo)
    cx, cy = g[low, 0].mean(), g[low, 1].mean()
    phi = np.degrees(np.arctan2(g[:, 1] - cy, g[:, 0] - cx)) % 360
    rad = np.hypot(g[:, 0] - cx, g[:, 1] - cy)
    zi = np.clip(((z - zlo) / (zhi - zlo) * NZ).astype(int), 0, NZ - 1)
    pi = np.clip((phi / 360 * NPHI).astype(int), 0, NPHI - 1)
    grid = -np.ones((NZ, NPHI), int)
    for a in range(NZ):
        for b in range(NPHI):
            m = (zi == a) & (pi == b)
            if m.any():
                v, c = np.unique(ids[m], return_counts=True)
                grid[a, b] = v[np.argmax(c)]
    cell_h = 100.0 * (zhi - zlo) / NZ                                  # % of pot size
    cell_w = np.array([100.0 * np.radians(360 / NPHI) * np.median(rad[zi == a])
                       if (zi == a).any() else np.nan for a in range(NZ)])
    return grid, cell_h, cell_w


def holes(grid: np.ndarray) -> list[dict]:
    """Connected empty cells below BODY_TOP (angle wraps), with the sherds around each."""
    top = int(BODY_TOP * NZ)
    seen = np.zeros_like(grid, bool)
    out = []
    for a in range(top):
        for b in range(NPHI):
            if grid[a, b] >= 0 or seen[a, b]:
                continue
            stack, cells = [(a, b)], []
            seen[a, b] = True
            while stack:
                i, j = stack.pop()
                cells.append((i, j))
                for di, dj in STEPS:
                    ii, jj = i + di, (j + dj) % NPHI
                    if 0 <= ii < top and grid[ii, jj] < 0 and not seen[ii, jj]:
                        seen[ii, jj] = True
                        stack.append((ii, jj))
            border = {}
            for i, j in cells:
                for di, dj in STEPS:
                    ii, jj = i + di, (j + dj) % NPHI
                    if 0 <= ii < NZ and grid[ii, jj] >= 0:
                        border[int(grid[ii, jj])] = border.get(int(grid[ii, jj]), 0) + 1
            out.append({"cells": cells, "border": border})
    return sorted(out, key=lambda h: -len(h["cells"]))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--npz", required=True)
    ap.add_argument("--out", default="artifacts/shape12/juglet_gap_map.png")
    a = ap.parse_args()

    obj = load_object(a.npz)
    gt, ids = obj["gt"], obj["ids"]
    grid, cell_h, cell_w = unroll(gt, ids)
    hs = holes(grid)

    per = [measure_draw(gt, obj["pred"][k], obj["prop"][k], ids)
           for k in range(len(obj["pred"]))]
    _, flags = mirror_flags(per)
    anchor = per[0]["anchor"]
    parts = per[0]["parts"]
    free = [s for s in parts if s != anchor]

    print(f"{obj['name']}: cells {360 // NPHI} deg around x {cell_h:.1f}% of pot size tall "
          f"({np.nanmedian(cell_w[:int(BODY_TOP * NZ)]):.1f}% wide on the body). "
          f"Holes below {100 * BODY_TOP:.0f}% of the height:")
    for n, h in enumerate(hs):
        rows = sorted({i for i, _ in h["cells"]})
        cols = sorted({j for _, j in h["cells"]})
        print(f"  hole {n}: {len(h['cells'])} cells, height "
              f"{100 * rows[0] / NZ:.0f}-{100 * (rows[-1] + 1) / NZ:.0f}% of the vessel, "
              f"{len(cols) * 360 // NPHI} deg around; bordered by sherds "
              f"{dict(sorted(h['border'].items(), key=lambda kv: -kv[1]))} (edge cells)")

    border = {}
    for h in hs:
        for s, c in h["border"].items():
            border[s] = border.get(s, 0) + c
    rows = []
    print(f"\n  {'sherd':>5s} {'hole edge':>9s} {'from home':>10s} {'seated':>7s} {'mirror':>7s}"
          f"   (over {len(per)} draws, rigid assembly)")
    for s in free:
        home = [d["rigid_own"][s] for d in per]
        r = {"sherd": s, "edge": border.get(s, 0), "home": float(np.median(home)),
             "seated": float(np.mean([v < SEAT_PCT for v in home])),
             "mirror": float(np.mean([f[s] == "mirror" for f in flags]))}
        rows.append(r)
        print(f"  {s:>5d} {r['edge']:>9d} {r['home']:9.1f}% {100 * r['seated']:6.0f}% "
              f"{100 * r['mirror']:6.0f}%")
    for tag, grp in (("border a hole", [r for r in rows if r["edge"] > 0]),
                     ("do not", [r for r in rows if r["edge"] == 0])):
        if grp:
            print(f"  {tag:>13s} ({len(grp)}): from home median "
                  f"{np.median([r['home'] for r in grp]):5.1f}%, seated "
                  f"{100 * np.mean([r['seated'] for r in grp]):3.0f}%, mirror "
                  f"{100 * np.mean([r['mirror'] for r in grp]):3.0f}% of draws")

    cmap = plt.get_cmap("tab10")
    img = np.ones((NZ, NPHI, 3))
    for i in range(NZ):
        for j in range(NPHI):
            if grid[i, j] >= 0:
                img[i, j] = cmap(parts.index(grid[i, j]) % 10)[:3]
    fig, (ax, tx) = plt.subplots(1, 2, figsize=(13, 5.6), layout="constrained",
                                 gridspec_kw={"width_ratios": [3.2, 1]})
    ax.imshow(img, origin="lower", extent=(0, 360, 0, 100), aspect="auto",
              interpolation="nearest")
    for i in range(NZ):
        for j in range(NPHI):
            x, y = (j + 0.5) * 360 / NPHI, (i + 0.5) * 100 / NZ
            if grid[i, j] >= 0:
                ax.text(x, y, str(grid[i, j]), fontsize=6, ha="center", va="center")
            elif i < int(BODY_TOP * NZ):
                ax.text(x, y, "x", fontsize=7, ha="center", va="center", color="red")
    ax.axhline(100 * BODY_TOP, color="grey", ls="--", lw=0.8)
    ax.text(2, 100 * BODY_TOP + 1, "above: neck and handle, off-axis (empty by shape)",
            fontsize=7, color="grey")
    ax.set_xlabel("angle around the vessel's upright axis (deg)")
    ax.set_ylabel("height (% of the vessel's height)")
    ax.set_title(f"{obj['name']} (the conservator's assembly) unrolled: each cell coloured "
                 f"by the sherd covering it; red x = no sherd, inside the body\n"
                 f"cells {360 // NPHI} deg x {cell_h:.1f}% of pot size; a chip smaller than "
                 f"one cell does not show", fontsize=9)
    tx.axis("off")
    lines = ["How TORA places each free sherd", f"({len(per)} draws, rigid assembly)", "",
             f"{'sherd':>5s} {'hole':>5s} {'home':>6s} {'seat':>5s} {'mirr':>5s}"]
    for r in rows:
        lines.append(f"{r['sherd']:>5d} {r['edge']:>5d} {r['home']:5.1f}% "
                     f"{100 * r['seated']:4.0f}% {100 * r['mirror']:4.0f}%")
    lines += ["", "hole = edge cells it shares", "with a hole", "home = median distance from",
              "its true place, % of pot size", f"seat = share of draws within {SEAT_PCT:.1f}%",
              "mirr = share of draws it came", "out as its mirror image"]
    tx.text(0, 1, "\n".join(lines), family="monospace", fontsize=8, va="top")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.out, dpi=130)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
