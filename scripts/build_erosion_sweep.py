"""C3 — the causal wear test: progressively wear pots TORA CAN currently rebuild.

Everything so far is correlational: worn objects (the Juglet) score worse than
fresh ones. That is consistent with "wear causes the failure" but does not
demonstrate it — the Juglet differs from the Fractura pots in more ways than
wear alone.

This flips it into an intervention. Take real pots TORA reassembles well, apply
increasing simulated abrasion to their BREAK SURFACES ONLY, and re-measure. If
seating accuracy falls as wear rises — on the same pots, same pieces, same
poses — then wear is the cause, not a correlate.

Uses GARF's already-validated mollifier (`fracture_mesh_ops.erode_fracture_band`,
imported unmodified). Two properties make it the right tool:
  * it edits vertices IN PLACE — faces and the assembled ground-truth pose are
    preserved, so the scoring stays valid and only the surfaces change;
  * it mollifies over a FIXED PHYSICAL radius, so the result cannot be an
    artifact of mesh density (the confound that invalidated an earlier
    roughness probe here, where real scans have ~100-200x more vertices than
    synthetic meshes).

The source objects are already scale-normalized (max|v| = 0.5), and erosion
barely changes extent, so NO renormalization is applied — the scale factor is
held fixed across strengths so the only thing varying is surface wear.

Calibration: surface relief is measured at every strength and written to a JSON
alongside, so achieved wear can be compared against the Juglet's own measured
roughness. GARF's Exp 7 undershot exactly here — its bridge plateaued below the
Juglet's wear level and could not be interpreted. Recording the achieved value
is what makes a negative result meaningful rather than ambiguous.

Usage:
  python scripts/build_erosion_sweep.py \
    --src dataset/real_heldout_norm.hdf5 --src-dataset real_heldout_norm \
    --strengths 0,0.25,0.5,0.75,1.0 --out-hdf5 dataset/erosion_sweep.hdf5
"""

import argparse
import json
import sys
from pathlib import Path

