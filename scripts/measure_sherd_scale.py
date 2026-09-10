"""What physical wear depth does each rung of the erosion ladder actually apply?

WHY THIS EXISTS. `erode_fracture_band` sets its smoothing radius from the
SHERD, not the vessel:

    piece_scale = float(max(m.extents))                  # fracture_mesh_ops.py:168
    r           = strength * kernel_frac_max * piece_scale    # kernel_frac_max = 0.05
    sigma       = 0.5 * r

so the wear depth at rung eNNN is `0.025 * max(extents) * strength`
millimetres and differs per sherd. `max(mesh.extents)` was never recorded
anywhere in this repo, so every absolute wear figure quoted so far rests on an
assumed "~40 mm sherd". Only two pots have a measured figure at all --
0.40-0.67 mm on `blue_pot` against 1.0-1.67 mm on `plate`
(wear_fracture_spectrum.py:150-151), a 2.5x spread that is itself the reason
pots are never pooled.

WHAT IT DECIDES. Whether a rung's displacement is larger than the point
spacing of the reference it is compared against. The Juglet's break-face
vertices sit 0.29-0.48 mm apart, so a rung that moves the surface less than
that is below the reference's own noise floor and cannot be compared to it,
regardless of how well the instrument works. This script says which rungs
those are, per pot, from measurement instead of assumption.

It also reports 2V/A wall thickness per sherd, absent from the repo for both
the eight pots and the Juglet, because the patch-radius rule is a ratio to
wall thickness and is never transferable in millimetres.

Read at e000 only: the ladder is pure vertex displacement on identical
topology and the rescale drifts at worst 0.43% across rungs.

Usage:
  python scripts/measure_sherd_scale.py \
      --erosion dataset/erosion_ceramics.hdf5 \
      --raw     dataset/fractura_real.hdf5 \
      --juglet  dataset/juglet_gt.hdf5 \
      --out     artifacts/sherd_scale.json
"""

import argparse
import json
from pathlib import Path

import h5py
import numpy as np
import trimesh

STRENGTH = {"e025": 0.25, "e050": 0.50, "e075": 0.75, "e100": 1.00}
KERNEL_FRAC_MAX = 0.05          # fracture_mesh_ops.py:112
JUGLET_SPACING = (0.29, 0.48)   # O7-wear-grounding.md:312, break-face vertices


def sigma_mm(extent_mm, strength):
    """The operator's Gaussian sigma in mm: 0.5 * strength * 0.05 * extent."""
    return 0.5 * strength * KERNEL_FRAC_MAX * extent_mm


def sherd_stats(v, f):
    """Extent, area and 2V/A in whatever units the vertices arrive in."""
    m = trimesh.Trimesh(vertices=v, faces=f, process=False)
    area = float(m.area)
    # 2V/A is a thickness only for a thin shell; abs() guards inverted winding
    thick = (2.0 * abs(float(m.volume)) / area) if area > 0 else float("nan")
    return dict(extent=float(max(m.extents)), wall_2va=thick,
                area=area, n_vertices=int(len(v)))


def walk(h5_path, group, tag_filter=None):
    """Per-sherd stats for every tag in a group, in file units."""
    out = {}
    with h5py.File(h5_path, "r") as h:
        if group not in h:
            raise SystemExit("no group '" + group + "' in " + h5_path +
                             "; top level: " + str(list(h.keys())))
        for tag in sorted(h[group].keys()):
            if tag_filter and tag_filter not in tag:
                continue
            node = h[group][tag]
            if "pieces" not in node:
                continue
            g = node["pieces"]
            out[tag] = [sherd_stats(
                np.asarray(g[k]["vertices"][:], dtype=np.float64),
                np.asarray(g[k]["faces"][:], dtype=np.int64))
                for k in sorted(g.keys(), key=lambda s: (len(s), s))]
    return out


def raw_scales(raw_path, raw_group):
    """Same rescale as wear_fracture_spectrum.raw_scales: max|v| / 0.5."""
    scale_of = {}
    with h5py.File(raw_path, "r") as fr:
        if raw_group not in fr:
            raise SystemExit("no group '" + raw_group + "' in " + raw_path +
                             "; top level: " + str(list(fr.keys())))
        for pot in sorted(fr[raw_group].keys()):
            g = fr[raw_group][pot]["pieces"]
            mx = 0.0
            for k in sorted(g.keys()):
                a = np.asarray(g[k]["vertices"][:], dtype=np.float64)
                mx = max(mx, float(np.abs(a).max()))
            scale_of[pot] = mx / 0.5
    return scale_of


def juglet_union_extent(h5_path, group):
    """Longest side of the ASSEMBLED vessel, in file units.

    The fragments sit in their ground-truth pose in this file, so their union
    is the vessel. Per-fragment extents cannot give this: a fragment is
    smaller than the pot it came from.
    """
    lo = np.full(3, np.inf)
    hi = np.full(3, -np.inf)
    with h5py.File(h5_path, "r") as h:
        for tag in sorted(h[group].keys()):
            node = h[group][tag]
            if "pieces" not in node:
                continue
            for k in node["pieces"].keys():
                v = np.asarray(node["pieces"][k]["vertices"][:],
                               dtype=np.float64)
                lo = np.minimum(lo, v.min(axis=0))
                hi = np.maximum(hi, v.max(axis=0))
    return float((hi - lo).max()) if np.isfinite(lo).all() else 0.0


