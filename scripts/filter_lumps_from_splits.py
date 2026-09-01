"""Remove the solid lumps from the trainable splits of a built vessel set.

WHY THIS EXISTS, and why it is a removal rather than a flag.

`build_bbad_vessel_trainset.py` wrote every example into `train`/`val`/`test`
and recorded `passes_screen` alongside, on the reasoning that "the decision is
made once, visibly, by picking a split". That reasoning was wrong twice over.

  1. It was not actually reachable. `tora/data/datamodule.py` hardcodes
     `split="train"` and `split="val"`; there is no config knob. So the
     screened splits could not be selected without a code change, and the
     lumps were going to be trained on by default.

  2. Selecting the screen wholesale would have swapped one bias for another.
     The screen is `fill < 0.65 AND cells >= 1`. That second clause raises the
     median wall thickness of the kept set from 2.10% to 5.86% of object -- it
     keeps the vessels TORA finds EASY and drops the thin-walled ones, which
     are the closest thing in this corpus to real archaeological sherds. On
     the real erosion-sweep scans only ~4% of TORA's 5000 points land on
     genuine fracture against ~11% on the training vessels; training on the
     resolvable objects and testing on the unresolvable ones repeats the
     perfect-contact-join mistake one level up.

So this drops on FILL ALONE: a solid lump is not a vessel and its broad thick
break face is a cue that does not exist on the target material. A thin-walled
pot that TORA struggles to resolve is kept, because that is the actual job.

The 0.65 line is the conservator's, placed in a gap in the data: shown the two
middle objects as meshes they ruled the Vase at 0.549 still a vessel and the
Bowl at 0.747 not one, and only 30 of 1053 instances lie between them. The
ladder was rendered with each scanline's measured interior shaded before the
threshold was believed (`artifacts/fill_ladder.png`, job 29768556).

WHY IT REWRITES THE SPLIT TABLE RATHER THAN REBUILDING. The geometry is already
correct; only the membership lists are wrong. Rebuilding costs ~4 h of CPU to
produce identical meshes. It also keeps the split NAMES `train`/`val`, which
matters: `tora/data/dataset.py:309` gates the pose-prior-removing global
rotation on the split being literally "train", so a differently-named split
would train without augmentation and fail silently.

MEASURED ON THIS FILE, not on the csv. The first version of this filter read
`manifest[tag]["fill_fraction"]`, which `build_bbad_vessel_trainset.py:394`
copies out of `artifacts/corpus_screen.csv` -- measured by job 29765705 on the
OLD `bbad_vessels.hdf5` at the FRESH level. Applying it to worn v3 geometry is
a ruler borrowed from a different object. It turned out to be a good ruler
(`check_fill_provenance.py`: median drift -0.009, and only 3 of 1882 examples
change side), but "it happened to agree" is not a reason to keep depending on
it, so fill is now remeasured from the meshes being filtered and the manifest
is kept only as a cross-check that gets printed.

Non-destructive: the original membership is preserved as `train_all` /
`val_all` / `test_all` before anything is overwritten, and re-running is a
no-op on already-filtered files. `control` is left alone -- it is the
descriptive record of what the untouched corpus looks like.

Usage:
  python scripts/filter_lumps_from_splits.py \
      --src dataset/bbad_vessels_v3.hdf5 --dataset bbad_vessels --dry-run
  python scripts/filter_lumps_from_splits.py \
      --src dataset/bbad_vessels_v3.hdf5 --dataset bbad_vessels
"""

import argparse
import collections
import json
from pathlib import Path

import h5py
import numpy as np
import trimesh

from measure_gap_as_network_sees import load_meshes                # noqa: E402
from screen_vessel_corpus import fill_fraction                     # noqa: E402

SPLITS = ("train", "val", "test")


def load_manifest(src: Path) -> dict:
    """The manifest is a SIDECAR json, not an HDF5 attribute."""
    p = Path(str(src) + ".manifest.json")
    if not p.exists():
        raise SystemExit(f"no manifest beside the dataset: {p}")
    return json.loads(p.read_text())


