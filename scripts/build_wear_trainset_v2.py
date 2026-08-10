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
from wear_ops import apply_wear, sample_chip_level  # noqa: E402

# Smoothness is spanned; material loss stays realistic throughout (0.2-2.7% of
# volume, matching measurement on real sherds). Variants are named for what they
# are, not for a "level".
# Chip size is no longer written in here. It is SAMPLED per variant from the
# conservator's distribution (wear_ops.CHIP_LEVELS): common through "double",
# occasional "large", rare "very large". Fixing it per variant would give every
# sherd in the set the same size of damage.
VARIANTS = [
    # name              smoothing  passes  recession
    ("fresh",     dict(smoothing=0.0, smoothing_passes=1, recession=0.0)),
    ("smooth_1",  dict(smoothing=0.4, smoothing_passes=1, recession=0.0008)),
    ("smooth_2",  dict(smoothing=0.7, smoothing_passes=1, recession=0.0012)),
    ("smooth_3",  dict(smoothing=1.0, smoothing_passes=1, recession=0.0015)),
    ("smooth_4",  dict(smoothing=1.0, smoothing_passes=2, recession=0.0018)),
    ("smooth_5",  dict(smoothing=1.0, smoothing_passes=3, recession=0.0020)),
    # loss without much abrasion - real, and it isolates the other axis
    ("loss_only", dict(smoothing=0.2, smoothing_passes=1, recession=0.0020)),
]

# Objects excluded, and why. Recorded here rather than filtered silently: a
# dataset that quietly drops a tenth of its source is one nobody can reason
# about later.
#
# The three eggs have 1.2-1.6% walls, far thinner than anything archaeological
# here, and wear measures as running BACKWARDS on them - roughness rises
# 200-440% where every pot falls. The conservator inspected all three at every
# level and found them fine apart from the chip holes, which are now fixed. So
# measurement and eye disagree, and neither has been shown wrong.
#
# They are excluded rather than chased: three of twenty-seven objects, not
# pottery, and the anomaly is invisible at the scale a conservator inspects.
# Redesigning the wear model around them would be fixing a problem nobody can
# see, on material we do not study.
EXCLUDE = ["egg__egg1", "egg__egg2", "egg__egg3"]


# INCOMPLETE ASSEMBLAGES
#
# Conservator, 2026-08-10: the Juglet is also missing a few small pieces.
#
# This is not a detail. Every training example so far has been COMPLETE -- every
# fragment has all its neighbours present, so every break face has a partner
# somewhere in the set. The model has therefore only ever been asked to solve
# puzzles where a mate always exists, and it behaves accordingly: it will seat a
# fragment against something, because in its experience something always fits.
#
# A real assemblage is not like that. Small sherds are lost in the ground, in
# excavation, and in storage, so faces exist with nothing left to join. The
# model needs to learn that a face can have no partner and be left alone --
# which is the difference between an honest gap in a reconstruction and a wrong
# join that fills it.
#
# It also explains something we could not otherwise tell apart. In every render
# so far, a fragment whose neighbour is MISSING looks exactly like a fragment
# that was placed badly. Training on incomplete sets is the only way the model
# can distinguish the two, and it may be a large part of why pushing pieces
# together does not help on the Juglet.
#
# HOW BIG A PIECE GOES MISSING -- corrected 2026-08-10, from the conservator
# reassembling the Juglet by hand: it is missing a VERY VISIBLE piece, not a
# small one.
#
# The first version of this only lost small sherds, on the reasoning that small
# ones are fragile and go unnoticed. That is one real mechanism, but it is not
# the one that matters here, and training only on it would have taught the model
# that gaps are always minor -- while the object we are trying to solve has a
# substantial hole in it. The distribution now carries both:
#
#   attrition  small sherds vanish. Common: they are fragile, and easy to miss
#              in the ground, in excavation and in storage.
#   major      a substantial piece is simply absent. Less common but decisive,
#              and it is the Juglet's actual situation.
#
# The anchor is never dropped (the dataset needs a fixed reference) and at least
# three fragments are always kept, since below that the task stops being an
# assembly problem.
#
# Ground truth survives untouched: removing a fragment does not move the others,
# so the remaining poses stay exactly as correct as they were.
MISSING_LEVELS = [
    # name           pieces dropped   weight
    ("complete",     0,               5.0),
    ("lost_one",     1,               3.0),
    ("lost_two",     2,               1.5),
    ("lost_three",   3,               0.5),
]

