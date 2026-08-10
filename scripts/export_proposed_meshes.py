"""Export a proposed reassembly as real sherd MESHES, one file per fragment.

Asked for by the conservator, 2026-08-10, to answer a question the renders
cannot: is the model's failure a matter of getting the ROTATIONS wrong, or can
these sherds simply not form a better pot? Point-cloud pictures cannot be picked
up and turned. Meshes can — open them in MeshLab or Blender, rotate a sherd by
hand, and see whether a better join exists at all.

That distinction decides what to do next. If the sherds CAN be seated by hand,
the geometry carries enough information and the model is choosing badly, so the
work is on the model. If they cannot, no model will, and the work is on the
data — better scans, or accepting the pot is not reassemblable from geometry.

HOW THE POSE IS RECOVERED, exactly, without guesswork:

  The dataloader divides the assembled object by a single scale factor
  (`up_axis` is `y` here, so no axis permutation) and then, per fragment,
  centres and randomly rotates it to make the scattered input. Crucially it
  permutes the reference and input point clouds by the SAME order, so
  `pts_gt[i]` and the proposal's point `i` are the same surface point.

  That gives exact correspondence, so the fragment's pose is solved directly by
  Procrustes rather than estimated by ICP: fit `pts_gt[part] -> proposed[part]`,
  then apply that transform to the fragment's mesh.

Every step is checked rather than assumed. The script reports how far the
reference points sit from the mesh surface (validates the scale assumption) and
how well the fitted transform reproduces the proposal (validates the pose). Both
should be ~0; anything else means the export is wrong and says so.

Usage:
  python scripts/export_proposed_meshes.py \
      --npz <eval_run>/clouds/juglet_norm_sample00000.npz \
      --src dataset/juglet_norm.hdf5 --dataset juglet_norm \
      --out /path/to/out
"""

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np
import trimesh
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))

PALETTE = [
    (196, 78, 82), (85, 142, 213), (109, 178, 105), (222, 158, 54),
    (150, 110, 190), (140, 100, 80), (215, 130, 190), (128, 128, 128),
    (190, 190, 70), (90, 190, 200), (240, 140, 120), (70, 120, 90),
]


