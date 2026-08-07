"""Does the wall estimator report thinning that did not happen?

The conservator inspected the plate, the eggshell and the bone at every wear
level and found them all fine, apart from the chip holes. My measurement says
the plate loses 29% of its wall and the eggshell 37%. Both cannot be right, and
between a conservator's eye on the actual meshes and a statistic I wrote
yesterday, the statistic is the thing to doubt.

There is a specific mechanism by which it could be wrong, and it predicts
exactly the pattern we saw.

The estimator takes each surface point and finds the nearest point whose
surface faces the OPPOSITE way. On a flat wall that is the far side of the
wall: correct. But wear ROUNDS the broken edge, and a rounded lip has surfaces
facing every direction packed into a small volume. Near that lip, the nearest
opposite-facing point becomes much closer than the wall is thick -- not because
the wall thinned, but because the edge got rounded, which is exactly what wear
is supposed to do.

That predicts the observed threshold with no crushing at all. The measurement is
taken over the fracture band. On a THICK wall the rounded lip is a small part of
that band, so the median still reports the true wall. On a THIN wall the lip is
most of the band, so the median reports the lip. The changeover would land where
the rounding radius becomes comparable to the wall -- which is the smoothing
patch size, which is where the "threshold" appeared.

So this builds a case with a KNOWN answer. Two slabs of exactly known thickness
meeting at a flat interface: a fracture with no relief, on a wall we chose. Wear
is applied. The true thickness cannot change except where material is actually
removed, and away from the immediate edge it cannot change at all.

  If the estimator reports thinning on a slab whose thickness we control,
  it is measuring edge rounding and every wall number I have reported is void.

Slab thicknesses span both sides of the smoothing patch (5%), so the claimed
threshold gets tested rather than assumed.

Usage:
  python scripts/validate_wall_estimator.py
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parent))
from probe_wall_pinch import wall_thickness_frac  # noqa: E402
from wear_ops import _band_mask, apply_wear  # noqa: E402


def slab_pair(thickness_frac, span=1.0, subdiv=240):
    """Two slabs meeting at a flat interface. Wall thickness is exact by
    construction, so any reported change is the estimator's error."""
    t = thickness_frac * span
    meshes = []
    for sign in (-1.0, 1.0):
        b = trimesh.creation.box(extents=(span * 0.5, span, t))
        b.apply_translation((sign * span * 0.25, 0.0, 0.0))
        # subdivide so vertex density resembles a real scan; the smoothing and
        # band logic are both density-sensitive
        for _ in range(3):
            if len(b.faces) < subdiv * subdiv // 8:
                b = b.subdivide()
        meshes.append((np.asarray(b.vertices, dtype=np.float64),
                       np.asarray(b.faces, dtype=np.int64)))
    return meshes


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--thicknesses", default="1.5,3.5,6.0,10.0",
                    help="wall thickness as %% of object size")
    args = ap.parse_args()

    print("Positive control: slabs of KNOWN thickness, worn.")
    print("  The true wall cannot change away from the edge. Any reported")
    print("  thinning is the estimator responding to edge ROUNDING instead.")
    print(f"  Smoothing patch is 5.0% of object size -- the claimed threshold.")
    print()
    print(f"  {'true wall':>10s} {'measured fresh':>15s} {'measured worn':>14s} "
          f"{'reported change':>16s}")

    for ts in [float(x) for x in args.thicknesses.split(",")]:
        pieces = slab_pair(ts / 100.0)
        worn = apply_wear(pieces, smoothing=1.0, smoothing_passes=3,
                          recession=0.0020, chip_count=0, chip_size=0.0)

        band, _ = _band_mask(pieces, 0, pieces[0][0])
        restrict = pieces[0][0][band] if band.any() else None
        a = wall_thickness_frac(*pieces[0], restrict=restrict)
        b = wall_thickness_frac(*worn[0], restrict=restrict)
        chg = 100.0 * (b - a) / a if np.isfinite(a) and a > 0 else float("nan")

        flag = ""
        if np.isfinite(chg) and chg < -12.3:      # the measured noise floor
            flag = "  <-- FALSE thinning: nothing was crushed"
        print(f"  {ts:>9.1f}% {a * 100:>14.2f}% {b * 100:>13.2f}% "
              f"{chg:>15.1f}%{flag}", flush=True)

    print()
    print("If thinning is reported here, the wall numbers for the plate, the")
    print("eggshell and the narrow bottles are artifacts of correct edge")
    print("rounding, and the only real fault is the chip holes.")


if __name__ == "__main__":
    main()
