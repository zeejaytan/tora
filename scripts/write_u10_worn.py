"""U10 ticket 08: wear (or jitter) the break faces of the U10 corpus, nothing else.

Tora ticket `.scratch/u10-juglet-ceiling/issues/08-worn-generic-corpus.md`. Reads the two
files `write_u10_trainset.py` wrote (`u10_generic.hdf5`, `u10_ceiling.hdf5`) and writes
ONE pooled file per arm:

  worn   wear v3's operator, unchanged: `recede_surface` at the calibrated dose, THEN
         `recede_and_chip(recession_frac=0)` with dish chips (the order and the reasons
         are in build_bbad_vessel_trainset.py, WEAR_LEVELS). Light and moderate per
         breakage.
  noise  the cruder baseline O7 asks for: independent Gaussian jitter on the same contact
         band, weighted by the same feather, scaled so its RMS vertex displacement equals
         the worn variant's for that breakage and level. Same two levels.

WHAT DOES NOT CHANGE. Vessels, breakages, sherd count, split (train / val by vessel) and the
coordinate frame: vertices are written back in the source file's normalised frame with no
re-centring, so the only difference between arms is the break surface. No sherd is dropped
(wear v3 also removed one; that is a second variable and is left out here).

FRESH IS NOT WRITTEN. The fresh corpus is the source files themselves; wear v3 kept fresh
out of its worn arm because exactly-coincident joins teach lookup, not assembly
(build_bbad_vessel_trainset.py, change 2). A worn variant that still shares a vertex with a
neighbour is dropped and counted, as there.

MEASURED PER VARIANT (manifest json, and group attrs): coincident share before and after,
RMS displacement of the band, and the CONTACT GAP -- for every vertex within `--gap-cut` of
another sherd, its distance to the nearest vertex of another sherd, p10/p50/p90 as % of the
object's bounding-box diagonal. Wear v3's calibration ruler is not in the repo, so this is
a new ruler; `--measure` applies the same one to any file (the Juglet) for the reference.

    python scripts/write_u10_worn.py --src <dir with u10_{generic,ceiling}.hdf5> \
        --mode worn --out <dir> [--workers 32] [--limit N]
    python scripts/write_u10_worn.py --measure <file.hdf5> --dataset juglet_gt
"""
import argparse
import json
import sys
from multiprocessing import Pool
from pathlib import Path

import h5py
import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wear_ops import recede_and_chip, recede_surface, wear_context  # noqa: E402
from compare_wear_severity import coincident_frac  # noqa: E402

# wear v3's two trainable levels, verbatim (build_bbad_vessel_trainset.py, WEAR_LEVELS)
LEVELS = [("light", 0.0015, 2, 0.0022), ("moderate", 0.0030, 3, 0.0025)]
SOURCES = ("u10_generic", "u10_ceiling")


def diag(pieces):
    allv = np.concatenate([v for v, _ in pieces], axis=0)
    return float(np.linalg.norm(allv.max(0) - allv.min(0))) + 1e-12


def contact_gap(pieces, cut_frac):
    """p10/p50/p90 (% of diagonal) of vertex-to-other-sherd distance, within the cut."""
    D = diag(pieces)
    trees = [cKDTree(v) for v, _ in pieces]
    ds = []
    for i, (v, _) in enumerate(pieces):
        best = np.full(len(v), np.inf)
        for j, t in enumerate(trees):
            if i != j:
                best = np.minimum(best, t.query(v, workers=1)[0])
        ds.append(best[best <= cut_frac * D])
    d = np.concatenate(ds) / D * 100.0
    if not len(d):
        return None
    return [round(float(x), 4) for x in np.percentile(d, [10, 50, 90])] + [int(len(d))]


def band_rms(fresh, out, masks):
    sq, n = 0.0, 0
    for (v0, _), (v1, _), (_, feather) in zip(fresh, out, masks):
        if len(v0) != len(v1):
            raise RuntimeError("vertex count changed; dish chipping should preserve it")
        b = feather > 0.02
        sq += float(((v1[b] - v0[b]) ** 2).sum())
        n += int(b.sum())
    return (sq / max(n, 1)) ** 0.5


def jitter(fresh, masks, target_rms, rng):
    raw = []
    for (v, _), (_, feather) in zip(fresh, masks):
        w = np.where(feather > 0.02, feather, 0.0)
        raw.append(rng.standard_normal(v.shape) * w[:, None])
    sq = sum(float((r[(m[1] > 0.02)] ** 2).sum()) for r, m in zip(raw, masks))
    n = sum(int((m[1] > 0.02).sum()) for m in masks)
    k = target_rms / max((sq / max(n, 1)) ** 0.5, 1e-15)
    return [(v + k * r, f.copy()) for (v, f), r in zip(fresh, raw)]