def report(title, per_tag, unit):
    print("")
    print("=" * 78)
    print(title)
    print("=" * 78)
    lo_j, hi_j = JUGLET_SPACING
    for tag in sorted(per_tag):
        sherds = per_tag[tag]
        ext = np.array([s["extent"] for s in sherds])
        wall = np.array([s["wall_2va"] for s in sherds])
        wall = wall[np.isfinite(wall)]
        print("")
        print(tag + "   " + str(len(ext)) + " sherds")
        print("  sherd longest side   " + format(ext.min(), "6.2f") + " - " +
              format(ext.max(), "6.2f") + " " + unit + "   (median " +
              format(float(np.median(ext)), "6.2f") + ")")
        if len(wall):
            print("  wall 2V/A            " + format(wall.min(), "6.2f") +
                  " - " + format(wall.max(), "6.2f") + " " + unit +
                  "   (median " + format(float(np.median(wall)), "6.2f") + ")")
        if unit != "mm":
            continue
        print("  wear depth applied (sigma, mm) and whether it clears the")
        print("  Juglet's own point spacing of " + format(lo_j, ".2f") + "-" +
              format(hi_j, ".2f") + " mm:")
        for rung in ("e025", "e050", "e075", "e100"):
            s = sigma_mm(ext, STRENGTH[rung])
            if s.min() >= hi_j:
                verdict = "clears it on every sherd"
            elif s.max() < lo_j:
                verdict = "BELOW IT ON EVERY SHERD -- not comparable"
            else:
                frac = float(np.mean(s >= hi_j))
                verdict = ("clears it on " + format(100 * frac, ".0f") +
                           "% of sherds -- partial")
            print("    " + rung + "  sigma " + format(s.min(), "5.2f") + " - " +
                  format(s.max(), "5.2f") + " mm  (median " +
                  format(float(np.median(s)), "5.2f") + ")   " + verdict)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--erosion", required=True)
    p.add_argument("--erosion-group", default="erosion_ceramics")
    p.add_argument("--rung", default="e000")
    p.add_argument("--raw", required=True)
    p.add_argument("--raw-group", default="ceramics")
    p.add_argument("--juglet")
    p.add_argument("--juglet-group", default="juglet_gt")
    p.add_argument("--juglet-mm", type=float, default=65.0,
                   help="assembled vessel longest side, mm "
                        "(O7-wear-grounding.md:83)")
    p.add_argument("--out", default="artifacts/sherd_scale.json")
    a = p.parse_args()

    scales = raw_scales(a.raw, a.raw_group)
    print("rescale factors (max|v| / 0.5) from " + a.raw + ":")
    for k in sorted(scales):
        print("  " + k + "  x" + format(scales[k], ".4f"))

    ladder = walk(a.erosion, a.erosion_group, tag_filter=a.rung)
    if not ladder:
        raise SystemExit("no tags matching '" + a.rung + "' in group '" +
                         a.erosion_group + "'")
    pots = {}
    for tag, sherds in ladder.items():
        pot = tag.replace("_" + a.rung, "")
        sc = scales.get(pot)
        if sc is None:
            print("WARNING no rescale for '" + pot + "' -- SKIPPED, would be "
                  "in ladder units and silently 100x wrong")
            continue
        pots[pot] = [dict(extent=s["extent"] * sc,
                          wall_2va=s["wall_2va"] * sc,
                          area=s["area"] * sc * sc,
                          n_vertices=s["n_vertices"]) for s in sherds]
    report("EIGHT POTS at " + a.rung + ", rescaled to real scan millimetres",
           pots, "mm")

    jug = {}
    if a.juglet:
        jug = walk(a.juglet, a.juglet_group)
        # The Juglet has no raw counterpart to rescale from, so its file units
        # are set against the one measured figure: the assembled vessel is
        # 65 mm on its longest side (O7-wear-grounding.md:83). Older notes use
        # a "~100 mm juglet" convention -- flagged at O7:89 -- so the factor is
        # printed rather than folded in silently.
        union = juglet_union_extent(a.juglet, a.juglet_group)
        jf = (a.juglet_mm / union) if union > 0 else 1.0
        print("")
        print("juglet assembled longest side, file units: " +
              format(union, ".4f") + "   taken as " +
              format(a.juglet_mm, ".1f") + " mm  ->  x" + format(jf, ".4f"))
        jug = {t: [dict(extent=s["extent"] * jf,
                        wall_2va=s["wall_2va"] * jf,
                        area=s["area"] * jf * jf,
                        n_vertices=s["n_vertices"]) for s in v]
               for t, v in jug.items()}
        # No sigma table: the Juglet is the reference, not a rung of our
        # ladder. Its wall thickness is what the pots' patch radii scale to.
        report("JUGLET, scaled to a " + format(a.juglet_mm, ".1f") +
               " mm vessel", jug, "mm (reference, no ladder)")

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dict(pots=pots, juglet=jug, rung=a.rung,
                                   kernel_frac_max=KERNEL_FRAC_MAX,
                                   strength=STRENGTH,
                                   juglet_vessel_mm=a.juglet_mm,
                                   juglet_spacing_mm=JUGLET_SPACING,
                                   units="millimetres throughout"),
                              indent=2))
    print("")
    print("wrote " + str(out))


if __name__ == "__main__":
    main()
