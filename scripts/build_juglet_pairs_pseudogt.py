"""Build a TORA pairs HDF5 for the 9-piece Juglet with PF++ pseudo-GT poses.

B1 of the Juglet test plan (docs/notes/JUGLET_TORA_TEST_PLAN.md). Decomposes the
Juglet into all C(9,2)=36 two-piece subproblems and stores each piece already
transformed into PF++'s "plausible" assembled layout, so TORA's NATIVE metrics
(part_accuracy / rotation_error) become a valid pairwise mating score against
that reference — reusing scripts/analyze_pairwise_oracle.py unchanged.

  ┌─ CAVEAT (read before interpreting any B1 number) ────────────────────────┐
  │ The Juglet has NO true assembly GT. PF++'s layout is the only assembled   │
  │ reference, and — as GARF found (Exp 9) — it is FORM-LEVEL accurate (good  │
  │ vessel silhouette; coarse adjacency well-defined at gap/scale<0.03) but   │
  │ NOT contact-accurate: at a fine band the mating faces show contact        │
  │ fraction ~0.000, i.e. the pieces DON'T ACTUALLY TOUCH — they just form a  │
  │ good enough shape. So scoring TORA against this pseudo-GT tests whether   │
  │ TORA reproduces PF++'s COARSE relative placement (a macro-geometry / form │
  │ signal — exactly the Uni3D CKA channel), NOT verified true-contact        │
  │ mating. A "pass" means TORA's form-level pairing >= PF++'s, not that      │
  │ TORA truly mates the sherds.                                              │
  └──────────────────────────────────────────────────────────────────────────┘

Pieces are stored as point clouds (vertices = PF++ posed part_pcs_gt, zero
normals, no faces); TORA's dataloader resamples vertices when faces are absent.
Each pair is rescaled by a single shared factor to max|v|=0.5 (synthetic
convention) so part_accuracy's absolute CD<0.01 threshold is valid; rotation
error is scale-invariant regardless. True-mate labels come from the PF++
adjacency matrix (derive_pfpp_adjacency.py output).

The PF++ SE(3) reproduction (quat_to_matrix / final_transformation) is copied
verbatim from GARF/scripts/derive_pfpp_adjacency.py so poses match the labels.

Usage:
  python scripts/build_juglet_pairs_pseudogt.py \
    --pfpp-dir  .../inference/juglet_deploy/0 \
    --pc-npz    .../pc_data/juglet_deploy/val/00000.npz \
    --adjacency .../juglet_adjacency/adjacency.json \
    --out-hdf5  dataset/juglet_pairs.hdf5 \
    --out-adjacency dataset/juglet_pairs_adjacency.json
"""

import argparse
import glob
import json
from itertools import combinations
from pathlib import Path

import h5py
import numpy as np


def quat_to_matrix(q_wxyz: np.ndarray) -> np.ndarray:
    """Scalar-first (w,x,y,z) unit quaternion -> 3x3 rotation (Blender convention)."""
    w, x, y, z = q_wxyz / (np.linalg.norm(q_wxyz) + 1e-12)
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ], dtype=np.float64)


def Tmat(t: np.ndarray) -> np.ndarray:
    m = np.eye(4)
    m[:3, 3] = t
    return m


def Rmat(q_wxyz: np.ndarray) -> np.ndarray:
    m = np.eye(4)
    m[:3, :3] = quat_to_matrix(q_wxyz)
    return m


def final_transformation(init_pose, gt, pred):
    """PF++ myrenderer.compute_final_transformation as a 4x4 matrix."""
    return (Rmat(init_pose[3:]) @ Tmat(init_pose[:3]) @ Tmat(pred[:3]) @ Rmat(pred[3:])
            @ Rmat(gt[3:]).T @ Tmat(-gt[:3]) @ Tmat(-init_pose[:3]) @ Rmat(init_pose[3:]).T)


