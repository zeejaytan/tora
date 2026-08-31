"""Build the vessel-VARIETY training set from the Breaking Bad vessel corpus.

This exists to fill a different gap from `build_wear_trainset_v2.py`, and
confusing the two would waste the work. The conservator, after I had spent a
week on wear: *"the dataset provides more variety as to the shapes that get
trained. We can make the relevant object fragment worn, but we don't have the
shape/object in training right now. That's the gap."*

Right. The fine-tuning source holds **8 ceramic vessels**. Gate B found **371
vessel shapes** already fractured in a file on disk, with 2,946 genuinely
multi-piece breaks (`docs/notes/GATE_B_DECISION.md`). Wear was never the
bottleneck for shape coverage; shape coverage was.

WHAT WEAR IS APPLIED HERE, AND WHY IT IS NOT THE SAME RECIPE

These meshes are coarse -- 0.25-0.47% of object between vertices against
blue_pot's 0.057%. Measured on them (`test_wear_on_coarse.py`):

  blunting     0.0001-0.0053% of the surface stands proud at the cutoff, and
               blunting moves the joins by 0.0-0.7%. There are no teeth in the
               file to remove. Not a failure of the tool -- the geometry was
               never recorded at that scale.
  recession    the same 0.05% retreat opens these joins by 6-10%, against
               1.1-1.9% on our fine scans, because these fragments were cut
               from one mesh and mate exactly, so a retreat has nowhere to hide.

So this set uses RECESSION, which is retired for the fine corpus and un-retired
for this one. That reversal is on measured evidence, not preference: recession
was retired on a dose table taken entirely on fine meshes where blunting opened
joins more cheaply, and on a mesh where blunting can do nothing that comparison
simply does not apply.

What it costs the CURVE is measured in `test_recession_curve.py`, and the doses
below are set from that result. If you are changing them, re-run it first.

No scan-resolution blur either. `build_wear_trainset_v2.py` blurs to 0.25% of
object because its sources are four times finer than a real scan. These meshes
are ALREADY at 0.25-0.47%, so blurring them again would remove the shape, not
the fracture texture.

WHAT IS BORROWED, DELIBERATELY

Fragment loss (`sample_missing`) is imported rather than re-written. A real
assemblage is missing pieces -- the Juglet is missing a very visible one -- and
a model that has only ever seen complete puzzles will seat every fragment
against something. That argument is identical here and the code should not fork.

SPLIT BY OBJECT, NOT BY INSTANCE. Two fracture instances of the same vase are
the same shape broken twice; putting one in train and one in validation would
report shape generalisation the set does not demonstrate.

Usage:
  python scripts/build_bbad_vessel_trainset.py \
      --src dataset/breaking_bad_vol.hdf5 \
      --out-hdf5 dataset/bbad_vessels.hdf5
"""

import argparse
import json
import sys
from pathlib import Path

import h5py
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_wear_trainset_v2 import sample_missing  # noqa: E402
from fracture_mesh_ops import piece_relief_stats  # noqa: E402
from wear_ops import recede_and_chip, recede_surface, wear_context  # noqa: E402
from compare_wear_severity import coincident_frac  # noqa: E402

# Vessel-shaped classes. Judged by eye before use (`render_bbad_vessels.py`):
# wheel-thrown and hand-built forms with a wall, a base and a rim, broken into
# sherd-like pieces rather than slices.
CATS = ["Bottle", "Vase", "Mug", "Bowl", "Cup", "Teapot", "Plate", "WineBottle",
        "BeerBottle", "Teacup", "PillBottle", "WineGlass", "DrinkBottle",
        "DrinkingUtensil"]

