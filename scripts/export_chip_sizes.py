"""Export a chip-SIZE series, so the amount of loss can be judged by eye.

The graded wear series varies abrasion and holds chipping roughly fixed, which
is right for judging break-surface texture and useless for judging how much
material a chip should take. On real scans the standard chip removes 0.002% of
the sherd's volume -- essentially cosmetic, against the 0.2-2.7% we measured as
realistic overall. Whether that is too timid is a conservator's question, not a
statistical one: on a real sherd, is a chip at the pointy corner a small nibble
or a noticeable loss?

So this holds abrasion constant and varies ONLY chip size and count. Each level
is labelled with the material it actually removed, which is measurable for the
first time now that chipping no longer perforates the mesh -- an open mesh has
no volume, so this number could not have been quoted at all last week.

Levels are named for what they are rather than "light/heavy", because the
question is not how worn the sherd is but how big a bite a chip takes.

Usage:
  python scripts/export_chip_sizes.py --object ceramics__blue_pot --out /path
"""

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wear_ops import apply_wear  # noqa: E402

# fixed light abrasion throughout, so only the chipping changes between files
BASE = dict(smoothing=0.6, smoothing_passes=1, recession=0.0012)

LEVELS = [
    ("00_no_chips",   dict(chip_count=0, chip_size=0.0)),
    ("01_current",    dict(chip_count=3, chip_size=0.0022)),
    ("02_double",     dict(chip_count=3, chip_size=0.0045)),
    ("03_quadruple",  dict(chip_count=4, chip_size=0.0090)),
    ("04_large",      dict(chip_count=5, chip_size=0.0180)),
    ("05_very_large", dict(chip_count=6, chip_size=0.0300)),
]

README = """Chip SIZE series — {obj}, {n} sherds
================================================================

Everything about the wear is identical between these files EXCEPT how big a
bite each chip takes. Abrasion is held at a fixed light level throughout.

THE QUESTION
  On a real sherd, is a chip at an exposed corner a small nibble or a
  noticeable loss? The simulation currently takes the smallest bite in this
  series, and nobody has checked whether that looks like real damage.

  Open them in order and say which reads as ordinary archaeological chipping.
  There is no right answer in the numbers -- this is the part only someone who
  handles the material can settle.

WHAT TO LOOK FOR
  The pointy, exposed corners of each sherd, which is where chips form. Compare
  against 00_no_chips, which has the same abrasion and no chipping at all.

  A chip should leave a shallow scar with a defined edge, not a drilled pocket
  and not a hole through the sherd. If any of these perforate a sherd, that is
  a fault and worth saying so -- the previous version did exactly that.

MATERIAL REMOVED (measured, as a fraction of the sherd's solid volume)
{loss}
  For reference, total material loss across a real worn sherd was measured at
  0.2-2.7%, which includes abrasion and edge recession as well as chipping.

WHAT IS NOT SIMULATED
  Staining, encrustation, salt damage, colour change, glaze loss. Only geometry.

  Assembled poses are UNCHANGED at every level, so these stay valid as
  reassembly ground truth.
"""


def solid_volume(pieces):
    tot = 0.0
    for v, f in pieces:
        try:
            tot += abs(float(trimesh.Trimesh(vertices=v, faces=f,
                                             process=False).volume))
        except Exception:
            return float("nan")
    return tot


def load(src, dataset, obj):
    with h5py.File(src, "r") as h:
        grp = h[dataset][obj]
        g = grp["pieces"] if "pieces" in grp else grp
        keys = sorted(g.keys(), key=lambda s: int(s) if s.isdigit() else s)
        return [(np.asarray(g[k]["vertices"][:], dtype=np.float64),
                 np.asarray(g[k]["faces"][:], dtype=np.int64)) for k in keys]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", default="/data/gpfs/projects/punim2657/TORA/dataset/real_finetune.hdf5")
    ap.add_argument("--dataset", default="real_finetune")
    ap.add_argument("--object", default="ceramics__blue_pot")
    ap.add_argument("--out", required=True)
    ap.add_argument("--chip-method", default="auto")
    args = ap.parse_args()

    pieces = load(args.src, args.dataset, args.object)
    out = Path(args.out)
    (out / "assembled").mkdir(parents=True, exist_ok=True)
    for i in range(len(pieces)):
        (out / f"sherd_{i:02d}").mkdir(parents=True, exist_ok=True)

    v0 = solid_volume(pieces)
    print(f"{args.object}: {len(pieces)} sherds, "
          f"{sum(len(v) for v, _ in pieces)} vertices", flush=True)

    loss_lines = []
    for name, kw in LEVELS:
        worn = apply_wear(pieces, **BASE, **kw)
        v1 = solid_volume(worn)
        sealed = sum(int(trimesh.Trimesh(vertices=v, faces=f,
                                         process=False).is_watertight)
                     for v, f in worn)
        pct = 100.0 * (v0 - v1) / v0 if v0 and np.isfinite(v1) else float("nan")
        note = "" if sealed == len(worn) else f"   ** {len(worn) - sealed} sherd(s) NOT SEALED **"
        loss_lines.append(f"  {name:<15s} {pct:>7.3f}%{note}")
        print(f"  {name:<15s} removed {pct:>7.3f}%  sealed {sealed}/{len(worn)}",
              flush=True)

        scene = []
        for i, (v, f) in enumerate(worn):
            m = trimesh.Trimesh(vertices=v, faces=f, process=False)
            m.export(out / f"sherd_{i:02d}" / f"{name}.ply")
            scene.append(m)
        trimesh.util.concatenate(scene).export(out / "assembled" / f"{name}.ply")

    (out / "README.txt").write_text(
        README.format(obj=args.object, n=len(pieces), loss="\n".join(loss_lines)))
    print(f"  wrote {out}", flush=True)


if __name__ == "__main__":
    main()