def apply_mat(mat, v):
    return (np.c_[v, np.ones(len(v))] @ mat.T)[:, :3]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pfpp-dir", type=Path, required=True)
    ap.add_argument("--pc-npz", type=Path, required=True)
    ap.add_argument("--adjacency", type=Path, required=True,
                    help="PF++ adjacency.json (uses its 9x9 adjacency_matrix)")
    ap.add_argument("--out-hdf5", type=Path, required=True)
    ap.add_argument("--out-adjacency", type=Path, required=True)
    ap.add_argument("--dataset-name", default="juglet_pairs")
    ap.add_argument("--target-max-abs", type=float, default=0.5)
    args = ap.parse_args()

    init_pose = np.load(args.pfpp_dir / "init_pose.npy").astype(np.float64)
    gt = np.load(args.pfpp_dir / "gt.npy").astype(np.float64)
    traj = np.load(sorted(glob.glob(str(args.pfpp_dir / "predict_*.npy")))[0]).astype(np.float64)
    pred_final = traj[-1]
    pcs = np.load(args.pc_npz, allow_pickle=True)["part_pcs_gt"].astype(np.float64)  # (P,N,3)
    P = gt.shape[0]

    # identity sanity check (same guard the derive script uses)
    ident = final_transformation(init_pose, gt[0], gt[0])
    assert np.abs(ident - np.eye(4)).max() < 1e-6, "PF++ transform chain failed identity check"

    posed = [apply_mat(final_transformation(init_pose, gt[i], pred_final[i]), pcs[i])
             for i in range(P)]  # each (N,3) in the PF++ assembled layout

    adj = np.array(json.loads(args.adjacency.read_text())["adjacency_matrix"], dtype=int)
    assert adj.shape == (P, P), f"adjacency matrix {adj.shape} != ({P},{P})"

    args.out_hdf5.parent.mkdir(parents=True, exist_ok=True)
    names, pairs_out = [], {}
    n_mates = 0
    with h5py.File(args.out_hdf5, "w") as f:
        grp = f.create_group(args.dataset_name)
        for i, j in combinations(range(P), 2):
            key = f"Juglet-p{i + 1:02d}{j + 1:02d}"
            pair = [posed[i], posed[j]]
            allp = np.concatenate(pair, axis=0)
            c = allp.mean(axis=0)
            m = float(np.abs(allp - c).max()) + 1e-12
            factor = args.target_max_abs / m

            og = grp.create_group(key)
            pg = og.create_group("pieces")
            for local, pts in enumerate(pair):
                v = (pts - c) * factor
                sub = pg.create_group(str(local))
                sub.create_dataset("vertices", data=v.astype(np.float64))
                sub.create_dataset("normals", data=np.zeros_like(v, dtype=np.float64))
            og.create_dataset(
                "pieces_names",
                data=np.array([f"Piece{i + 1:02d}".encode(), f"Piece{j + 1:02d}".encode()],
                              dtype=object),
                dtype=h5py.special_dtype(vlen=bytes),
            )
            names.append(f"{args.dataset_name}/{key}")
            is_mate = bool(adj[i, j])
            n_mates += int(is_mate)
            pairs_out[key] = {"true_mate": is_mate, "piece_i": i + 1, "piece_j": j + 1}

        split_grp = f.create_group("data_split").create_group(args.dataset_name)
        arr = np.array([n.encode() for n in names], dtype=object)
        for split in ("train", "val", "test"):
            split_grp.create_dataset(split, data=arr, dtype=h5py.special_dtype(vlen=bytes))

    args.out_adjacency.write_text(json.dumps(
        {"n_parts": P, "n_pairs": len(names), "n_true_mates": n_mates, "pairs": pairs_out},
        indent=2))

    print(f"Wrote {len(names)} pairs ({n_mates} true mates) -> {args.out_hdf5}")
    print(f"Adjacency (analyzer format) -> {args.out_adjacency}")
    print("REMINDER: PF++ pseudo-GT is form-level, NOT contact-accurate (pieces "
          "don't truly touch). B1 tests coarse-layout agreement, not true mating.")


if __name__ == "__main__":
    main()