# Doses, in fraction of object size retreated from the break face, MEASURED
# rather than chosen (`test_recession_curve.py`, job 29475692).
#
# The conservator's prediction was that a uniform retreat cannot cost the curve,
# because shifting every point equally along its normal leaves each point's
# deviation from its neighbours untouched. Measured on these vessels at 0.10%:
#
#   joins opened   +22% to +42%
#   curve moved    -0.4% to -4.1% across 1.6%, 3.2% and 6.4% of object
#   retreat        piles up at the full requested amount, spread 0.17-0.26 of
#                  its own mean -- and that spread is almost entirely the taper
#                  at the edge of the contact face, which has to exist or the
#                  retreat would cut a step into the sherd
#
# 0.20% is EXCLUDED: it moved one object's curve by 6.6%. And note this does not
# generalise to the fine corpus -- the same 0.20% cost blue_pot 10.2% of its
# coarsest relief, which is why recession stays retired there.
#
# `fresh` is kept as the control that says what the corpus looks like untouched.
#
# ---------------------------------------------------------------------------
# REBUILT 2026-08-31, on jobs 29765789 (dose sweep) and 29765705 (corpus screen).
# THREE CHANGES, each measured rather than chosen. The reasoning above stands as
# written; what changed is that the ruler it was written against was wrong.
#
# 1. THE DOSE WAS SET FROM A SATURATING METRIC. `joint_gap` is a 10th percentile
#    of nearest-neighbour distance over all 5000 sampled points, most of which
#    are nowhere near a join -- a mixture that bottoms out at the sampling floor.
#    It reads 0.277 on a fresh build whose vertices are 44% EXACTLY COINCIDENT,
#    i.e. a true zero. Measured instead on the contact band (p50, % of object):
#
#        dose      Vase    Cup     Mug     real worn pot
#        fresh     0.088   0.000   0.000       0.615
#        0.10%     0.201   0.199   0.199
#        0.20%     0.397   0.399   0.397
#        0.30%     0.588   0.597   0.594   <-- lands on the real pot
#        0.40%     0.768   0.796   0.789
#
#    At 0.30% the Vase reads 0.181 / 0.588 / 1.771 for p10/p50/p90 against the
#    real pot's 0.182 / 0.615 / 1.692 -- ALL THREE percentiles line up, which
#    also retires the worry that a uniform retreat could not produce the tail.
#    Cost, honestly: the Vase's fine-scale curve moves 22.1% (Cup +3.7%,
#    Mug -1.6%). That is a real price and it is paid deliberately, because a
#    corpus whose joins are exactly zero teaches lookup, not assembly
#    (`LORA_VESSELS_29623885_RESULT.md`).
#
#    0.20% was excluded above for costing one object 6.6% of its curve. That
#    exclusion is overturned by the same evidence: the target it was measured
#    against was an artefact.
#
# 2. `fresh` NO LONGER GOES INTO TRAINING. It is the defect itself -- 44% of
#    vertices shared between fragments. It is still built, still measurable, and
#    is filed under split "control" so nothing can train on it by accident.
#
# 3. CHIPPING IS RESTORED. The dose render shows recession moving the fresh
#    spike at exactly 0 to a peak at 0.58, but TALL AND NARROW where the real
#    contact band is a broad hump. Uniform retreat cannot make that spread;
#    localised loss can. Chip settings are the validated restrained ones
#    (`WEAR_CONDITIONS`, job 28742114): 3-4 chips at 0.0022-0.0030. Larger
#    chips ADD relief through ragged boundaries and made "heavy wear" read
#    rougher than an untouched sherd.
# ---------------------------------------------------------------------------
#
# name, recession dose, chip count, chip size, split role
WEAR_LEVELS = [
    ("fresh", 0.0, 0, 0.0, "control"),
    ("worn_light", 0.0015, 2, 0.0022, "use"),
    ("worn_moderate", 0.0030, 3, 0.0025, "use"),
]


def effective_pieces(sizes):
    """Inverse Simpson index: how many pieces the break BEHAVES like.

    Four equal quarters gives 4.0; one remnant with three slivers gives ~1.0.
    Raw piece count would have selected 89% rubbish (Gate B).
    """
    p = np.asarray(sizes, dtype=float)
    if p.sum() <= 0:
        return 0.0
    p = p / p.sum()
    return 1.0 / float((p ** 2).sum())


def pick_instances(node, n_want, min_eff, rng):
    """The best-balanced fracture instances of one object.

    Sorted by balance rather than sampled: a corpus this large can afford to
    take only the breaks that are actually reassembly problems.
    """
    scored = []
    for fr in sorted(node.keys()):
        grp = node[fr]
        keys = sorted(grp.keys(), key=lambda s: int(s) if s.isdigit() else s)
        if len(keys) < 3:
            continue
        sz = [grp[k]["vertices"].shape[0] for k in keys]
        e = effective_pieces(sz)
        if e >= min_eff:
            scored.append((e, fr, keys))
    scored.sort(key=lambda r: -r[0])
    # Returns how many qualified as well as which were taken. A cap that is not
    # reported reads as "we used everything" when it did not.
    return scored[:n_want], len(scored)


