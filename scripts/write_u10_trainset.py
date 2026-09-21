"""U10 stage 1: write CSC's broken vessels as TORA training files, one per arm.

Spec module 5 (umbrella `.scratch/u10-juglet-ceiling/spec.md`), tora ticket
`u10-juglet-ceiling/02`. The audit that judges the result is `audit_u10_trainset.py`; it
reads only what this writes, so nothing here is trusted by it.

WHAT GOES IN. Exactly the corpus CSC ticket 04 assembled (`corpus.json`, written by
CSC/scripts/assemble_u10_corpus.py from the per-vessel jsons): per vessel, the breakages
left after the never-nine removal, the spare swap and the trim. The sherds are the
CLEANED ones CSC's runner saved with --keep (`<vessel>_sherds.npz`, mm, the tool's
zero-thickness internal walls already stripped) -- not the raw piece_*.obj, which still
carry those double walls.

LAYOUT. The one every other TORA file here uses (build_juglet_ground_truth.py,
build_wear_trainset_v2.py): `<dataset>/<object>/pieces/<i>/{vertices,faces}`, a
`pieces_names` list, and `data_split/<dataset>/{train,val,test}` naming the objects. One
file per arm, `u10_ceiling.hdf5` and `u10_generic.hdf5`, so each adapter is pointed at its
own arm by `dataset_names` and nothing else differs between them.

UNITS. The Juglet's file (`juglet_gt.hdf5`) is centred on its vertex mean and scaled by
one shared factor to max|coord| = 0.5. Every breakage here is stored the same way, so the
size TORA passes to the model as a label (tora/data/dataset.py, `scales`) matches the
Juglet's. That is also why only ratios survive as shape variety (spec, "Size"). The mm
factor is kept per breakage (`mm_per_unit`) so the audit can measure walls in mm.

SPLIT BY VESSEL. Training vessels -> `train`, choosing vessels -> `val`. A vessel's
breakages repeat its own bands (CSC ticket 06), so splitting by breakage would put the
same fragments on both sides. `test` is left empty on purpose: the Juglet is the test,
and wear v3's file carrying `test` as a copy of `val` is a trap noted in its config.

No wear and no dropped pieces (stage 1 is "shape prior on fresh breaks").

Stored per breakage (group attrs): vessel, fracture, arm, role, form, recipe (json),
sherds, mm_per_unit, coincident_share -- the share of break-face vertices that sit exactly
on a neighbour's vertex. It is expected to be ~1: fracture-modes cuts every sherd from one
mesh, so every join is a perfect fit by design (spec, "Every join is a perfect fit").

    python scripts/write_u10_trainset.py --corpus <corpus.json> --recipes <recipes.json> \
        --sherds <dir of <vessel>_sherds.npz and _fracture.json> --out <dataset dir>
"""
import argparse
import hashlib
import json
from pathlib import Path

import h5py
import numpy as np
from scipy.spatial import cKDTree

FROZEN = "422081368edc75f4d67016ba34ff705d09ff091ce69e41ac48e777aa8d41f424"
TARGET_MAX_ABS = 0.5
COINCIDE_MM = 1e-4
SPLIT = {"train": "train", "choose": "val"}


