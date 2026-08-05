"""Export worn sherds as mesh files, for inspection one at a time.

A rendered picture cannot settle whether simulated wear looks like real wear —
five successive views failed to show it honestly, and even the one that worked
is a fixed viewpoint under fixed lighting. Judging a sherd edge needs the piece
in hand: rotated, lit from different angles, examined edge-on.

So this writes actual meshes. Open them in MeshLab, Blender or CloudCompare and
inspect each sherd across wear levels.

Layout — organised BY SHERD so one piece can be compared across levels, which is
the comparison that matters:

    <out>/sherd_00/00_original.ply
    <out>/sherd_00/01_light.ply
    ...
    <out>/assembled/00_original.ply      whole vessel at each level
    <out>/README.txt                     what each level is, in plain terms

Wear levels here are a graded ABRASION series at fixed material loss, so the
variable under inspection is one thing rather than several at once.

Usage:
  python scripts/export_wear_sherds.py --object Teacup --out /path/to/dir
"""

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fracture_mesh_ops import piece_relief_stats  # noqa: E402
from wear_ops import apply_wear  # noqa: E402

# A graded series. Abrasion increases; chipping and recession stay modest and
# fixed, so what varies between files is the break-surface texture.
LEVELS = [
    ("00_original", None),
    ("01_light",    dict(smoothing=0.3, recession=0.0006, chip_count=2, chip_size=0.0015)),
    ("02_moderate", dict(smoothing=0.6, recession=0.0012, chip_count=3, chip_size=0.0020)),
    ("03_heavy",    dict(smoothing=1.0, recession=0.0020, chip_count=4, chip_size=0.0022)),
    ("04_severe",   dict(smoothing=1.0, recession=0.0035, chip_count=6, chip_size=0.0030)),
]

README = """Simulated archaeological wear — {obj}, {n} sherds
================================================================

Open the .ply files in MeshLab, Blender or CloudCompare.

WHAT TO LOOK FOR
  Compare one sherd across levels: sherd_00/00_original.ply through 04_severe.
  Light the break face at a low angle (raking light) — that is where the wear is.

  The break surface should progressively lose its fine sharpness while keeping
  its overall shape. Edges should soften. Small chips should appear at the
  pointy, exposed corners. The sherd should NOT look melted, blurred, or
  digitally smoothed all over: only the break faces are worn, because on a real
  vessel the finished outer surface is far more durable than a fresh break.

LEVELS
  00_original   untouched, as fractured
  01_light      light abrasion, a couple of small chips
  02_moderate   moderate abrasion
  03_heavy      heavy abrasion, edges receding
  04_severe     severe abrasion and material loss

  Abrasion increases across the series; chipping and edge loss stay modest, so
  the thing changing between files is mainly the break-surface texture.

MEASURED FRACTURE TEXTURE (lower = smoother; this is what the model targets)
{relief}

WHAT IS NOT SIMULATED
  Staining, encrustation, salt damage, colour change, glaze loss. Only geometry.

  Also: the assembled poses are UNCHANGED at every level, so these files stay
  valid as reassembly ground truth. That is the constraint that makes this
  useful for training and is why the wear is applied without ever moving a sherd.
"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", default="/data/gpfs/projects/punim2657/TORA/dataset/thinwalled.hdf5")
    ap.add_argument("--dataset", default="everyday")
    ap.add_argument("--object", default="Teacup")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    with h5py.File(args.src, "r") as h:
        grp = h[args.dataset][args.object]
        g = grp["pieces"] if "pieces" in grp else grp
        keys = sorted(g.keys(), key=lambda s: int(s) if s.isdigit() else s)
        pieces = [(np.asarray(g[k]["vertices"][:], dtype=np.float64),
                   np.asarray(g[k]["faces"][:], dtype=np.int64)) for k in keys]

    out = Path(args.out)
    (out / "assembled").mkdir(parents=True, exist_ok=True)
    for i in range(len(pieces)):
        (out / f"sherd_{i:02d}").mkdir(parents=True, exist_ok=True)

    print(f"{args.object}: {len(pieces)} sherds, "
          f"{sum(len(v) for v, _ in pieces)} vertices", flush=True)

    relief_lines = []
    for name, kw in LEVELS:
        worn = pieces if kw is None else apply_wear(pieces, **kw)
        rel = float(np.mean([piece_relief_stats(v, f)["relief_p90"] for v, f in worn]))
        relief_lines.append(f"  {name:<14s} {rel:.4f}")
        print(f"  {name:<14s} fracture texture {rel:.4f}", flush=True)

        scene = []
        for i, (v, f) in enumerate(worn):
            m = trimesh.Trimesh(vertices=v, faces=f, process=False)
            m.export(out / f"sherd_{i:02d}" / f"{name}.ply")
            scene.append(m)
        # whole vessel, sherds in their assembled positions
        trimesh.util.concatenate(scene).export(out / "assembled" / f"{name}.ply")

    (out / "README.txt").write_text(
        README.format(obj=args.object, n=len(pieces), relief="\n".join(relief_lines)))
    print(f"  wrote {out}", flush=True)


if __name__ == "__main__":
    main()
