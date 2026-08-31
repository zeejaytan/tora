"""Does the corpus screen's `fill` number mean what its label says?

The screen (`screen_vessel_corpus.py`, job 29765705) sorted 1053 objects into
"thin shell" through "SOLID -- not a vessel" on one scalar. The instrument was
checked against a solid sphere and two shells of known thickness, which proves
the arithmetic; it does not prove the LABEL is right on real objects with real
fractures through them.

So: eight objects picked to land on a ladder across the whole measured range,
0.04 to 0.99, each drawn as a section with its own measured fill and cell count
in the title. If the pictures walk from a thin ring to a filled lump in step
with the number, the bins mean what they say and the corpus verdict can be
reported. If they do not, the verdict cannot -- and it would be the third
solidity instrument to fail here, after loop counting and shapely
`polygons_full`.

The section is drawn with the SCANLINE fill, the same routine the screen used,
not shapely's -- shapely returns nothing on a fragmented section and that is
what put "fill n/a" on every panel of the earlier figure.

Usage:
  python scripts/render_fill_ladder.py --root . --out artifacts/fill_ladder.png
"""

import argparse
from pathlib import Path

import h5py
import numpy as np
import trimesh

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                   # noqa: E402

from measure_gap_as_network_sees import load_meshes               # noqa: E402
from screen_vessel_corpus import _fill_one_cut, fill_fraction     # noqa: E402

# object, cells, fill -- straight off artifacts/corpus_screen.csv, chosen to
# sit at roughly equal steps across the measured fill range
LADDER = [
    ("Cup__89cf9af7513e__mode_10", 0.26, 0.043),
    ("Vase__ceff9f8c32f7__mode_12", 0.48, 0.100),
    ("Vase__1654250bf1bc__mode_16", 0.91, 0.199),
    ("Mug__d0a3fdd33c7e__mode_12", 1.26, 0.352),
    ("Vase__bcf5a4b764dd__mode_15", 4.06, 0.549),
    ("Bowl__4417f06a1a1d__mode_19", 2.84, 0.747),
    ("Bowl__7ebbe5e7d05d__mode_6", 4.92, 0.898),
    ("DrinkBottle__a429f8eb0c3e__mode_11", 8.68, 0.990),
]
LEVEL = "__fresh"


def find_tag(dg, obj):
    for tag in sorted(dg.keys()):
        if tag.startswith(obj) and tag.endswith(LEVEL):
            return tag
    return None


def draw(ax, mesh, title):
    """Section on the plane that gives the MEDIAN fill, not a flattering one.

    Picking the prettiest of three cuts is how the Plate came to look filled in
    the first hollowness figure. The screen takes the median over three
    orthogonal cuts, so the picture must show the cut that produced it.
    """
    vals = [(_fill_one_cut(mesh, ax_i), ax_i) for ax_i in range(3)]
    vals = [(v, a) for v, a in vals if v is not None]
    if not vals:
        ax.set_title(title + "\n(no section)", fontsize=8)
        ax.set_axis_off()
        return
    vals.sort()
    _, axis = vals[len(vals) // 2]

    origin = mesh.bounds.mean(axis=0)
    normal = np.zeros(3)
    normal[axis] = 1.0
    size = float(np.linalg.norm(mesh.extents))
    segs = trimesh.intersections.mesh_plane(mesh, plane_normal=normal,
                                            plane_origin=origin)
    keep = [i for i in range(3) if i != axis]
    for s in segs:
        p = s[:, keep] * 100.0 / size
        ax.plot(p[:, 0], p[:, 1], lw=0.7, color="#1f77b4")
    ax.set_aspect("equal")
    ax.set_title(title, fontsize=8)
    ax.tick_params(labelsize=6)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--src", default="dataset/bbad_vessels.hdf5")
    ap.add_argument("--dataset", default="bbad_vessels")
    ap.add_argument("--out", default="artifacts/fill_ladder.png")
    a = ap.parse_args()

    fig, axes = plt.subplots(2, 4, figsize=(17, 8.5))
    with h5py.File(str(Path(a.root) / a.src), "r") as h:
        dg = h[a.dataset]
        for ax, (obj, cells, fill) in zip(axes.ravel(), LADDER):
            tag = find_tag(dg, obj)
            if tag is None:
                ax.set_title(obj + "\nnot found", fontsize=8)
                ax.set_axis_off()
                continue
            meshes = load_meshes(dg[tag])
            asm = trimesh.util.concatenate(meshes)
            got = fill_fraction(asm)
            title = (obj.split("__")[0] + "  " + obj.split("__")[1][:8] +
                     "\nscreen said fill " + format(fill, ".2f") +
                     ", redrawn " + ("n/a" if got is None
                                     else format(got, ".2f")) +
                     "   cells " + format(cells, ".2f"))
            draw(ax, asm, title)
            print(obj + "  screen " + format(fill, ".3f") + "  redrawn " +
                  ("n/a" if got is None else format(got, ".3f")), flush=True)

    fig.suptitle("Does 'fill' mean what the screen's labels say?  Eight objects "
                 "across the measured range, sections on the median cut.\n"
                 "Left = the screen calls it a thin shell.  Right = the screen "
                 "calls it solid.  The eye decides whether it is right.",
                 fontsize=11)
    fig.tight_layout()
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.out, dpi=125)
    print("wrote " + a.out)


if __name__ == "__main__":
    main()
