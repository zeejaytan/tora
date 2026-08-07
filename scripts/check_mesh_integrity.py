"""Does wear leave holes in the mesh? Count them.

Flagged by the conservator on 2026-08-07, from inspecting the exported sherds:
the meshes develop holes as the wear series progresses.

The cause is in plain sight in `recede_and_chip`. Both of its effects work by
DELETING FACES -- edge recession drops faces near the fracture rim, chipping
drops small patches at sharp protrusions -- and nothing ever closes the boundary
that leaves behind. That was a deliberate choice, made for a good reason: the
previous approach displaced vertices inward and corrugated the surface, blowing
relief up sixfold. Removing geometry cannot corrugate anything because it never
moves a vertex. But removing geometry from a closed surface opens it, and on a
thin shell the deletion goes straight through the wall.

I had already seen a symptom of this and misfiled it. Volume-loss reporting was
noted as "broken for chipped conditions, trimesh assumes watertight" and treated
as a reporting nuisance. It was not a reporting problem; it was the mesh no
longer being closed.

What this measures, per object and per wear level:

    watertight        does the mesh enclose a volume at all
    boundary edges    edges belonging to exactly one face -- the raw hole count
    hole loops        how many separate openings
    largest hole      biggest opening, as a fraction of object size
    Euler number      topology check independent of the above

Crucially it also measures the UNTOUCHED mesh. Real scans are often not
watertight to begin with, and "wear creates holes" means something quite
different from "wear widens holes the scanner left". Those two lead to different
fixes, and only one of them is our fault.

Usage:
  python scripts/check_mesh_integrity.py --objects ceramics__plate,egg__egg1
"""

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wear_ops import apply_wear  # noqa: E402

# same graded series the inspection exports use
LEVELS = [
    ("00_original", None),
    ("01_light",    dict(smoothing=0.3, recession=0.0006, chip_count=2, chip_size=0.0015)),
    ("02_moderate", dict(smoothing=0.6, recession=0.0012, chip_count=3, chip_size=0.0020)),
    ("03_heavy",    dict(smoothing=1.0, recession=0.0020, chip_count=4, chip_size=0.0022)),
    ("04_severe",   dict(smoothing=1.0, recession=0.0035, chip_count=6, chip_size=0.0030)),
]


def integrity(v, f):
    """Openness of a single mesh, without repairing it first."""
    m = trimesh.Trimesh(vertices=v, faces=f, process=False)
    scale = float(max(m.extents)) if len(m.vertices) else 1.0

    try:
        watertight = bool(m.is_watertight)
    except Exception:
        watertight = False

    # an edge on the boundary belongs to exactly one face
    try:
        edges = np.sort(m.edges_sorted, axis=1)
        _, inv, counts = np.unique(edges, axis=0, return_inverse=True,
                                   return_counts=True)
        n_boundary = int((counts == 1).sum())
    except Exception:
        n_boundary = -1

    try:
        loops = m.outline().entities
        n_loops = len(loops)
        spans = []
        for ent in loops:
            pts = m.outline().vertices[ent.points]
            if len(pts) > 1:
                spans.append(float(np.linalg.norm(pts.max(0) - pts.min(0))))
        largest = max(spans) / scale if spans else 0.0
    except Exception:
        n_loops, largest = -1, float("nan")

    euler = int(m.euler_number) if len(m.faces) else 0
    return watertight, n_boundary, n_loops, largest, euler


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", default="/data/gpfs/projects/punim2657/TORA/dataset/real_finetune.hdf5")
    ap.add_argument("--dataset", default="real_finetune")
    ap.add_argument("--objects",
                    default="ceramics__plate,ceramics__blue_pot,egg__egg1,bones__limb3")
    args = ap.parse_args()

    print("Does wear leave holes in the mesh?")
    print("  The untouched mesh is measured too: real scans are often already")
    print("  open, and widening a scanner's holes is a different fault from")
    print("  making new ones.")
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

            print(f"  {obj}  ({len(pieces)} sherds)")
            print(f"    {'level':<13s} {'sealed':>7s} {'open edges':>11s} "
                  f"{'holes':>7s} {'largest':>9s} {'faces':>10s}")

            base_boundary = None
            for name, kw in LEVELS:
                worn = pieces if kw is None else apply_wear(pieces, **kw)
                wt = 0
                nb = nl = 0
                lg = 0.0
                nf = 0
                for v, f in worn:
                    a, b, c, d, _ = integrity(v, f)
                    wt += int(a)
                    nb += max(b, 0)
                    nl += max(c, 0)
                    lg = max(lg, d if np.isfinite(d) else 0.0)
                    nf += len(f)
                if base_boundary is None:
                    base_boundary = nb
                extra = nb - base_boundary
                tag = "" if kw is None else f"  ({extra:+d} vs original)"
                print(f"    {name:<13s} {wt:>4d}/{len(worn):<2d} {nb:>11d} "
                      f"{nl:>7d} {lg * 100:>8.2f}% {nf:>10d}{tag}", flush=True)
            print(flush=True)

    print("Reading it:")
    print("  'sealed' counts sherds that enclose a volume. If the original row")
    print("  already shows 0 sealed, the scans arrive open and wear is not the")
    print("  origin of the problem -- though it may still make it worse.")
    print("  'open edges' rising with wear level is the fault the conservator saw.")


if __name__ == "__main__":
    main()