def load_screen(path):
    """cells-through-wall and section fill per fracture instance, or {}.

    Keyed the way the tags are built (category__object[:12]__instance) so the
    screen and the build cannot drift apart silently.
    """
    if not path or not Path(path).exists():
        return {}
    out = {}
    with open(path, encoding="utf-8") as fh:
        head = fh.readline().rstrip().split(",")
        ic, ie, il = head.index("object"), head.index("cells"), head.index("fill")
        for line in fh:
            p = line.rstrip().split(",")
            if len(p) <= max(ic, ie, il):
                continue
            try:
                out[p[ic]] = {"cells": float(p[ie]), "fill": float(p[il])}
            except ValueError:
                continue
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", required=True)
    ap.add_argument("--src-dataset", default="everyday")
    ap.add_argument("--out-hdf5", required=True)
    ap.add_argument("--dataset-name", default="bbad_vessels")
    ap.add_argument("--min-effective", type=float, default=4.0)
    ap.add_argument("--instances-per-object", type=int, default=3)
    ap.add_argument("--max-objects", type=int, default=0,
                    help="0 = all; small values for a smoke test")
    ap.add_argument("--val-frac", type=float, default=0.1)
    ap.add_argument("--target-max-abs", type=float, default=0.5)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--screen-csv", default="",
                    help="artifacts/corpus_screen.csv; adds *_screened splits")
    ap.add_argument("--screen-cells", type=float, default=1.0,
                    help="min cells through the wall at TORA's 5000 points")
    # 0.65 IS THE CONSERVATOR'S LINE, PLACED IN A GAP IN THE DATA (2026-08-31).
    # Shown the two middle objects as meshes, they ruled the Vase at fill 0.549
    # still a vessel -- it has a real bore -- and the Bowl at 0.747 not one, it
    # is a solid lump with a shallow dish scooped into the top. The corpus is
    # bimodal and only 30 of 1053 instances (2.8%) lie between those two, so
    # the cut is put in the middle of that empty band where it is least
    # sensitive: 0.55 keeps 214, 0.65 keeps 217, 0.75 keeps 227.
    ap.add_argument("--screen-fill", type=float, default=0.65,
                    help="max section fill; >=0.8 is a solid lump, not a vessel")
    args = ap.parse_args()

    screen = load_screen(args.screen_csv)
    if screen:
        print(f"screen: {len(screen)} instances measured, "
              f"keeping cells >= {args.screen_cells} and fill < {args.screen_fill}",
              flush=True)
    else:
        print("screen: none given -- no *_screened splits will be written",
              flush=True)

    out_path = Path(args.out_hdf5)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    manifest = {}
    split_members = {"train": [], "val": [], "test": [], "control": [],
                     "train_screened": [], "val_screened": []}
    n_coincident_dropped = 0

    with h5py.File(args.src, "r") as fin, h5py.File(out_path, "w") as fout:
        ev = fin[args.src_dataset]
        dgrp = fout.create_group(args.dataset_name)

        # Every object of every vessel class, so the shape coverage is the
        # whole point rather than a sample of it.
        catalogue = []
        for c in CATS:
            if c not in ev:
                continue
            for o in sorted(ev[c].keys()):
                catalogue.append((c, o))
        if args.max_objects:
            catalogue = catalogue[:args.max_objects]
        print(f"{len(catalogue)} vessel objects in {args.src_dataset}", flush=True)

        # SPLIT ON THE OBJECT, decided before anything is built, so no fracture
        # instance of a validation shape can reach training.
        order = rng.permutation(len(catalogue))
        n_val = max(1, int(round(args.val_frac * len(catalogue))))
        val_objs = {catalogue[i] for i in order[:n_val]}

        n_obj_used, n_avail_total, n_taken_total, n_obj_none = 0, 0, 0, 0
        for c, o in catalogue:
            insts, n_avail = pick_instances(ev[c][o], args.instances_per_object,
                                            args.min_effective, rng)
            if not insts:
                n_obj_none += 1
                continue
            n_obj_used += 1
            n_avail_total += n_avail
            n_taken_total += len(insts)
            split = "val" if (c, o) in val_objs else "train"
            print(f"{c}/{o[:10]}: {len(insts)} instances "
                  f"(best balance {insts[0][0]:.1f})  [{split}]", flush=True)

            for e, fr, keys in insts:
                grp = ev[c][o][fr]
                pieces = [(np.asarray(grp[k]["vertices"][:], dtype=np.float64),
                           np.asarray(grp[k]["faces"][:], dtype=np.int64))
                          for k in keys]
                if len(pieces) < 3:
                    continue
                # Contact bands depend only on the fresh geometry, so they are
                # computed once and reused across wear levels. Recomputing per
                # variant is what ran the previous build out of wall time.
                ctx_masks, _ = wear_context(pieces)

                for wname, dose, n_chip, chip_sz, role in WEAR_LEVELS:
                    # TWO OPERATIONS, IN THIS ORDER, AND NOT ONE CALL.
                    #
                    # `recede_and_chip` looks like it does both, and using it
                    # that way would be wrong twice over. Its recession deletes
                    # FACES AT THE RIM (`feather` between 0.15 and 0.98), which
                    # trims the outline of the break and leaves the middle of
                    # the contact still meeting exactly -- the defect this
                    # rebuild exists to remove would survive it untouched. And
                    # the 0.30% dose was calibrated on `recede_surface` (job
                    # 29765789), which is a different operation with a
                    # different response, so the number would not mean what the
                    # sweep measured.
                    #
                    # So: recede the SURFACE first, at the calibrated dose --
                    # it displaces band vertices and preserves vertex indexing,
                    # which is why the contact masks computed once on the fresh
                    # geometry stay valid across it. Then chip, with recession
                    # switched off so the chipping is the only thing that call
                    # contributes. Same order the combined function uses
                    # internally.
                    worn = pieces
                    if dose > 0:
                        worn = recede_surface(worn, recession_frac=dose,
                                              masks=ctx_masks)
                    if n_chip > 0:
                        worn = recede_and_chip(worn, recession_frac=0.0,
                                               chip_count=n_chip,
                                               chip_frac=chip_sz,
                                               seed=int(rng.integers(1 << 30)),
                                               masks=ctx_masks,
                                               chip_method="dish")

                    # THE GATE THIS REBUILD EXISTS FOR. Fragments cut from one
                    # mesh share their mating vertices exactly; a set built that
                    # way teaches the model to look joins up rather than solve
                    # them. Anything worn that still shares a vertex means the
                    # recession did not reach the contact band and the example
                    # is not what it claims to be -- so it is dropped, loudly,
                    # not quietly written with a worn label on it.
                    coin = coincident_frac([v for v, _ in worn])
                    if dose > 0 and coin > 0.0:
                        n_coincident_dropped += 1
                        print(f"    DROP {c}/{o[:10]}/{fr}/{wname}: "
                              f"{100 * coin:.2f}% of vertices still coincident",
                              flush=True)
                        continue

                    miss_name, kept = sample_missing(rng, worn)
                    worn = [worn[i] for i in kept]
                    if len(worn) < 3:
                        continue
                    rel = float(np.mean([piece_relief_stats(v, f)["relief_p90"]
                                         for v, f in worn]))

                    # ONE shared normalisation factor, so relative geometry --
                    # and therefore the assembly problem -- is untouched.
                    allv = np.concatenate([v for v, _ in worn], axis=0)
                    ctr = allv.mean(axis=0)
                    m = float(np.abs(allv - ctr).max()) + 1e-12
                    fac = args.target_max_abs / m

                    tag = f"{c}__{o[:12]}__{fr}__{wname}"
                    og = dgrp.create_group(tag)
                    pg = og.create_group("pieces")
                    for i, (v, f) in enumerate(worn):
                        sg = pg.create_group(str(i))
                        sg.create_dataset("vertices", data=(v - ctr) * fac)
                        if f is not None and len(f):
                            sg.create_dataset("faces", data=f)
                    og.create_dataset(
                        "pieces_names",
                        data=np.array([f"Piece{i + 1:02d}".encode()
                                       for i in range(len(worn))], dtype=object),
                        dtype=h5py.special_dtype(vlen=bytes))

                    full = f"{args.dataset_name}/{tag}"
                    this_split = "control" if role == "control" else split
                    split_members[this_split].append(full)

                    # The corpus screen travels WITH each example instead of
                    # deciding here what may be trained on. 37% of this corpus
                    # is a solid lump rather than a vessel, and 97% of objects
                    # sit on the diagonal where "TORA can resolve the break
                    # face" and "the object is not a vessel" are the same
                    # objects (job 29765705, confirmed by eye in
                    # artifacts/fill_ladder.png). That is a training-time
                    # choice with a real cost either way -- 207 screened
                    # examples against 1053 -- so BOTH arms are written and the
                    # decision is made once, visibly, by picking a split.
                    scr = screen.get(f"{c}__{o[:12]}__{fr}")
                    cells = None if scr is None else scr["cells"]
                    fill = None if scr is None else scr["fill"]
                    passes = (scr is not None and cells >= args.screen_cells
                              and fill < args.screen_fill)
                    if passes and role != "control":
                        split_members[split + "_screened"].append(full)

                    manifest[tag] = {"category": c, "object": o,
                                     "instance": fr, "wear": wname,
                                     "recession": dose,
                                     "chip_count": n_chip, "chip_size": chip_sz,
                                     "coincident_frac": coin,
                                     "effective_pieces": float(e),
                                     "n_pieces": len(worn),
                                     "smoothness": rel,
                                     "cells_through_wall": cells,
                                     "fill_fraction": fill,
                                     "passes_screen": bool(passes),
                                     "missing": miss_name, "split": this_split}

        sgrp = fout.create_group("data_split").create_group(args.dataset_name)
        for split in ("train", "val", "test", "control",
                      "train_screened", "val_screened"):
            mem = split_members.get(split) or []
            if split == "test" and not mem:
                mem = split_members.get("val") or []
            sgrp.create_dataset(
                split, data=np.array([n.encode() for n in mem], dtype=object),
                dtype=h5py.special_dtype(vlen=bytes))
            print(f"  split {split}: {len(mem)} examples")

    Path(str(out_path) + ".manifest.json").write_text(json.dumps(manifest, indent=2))

    shapes = {(m["category"], m["object"]) for m in manifest.values()}
    effs = [m["effective_pieces"] for m in manifest.values()]
    print(f"\nwrote {len(manifest)} examples -> {out_path}")
    print(f"  distinct vessel shapes: {len(shapes)}  "
          f"(against 8 ceramic vessels in the fine-tuning source)")
    if effs:
        print(f"  effective piece count: {min(effs):.1f} to {max(effs):.1f}, "
              f"mean {np.mean(effs):.1f}  (the Juglet is nine sherds)")

    # WHAT WAS LEFT OUT, said plainly. Instances are ranked by balance and the
    # top few taken, so this set is the well-balanced tail of the corpus rather
    # than a sample of it -- which is deliberate, and would read as full
    # coverage if it went unreported.
    print(f"\n  coverage: {n_obj_used} objects contributed, {n_obj_none} had no "
          f"break at effective >= {args.min_effective:.0f}")
    print(f"  instances: {n_taken_total} used of {n_avail_total} that qualified "
          f"-- the best-balanced {args.instances_per_object} per object, not a "
          f"random sample")
    print(f"  dropped: {n_coincident_dropped} worn examples still had "
          f"coincident vertices after recession -- the defect this rebuild "
          f"exists to remove, so they are not in the file")

    # WHAT THE JOINS NOW LOOK LIKE, stated per level rather than in aggregate,
    # because the whole point of the rebuild is that the fresh level's zero was
    # hiding inside a mean.
    print("")
    for wname, dose, n_chip, chip_sz, role in WEAR_LEVELS:
        got = [m for m in manifest.values() if m["wear"] == wname]
        if not got:
            continue
        cf = np.array([m["coincident_frac"] for m in got])
        print(f"  {wname:<14} recession {100 * dose:.2f}% of object, "
              f"{n_chip} chips at {100 * chip_sz:.2f}%  ->  "
              f"{len(got)} examples, coincident vertices "
              f"mean {100 * cf.mean():.2f}%  [{role}]")

    if screen:
        kept = [m for m in manifest.values()
                if m["passes_screen"] and m["split"] != "control"]
        meas = [m for m in manifest.values() if m["cells_through_wall"] is not None]
        print("")
        print(f"  screen: {len(kept)} of {len(meas)} measured examples are a "
              f"HOLLOW vessel whose break face TORA can resolve "
              f"(cells >= {args.screen_cells}, fill < {args.screen_fill}).")
        print("  Both arms are in the file: train / val use everything, "
              "train_screened / val_screened use only those. Choosing between "
              "them is a training decision, not a build one.")

    print("")
    print("  NOT rendered by this script. Run render_trainset_sample.py before "
          "training on it.")


if __name__ == "__main__":
    main()
