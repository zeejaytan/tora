"""Scramble Juglet sherds into blind tasks for a general-purpose agent (AssemblyWorld test).

Ticket `.scratch/agent-assembly/issues/01`. Runs on Spartan: the answer key never leaves it.

WHAT THIS REPRODUCES. AssemblyWorld (arXiv 2609.40353v1, App. A.1 "Initialization") hands the
agent each part in its own principal-axis frame (smallest axis along Z, right-handed), at one
shared scale (twice the largest vertex radius about any part's centroid), turned by a random
yaw and scattered on the floor with non-overlapping boxes and a 0.02 gap, seed 0. The scrambled
pose is baked into the vertices, part names are anonymised, and the agent sees no target.

WHAT IS WRITTEN.
  <out>/public/<task>/pieces/<id>.ply   scrambled, lightened sherds (what the agent gets)
  <out>/public/<task>/task.json         part ids and the scene conventions, no answer
  <out>/secret/<task>.json              for each id: original sherd index and the 4x4 map
                                        from answer-key coordinates to scene coordinates
  <out>/pairs.json                      every touching pair, with contact area in mm^2

TASKS. `pair_<i>_<j>` for the N touching pairs with the largest contact (the paper's
two-fragment setting, on real breaks), and `whole` (all sherds, no picture). The paper used one
scramble per object for every system; so do we, and repeat the agent instead.

Usage (Spartan, tora env):
  python scripts/agent_assembly/prep_tasks.py --h5 dataset/juglet_gt.hdf5 \
      --out ../agent_assembly/tasks_v1 --pairs 4 --pot-mm 65 --faces 30000
"""

import argparse
import json
import string
from pathlib import Path

import h5py
import numpy as np
import trimesh
from scipy.spatial import cKDTree


def load_pieces(h5_path):
    """(name, [(V, F), ...]) for the first object group holding `pieces`."""
    with h5py.File(h5_path, "r") as h:
        found = []

        def visit(name, obj):
            if isinstance(obj, h5py.Group) and "pieces" in obj and not found:
                found.append(name)
        h.visititems(visit)
        if not found:
            raise SystemExit(f"no group with 'pieces' in {h5_path}")
        g = h[found[0]]["pieces"]
        keys = sorted(g.keys(), key=lambda k: int(k))
        return found[0], [(np.asarray(g[k]["vertices"][:], float),
                           np.asarray(g[k]["faces"][:], np.int64)) for k in keys]


def lighten(mesh, faces):
    """Quadric decimation to about `faces` faces; the original if no decimator is installed."""
    if len(mesh.faces) <= faces:
        return mesh, "kept"
    try:
        out = mesh.simplify_quadric_decimation(face_count=faces)
        return out, "quadric"
    except Exception as e:  # fast_simplification missing, or an older trimesh
        try:
            import open3d as o3d
            m = o3d.geometry.TriangleMesh(o3d.utility.Vector3dVector(mesh.vertices),
                                          o3d.utility.Vector3iVector(mesh.faces))
            m = m.simplify_quadric_decimation(faces)
            return trimesh.Trimesh(np.asarray(m.vertices), np.asarray(m.triangles)), "open3d"
        except Exception:
            print(f"  ** no decimator ({e}); sherd kept at {len(mesh.faces)} faces")
            return mesh, "kept"


def contacts(meshes, mm_per_unit, gap_mm=0.5, n=40000, seed=0):
    """Area of each sherd lying within gap_mm of another sherd, in mm^2, for every pair."""
    rng = np.random.default_rng(seed)
    samples = []
    for m in meshes:
        p, _ = trimesh.sample.sample_surface(m, n, seed=int(rng.integers(1 << 31)))
        samples.append((p, m.area / n))
    trees = [cKDTree(p) for p, _ in samples]
    gap = gap_mm / mm_per_unit
    out = []
    for i in range(len(meshes)):
        for j in range(i + 1, len(meshes)):
            di, _ = trees[j].query(samples[i][0], distance_upper_bound=gap)
            dj, _ = trees[i].query(samples[j][0], distance_upper_bound=gap)
            a_i = np.isfinite(di).sum() * samples[i][1] * mm_per_unit ** 2
            a_j = np.isfinite(dj).sum() * samples[j][1] * mm_per_unit ** 2
            if a_i > 0 or a_j > 0:
                out.append({"i": i, "j": j, "contact_mm2": round(float((a_i + a_j) / 2), 1)})
    return sorted(out, key=lambda r: -r["contact_mm2"])


def pca_frame(v):
    """Rotation whose rows are the principal axes, largest first, smallest last (= local Z)."""
    c = v.mean(0)
    _, _, vt = np.linalg.svd(v - c, full_matrices=False)
    R = vt.copy()
    if np.linalg.det(R) < 0:
        R[2] *= -1
    return c, R


