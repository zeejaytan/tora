"""Pull named objects out of a training HDF5 as meshes you can open.

WHY THIS EXISTS. Every solidity finding on this corpus has so far been argued
from a section I chose the plane for, and choosing the plane is exactly how the
Plate came to look filled when it was not (`GATE_B_DECISION.md`). Handing over
the mesh removes me from that step: the conservator picks the viewpoint, picks
the clip, and can toggle fragments off to look straight at a break face.

WHAT IT WRITES, per object:

  <tag>/piece_00.ply ...     one file per fragment, so hiding a fragment in the
                             viewer exposes its neighbour's break face. THAT is
                             the direct test of solid vs shell: a sherd's break
                             is a narrow ribbon through a wall, a solid's is a
                             broad face across the body.
  <tag>__assembled.ply       all fragments in one file, each a different colour
  <tag>__halved.ply          the assembled object clipped in half and capped,
                             so the inside is visible without any clipping tool

UNITS ARE NOT MILLIMETRES. This file stores each object centred and scaled so
its largest coordinate is 0.5 -- one shared factor per object, so the relative
geometry is untouched but nothing is life-size. Every measurement quoted about
these objects is therefore a PERCENTAGE OF OBJECT SIZE, and the meshes here are
in those same normalised units. Do not read a wall thickness off them in mm.

Usage:
  python scripts/export_object_meshes.py \
      --src dataset/bbad_vessels.hdf5 --dataset bbad_vessels \
      --tags Vase__bcf5a4b764dd__mode_15__fresh,Bowl__4417f06a1a1d__mode_19__fresh \
      --out artifacts/meshes
"""

import argparse
from pathlib import Path

import h5py
import numpy as np
import trimesh

# Distinguishable at a glance and colour-blind safe enough to tell fragments
# apart in a viewer; cycled if an object has more pieces than colours.
PALETTE = np.array([
    [230, 159, 0], [86, 180, 233], [0, 158, 115], [240, 228, 66],
    [0, 114, 178], [213, 94, 0], [204, 121, 167], [153, 153, 153],
    [120, 94, 240], [26, 133, 255], [212, 17, 89], [64, 176, 166],
], dtype=np.uint8)


def load_pieces(grp):
    """(verts, faces) per fragment, in the order the file stores them."""
    pg = grp["pieces"]
    keys = sorted(pg.keys(), key=lambda s: int(s) if s.isdigit() else s)
    out = []
    for k in keys:
        v = np.asarray(pg[k]["vertices"][:], dtype=np.float64)
        f = (np.asarray(pg[k]["faces"][:], dtype=np.int64)
             if "faces" in pg[k] else None)
        if f is None or not len(f):
            continue
        out.append((v, f))
    return out


def describe(v, f):
    """The numbers a viewer cannot show you, on the same mesh you are opening.

    Watertightness matters here: `volume` is meaningless on an open surface, so
    a solidity claim made from volume on a leaky mesh is not a claim at all.
    """
    m = trimesh.Trimesh(vertices=v, faces=f, process=False)
    wt = bool(m.is_watertight)
    return {
        "verts": len(v), "faces": len(f),
        "area": float(m.area),
        "volume": (abs(float(m.volume)) if wt else float("nan")),
        "watertight": wt,
    }


def halve(mesh, out_path):
    """Clip the assembled object through its centre and cap the cut.

    The whole point of the export is to let someone see whether there is a
    cavity, and a closed surface hides its own interior. Capping matters: an
    uncapped clip shows the far wall through the hole and reads as hollow
    whatever the truth is.
    """
    try:
        origin = mesh.bounds.mean(axis=0)
        # Cut across the object's THINNEST principal direction, which is the
        # one that opens the largest section -- the same reason the screen
        # averages three cuts rather than trusting one.
        ext = mesh.extents
        normal = np.zeros(3)
        normal[int(np.argmax(ext))] = 1.0
        half = trimesh.intersections.slice_mesh_plane(
            mesh, plane_normal=-normal, plane_origin=origin, cap=True)
        if half is None or not len(half.faces):
            return False
        half.export(out_path)
        return True
    except Exception as e:                                    # noqa: BLE001
        print("    (no halved mesh: " + str(e) + ")")
        return False


def export_one(dg, tag, outdir):
    if tag not in dg:
        near = [k for k in dg.keys() if k.startswith(tag.split("__")[0])][:4]
        print("MISSING " + tag + "   nearby: " + ", ".join(near))
        return
    pieces = load_pieces(dg[tag])
    if not pieces:
        print("MISSING geometry for " + tag)
        return

    d = Path(outdir) / tag
    d.mkdir(parents=True, exist_ok=True)
    print("")
    print("=" * 74)
    print(tag + "   " + str(len(pieces)) + " fragments")
    print("=" * 74)
    print("  piece   verts   faces        area      volume   watertight")

    parts = []
    for i, (v, f) in enumerate(pieces):
        s = describe(v, f)
        col = PALETTE[i % len(PALETTE)]
        m = trimesh.Trimesh(vertices=v, faces=f, process=False)
        m.visual.vertex_colors = np.tile(
            np.append(col, 255), (len(v), 1)).astype(np.uint8)
        m.export(d / ("piece_%02d.ply" % i))
        parts.append(m)
        print("  %5d  %6d  %6d  %10.5f  %10.5f   %s"
              % (i, s["verts"], s["faces"], s["area"], s["volume"],
                 "yes" if s["watertight"] else "NO"))

    asm = trimesh.util.concatenate(parts)
    asm.export(Path(outdir) / (tag + "__assembled.ply"))

    # THE NUMBER THE PICTURE WAS ARGUED FROM, on the mesh being handed over, so
    # the two cannot drift apart. 2V/A is a mean thickness: for a thin shell it
    # is the wall, for a solid it is a large fraction of the object.
    ext = float(np.linalg.norm(asm.extents))
    tot_area = float(asm.area)
    vol = abs(float(asm.volume))
    print("  ----")
    print("  assembled: extent %.4f   area %.4f   volume %.4f"
          % (ext, tot_area, vol))
    if tot_area > 0:
        print("  2V/A over the WHOLE surface (break faces included, so this is "
              "a floor): %.2f%% of object" % (100.0 * 2.0 * vol / tot_area / ext))

    ok = halve(asm, Path(outdir) / (tag + "__halved.ply"))
    print("  wrote " + str(d) + "/piece_NN.ply, " + tag + "__assembled.ply"
          + (", " + tag + "__halved.ply" if ok else ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--dataset", default="bbad_vessels")
    ap.add_argument("--tags", required=True, help="comma separated group names")
    ap.add_argument("--out", default="artifacts/meshes")
    a = ap.parse_args()

    Path(a.out).mkdir(parents=True, exist_ok=True)
    with h5py.File(a.src, "r") as h:
        dg = h[a.dataset]
        for tag in [t.strip() for t in a.tags.split(",") if t.strip()]:
            export_one(dg, tag, a.out)

    print("")
    print("UNITS ARE NORMALISED, NOT MILLIMETRES: each object is centred and "
          "scaled so its largest coordinate is 0.5.")
    print("Everything quoted about these objects is a percentage of object "
          "size, and these meshes are in those same units.")


if __name__ == "__main__":
    main()
