"""Write a Juglet HDF5 (juglet_gt or a re-seated copy) as ONE coloured PLY in millimetres, for
the visual-qa viewer (pr-workspace uneven-wear ticket 08: old and new pose side by side).

Every sherd keeps its own colour on both sides (sherd 2 tan, sherd 7 teal, the two the
conservator is asked to look at). The scale comes from --scale-from (the original file), so a
re-seated copy, whose extent moved slightly, is drawn in the same millimetres.

    python scripts/export_juglet_ply.py <in.hdf5> <out.ply> --scale-from juglet_gt.hdf5
"""
import argparse
import sys
from pathlib import Path

import h5py
import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parent))
from diagnose_juglet_selection import vessel_scale                 # noqa: E402

COLOURS = {0: (150, 150, 150), 1: (91, 141, 214), 2: (210, 170, 110), 3: (140, 110, 190),
           4: (220, 120, 120), 5: (120, 180, 120), 6: (200, 200, 90), 7: (60, 170, 170),
           8: (230, 150, 200)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("inp")
    p.add_argument("out")
    p.add_argument("--scale-from", required=True)
    p.add_argument("--group", default="juglet_gt")
    p.add_argument("--juglet-mm", type=float, default=65.0)
    a = p.parse_args()
    jf = vessel_scale(a.scale_from, a.group, a.juglet_mm)
    meshes = []
    with h5py.File(a.inp, "r") as h:
        tag = sorted(t for t in h[a.group] if "pieces" in h[a.group][t])[0]
        g = h[a.group][tag]["pieces"]
        for k in sorted(g.keys(), key=lambda s: (len(s), s)):
            v = np.asarray(g[k]["vertices"][:], float) * jf
            f = np.asarray(g[k]["faces"][:], np.int64)
            m = trimesh.Trimesh(v, f, process=False)
            m.visual.vertex_colors = np.tile((*COLOURS[int(k) % 9], 255), (len(v), 1))
            meshes.append(m)
    whole = trimesh.util.concatenate(meshes)
    whole.export(a.out)
    print(f"wrote {a.out}: {len(meshes)} sherds, {len(whole.vertices)} vertices, x{jf:.4f} "
          f"to mm (from {a.scale_from})")


if __name__ == "__main__":
    main()
