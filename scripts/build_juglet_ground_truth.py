"""Turn the conservator's hand reassembly into a scoreable ground truth.

The Juglet has never had a valid answer key. Its "ground truth" was the
scan-table layout — the arrangement the sherds happened to be in when they were
scanned — which is not a reassembly at all. Every part-accuracy, rotation error
and chamfer distance ever computed for this pot was scored against it, and so
meant nothing. That is documented and was one of two independent faults behind
the Juglet result.

On 2026-08-10 the conservator reassembled the pot by hand in Blender and
exported `groundtruth.obj`. This converts that into a dataset the evaluator can
score against.

How exact it is: the file was built by moving the fragments exported from here,
so it contains the same vertices in the same order, and the pose of each sherd
comes out as a rigid fit with a residual of 0.0000% of the object. Nothing is
approximated. The rotations the conservator applied run from 26° to 177°, which
is a measure of how wrong the scan layout was as an answer key.

What this unlocks, and what it does not:

  DOES  Scores on this pot become real. Seating rate, rotation error and
        recall against a correct assembly, for the first time.

  DOES  The pairwise mating test stops depending on PF++ pseudo-GT, which
        inherits PF++'s own errors.

  NOT   It does not make the pot complete. A visible piece is missing, and no
        reassembly can put it back — a reconstruction that leaves that gap open
        is CORRECT, and a model that fills it is wrong. Any metric rewarding
        contact everywhere will still mislead here.

  NOT   One object, one conservator, one afternoon. It is authoritative in a way
        nothing else here is, but it is a single reading of a single pot.

Usage:
  python scripts/build_juglet_ground_truth.py \
      --obj /path/to/groundtruth.obj \
      --src dataset/juglet_norm.hdf5 --dataset juglet_norm \
      --out-hdf5 dataset/juglet_gt.hdf5
"""

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))


def parse_obj_groups(path):
    """Vertices per named object in an OBJ, keeping file order."""
    verts, groups, cur = [], {}, None
    for line in open(path, errors="ignore"):
        if line.startswith("v "):
            verts.append([float(x) for x in line.split()[1:4]])
        elif line.startswith(("o ", "g ")):
            cur = line.split(None, 1)[1].strip()
            groups.setdefault(cur, [])
        elif line.startswith("f ") and cur is not None:
            for tok in line.split()[1:]:
                groups[cur].append(int(tok.split("/")[0]) - 1)
    V = np.asarray(verts, dtype=np.float64)
    return {g: V[np.unique(idx)] for g, idx in groups.items()}, V


def solve_rigid(src, dst):
    cs, cd = src.mean(0), dst.mean(0)
    H = (src - cs).T @ (dst - cd)
    U, S, Vt = np.linalg.svd(H)
    R = Vt.T @ np.diag([1.0, 1.0, np.sign(np.linalg.det(Vt.T @ U.T))]) @ U.T
    return R, cd - R @ cs


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--obj", required=True)
    ap.add_argument("--src", required=True)
    ap.add_argument("--dataset", default="juglet_norm")
    ap.add_argument("--object", default="")
    ap.add_argument("--out-hdf5", required=True)
    ap.add_argument("--out-dataset", default="juglet_gt")
    ap.add_argument("--target-max-abs", type=float, default=0.5)
    args = ap.parse_args()

    gt_groups, _ = parse_obj_groups(args.obj)
    print(f"ground truth: {len(gt_groups)} named sherds in {Path(args.obj).name}")

    with h5py.File(args.src, "r") as h:
        ds = h[args.dataset]
        obj = args.object or sorted(ds.keys())[0]
        grp = ds[obj]
        g = grp["pieces"] if "pieces" in grp else grp
        keys = sorted(g.keys(), key=lambda s: int(s) if s.isdigit() else s)
        pieces = [(np.asarray(g[k]["vertices"][:], dtype=np.float64),
                   np.asarray(g[k]["faces"][:], dtype=np.int64)) for k in keys]
    print(f"source: {obj}, {len(pieces)} fragments")

    if len(pieces) != len(gt_groups):
        print(f"  ** {len(pieces)} fragments but {len(gt_groups)} in the OBJ; "
              f"cannot pair them. Aborting. **")
        return

    # Pair by vertex count. It is unique here and it does not assume the naming
    # convention survived a round trip through Blender.
    by_count = {}
    for name, V in gt_groups.items():
        by_count.setdefault(len(V), []).append((name, V))

    placed, resid = [], []
    for i, (v, f) in enumerate(pieces):
        cand = by_count.get(len(v))
        if not cand:
            print(f"  ** fragment {i} has {len(v)} vertices, nothing in the OBJ "
                  f"matches. Aborting. **")
            return
        name, G = cand.pop(0)

        # Same vertices in the same order would make this exact. Verify rather
        # than assume: if the order was shuffled, fall back to nearest-point
        # correspondence and say so.
        R, t = solve_rigid(v, G)
        err = float(np.linalg.norm(v @ R.T + t - G, axis=1).mean())
        if err > 1e-6 * max(np.ptp(G, axis=0).max(), 1e-9):
            _, idx = cKDTree(G).query(v)
            R, t = solve_rigid(v, G[idx])
            err = float(np.linalg.norm(v @ R.T + t - G[idx], axis=1).mean())
            print(f"  fragment {i}: order not preserved, matched by proximity")
        placed.append((v @ R.T + t, f))
        resid.append(err)
        ang = np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1)))
        print(f"  fragment {i} <- {name:<24s} rotated {ang:6.1f}°, "
              f"fit residual {err:.2e}")

    allv = np.concatenate([v for v, _ in placed], axis=0)
    size = float(np.linalg.norm(allv.max(0) - allv.min(0)))
    print(f"\n  assembled size {size:.3f}, mean fit residual "
          f"{np.mean(resid):.2e} ({100 * np.mean(resid) / size:.4f}% of object)")
    if np.mean(resid) / size > 1e-4:
        print("  ** residual too large; these are not the same fragments. **")
        return

    # normalise the way the rest of the datasets are: one shared factor, so the
    # geometry and therefore the assembly problem are exactly preserved
    c = allv.mean(axis=0)
    m = float(np.abs(allv - c).max()) + 1e-12
    fac = args.target_max_abs / m

    out = Path(args.out_hdf5)
    out.parent.mkdir(parents=True, exist_ok=True)
    with h5py.File(out, "w") as fo:
        dgrp = fo.create_group(args.out_dataset)
        og = dgrp.create_group(obj)
        pg = og.create_group("pieces")
        for i, (v, f) in enumerate(placed):
            sg = pg.create_group(str(i))
            sg.create_dataset("vertices", data=(v - c) * fac)
            sg.create_dataset("faces", data=f)
        og.create_dataset(
            "pieces_names",
            data=np.array([f"Piece{i + 1:02d}".encode() for i in range(len(placed))],
                          dtype=object),
            dtype=h5py.special_dtype(vlen=bytes))

        sgrp = fo.create_group("data_split").create_group(args.out_dataset)
        row = np.array([f"{args.out_dataset}/{obj}".encode()], dtype=object)
        for split in ("train", "val", "test"):
            sgrp.create_dataset(split, data=row,
                                dtype=h5py.special_dtype(vlen=bytes))

    print(f"\nwrote {out}")
    print("Scores on this pot are now real. Two things they still cannot tell you:")
    print("  - a piece is MISSING, so a reconstruction that leaves that gap open")
    print("    is correct and one that fills it is wrong;")
    print("  - this is one pot, reassembled once, by one person.")


if __name__ == "__main__":
    main()