# how the missing pieces are chosen, once the count is drawn
LOSS_MODES = [("attrition", 0.6), ("major", 0.4)]


def sample_missing(rng, pieces):
    """Choose which fragments are absent.

    Returns (name, kept_indices). Two mechanisms, because both happen and they
    leave very different holes:

      attrition  weighted by inverse size, so small sherds vanish often and
                 large ones rarely.
      major      size-neutral among non-anchor fragments, so a substantial
                 piece can simply be absent -- which is the Juglet's case.
    """
    w = np.array([m[2] for m in MISSING_LEVELS], dtype=float)
    w /= w.sum()
    name, n_drop, _ = MISSING_LEVELS[int(rng.choice(len(MISSING_LEVELS), p=w))]

    n = len(pieces)
    keep_min = 3
    sizes = np.array([len(v) for v, _ in pieces], dtype=float)
    anchor = int(np.argmax(sizes))
    n_drop = min(n_drop, max(0, n - keep_min))
    if n_drop == 0:
        return "complete", list(range(n))

    mw = np.array([m[1] for m in LOSS_MODES], dtype=float)
    mw /= mw.sum()
    mode = LOSS_MODES[int(rng.choice(len(LOSS_MODES), p=mw))][0]

    cand = [i for i in range(n) if i != anchor]
    if mode == "attrition":
        pr = 1.0 / np.maximum(sizes[cand], 1.0)
    else:
        pr = np.ones(len(cand), dtype=float)
    pr = pr / pr.sum()
    drop = sorted(rng.choice(cand, size=min(n_drop, len(cand)),
                             replace=False, p=pr).tolist())
    kept = [i for i in range(n) if i not in drop]
    # record how much of the object went, not just how many pieces
    lost_frac = 100.0 * sizes[drop].sum() / sizes.sum()
    return f"{name}/{mode}({len(drop)},{lost_frac:.0f}%)", kept


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
        objects = [o for o in sorted(ds.keys()) if o not in EXCLUDE]
        dropped = [o for o in sorted(ds.keys()) if o in EXCLUDE]
        if dropped:
            print("excluded " + str(len(dropped)) + ": " + ", ".join(dropped))
        rng = np.random.default_rng(args.seed)

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
                    # Chip size drawn per variant from the archaeological
                    # distribution, placement varied by seed, so the set does not
                    # repeat one damage pattern across every sherd.
                    if vname == "fresh":
                        worn, chip_name = pieces, "none"
                    else:
                        chip_name, chip_kw = sample_chip_level(rng)
                        worn = apply_wear(pieces, seed=args.seed + vi,
                                          **kw, **chip_kw)

                    # Remove fragments AFTER wearing, so the ones that remain
                    # are worn exactly as they would have been in the whole
                    # pot -- their break faces were shaped by neighbours that
                    # are now gone, which is what a real gap looks like.
                    miss_name, kept = sample_missing(rng, worn)
                    worn = [worn[i] for i in kept]
                    if len(worn) < 2:
                        continue
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
                                     "chip_level": chip_name,
                                     "missing": miss_name,
                                     "kept_pieces": kept,
                                     "split": src_split.get(obj, "train")}
                    print(f"    {vname:<10s} smoothness {rel:.4f}  "
                          f"chips {chip_name:<12s} {miss_name}", flush=True)

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
