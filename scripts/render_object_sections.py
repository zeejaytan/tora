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
where a plane crosses the surface. Hollow gives two nested loops with space
between them; solid gives one. Vertex density cannot fake either.

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
    n_loop = 0
    for ent in planar.entities:
        pts = planar.vertices[ent.points]
        ax.plot(100 * pts[:, 0] / size, 100 * pts[:, 1] / size,
                lw=0.9, color="#1f77b4")
        n_loop += 1
    ax.set_aspect("equal")
    ax.set_title(title + "\n" + str(n_loop) + " loops in this cut", fontsize=8)
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
                 "Two nested loops = a wall with a cavity.  One loop = solid.",
                 fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.965))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.out, dpi=150)
    print("wrote " + a.out)


if __name__ == "__main__":
    main()
