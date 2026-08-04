"""Check the SDF offset properly: sign convention first, then look at it.

The SDF offset was rejected on numbers alone — days after visual confirmation was
made mandatory for geometry operations. That was inconsistent, and one of those
numbers is suspicious.

RELIEF LOSS is credible and probably inherent: these meshes carry detail at
~0.002-0.005 of object size, and a 256 grid has ~0.004 voxels, so the fracture
texture sits at grid scale and the round-trip averages it away.

JOINS CLOSING on limb3 (x0.73) is NOT explained by that. Grid coarseness blurs a
surface, it does not move it the wrong way. That is the signature of a SIGN
CONVENTION error — if the field is negative inside rather than positive, raising
the level GROWS the object instead of shrinking it. Which would be the same class
of bug the SDF was adopted to eliminate.

So this checks, in order:
  1. which sign convention the backend actually uses (measured, not assumed);
  2. whether the offset moves the surface in or out, by volume;
  3. what it looks like.

Only then is a rejection honest.

Usage:
  python scripts/diagnose_sdf.py --object limb3
"""

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sdf_offset  # noqa: E402
from visual_check import closest_pair, render_pair_panel  # noqa: E402


def sdf_sign_convention(verts, faces, grid=64):
    """Is the field NEGATIVE or POSITIVE inside? Measure, do not assume."""
    v = np.asarray(verts, dtype=np.float64)
    f = np.asarray(faces, dtype=np.int64)
    centre = 0.5 * (v.max(0) + v.min(0))
    extent = float((v.max(0) - v.min(0)).max())
    s = 0.92 * 2.0 / extent
    vn = (v - centre) * s

    import mesh2sdf
    sdf = mesh2sdf.compute(vn, f, size=grid, fix=True, level=2.0 / grid,
                           return_mesh=False)
    c = grid // 2
    # sample a small box at the centre of the grid; for a solid fragment the
    # centre is far more likely inside than out
    core = sdf[c - 2:c + 3, c - 2:c + 3, c - 2:c + 3]
    med = float(np.median(core))
    corner = float(np.median(sdf[:4, :4, :4]))
    return med, corner


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", default="/data/gpfs/projects/punim2657/TORA/dataset/real_heldout_norm.hdf5")
    ap.add_argument("--dataset", default="real_heldout_norm")
    ap.add_argument("--object", default="limb3")
    ap.add_argument("--grid", type=int, default=256)
    ap.add_argument("--recession", type=float, default=0.0015)
    ap.add_argument("--out", default="sdf_check.png")
    args = ap.parse_args()

    if not sdf_offset.available():
        print("no SDF backend installed")
        return

    with h5py.File(args.src, "r") as h:
        grp = h[args.dataset][args.object]
        g = grp["pieces"] if "pieces" in grp else grp
        keys = sorted(g.keys(), key=lambda s: int(s) if s.isdigit() else s)
        pieces = [(np.asarray(g[k]["vertices"][:], dtype=np.float64),
                   np.asarray(g[k]["faces"][:], dtype=np.int64)) for k in keys]

    print(f"{args.object}: {len(pieces)} fragments")

    # --- 1. sign convention ---
    med, corner = sdf_sign_convention(*pieces[0][:2])
    inside_negative = med < corner
    print(f"  SDF at fragment centre {med:+.4f}, at grid corner {corner:+.4f}")
    print(f"  -> convention: inside is {'NEGATIVE' if inside_negative else 'POSITIVE'}")
    if inside_negative:
        print("  !! offset_mesh raises the level to shrink, which is only correct")
        print("     when inside is POSITIVE. With inside NEGATIVE it GROWS the")
        print("     fragment — which would explain joins CLOSING, and means the")
        print("     rejection was premature.", flush=True)

    # --- 2. does it move in or out? volume is the blunt test ---
    for label, (v, f) in [("original", pieces[0])]:
        m = trimesh.Trimesh(vertices=v, faces=f, process=False)
        try:
            vol0 = float(abs(m.volume))
        except Exception:
            vol0 = float("nan")
    try:
        nv, nf = sdf_offset.offset_mesh(*pieces[0][:2],
                                        distance=args.recession * float(
                                            np.linalg.norm(
                                                np.concatenate([p[0] for p in pieces]).max(0)
                                                - np.concatenate([p[0] for p in pieces]).min(0))),
                                        grid=args.grid)
        m2 = trimesh.Trimesh(vertices=nv, faces=nf, process=False)
        vol1 = float(abs(m2.volume))
        print(f"  volume {vol0:.6f} -> {vol1:.6f}  "
              f"({'SHRANK, correct' if vol1 < vol0 else 'GREW — WRONG DIRECTION'})",
              flush=True)
    except Exception as e:
        print(f"  offset failed: {e}")
        return

    # --- 3. look at it ---
    off, ok = sdf_offset.offset_pieces(pieces, distance_frac=args.recession,
                                       grid=args.grid)
    i, j = closest_pair(pieces)
    if ok and len(off) == len(pieces):
        render_pair_panel(
            [("original", [pieces[i], pieces[j]]),
             (f"SDF offset (grid {args.grid})", [off[i], off[j]])],
            args.out, title=f"{args.object}: SDF offset — visual check")
        print(f"  rendered {args.out}", flush=True)
    else:
        print("  offset incomplete, not rendering", flush=True)


if __name__ == "__main__":
    main()