def solve_rigid(src, dst):
    """Least-squares rotation+translation carrying src onto dst (correspondence known)."""
    cs, cd = src.mean(0), dst.mean(0)
    H = (src - cs).T @ (dst - cd)
    U, S, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1.0, 1.0, d]) @ U.T
    return R, cd - R @ cs


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--npz", required=True)
    ap.add_argument("--src", required=True)
    ap.add_argument("--dataset", default="juglet_norm")
    ap.add_argument("--object", default="")
    ap.add_argument("--out", required=True)
    ap.add_argument("--attempts", default="all",
                    help="comma-separated 1-based attempt numbers, or 'all'")
    args = ap.parse_args()

    d = np.load(args.npz, allow_pickle=True)
    pts_gt = d["pts_gt"]
    proposed = d["generations_proposed"]      # (K, N, 3), rigid placement
    ppp = d["points_per_part"]
    ppp = ppp[ppp > 0]
    scale = float(d["scale"]) if "scale" in d.files else 1.0
    name = str(d["name"])
    print(f"npz: {name}   {len(ppp)} fragments, {proposed.shape[0]} attempts, "
          f"dataset scale {scale:.4f}")

    with h5py.File(args.src, "r") as h:
        ds = h[args.dataset]
        obj = args.object or (name if name in ds else sorted(ds.keys())[0])
        grp = ds[obj]
        g = grp["pieces"] if "pieces" in grp else grp
        keys = sorted(g.keys(), key=lambda s: int(s) if s.isdigit() else s)
        meshes = [trimesh.Trimesh(
            vertices=np.asarray(g[k]["vertices"][:], dtype=np.float64),
            faces=np.asarray(g[k]["faces"][:], dtype=np.int64), process=False)
            for k in keys]
    print(f"meshes: {obj}, {len(meshes)} fragments, "
          f"{sum(len(m.vertices) for m in meshes)} vertices")

    if len(meshes) != len(ppp):
        print(f"  ** fragment count mismatch: {len(meshes)} meshes vs "
              f"{len(ppp)} in the npz. Cannot pair them; aborting. **")
        return

    # The dataloader puts the object in its CENTRE-OF-MASS frame and then
    # divides by one global factor. The factor is saved in the npz; the centring
    # is not, and assuming it was the vertex mean gave a 540% mismatch on the
    # first attempt -- the reference points are an AREA-weighted surface sample,
    # whose centre is not the mean of the vertices.
    #
    # Rather than guess, solve for it. Scale is known, so only a translation is
    # unknown, and a translation is recovered by walking the meshes onto the
    # reference points a few times. The check below then confirms it or aborts.
    verts_all = [np.asarray(m.vertices, dtype=np.float64) for m in meshes]
    com = np.concatenate(verts_all, axis=0).mean(axis=0)
    for _ in range(24):
        placed = [(v - com) / scale for v in verts_all]
        tree = cKDTree(np.concatenate(placed, axis=0))
        dist, idx = tree.query(pts_gt)
        nearest = np.concatenate(placed, axis=0)[idx]
        com = com - (nearest - pts_gt).mean(axis=0) * scale
    for m, v in zip(meshes, verts_all):
        m.vertices = (v - com) / scale
    print(f"  recovered centring: {com}")

    bounds = np.concatenate([[0], np.cumsum(ppp)])
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    # --- check 1: do the reference points actually lie on these meshes? ---
    print("\n  check: reference points vs mesh surface (validates the scaling)")
    obj_size = float(np.linalg.norm(pts_gt.max(0) - pts_gt.min(0)))
    bad = False
    for i, (a, b) in enumerate(zip(bounds[:-1], bounds[1:])):
        dist = cKDTree(np.asarray(meshes[i].vertices)).query(pts_gt[a:b])[0]
        rel = float(dist.mean()) / obj_size * 100.0
        flag = "" if rel < 1.0 else "   ** does not match **"
        bad |= rel >= 1.0
        print(f"    fragment {i:>2d}: {rel:6.3f}% of object size{flag}")
    if bad:
        print("  ** the meshes and the npz do not describe the same object in the")
        print("     same frame. Export aborted rather than writing wrong poses. **")
        return

    which = (range(proposed.shape[0]) if args.attempts == "all"
             else [int(x) - 1 for x in args.attempts.split(",")])

    for k in which:
        adir = out / f"attempt{k + 1:02d}"
        adir.mkdir(parents=True, exist_ok=True)
        scene, resid = [], []
        for i, (a, b) in enumerate(zip(bounds[:-1], bounds[1:])):
            R, t = solve_rigid(pts_gt[a:b], proposed[k][a:b])
            # check 2: does that transform actually reproduce the proposal?
            fit = pts_gt[a:b] @ R.T + t
            resid.append(float(np.linalg.norm(fit - proposed[k][a:b], axis=1).mean())
                         / obj_size * 100.0)

            m = meshes[i].copy()
            m.vertices = np.asarray(m.vertices) @ R.T + t
            m.visual.vertex_colors = np.tile(
                np.array(PALETTE[i % len(PALETTE)] + (255,), dtype=np.uint8),
                (len(m.vertices), 1))
            m.export(adir / f"sherd_{i:02d}.ply")
            scene.append(m)

        trimesh.util.concatenate(scene).export(adir / "assembled.ply")
        print(f"  attempt {k + 1}: wrote {len(scene)} sherds  "
              f"(pose fit residual mean {np.mean(resid):.4f}% of object size)")
        if np.mean(resid) > 0.01:
            print("      ** residual should be ~0; the fitted pose does not")
            print("         reproduce the proposal, so treat these files as suspect **")

    # the sherds as given, unmoved, for comparison in the same units
    ref = out / "reference_scan_layout"
    ref.mkdir(parents=True, exist_ok=True)
    scene = []
    for i, m in enumerate(meshes):
        mm = m.copy()
        mm.visual.vertex_colors = np.tile(
            np.array(PALETTE[i % len(PALETTE)] + (255,), dtype=np.uint8),
            (len(mm.vertices), 1))
        mm.export(ref / f"sherd_{i:02d}.ply")
        scene.append(mm)
    trimesh.util.concatenate(scene).export(ref / "assembled.ply")
    print(f"  reference (scan layout, NOT a correct reassembly): {len(scene)} sherds")

    (out / "README.txt").write_text(f"""Proposed reassembly as meshes — {obj}
================================================================

One folder per attempt. The model was run {proposed.shape[0]} times from
different starting noise, so these are {proposed.shape[0]} independent proposals,
not refinements of one another.

  attemptNN/sherd_00.ply ... one file per fragment, in its proposed pose
  attemptNN/assembled.ply    all fragments together, same poses
  reference_scan_layout/     the sherds as scanned. NOT a correct reassembly —
                             this is the scan-table arrangement, and treating it
                             as an answer key is what invalidated an earlier
                             round of scoring on this pot.

THE QUESTION THESE ARE FOR
  Can these sherds be seated better BY HAND than the model seated them?

  If yes, the geometry carries enough information and the model is choosing
  badly — the problem is the model.
  If no, no model will do better from this data — the problem is the data.

  That is the fork the numbers cannot resolve, and it is why meshes rather than
  renders: these can be picked up and turned.

HOW THE POSES WERE PRODUCED
  Each fragment is placed by a single rotation and translation — a rigid
  motion, exactly what a real sherd can do. No fragment has been deformed.

  Worth knowing: the model's raw output DOES deform fragments, and its renders
  therefore look better than any achievable reassembly. On this pot the worst
  fragment was bent by nearly 6% of the pot's width. These files show only what
  rigid sherds can actually do.

MEASURED SANITY CHECKS (both should be ~0, and are printed on export)
  - reference points against the mesh surface: confirms the meshes and the
    saved arrays describe the same object at the same scale
  - fitted pose against the saved proposal: confirms these poses are the ones
    the model actually proposed
""")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