def recipe_hash(recipes):
    return hashlib.sha256(json.dumps(recipes, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def coincident_share(sherds):
    """Share of break-face vertices that coincide with another sherd's vertex."""
    trees = [cKDTree(V) for V, _, _ in sherds]
    hit = tot = 0
    for i, (V, F, brk) in enumerate(sherds):
        vid = np.unique(F[brk])
        if not len(vid):
            continue
        P = V[vid]
        near = np.zeros(len(P), bool)
        for j, t in enumerate(trees):
            if j != i:
                d, _ = t.query(P, distance_upper_bound=COINCIDE_MM)
                near |= np.isfinite(d)
        hit += int(near.sum())
        tot += len(P)
    return hit / tot if tot else float("nan")


def load_breakage(z, k):
    n = int(z[f"f{k}_n"])
    return [(z[f"f{k}_p{i}_V"].astype(np.float64), z[f"f{k}_p{i}_F"].astype(np.int64),
             z[f"f{k}_p{i}_break"].astype(bool)) for i in range(n)]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--recipes", required=True)
    ap.add_argument("--sherds", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    corpus = json.loads(Path(args.corpus).read_text())
    recipes = json.loads(Path(args.recipes).read_text())["recipes"]
    if recipe_hash(recipes) != FROZEN or corpus["recipe_hash"] != FROZEN:
        raise SystemExit("refusing: recipe list or corpus is not the frozen one")
    by_name = {r["name"]: r for r in recipes}
    src = Path(args.sherds)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    manifest = {}

    for arm in ("ceiling", "generic"):
        ds_name = f"u10_{arm}"
        path = out / f"{ds_name}.hdf5"
        members = {"train": [], "val": [], "test": []}
        with h5py.File(path, "w") as fo:
            fo.attrs["recipe_hash"] = FROZEN
            fo.attrs["recipes"] = json.dumps(recipes, sort_keys=True, separators=(",", ":"))
            fo.attrs["arm"] = arm
            fo.attrs["source"] = "CSC ticket 04, job 30888410, corpus.json"
            fo.attrs["target_max_abs"] = TARGET_MAX_ABS
            dgrp = fo.create_group(ds_name)
            for v in corpus["vessels"]:
                role = v.get("role_in_corpus")
                if v["arm"] != arm or role not in SPLIT or not v["corpus"]:
                    continue
                rec = json.loads((src / f"{v['name']}_fracture.json").read_text())
                index_of = {p["fracture"]: k for k, p in enumerate(rec["per_fracture"])}
                z = np.load(src / f"{v['name']}_sherds.npz")
                saved = set(int(k) for k in z["saved"])
                for frac in v["corpus"]:
                    k = index_of[frac]
                    if k not in saved:
                        raise SystemExit(f"{v['name']} {frac}: kept but not saved in the npz")
                    sherds = load_breakage(z, k)
                    share = coincident_share(sherds)
                    allv = np.concatenate([V for V, _, _ in sherds])
                    c = allv.mean(axis=0)
                    m = float(np.abs(allv - c).max()) + 1e-12
                    fac = TARGET_MAX_ABS / m
                    tag = f"{v['name']}__{frac}"
                    og = dgrp.create_group(tag)
                    pg = og.create_group("pieces")
                    for i, (V, F, _) in enumerate(sherds):
                        sg = pg.create_group(f"{i:02d}")
                        sg.create_dataset("vertices", data=((V - c) * fac).astype(np.float32))
                        sg.create_dataset("faces", data=F.astype(np.int32))
                    og.create_dataset(
                        "pieces_names",
                        data=np.array([f"Piece{i + 1:02d}".encode() for i in range(len(sherds))],
                                      dtype=object),
                        dtype=h5py.special_dtype(vlen=bytes))
                    recipe = by_name[v["name"]]
                    og.attrs.update(vessel=v["name"], fracture=frac, arm=arm, role=role,
                                    form=recipe["form"],
                                    recipe=json.dumps(recipe, sort_keys=True),
                                    sherds=len(sherds), mm_per_unit=1.0 / fac,
                                    coincident_share=share)
                    members[SPLIT[role]].append(f"{ds_name}/{tag}")
                    manifest[f"{ds_name}/{tag}"] = dict(vessel=v["name"], split=SPLIT[role],
                                                         sherds=len(sherds),
                                                         coincident_share=round(share, 6))
                print(f"{arm} {v['name']:<18s} {role:<6s} {len(v['corpus']):3d} breakages",
                      flush=True)
            sgrp = fo.create_group("data_split").create_group(ds_name)
            for sp, mem in members.items():
                sgrp.create_dataset(sp, data=np.array([n.encode() for n in mem], dtype=object),
                                    dtype=h5py.special_dtype(vlen=bytes))
        print(f"wrote {path}: train {len(members['train'])}, val {len(members['val'])}",
              flush=True)
    (out / "u10_trainset.manifest.json").write_text(json.dumps(manifest, indent=1))


if __name__ == "__main__":
    main()
