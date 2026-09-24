"""Pose the real Juglet sherd meshes with one TORA attempt, for visual-qa.

TORA writes point clouds, which the viewer does not take. Each sherd's points
sit in the result file twice, in the same order: at the correct place
(pts_gt) and where TORA put them as solid sherds (generations_proposed, one rigid
move per sherd -- the raw output may bend sherds). A rigid fit between the
two is the move TORA made to that sherd; applying it to the sherd's mesh
gives a mesh attempt the conservator can inspect beside the correct one.

Writes two coloured PLYs in millimetres (one colour per sherd, same on both
sides), and prints the fit residuals so a bad fit cannot pass silently.

Usage (from C:\\PR\\tora):
  python .scratch/anchor-choice/scripts/pose_meshes.py <npz> <attempt> <out_dir>
"""
import sys
from pathlib import Path

import h5py
import numpy as np
import trimesh
from scipy.spatial import cKDTree

sys.path.insert(0, "scripts")
from readout import part_slices  # noqa: E402

VESSEL_MM = 65.0  # longest side of the reassembled Juglet (juglet-sfs ticket 01)
COLOURS = np.array([[31, 119, 180], [214, 39, 40], [44, 160, 44], [148, 103, 189],
                    [255, 127, 14], [140, 86, 75], [23, 190, 207], [227, 119, 194],
                    [188, 189, 34]], np.uint8)


def kabsch(a, b):
    """R, t with R @ a + t ~ b."""
    ca, cb = a.mean(0), b.mean(0)
    u, _, vt = np.linalg.svd((a - ca).T @ (b - cb))
    d = np.sign(np.linalg.det(vt.T @ u.T))
    r = vt.T @ np.diag([1, 1, d]) @ u.T
    return r, cb - r @ ca


def main():
    npz, t, out = Path(sys.argv[1]), int(sys.argv[2]), Path(sys.argv[3])
    d = np.load(npz, allow_pickle=True)
    gt, pred = d["pts_gt"].astype(float), d["generations_proposed"][t].astype(float)
    sl = list(part_slices(d["points_per_part"]))
    with h5py.File("artifacts/juglet_gt.hdf5", "r") as f:
        g = f["juglet_gt/Juglet-000/pieces"]
        meshes = [(g[f"{s}/vertices"][:], g[f"{s}/faces"][:]) for s in range(len(sl))]

    # Mesh file frame -> TORA frame: one similarity for the whole pot, found
    # from the bounding boxes and then checked point by point below.
    allv = np.vstack([v for v, _ in meshes])
    k = np.ptp(gt, 0).max() / np.ptp(allv, 0).max()
    off = (gt.min(0) + gt.max(0)) / 2 - k * (allv.min(0) + allv.max(0)) / 2
    tree = cKDTree(k * allv + off)
    gap = tree.query(gt)[0]
    mm = VESSEL_MM / np.ptp(gt, 0).max()
    print(f"mesh-to-points check: median {np.median(gap) * mm:.3f} mm, "
          f"max {gap.max() * mm:.3f} mm (must be near 0)")
    if np.median(gap) * mm > 0.5:
        raise SystemExit("refusing: mesh frame does not match the result's points")

    left, right = [], []
    for s, ((p, q), (v, fc)) in enumerate(zip(sl, meshes)):
        r, tr = kabsch(gt[p:q], pred[p:q])
        res = np.linalg.norm((gt[p:q] @ r.T + tr) - pred[p:q], axis=1)
        print(f"sherd {s}: rigid-fit residual median {np.median(res) * mm:.3f} mm")
        vt = k * v + off
        col = np.tile(COLOURS[s], (len(v), 1))
        left.append(trimesh.Trimesh(vt * mm, fc, vertex_colors=col, process=False))
        right.append(trimesh.Trimesh((vt @ r.T + tr) * mm, fc, vertex_colors=col,
                                     process=False))
    out.mkdir(parents=True, exist_ok=True)
    trimesh.util.concatenate(left).export(out / "correct.ply")
    trimesh.util.concatenate(right).export(out / f"attempt{t}.ply")
    print("wrote", out / "correct.ply", out / f"attempt{t}.ply")


if __name__ == "__main__":
    main()
