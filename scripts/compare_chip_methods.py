"""Cut the flake away, or press a dish in? Decide on real scans.

manifold3d is installed now (2026-08-07), so a chip can be a genuine boolean
subtraction rather than an approximation. On synthetic slabs both methods behave:
sealed everywhere, material removed everywhere, comparable amounts. Synthetic
slabs are clean solids, which is exactly what real scans are not.

Boolean operations are unreliable on scanned geometry in a way they are not on
clean solids -- self-intersections, duplicate faces, near-degenerate triangles
and inconsistent winding all break them, and these scans are known to have
7-15% of their normals wound inward. So the question is not which method is
nicer in principle but which survives 500k-face archaeological scans.

Reported per object and per method:

    sealed          sherds still enclosing a volume -- the fault being fixed
    material lost   a chip must REMOVE material; anything negative is a chip
                    that added some, which is how the first cap attempt failed
    roughness       chipping must not inflate it. Sharp hole rims read as
                    break-surface texture, which is what made the plate appear
                    to roughen (+6.6% with chips against -5.6% without)
    time            practical limit: this runs 27 objects x 7 variants

The dish stays as the fallback regardless. A method that works until it does not
is not a foundation for a dataset build that runs for two hours unattended.

Usage:
  python scripts/compare_chip_methods.py
"""

import argparse
import sys
import time
from pathlib import Path

import h5py
import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fracture_mesh_ops import piece_relief_stats  # noqa: E402
from wear_ops import recede_and_chip  # noqa: E402


def survey(ws):
    sealed = open_edges = 0
    vol = 0.0
    for v, f in ws:
        m = trimesh.Trimesh(vertices=v, faces=f, process=False)
        sealed += int(m.is_watertight)
        try:
            vol += abs(float(m.volume))
        except Exception:
            vol = float("nan")
        e = np.sort(f[:, [0, 1, 1, 2, 2, 0]].reshape(-1, 2), axis=1)
        open_edges += int((np.unique(e, axis=0, return_counts=True)[1] == 1).sum())
    rel = float(np.mean([piece_relief_stats(v, f)["relief_p90"] for v, f in ws]))
    return sealed, open_edges, vol, rel


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", default="/data/gpfs/projects/punim2657/TORA/dataset/real_finetune.hdf5")
    ap.add_argument("--dataset", default="real_finetune")
    ap.add_argument("--objects",
                    default="ceramics__plate,ceramics__blue_pot,egg__egg1,"
                            "bones__limb3,ceramics__narrow_bottle3")
    ap.add_argument("--chip-count", type=int, default=4)
    ap.add_argument("--chip-size", type=float, default=0.0022)
    args = ap.parse_args()

    print("Boolean subtraction vs pressed dish, on real scans.")
    print("  Synthetic slabs are clean solids; these are not. Booleans fail on")
    print("  self-intersections and inconsistent winding, and these scans have")
    print("  7-15% of normals wound inward.")
    print()

    with h5py.File(args.src, "r") as h:
        ds = h[args.dataset]
        for obj in [o.strip() for o in args.objects.split(",") if o.strip()]:
            if obj not in ds:
                print(f"  {obj}: not present")
                continue
            grp = ds[obj]
            g = grp["pieces"] if "pieces" in grp else grp
            keys = sorted(g.keys(), key=lambda s: int(s) if s.isdigit() else s)
            pieces = [(np.asarray(g[k]["vertices"][:], dtype=np.float64),
                       np.asarray(g[k]["faces"][:], dtype=np.int64)) for k in keys]

            s0, o0, v0, r0 = survey(pieces)
            print(f"  {obj}  ({len(pieces)} sherds, "
                  f"{sum(len(f) for _, f in pieces)} faces)")
            print(f"    {'method':<10s} {'sealed':>8s} {'open':>6s} "
                  f"{'material lost':>14s} {'roughness':>18s} {'time':>8s}")
            print(f"    {'untouched':<10s} {s0:>5d}/{len(pieces):<2d} {o0:>6d} "
                  f"{'--':>14s} {r0:>18.4f} {'--':>8s}")

            for meth in ("dish", "boolean"):
                t0 = time.time()
                try:
                    w = recede_and_chip(pieces, recession_frac=0.0,
                                        chip_count=args.chip_count,
                                        chip_frac=args.chip_size, seed=0,
                                        chip_method=meth)
                    s1, o1, v1, r1 = survey(w)
                    dv = (100.0 * (v0 - v1) / v0
                          if np.isfinite(v0) and np.isfinite(v1) and v0 > 0
                          else float("nan"))
                    dr = 100.0 * (r1 - r0) / r0 if r0 > 1e-9 else float("nan")
                    warn = ""
                    if s1 < len(w):
                        warn += "  NOT SEALED"
                    if np.isfinite(dv) and dv < 0:
                        warn += "  ADDED MATERIAL"
                    if np.isfinite(dr) and dr > 5:
                        warn += "  ROUGHENED"
                    print(f"    {meth:<10s} {s1:>5d}/{len(w):<2d} {o1:>6d} "
                          f"{dv:>13.3f}% {r1:>10.4f} ({dr:>+5.1f}%) "
                          f"{time.time() - t0:>7.1f}s{warn}", flush=True)
                except Exception as e:
                    print(f"    {meth:<10s}  FAILED after "
                          f"{time.time() - t0:.1f}s: {type(e).__name__}: {e}",
                          flush=True)
            print(flush=True)

    print("Boolean wins only if it is sealed, removes material, does not")
    print("roughen, and never fails. Anything less and the dish stays default --")
    print("a method that works until it does not is no foundation for an")
    print("unattended two-hour dataset build.")


if __name__ == "__main__":
    main()