def scramble(meshes, idx, rng, gap=0.02):
    """Paper's initialisation for the sherds `idx`: 4x4 maps from answer-key to scene coords."""
    sub = [meshes[k] for k in idx]
    radius = max(np.linalg.norm(m.vertices - m.vertices.mean(0), axis=1).max() for m in sub)
    s = 2.0 * radius
    maps, boxes = [], []
    for m in sub:
        c, R = pca_frame(np.asarray(m.vertices))
        yaw = rng.uniform(-np.pi, np.pi)
        Rz = np.array([[np.cos(yaw), -np.sin(yaw), 0], [np.sin(yaw), np.cos(yaw), 0], [0, 0, 1]])
        A = Rz @ R / s
        local = (np.asarray(m.vertices) - c) @ A.T
        lo, hi = local.min(0), local.max(0)
        M = np.eye(4)
        M[:3, :3] = A
        M[:3, 3] = -A @ c - np.array([0, 0, lo[2]])   # rest on the floor (z = 0)
        maps.append(M)
        boxes.append((hi - lo)[:2])
    # scatter: shuffled order, one row after another, boxes never overlap
    order = rng.permutation(len(sub))
    width = max(1.0, np.sqrt(sum(b[0] * b[1] for b in boxes)) * 1.6)
    x = y = row_h = 0.0
    placed = [None] * len(sub)
    for k in order:
        w, h = boxes[k]
        if x > 0 and x + w > width:
            x, y, row_h = 0.0, y + row_h + gap, 0.0
        placed[k] = (x + w / 2, y + h / 2)
        x += w + gap
        row_h = max(row_h, h)
    xs = np.array([p[0] for p in placed]); ys = np.array([p[1] for p in placed])
    cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
    for k, M in enumerate(maps):
        local = trimesh.transform_points(np.asarray(sub[k].vertices), M)
        mid = (local.min(0) + local.max(0)) / 2
        M[0, 3] += placed[k][0] - cx - mid[0]
        M[1, 3] += placed[k][1] - cy - mid[1]
    return maps, s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--h5", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--pairs", type=int, default=4)
    ap.add_argument("--pot-mm", type=float, default=65.0,
                    help="real size of the longest side of the assembled pot's box")
    ap.add_argument("--faces", type=int, default=30000)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    name, pieces = load_pieces(a.h5)
    full = [trimesh.Trimesh(v, f, process=False) for v, f in pieces]
    allv = np.vstack([v for v, _ in pieces])
    longest = float((allv.max(0) - allv.min(0)).max())
    mm_per_unit = a.pot_mm / longest
    print(f"{name}: {len(full)} sherds; 1 unit = {mm_per_unit:.3f} mm")

    out = Path(a.out)
    (out / "secret").mkdir(parents=True, exist_ok=True)
    light = []
    for k, m in enumerate(full):
        lm, how = lighten(m, a.faces)
        light.append(lm)
        print(f"  sherd {k}: {len(m.faces)} -> {len(lm.faces)} faces ({how}), "
              f"area {m.area * mm_per_unit ** 2:.0f} mm^2")

    pairs = contacts(full, mm_per_unit)
    (out / "pairs.json").write_text(json.dumps(
        {"object": name, "mm_per_unit": mm_per_unit, "gap_mm": 0.5, "pairs": pairs}, indent=1))
    print("touching pairs (contact mm^2):",
          ", ".join(f"{p['i']}-{p['j']}:{p['contact_mm2']}" for p in pairs))

    tasks = {f"pair_{p['i']}_{p['j']}": [p["i"], p["j"]] for p in pairs[:a.pairs]}
    tasks["whole"] = list(range(len(full)))
    rng = np.random.default_rng(a.seed)
    for tname, idx in tasks.items():
        maps, s = scramble(full, idx, rng)
        ids = [f"part_{c}" for c in rng.permutation(list(string.ascii_lowercase))[:len(idx)]]
        pdir = out / "public" / tname / "pieces"
        pdir.mkdir(parents=True, exist_ok=True)
        for pid, k, M in zip(ids, idx, maps):
            m = light[k].copy()
            m.apply_transform(M)
            m.export(pdir / f"{pid}.ply")
        (out / "public" / tname / "task.json").write_text(json.dumps({
            "task": tname, "parts": sorted(ids),
            "conventions": "scene units; world up +Z; parts start scattered on the floor z=0",
        }, indent=1))
        (out / "secret" / f"{tname}.json").write_text(json.dumps({
            "task": tname, "object": name, "h5": str(Path(a.h5).resolve()),
            "mm_per_unit": mm_per_unit, "shared_scale": s, "seed": a.seed,
            "parts": {pid: {"sherd": int(k), "gt_to_scene": M.tolist()}
                      for pid, k, M in zip(ids, idx, maps)},
        }, indent=1))
        print(f"  task {tname}: sherds {idx} as {ids}")


if __name__ == "__main__":
    main()
