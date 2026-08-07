"""Was the "wear runs backwards on eggshell" result just the chip holes?

The original finding was that wear made eggshell ROUGHER instead of smoother:
egg1 +198% at a 1.2% probe, egg2 +77%, against -48% to -62% on thick pots. That
is what started this whole investigation.

The conservator has since inspected the exports and found the eggs fine except
for one thing -- the chips punch holes, and on the eggshell there are many of
them. That is confirmed independently: every sherd is open at every wear level,
and the hole count is exactly chip_count x sherds.

Which makes an obvious alternative explanation, and I did not consider it.

A hole has a rim. A rim is a free edge where the surface simply stops, and the
surface directions around it disagree completely -- which is what the roughness
measure is built to detect. On a thick pot a chip hole is small against the
whole break face and barely registers. On an eggshell the hole rim is a large
part of the surface, so it could dominate the reading on its own.

If so, the eggs were never getting rougher from crushing. They were getting
rougher because we punched holes in them, and the roughness measure was
faithfully reporting the rims of those holes.

The test is one flag. Run the same comparison with chipping OFF. Nothing else
changes.

  roughness still RISES  -> something really does run backwards on thin shells
  roughness FALLS        -> the finding was the chip holes all along, and the
                            wear model's only fault is that chips are punctures

Usage:
  python scripts/test_roughness_without_chips.py
"""

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wear_ops import apply_wear  # noqa: E402

PROBE_RADIUS = 0.012


def relief_at(v, f, radius_frac, n_pts=4000, seed=0):
    from scipy.spatial import cKDTree

    m = trimesh.Trimesh(vertices=v.astype(np.float64), faces=f.astype(np.int64),
                        process=False)
    if len(m.faces) < 8 or max(m.extents) <= 0:
        return 0.0
    scale = float(max(m.extents))
    pts, fid = trimesh.sample.sample_surface(m, n_pts, seed=seed)
    fn = m.face_normals[fid]
    tree = cKDTree(pts)
    rel = np.zeros(len(pts))
    for i, ne in enumerate(tree.query_ball_point(pts, radius_frac * scale)):
        if len(ne) >= 3:
            rel[i] = 1.0 - float(np.clip(fn[ne] @ fn[i], -1, 1).mean())
    return float(np.percentile(rel, 90))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", default="/data/gpfs/projects/punim2657/TORA/dataset/real_finetune.hdf5")
    ap.add_argument("--dataset", default="real_finetune")
    ap.add_argument("--objects",
                    default="egg__egg1,egg__egg2,egg__egg3,ceramics__plate,"
                            "ceramics__narrow_bottle3,ceramics__blue_pot")
    args = ap.parse_args()

    print("Does the roughness still run backwards with chipping OFF?")
    print("  Same wear, same probe, one flag changed.")
    print()
    print(f"  {'object':<26s} {'fresh':>8s} {'with chips':>11s} {'no chips':>10s} "
          f"{'chips':>8s} {'no chips':>9s}")

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

            base = dict(smoothing=1.0, smoothing_passes=3, recession=0.0020)
            with_chips = apply_wear(pieces, chip_count=4, chip_size=0.0022, **base)
            no_chips = apply_wear(pieces, chip_count=0, chip_size=0.0, **base)

            a = float(np.mean([relief_at(v, f, PROBE_RADIUS) for v, f in pieces]))
            b = float(np.mean([relief_at(v, f, PROBE_RADIUS) for v, f in with_chips]))
            c = float(np.mean([relief_at(v, f, PROBE_RADIUS) for v, f in no_chips]))
            pb = 100.0 * (b - a) / a if a > 1e-9 else float("nan")
            pc = 100.0 * (c - a) / a if a > 1e-9 else float("nan")

            print(f"  {obj:<26s} {a:>8.4f} {b:>11.4f} {c:>10.4f} "
                  f"{pb:>7.1f}% {pc:>8.1f}%", flush=True)

    print()
    print("  Last two columns are the whole test. If 'chips' is positive and")
    print("  'no chips' is negative, the eggshell was never running backwards --")
    print("  we were measuring the rims of the holes we punched in it.")


if __name__ == "__main__":
    main()
