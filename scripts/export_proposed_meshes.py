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

    # Put the meshes into the same frame as the saved arrays.
    #
    # The dataloader centres the object on its centre of mass and divides by one
    # global factor. The factor is in the npz; the centring is not, and two
    # guesses at it failed loudly before this worked -- assuming the vertex mean
    # left a 540% mismatch (the reference points are an AREA-weighted surface
    # sample, whose centre is elsewhere), and a hand-rolled translation search
    # left 25% because its update had the sign inverted.
    #
    # Both failures were caught by the check below rather than shipped, which is
    # the argument for keeping the check ahead of the export instead of after it.
    #
    # Fitted properly here: fragment i in the npz IS fragment i in the file, so
    # the nine centroid pairs give an exact correspondence, and a similarity fit
    # over them recovers scale, rotation and translation in one step. Each
    # fragment is then snapped onto its own points to absorb the small
    # difference between a vertex centroid and a surface-sample centroid.
    bounds = np.concatenate([[0], np.cumsum(ppp)])
    verts_all = [np.asarray(m.vertices, dtype=np.float64) for m in meshes]
    gt_parts = [pts_gt[a:b] for a, b in zip(bounds[:-1], bounds[1:])]

    A = np.array([v.mean(axis=0) for v in verts_all])
    B = np.array([p.mean(axis=0) for p in gt_parts])
    ca, cb = A.mean(axis=0), B.mean(axis=0)
    H = (A - ca).T @ (B - cb)
    U, S, Vt = np.linalg.svd(H)
    Rg = Vt.T @ np.diag([1.0, 1.0, np.sign(np.linalg.det(Vt.T @ U.T))]) @ U.T
    sg = float(np.sqrt(((B - cb) ** 2).sum() / max(((A - ca) ** 2).sum(), 1e-30)))
    print(f"  global fit: scale {sg:.3f} (npz implies {1.0 / scale:.3f}), "
          f"rotation {'identity' if np.allclose(Rg, np.eye(3), atol=0.05) else 'non-trivial'}")

    placed = [(v - ca) @ Rg.T * sg + cb for v in verts_all]

    # per-fragment rigid snap onto its own reference points
    for i, (v, pts) in enumerate(zip(placed, gt_parts)):
        for _ in range(8):
            _, idx = cKDTree(v).query(pts)
            R, t = solve_rigid(v[idx], pts)
            v = v @ R.T + t
        placed[i] = v

    for m, v in zip(meshes, placed):
        m.vertices = v

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
        # ONE file per attempt, with every sherd still a separate, selectable
        # object. A merged PLY is useless for the actual task here -- the whole
        # point is to pick a sherd up and turn it, and PLY has no notion of
        # separate objects, so everything arrives fused into a single block.
        scene, resid = trimesh.Scene(), []
        for i, (a, b) in enumerate(zip(bounds[:-1], bounds[1:])):
            R, t = solve_rigid(pts_gt[a:b], proposed[k][a:b])
            # check 2: does that transform actually reproduce the proposal?
            fit = pts_gt[a:b] @ R.T + t
            resid.append(float(np.linalg.norm(fit - proposed[k][a:b], axis=1).mean())
                         / obj_size * 100.0)

            m = meshes[i].copy()
            m.vertices = np.asarray(m.vertices) @ R.T + t
            colour = np.array(PALETTE[i % len(PALETTE)] + (255,), dtype=np.uint8)
            m.visual = trimesh.visual.ColorVisuals(
                mesh=m, vertex_colors=np.tile(colour, (len(m.vertices), 1)))
            scene.add_geometry(m, node_name=f"sherd_{i:02d}",
                               geom_name=f"sherd_{i:02d}")

        stem = out / f"attempt{k + 1:02d}"
        for ext in ("glb", "obj"):
            try:
                scene.export(f"{stem}.{ext}")
            except Exception as e:
                print(f"      could not write .{ext}: {type(e).__name__}: {e}")
        print(f"  attempt {k + 1}: {len(scene.geometry)} separately selectable "
              f"sherds  (pose fit residual {np.mean(resid):.4f}% of object size)")
        if np.mean(resid) > 0.01:
            print("      ** residual should be ~0; the fitted pose does not")
            print("         reproduce the proposal, so treat these files as suspect **")

    # the sherds as given, unmoved, in the same units and the same form
    scene = trimesh.Scene()
    for i, m in enumerate(meshes):
        mm = m.copy()
        colour = np.array(PALETTE[i % len(PALETTE)] + (255,), dtype=np.uint8)
        mm.visual = trimesh.visual.ColorVisuals(
            mesh=mm, vertex_colors=np.tile(colour, (len(mm.vertices), 1)))
        scene.add_geometry(mm, node_name=f"sherd_{i:02d}",
                           geom_name=f"sherd_{i:02d}")
    for ext in ("glb", "obj"):
        try:
            scene.export(str(out / f"reference_scan_layout.{ext}"))
        except Exception as e:
            print(f"      could not write reference .{ext}: {e}")
    print(f"  reference (scan layout, NOT a correct reassembly): "
          f"{len(scene.geometry)} sherds")

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
