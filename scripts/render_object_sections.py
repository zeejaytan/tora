"""Are the training "vessels" hollow pots, or solid blobs shaped like pots?

This is a re-check, not a new question, and it exists because a number came back
that contradicts a finding already in `docs/notes/GATE_B_DECISION.md`.

That note says the corpus is hollow: `wear_ops._wall_estimate` found a wall in
72 of 72 sampled objects, median 0.95-3.10% of object. But
`measure_wall_vs_sampling.py`, whose ray caster is checked against shells of
known thickness (`--selftest`, within 0.1%), reads three of the eight training
objects at 10-15% of object:

    BeerBottle  12.66%      Bowl     1.10%
    Bottle      14.72%      Teapot   0.81%
    DrinkBottle 10.39%      Vase     1.42% / 1.21%
                            Mug      3.06%

The five thin ones agree with the earlier note almost exactly. Only the three
thick ones disagree -- which is the signature of a REACH limit, not of noise.
`_wall_estimate` thins the reference set to 20,000 points (spacing ~0.4% of
object on these meshes) and takes 64 neighbours, so it can see roughly 2% of
object and no further. Past that it returns 0.0, and 0.0 is dropped rather than
counted, so a solid object leaves the median instead of raising it.

That is an argument, though, and an argument is not evidence -- especially an
argument that happens to favour my own new measurement. So: cut the objects open
and look.

A SECTION, not a vertex scatter. `mesh.section()` returns the actual polygon
where a plane crosses the surface, and the polygon is shaded, so material and
cavity are distinguishable by eye. Vertex density cannot fake either.

Counting loops does NOT work here and the first version of this figure tried
it: the objects are already broken into sherds, so every sherd contributes a
closed loop whether the vessel is hollow or not, and all six objects came back
with 6-42 loops per cut. The number printed instead is the fraction of the
outline's area that is material -- which is what "hollow" actually means, and
unlike the picture it does not depend on which way the plane was turned.

Three cuts per object, one perpendicular to each principal axis, because a
single slab direction can lie: the Plate in the earlier hollowness figure looked
filled purely because its thin axis was the slab axis, so the cut caught the
whole disc face-on instead of sectioning it (`GATE_B_DECISION.md`).

Usage:
  python scripts/render_object_sections.py --out artifacts/object_sections.png
"""

import argparse
from pathlib import Path

import h5py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import trimesh

from measure_gap_as_network_sees import load_meshes

ROOT = Path("/data/gpfs/projects/punim2657/TORA")

# The three that read thick and three that read thin, so the picture is a
# comparison rather than a demonstration.
OBJECTS = [
    ("Bottle__81bbf3134d1c", "__fresh", "Bottle  (ray says 14.7%)"),
    ("BeerBottle__2927d6c8438f", "__fresh", "BeerBottle  (ray says 12.7%)"),
    ("DrinkBottle__1ef68777bfdb", "__fresh", "DrinkBottle  (ray says 10.4%)"),
    ("Teapot__7c381f85d3b6", "__fresh", "Teapot  (ray says 0.8%)"),
    ("Vase__7545c5b77008", "__fresh", "Vase  (ray says 1.4%)"),
    ("Bowl__50ad83141272", "__fresh", "Bowl  (ray says 1.1%)"),
]


def find_tag(dg, obj, suffix):
    for tag in sorted(dg.keys()):
        if tag.startswith(obj) and tag.endswith(suffix):
            return tag
    return None


def assemble(meshes):
    return trimesh.util.concatenate(meshes)


def fill_fraction(planar):
    """How much of the cut is material, versus the area its outline encloses.

    The loop count is useless here: the objects are already fragmented, so every
    sherd contributes its own closed loop whether the vessel is hollow or not.
    Fill fraction is not fooled by that, and unlike the picture it does not
    depend on which way the plane was turned. Solid -> ~1. A wall of t on a
    vessel of radius r -> roughly 2t/r.
    """
    try:
        from shapely.ops import unary_union
        from shapely.geometry import Polygon
        polys = planar.polygons_full
    except Exception:
        return None
    if len(polys) == 0:
        return None
    uni = unary_union(list(polys))
    geoms = getattr(uni, "geoms", [uni])
    filled = outer = 0.0
    for g in geoms:
        filled += g.area
        outer += Polygon(g.exterior).area
    if outer <= 0:
        return None
    return filled / outer


def draw(ax, mesh, axis, title):
    """Cut one plane through the centroid, perpendicular to `axis`."""
    origin = mesh.bounds.mean(axis=0)
    normal = np.zeros(3)
    normal[axis] = 1.0
    size = float(np.linalg.norm(mesh.extents))
    try:
        sec = mesh.section(plane_origin=origin, plane_normal=normal)
    except Exception:
        sec = None
    if sec is None:
        ax.set_title(title + "\n(no intersection)", fontsize=8)
        ax.set_axis_off()
        return
    planar, _ = sec.to_planar()

    # shade the material, so the picture and the number say the same thing
    try:
        for poly in planar.polygons_full:
            xy = 100 * np.asarray(poly.exterior.coords) / size
            ax.fill(xy[:, 0], xy[:, 1], color="#c6d9ec", lw=0)
            for ring in poly.interiors:
                xy = 100 * np.asarray(ring.coords) / size
                ax.fill(xy[:, 0], xy[:, 1], color="white", lw=0)
    except Exception:
        pass

    for ent in planar.entities:
        pts = planar.vertices[ent.points]
        ax.plot(100 * pts[:, 0] / size, 100 * pts[:, 1] / size,
                lw=0.9, color="#1f77b4")
    ff = fill_fraction(planar)
    tail = "fill n/a" if ff is None else ("%.0f%% of the outline is material"
                                          % (100 * ff))
    ax.set_aspect("equal")
    ax.set_title(title + "\n" + tail, fontsize=8)
    ax.tick_params(labelsize=7)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--src", default="dataset/bbad_vessels.hdf5")
    ap.add_argument("--dataset", default="bbad_vessels")
    ap.add_argument("--out", default="artifacts/object_sections.png")
    a = ap.parse_args()

    path = Path(a.root) / a.src
    fig, axes = plt.subplots(len(OBJECTS), 3,
                             figsize=(10, 3.1 * len(OBJECTS)))
    with h5py.File(path, "r") as h:
        dg = h[a.dataset]
        for row, (obj, suffix, label) in enumerate(OBJECTS):
            tag = find_tag(dg, obj, suffix)
            if tag is None:
                axes[row][0].set_title("no tag for " + obj, fontsize=8)
                continue
            mesh = assemble(load_meshes(dg[tag]))
            for col, axis in enumerate(range(3)):
                draw(axes[row][col], mesh,
                     axis, label + "\ncut across axis " + "XYZ"[axis])
            del mesh

    fig.suptitle("Cross-sections of the training vessels, assembled.\n"
                 "Shaded = material.  A hollow vessel is a thin rim of shading;\n"
                 "a solid one is filled to the outline.",
                 fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.965))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.out, dpi=150)
    print("wrote " + a.out)


if __name__ == "__main__":
    main()