def work(job):
    key, pieces, mode, seed, cut = job
    rng = np.random.default_rng(seed)
    masks, _ = wear_context(pieces)
    res = {"key": key, "coincident_fresh": coincident_frac([v for v, _ in pieces]),
           "gap_fresh": contact_gap(pieces, cut), "variants": []}
    for name, dose, n_chip, chip_sz in LEVELS:
        worn = recede_surface(pieces, recession_frac=dose, masks=masks)
        worn = recede_and_chip(worn, recession_frac=0.0, chip_count=n_chip,
                               chip_frac=chip_sz, seed=int(rng.integers(1 << 30)),
                               masks=masks, chip_method="dish")
        rms = band_rms(pieces, worn, masks)
        out = worn if mode == "worn" else jitter(pieces, masks, rms, rng)
        coin = coincident_frac([v for v, _ in out])
        res["variants"].append({
            "level": name, "dose": dose, "chips": n_chip, "chip_size": chip_sz,
            "band_rms_pct": rms / diag(pieces) * 100.0,
            "band_rms_out_pct": band_rms(pieces, out, masks) / diag(pieces) * 100.0,
            "coincident": coin, "gap": contact_gap(out, cut),
            "pieces": out if coin == 0.0 else None})
    return res


def read_obj(grp):
    names = sorted(grp["pieces"].keys())
    return [(grp["pieces"][k]["vertices"][:].astype(np.float64),
             grp["pieces"][k]["faces"][:].astype(np.int64)) for k in names]


def measure(path, dataset, cut):
    with h5py.File(path, "r") as f:
        for tag in f[dataset]:
            p = read_obj(f[dataset][tag])
            print(json.dumps({"object": tag, "sherds": len(p),
                              "coincident": coincident_frac([v for v, _ in p]),
                              "gap_p10_p50_p90_n": contact_gap(p, cut)}), flush=True)


def jobs(src, mode, limit, cut):
    for s in SOURCES:
        with h5py.File(src / f"{s}.hdf5", "r") as f:
            split = {sp: [n.decode() for n in f["data_split"][s][sp][:]]
                     for sp in ("train", "val")}
            members = split["train"] + split["val"]
            for i, full in enumerate(members[:limit] if limit else members):
                tag = full.split("/", 1)[1]
                g = f[s][tag]
                attrs = {k: (v.item() if hasattr(v, "item") else v) for k, v in g.attrs.items()}
                sp = "train" if full in split["train"] else "val"
                yield (f"{s}/{tag}", read_obj(g), mode, hash((s, tag)) & 0x7fffffff,
                       cut), (s, tag, sp, attrs)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--src")
    ap.add_argument("--mode", choices=("worn", "noise"))
    ap.add_argument("--out")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int, default=0, help="per source file, for a dry run")
    ap.add_argument("--gap-cut", type=float, default=0.02, help="fraction of diagonal")
    ap.add_argument("--measure")
    ap.add_argument("--dataset")
    a = ap.parse_args()
    if a.measure:
        return measure(a.measure, a.dataset, a.gap_cut)

    src, out = Path(a.src), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    ds = f"u10_{a.mode}"
    path = out / f"{ds}.hdf5"
    pairs = list(jobs(src, a.mode, a.limit, a.gap_cut))
    meta = {p[0][0]: p[1] for p in pairs}
    members = {"train": [], "val": [], "test": []}
    manifest, dropped = {}, 0
    vlen = h5py.special_dtype(vlen=bytes)
    with h5py.File(path, "w") as fo, Pool(a.workers) as pool:
        fo.attrs.update(mode=a.mode, levels=json.dumps(LEVELS), sources=json.dumps(SOURCES),
                        gap_cut=a.gap_cut, ticket="tora u10-juglet-ceiling/08")
        dg = fo.create_group(ds)
        for res in pool.imap_unordered(work, (p[0] for p in pairs), chunksize=1):
            s, tag, sp, attrs = meta[res["key"]]
            for var in res["variants"]:
                rec = {k: v for k, v in var.items() if k != "pieces"}
                rec.update(coincident_fresh=res["coincident_fresh"], gap_fresh=res["gap_fresh"],
                           split=sp)
                name = f"{s}__{tag}__{var['level']}"
                manifest[name] = rec
                if var["pieces"] is None:
                    dropped += 1
                    print(f"DROP {name}: {100 * var['coincident']:.3f}% still coincident",
                          flush=True)
                    continue
                og = dg.create_group(name)
                pg = og.create_group("pieces")
                for i, (v, f) in enumerate(var["pieces"]):
                    sg = pg.create_group(f"{i:02d}")
                    sg.create_dataset("vertices", data=v.astype(np.float32))
                    sg.create_dataset("faces", data=f.astype(np.int32))
                og.create_dataset("pieces_names", dtype=vlen, data=np.array(
                    [f"Piece{i + 1:02d}".encode() for i in range(len(var["pieces"]))],
                    dtype=object))
                og.attrs.update(attrs)
                og.attrs.update(source=s, wear_mode=a.mode, wear_level=var["level"],
                                coincident_after=var["coincident"],
                                band_rms_pct=var["band_rms_out_pct"],
                                gap=json.dumps(var["gap"]))
                members[sp].append(f"{ds}/{name}")
            print(f"{res['key']}: fresh gap {res['gap_fresh']} -> "
                  + ", ".join(f"{v['level']} {v['gap']} rms {v['band_rms_out_pct']:.3f}%"
                              for v in res["variants"]), flush=True)
        sg = fo.create_group("data_split").create_group(ds)
        for sp, mem in members.items():
            sg.create_dataset(sp, dtype=vlen, data=np.array([m.encode() for m in mem],
                                                            dtype=object))
    (out / f"{ds}.manifest.json").write_text(json.dumps(manifest, indent=1))
    print(f"wrote {path}: train {len(members['train'])}, val {len(members['val'])}, "
          f"dropped {dropped}", flush=True)


if __name__ == "__main__":
    main()