import h5py
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fracture_mesh_ops import erode_fracture_band, piece_relief_stats  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", type=Path, required=True)
    ap.add_argument("--src-dataset", default="real_heldout_norm")
    ap.add_argument("--objects", default="",
                    help="comma-separated; default = all in the source dataset")
    ap.add_argument("--strengths", default="0,0.25,0.5,0.75,1.0")
    ap.add_argument("--out-hdf5", type=Path, required=True)
    ap.add_argument("--out-calibration", type=Path, default=None)
    ap.add_argument("--dataset-name", default="erosion_sweep")
    ap.add_argument("--kernel-frac-max", type=float, default=0.05)
    ap.add_argument("--normalize", action="store_true",
                    help="rescale each variant to max|v|=0.5 (shared factor per "
                         "variant) so the absolute part-accuracy threshold is valid; "
                         "needed when the source is in raw scan units")
    ap.add_argument("--preserve-split", action="store_true",
                    help="assign each variant to the same train/val split as its "
                         "source object, instead of putting everything in all "
                         "splits. Use when building TRAINING data, so worn copies "
                         "of a val object never leak into train.")
    ap.add_argument("--skip-relief", action="store_true",
                    help="skip the relief calibration measurement (slow on large "
                         "meshes); fine for training data, NOT for a causal sweep")
    args = ap.parse_args()

    strengths = [float(s) for s in args.strengths.split(",")]
    calib = {}
    names = []

    with h5py.File(args.src, "r") as src:
        ds = src[args.src_dataset]
        objects = ([o.strip() for o in args.objects.split(",") if o.strip()]
                   or sorted(ds.keys()))

        # which source objects belong to which split (for --preserve-split)
        src_split = {}
        if args.preserve_split and "data_split" in src:
            sg = src["data_split"].get(args.src_dataset)
            if sg is not None:
                for sp in sg.keys():
                    for r in sg[sp][:]:
                        src_split[r.decode().split("/")[-1]] = sp

        args.out_hdf5.parent.mkdir(parents=True, exist_ok=True)
        split_members = {"train": [], "val": [], "test": []}
        with h5py.File(args.out_hdf5, "w") as out:
            dgrp = out.create_group(args.dataset_name)
            for obj in objects:
                grp = ds[obj]
                pg = grp["pieces"] if "pieces" in grp else grp
                keys = sorted(pg.keys(), key=lambda s: int(s) if s.isdigit() else s)
                pieces = [(np.asarray(pg[k]["vertices"][:], dtype=np.float64),
                           np.asarray(pg[k]["faces"][:], dtype=np.int64)) for k in keys]
                print(f"{obj}: {len(pieces)} pieces", flush=True)

                for s in strengths:
                    if s <= 0:
                        verts = [v for v, _ in pieces]
                    else:
                        verts = erode_fracture_band(
                            pieces, strength=s, kernel_frac_max=args.kernel_frac_max)

                    tag = f"{obj}_e{int(round(s * 100)):03d}"
                    if args.skip_relief:
                        print(f"    strength {s:.2f}: built", flush=True)
                    else:
                        rel = [piece_relief_stats(v, f)["relief_p90"]
                               for v, (_, f) in zip(verts, pieces)]
                        calib[tag] = {"object": obj, "strength": s,
                                      "relief_p90_mean": float(np.mean(rel)),
                                      "relief_p90_per_piece": [float(x) for x in rel]}
                        print(f"    strength {s:.2f}: mean relief_p90 = {np.mean(rel):.4f}",
                              flush=True)

                    if args.normalize:
                        allv = np.concatenate(verts, axis=0)
                        c = allv.mean(axis=0)
                        m = float(np.abs(allv - c).max()) + 1e-12
                        fac = 0.5 / m
                        verts = [(v - c) * fac for v in verts]

                    og = dgrp.create_group(tag)
                    opg = og.create_group("pieces")
                    for i, (v, (_, f)) in enumerate(zip(verts, pieces)):
                        sg = opg.create_group(str(i))
                        sg.create_dataset("vertices", data=np.asarray(v, dtype=np.float64))
                        sg.create_dataset("faces", data=f)
                    og.create_dataset(
                        "pieces_names",
                        data=np.array([f"Piece{i + 1:02d}".encode() for i in range(len(verts))],
                                      dtype=object),
                        dtype=h5py.special_dtype(vlen=bytes))
                    full = f"{args.dataset_name}/{tag}"
                    names.append(full)
                    if args.preserve_split:
                        # worn copies inherit their source object's split, so a
                        # val object's variants can never leak into training
                        split_members.setdefault(src_split.get(obj, "train"), []).append(full)

            sgrp = out.create_group("data_split").create_group(args.dataset_name)
            if args.preserve_split:
                for split in ("train", "val", "test"):
                    mem = split_members.get(split) or []
                    if split == "test" and not mem:
                        mem = split_members.get("val") or []
                    sgrp.create_dataset(
                        split, data=np.array([n.encode() for n in mem], dtype=object),
                        dtype=h5py.special_dtype(vlen=bytes))
                    print(f"  split {split}: {len(mem)} variants")
            else:
                arr = np.array([n.encode() for n in names], dtype=object)
                for split in ("train", "val", "test"):
                    sgrp.create_dataset(split, data=arr, dtype=h5py.special_dtype(vlen=bytes))

    out_cal = args.out_calibration or args.out_hdf5.with_suffix(".calibration.json")
    out_cal.write_text(json.dumps(calib, indent=2))
    print(f"\nwrote {len(names)} variants -> {args.out_hdf5}")
    print(f"wear calibration -> {out_cal}")
    print("Compare achieved relief_p90 against the Juglet's own measured wear "
          "before interpreting a negative result (GARF Exp 7 undershot here).")


if __name__ == "__main__":
    main()
