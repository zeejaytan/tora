"""Build a piece-count sweep HDF5 from a real, VALID-GT multi-piece object.

C1 of the Juglet test plan (docs/notes/JUGLET_TORA_TEST_PLAN.md). Tests H2:
is TORA's mating signal *pairwise* or *contextual*? The open contradiction this
resolves — the pairwise oracle historically looked weak on isolated 2-piece real
fractures, yet whole 5-10-piece real objects assemble at 0.861 part accuracy.

Method: take one real object with genuine assembled GT (default galli_pot,
10 pieces, from real_heldout_norm.hdf5 — already scale-normalized) and emit
sub-assemblies at increasing piece counts k, several random replicates each.
Evaluate all in one run and read placement quality as a function of k.

  - k = 2 behaves like the pairwise oracle (isolated pair).
  - k growing adds *context* without changing the fracture surfaces at all.

Signature reading (see analyze_piececount_sweep.py, which reports the
anchor-corrected NON-ANCHOR placement rate so numbers are comparable across k,
since raw part_accuracy has a floor of 1/k from the clamped anchor):
  - rate low at k=2 and rising with k  => H2: mating signal is CONTEXTUAL.
  - rate flat/high from k=2            => mating is genuinely pairwise.

Unlike the Juglet B1 oracle, this uses REAL ground truth — no PF++ pseudo-GT,
no form-level caveat, and no proximity confound (every subset is scored against
its own true assembled pose).

Each subset is rescaled by a single shared factor to max|v| = 0.5 (the synthetic
convention) so the evaluator's absolute CD<0.01 part-accuracy threshold means the
same thing at every k; a shared factor preserves relative geometry exactly.

Usage:
  python scripts/build_piececount_sweep.py \
    --src dataset/real_heldout_norm.hdf5 --src-dataset real_heldout_norm \
    --object galli_pot --ks 2,3,4,6,8,10 --replicates 5 \
    --out-hdf5 dataset/piececount_sweep.hdf5
"""

import argparse
from pathlib import Path

import h5py
import numpy as np

TARGET_MAX_ABS = 0.5


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", type=Path, required=True)
    ap.add_argument("--src-dataset", default="real_heldout_norm")
    ap.add_argument("--object", default="galli_pot")
    ap.add_argument("--ks", default="2,3,4,6,8,10")
    ap.add_argument("--replicates", type=int, default=5)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out-hdf5", type=Path, required=True)
    ap.add_argument("--dataset-name", default="piececount_sweep")
    args = ap.parse_args()

    ks = [int(x) for x in args.ks.split(",")]
    rng = np.random.default_rng(args.seed)

    with h5py.File(args.src, "r") as src:
        grp = src[args.src_dataset][args.object]
        pieces = grp["pieces"] if "pieces" in grp else grp
        keys = sorted(pieces.keys(), key=lambda s: int(s) if s.isdigit() else s)
        P = len(keys)
        cache = {k: (np.asarray(pieces[k]["vertices"][:], dtype=np.float64),
                     np.asarray(pieces[k]["faces"][:], dtype=np.int64)
                     if "faces" in pieces[k] else None)
                 for k in keys}
    print(f"source {args.object}: {P} pieces")

    args.out_hdf5.parent.mkdir(parents=True, exist_ok=True)
    names = []
    with h5py.File(args.out_hdf5, "w") as out:
        dgrp = out.create_group(args.dataset_name)
        for k in ks:
            if k > P:
                print(f"  skip k={k} (> {P} available)")
                continue
            seen = set()
            for r in range(args.replicates):
                # distinct subsets where possible; full set has only one subset
                for _ in range(50):
                    sub = tuple(sorted(rng.choice(P, size=k, replace=False).tolist()))
                    if sub not in seen or k == P:
                        break
                seen.add(sub)
                verts = [cache[keys[i]][0] for i in sub]
                allv = np.concatenate(verts, axis=0)
                c = allv.mean(axis=0)
                m = float(np.abs(allv - c).max()) + 1e-12
                factor = TARGET_MAX_ABS / m

                obj = f"{args.object}_k{k:02d}_r{r:02d}"
                og = dgrp.create_group(obj)
                pg = og.create_group("pieces")
                for local, i in enumerate(sub):
                    v = (cache[keys[i]][0] - c) * factor
                    sg = pg.create_group(str(local))
                    sg.create_dataset("vertices", data=v)
                    f_ = cache[keys[i]][1]
                    if f_ is not None and len(f_):
                        sg.create_dataset("faces", data=f_)
                og.create_dataset(
                    "pieces_names",
                    data=np.array([f"Piece{i + 1:02d}".encode() for i in sub], dtype=object),
                    dtype=h5py.special_dtype(vlen=bytes),
                )
                names.append(f"{args.dataset_name}/{obj}")
                if k == P:
                    break  # only one distinct full-object subset

        sgrp = out.create_group("data_split").create_group(args.dataset_name)
        arr = np.array([n.encode() for n in names], dtype=object)
        for split in ("train", "val", "test"):
            sgrp.create_dataset(split, data=arr, dtype=h5py.special_dtype(vlen=bytes))

    print(f"wrote {len(names)} sub-assemblies -> {args.out_hdf5}")
    for k in ks:
        c = sum(1 for n in names if f"_k{k:02d}_" in n)
        if c:
            print(f"  k={k:2d}: {c} subsets")


if __name__ == "__main__":
    main()
