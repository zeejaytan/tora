"""How far did each rung of the erosion ladder actually move the surface?

Measured, not inferred. The ladder's topology is byte-identical at every rung
(pure vertex displacement, verified on four pots in job 30356470), so vertex
i at e000 and vertex i at e100 are the same point on the same pot, and the
wear depth is simply the distance between them. No model, no kernel algebra,
no assumption.

WHY THIS IS NEEDED, given that measure_sherd_scale.py already reports a sigma
per rung. Sigma is the WIDTH OF THE SMOOTHING, not the DEPTH OF REMOVAL, and
the two are not interchangeable: smoothing a nearly-flat surface with a wide
kernel moves it very little. Worse, the nominal kernel does not survive
contact with the code. `erode_fracture_band` takes

    dist, idx = cKDTree(self_pts).query(verts[band], k=knn,     # knn = 48
                                        distance_upper_bound=r)

so at most 48 surface samples are ever used, drawn from a FIXED 20,000 per
sherd. Once r exceeds the radius that holds 48 of those samples the extra
radius buys nothing, every neighbour sits well inside sigma and receives
weight ~1, and the target degenerates to the unweighted centroid of the 48
nearest samples. The nominal `0.05 * max(extents) * strength` then describes
nothing that happens. That is the saturation from e075 already noted in
wear_fracture_spectrum.py; this script does not reason about it, it measures
past it.

WHAT IT DECIDES. Whether a rung moves the surface further than the point
spacing of the reference it is compared against -- the Juglet's break-face
vertices sit 0.29-0.48 mm apart. A rung below that cannot be compared to the
Juglet however good the instrument is. measure_sherd_scale.py answered this
with nominal sigma, which is the wrong quantity; this answers it with the
displacement itself.

Reported on the band that moved, not on the whole sherd: most vertices are
nowhere near a break and their displacement is exactly zero, which would drag
every average to nothing.
"""

import argparse
import json
from pathlib import Path

import h5py
import numpy as np

RUNGS = ["e025", "e050", "e075", "e100"]
JUGLET_SPACING = (0.29, 0.48)   # O7-wear-grounding.md:312, break-face vertices


def pot_names(h5, group, rung="e000"):
    return sorted(t.replace("_" + rung, "") for t in h5[group].keys()
                  if t.endswith("_" + rung))


def piece_verts(h5, group, tag):
    g = h5[group][tag]["pieces"]
    return {k: np.asarray(g[k]["vertices"][:], dtype=np.float64)
            for k in g.keys()}


def raw_scales(raw_path, raw_group):
    """max|v| / 0.5 per pot -- the same rescale wear_fracture_spectrum uses."""
    scale_of = {}
    with h5py.File(raw_path, "r") as fr:
        for pot in sorted(fr[raw_group].keys()):
            g = fr[raw_group][pot]["pieces"]
            mx = 0.0
            for k in sorted(g.keys()):
                a = np.asarray(g[k]["vertices"][:], dtype=np.float64)
                mx = max(mx, float(np.abs(a).max()))
            scale_of[pot] = mx / 0.5
    return scale_of


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--erosion", required=True)
    p.add_argument("--erosion-group", default="erosion_ceramics")
    p.add_argument("--raw", required=True)
    p.add_argument("--raw-group", default="ceramics")
    p.add_argument("--moved-eps", type=float, default=1e-9,
                   help="a vertex counts as in the band if it moved further "
                        "than this, in normalised units, at e100")
    p.add_argument("--out", default="artifacts/achieved_wear.json")
    a = p.parse_args()

    scales = raw_scales(a.raw, a.raw_group)
    lo_j, hi_j = JUGLET_SPACING
    result = {}

    with h5py.File(a.erosion, "r") as h:
        pots = pot_names(h, a.erosion_group)
        print("pots: " + ", ".join(pots))
        for pot in pots:
            sc = scales.get(pot)
            if sc is None:
                print("WARNING no rescale for " + pot + " -- skipped")
                continue
            base = piece_verts(h, a.erosion_group, pot + "_e000")
            print("")
            print("=" * 74)
            print(pot + "   rescale x" + format(sc, ".4f") + "   " +
                  str(len(base)) + " sherds")
            print("=" * 74)
            print("  ACHIEVED wear depth in mm -- how far the surface actually")
            print("  moved. Band = vertices that moved at all by e100.")
            per_rung = {}
            # the band is defined once, at full strength, so every rung is
            # reported over the SAME set of vertices and the rungs are
            # comparable to each other
            top = piece_verts(h, a.erosion_group, pot + "_e100")
            band = {}
            for k, v0 in base.items():
                if k not in top or top[k].shape != v0.shape:
                    print("  SHAPE MISMATCH on sherd " + k +
                          " -- topology is not identical, cannot subtract")
                    band[k] = None
                    continue
                band[k] = np.linalg.norm(top[k] - v0, axis=1) > a.moved_eps
            n_band = sum(int(b.sum()) for b in band.values() if b is not None)
            n_all = sum(len(v) for v in base.values())
            print("  band: " + str(n_band) + " of " + str(n_all) +
                  " vertices moved (" + format(100.0 * n_band / max(n_all, 1),
                                               ".1f") + "%)")
            for rung in RUNGS:
                tag = pot + "_" + rung
                if tag not in h[a.erosion_group]:
                    continue
                cur = piece_verts(h, a.erosion_group, tag)
                d = []
                for k, v0 in base.items():
                    b = band.get(k)
                    if b is None or k not in cur or cur[k].shape != v0.shape:
                        continue
                    if not b.any():
                        continue
                    d.append(np.linalg.norm(cur[k][b] - v0[b], axis=1))
                if not d:
                    continue
                d = np.concatenate(d) * sc
                med = float(np.median(d))
                p90 = float(np.percentile(d, 90))
                mx = float(d.max())
                if med >= hi_j:
                    verdict = "above the Juglet's spacing -- comparable"
                elif p90 < lo_j:
                    verdict = "BELOW IT -- the Juglet cannot register this"
                else:
                    verdict = "straddles it -- partly below the reference"
                print("    " + rung + "  median " + format(med, "5.3f") +
                      "  p90 " + format(p90, "5.3f") + "  max " +
                      format(mx, "5.3f") + " mm   " + verdict)
                per_rung[rung] = dict(median_mm=med, p90_mm=p90, max_mm=mx,
                                      n_band=int(len(d)))
            result[pot] = dict(scale=sc, n_band=n_band, n_all=n_all,
                               rungs=per_rung)

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dict(pots=result,
                                   juglet_spacing_mm=JUGLET_SPACING,
                                   units="millimetres"), indent=2))
    print("")
    print("wrote " + str(out))


if __name__ == "__main__":
    main()
