"""Build the training set with the validated wear model.

Supersedes the first attempt (`build_erosion_sweep.py --dataset-name
wear_trainset`), which was built before the wear model was understood and swept a
single "wear level" dial uniformly.

Two things drive the design, both from the conservator:

1. **Wear is material loss; smoothness is loss of the sharp edges.** They are
   independent axes, not one dial.

2. **Smoothness is where the information lives.** "Material loss is generally not
   terrible. Smoothness is where the information of how sherds lock into each
   other is diminished." That is why GARF, reading only the fracture surface,
   fails on worn material, and why TORA, also reading whole-object form, does
   better.

So the axes get different treatment:

  MATERIAL LOSS — kept REALISTIC. Measured at 0.2-2.7% of volume in the
  validated conditions, which matches real sherds. An over-lossy dataset would
  teach the model to expect damage that is rare.

  SMOOTHNESS — SPANNED as widely as the simulation allows, because it is the
  axis that breaks the methods. Under-representing smooth break faces trains for
  a problem the field has already solved.

Known limit, carried forward honestly: smoothing saturates, and repeated passes
help only to a point (reversing after 2-3). limb3 reaches past the Juglet's
0.171, but naturally-rough ceramics bottom out around 0.21. Some objects cannot
be made as smooth as the real target, so coverage of the critical axis is partial
and varies by object. The per-object achieved smoothness is recorded so training
can be weighted, or gaps acknowledged, rather than assumed away.

Usage:
  python scripts/build_wear_trainset_v2.py \
      --src dataset/real_finetune.hdf5 --src-dataset real_finetune \
      --out-hdf5 dataset/wear_trainset_v2.hdf5
"""

import argparse
import json
import sys
from pathlib import Path

import h5py
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fracture_mesh_ops import piece_relief_stats  # noqa: E402
from wear_ops import apply_wear  # noqa: E402

# Smoothness is spanned; material loss stays realistic throughout (0.2-2.7% of
# volume, matching measurement on real sherds). Variants are named for what they
# are, not for a "level".
VARIANTS = [
    # name              smoothing passes  recession  chips  chip size
    ("fresh",     dict(smoothing=0.0, smoothing_passes=1, recession=0.0,    chip_count=0, chip_size=0.0)),
    ("smooth_1",  dict(smoothing=0.4, smoothing_passes=1, recession=0.0008, chip_count=2, chip_size=0.0018)),
    ("smooth_2",  dict(smoothing=0.7, smoothing_passes=1, recession=0.0012, chip_count=3, chip_size=0.0020)),
    ("smooth_3",  dict(smoothing=1.0, smoothing_passes=1, recession=0.0015, chip_count=3, chip_size=0.0022)),
    ("smooth_4",  dict(smoothing=1.0, smoothing_passes=2, recession=0.0018, chip_count=4, chip_size=0.0022)),
    ("smooth_5",  dict(smoothing=1.0, smoothing_passes=3, recession=0.0020, chip_count=4, chip_size=0.0022)),
    # loss without much abrasion — real, and it isolates the other axis
    ("loss_only", dict(smoothing=0.2, smoothing_passes=1, recession=0.0020, chip_count=5, chip_size=0.0028)),
]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", required=True)
    ap.add_argument("--src-dataset", default="real_finetune")
    ap.add_argument("--out-hdf5", required=True)
    ap.add_argument("--dataset-name", default="wear_trainset_v2")
    ap.add_argument("--target-max-abs", type=float, default=0.5)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    src = Path(args.src)
    out_path = Path(args.out_hdf5)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    manifest = {}
    names = []
    split_members = {"train": [], "val": [], "test": []}

    with h5py.File(src, "r") as fin:
        ds = fin[args.src_dataset]
        objects = sorted(ds.keys())

        # which split each source object belongs to, so worn copies of a
        # validation object can never leak into training
        src_split = {}
        if "data_split" in fin and args.src_dataset in fin["data_split"]:
            sg = fin["data_split"][args.src_dataset]
            for sp in sg.keys():
                for r in sg[sp][:]:
                    src_split[r.decode().split("/")[-1]] = sp

        with h5py.File(out_path, "w") as fout:
            dgrp = fout.create_group(args.dataset_name)

            for obj in objects:
                grp = ds[obj]
                g = grp["pieces"] if "pieces" in grp else grp
                keys = sorted(g.keys(), key=lambda s: int(s) if s.isdigit() else s)
                pieces = [(np.asarray(g[k]["vertices"][:], dtype=np.float64),
                           np.asarray(g[k]["faces"][:], dtype=np.int64)) for k in keys]
                if len(pieces) < 2:
                    continue
                print(f"{obj}: {len(pieces)} sherds", flush=True)

                for vi, (vname, kw) in enumerate(VARIANTS):
                    # vary chip placement per variant, so the model does not see
                    # the same damage pattern repeated across the whole set
                    worn = (pieces if vname == "fresh"
                            else apply_wear(pieces, seed=args.seed + vi, **kw))
                    rel = float(np.mean([piece_relief_stats(v, f)["relief_p90"]
                                         for v, f in worn]))

                    # normalise with a SHARED factor so relative geometry, and
                    # therefore the assembly problem, is exactly preserved
                    allv = np.concatenate([v for v, _ in worn], axis=0)
                    c = allv.mean(axis=0)
                    m = float(np.abs(allv - c).max()) + 1e-12
                    fac = args.target_max_abs / m

                    tag = f"{obj}__{vname}"
                    og = dgrp.create_group(tag)
                    pg = og.create_group("pieces")
                    for i, (v, f) in enumerate(worn):
                        sg2 = pg.create_group(str(i))
                        sg2.create_dataset("vertices", data=(v - c) * fac)
                        if f is not None and len(f):
                            sg2.create_dataset("faces", data=f)
                    og.create_dataset(
                        "pieces_names",
                        data=np.array([f"Piece{i + 1:02d}".encode()
                                       for i in range(len(worn))], dtype=object),
                        dtype=h5py.special_dtype(vlen=bytes))

                    full = f"{args.dataset_name}/{tag}"
                    names.append(full)
                    split_members.setdefault(src_split.get(obj, "train"), []).append(full)
                    manifest[tag] = {"object": obj, "variant": vname,
                                     "smoothness": rel, "n_pieces": len(worn),
                                     "split": src_split.get(obj, "train")}
                    print(f"    {vname:<10s} smoothness {rel:.4f}", flush=True)

            sgrp = fout.create_group("data_split").create_group(args.dataset_name)
            for split in ("train", "val", "test"):
                mem = split_members.get(split) or []
                if split == "test" and not mem:
                    mem = split_members.get("val") or []
                sgrp.create_dataset(
                    split, data=np.array([n.encode() for n in mem], dtype=object),
                    dtype=h5py.special_dtype(vlen=bytes))
                print(f"  split {split}: {len(mem)} variants")

    Path(str(out_path) + ".manifest.json").write_text(json.dumps(manifest, indent=2))

    # report the achieved smoothness coverage — the axis that matters
    vals = [m["smoothness"] for m in manifest.values()]
    print(f"\nwrote {len(names)} variants -> {out_path}")
    print(f"smoothness coverage: {min(vals):.4f} to {max(vals):.4f}  "
          f"(Juglet sits at 0.171)")
    below = sum(1 for v in vals if v <= 0.171)
    print(f"  variants at or below the Juglet's smoothness: {below}/{len(vals)}")
    if below == 0:
        print("  WARNING: nothing in this dataset is as smooth as the target object.")


if __name__ == "__main__":
    main()