def decode(arr) -> list:
    return [v.decode() if isinstance(v, bytes) else str(v) for v in arr]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--dataset", default="bbad_vessels")
    ap.add_argument("--max-fill", type=float, default=0.65,
                    help="drop examples at or above this section fill")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--trust-manifest", action="store_true",
                    help="use the stale corpus_screen fill instead of "
                         "remeasuring (for reproducing the first run)")
    args = ap.parse_args()

    src = Path(args.src)
    man = load_manifest(src)
    print(f"manifest: {len(man)} examples\n")

    mode = "r" if args.dry_run else "r+"
    with h5py.File(src, mode) as h:
        sgrp = h["data_split"][args.dataset]

        # Refuse to run twice in a way that would clobber the pristine lists.
        already = [s for s in SPLITS if f"{s}_all" in sgrp]
        if already and set(already) != set(SPLITS):
            raise SystemExit(
                f"partial previous run: {already} exist but not all of "
                f"{SPLITS}. Not touching this file -- inspect it by hand.")
        second_run = bool(already)
        fills_now = {}
        if second_run:
            print("NOTE: *_all already present, so this file has been filtered "
                  "before. Re-filtering from the pristine *_all lists.\n")

        for split in SPLITS:
            source_key = f"{split}_all" if second_run else split
            members = decode(sgrp[source_key][:])

            keep, drop, unknown, moved = [], [], [], []
            for full in members:
                # split members are "<dataset>/<tag>"; manifest keys are "<tag>"
                tag = full.split("/", 1)[1] if "/" in full else full
                rec = man.get(tag)
                old = None if rec is None else rec.get("fill_fraction")

                if args.trust_manifest:
                    f = old
                else:
                    asm = trimesh.util.concatenate(
                        load_meshes(h[args.dataset][tag]))
                    f = fill_fraction(asm)
                    fills_now[tag] = f
                    if (f is not None and old is not None
                            and (float(old) >= args.max_fill)
                                != (f >= args.max_fill)):
                        moved.append((tag, float(old), f))

                if f is None:
                    unknown.append(full)
                    continue
                (keep if float(f) < args.max_fill else drop).append(full)

            if unknown:
                raise SystemExit(
                    f"{len(unknown)} examples in '{split}' have no usable fill, "
                    f"e.g. {unknown[:3]}. Refusing to guess -- an unmeasured "
                    f"object must not be silently kept or dropped.")

            if moved:
                print(f"  {len(moved)} example(s) fall on the other side of "
                      f"{args.max_fill} than the stale csv said:")
                for tag, o, n in moved[:8]:
                    print(f"    {tag:52s} csv {o:.3f} -> measured {n:.3f}")

            cls = collections.Counter(f.split("/")[-1].split("__")[0] for f in keep)
            shapes = {"__".join(f.split("/")[-1].split("__")[:2]) for f in keep}
            print(f"{split:6s} {len(members):5d} -> {len(keep):5d} kept, "
                  f"{len(drop):5d} dropped as solid lumps "
                  f"({len(shapes)} distinct shapes)")
            print(f"       {', '.join(f'{k} {v}' for k, v in cls.most_common(6))}")

            # The two sides must account for every original member.
            assert len(keep) + len(drop) == len(members), "lost an example"

            if args.dry_run:
                continue

            if not second_run:
                sgrp.create_dataset(
                    f"{split}_all",
                    data=np.array([m.encode() for m in members], dtype=object),
                    dtype=h5py.special_dtype(vlen=bytes))
            del sgrp[split]
            sgrp.create_dataset(
                split, data=np.array([k.encode() for k in keep], dtype=object),
                dtype=h5py.special_dtype(vlen=bytes))

        if not args.dry_run:
            # Read back what is now on disk, not what we think we wrote.
            print("\nverifying against the file:")
            for split in SPLITS:
                got = decode(sgrp[split][:])
                fills = [float(fills_now[f.split("/", 1)[1]])
                         if not args.trust_manifest
                         else float(man[f.split("/", 1)[1]]["fill_fraction"])
                         for f in got]
                bad = [f for f in fills if f >= args.max_fill]
                if bad:
                    raise SystemExit(
                        f"{len(bad)} lumps still in '{split}' after the "
                        f"rewrite -- the filter did not take.")
                print(f"  {split:6s} {len(got):5d} examples, max fill "
                      f"{max(fills):.3f} (< {args.max_fill})  OK")
            print(f"  originals preserved as {', '.join(s + '_all' for s in SPLITS)}")

    print("\ncontrol left untouched: it records what the untouched corpus is.")
    if args.dry_run:
        print("DRY RUN -- nothing written.")


if __name__ == "__main__":
    main()
