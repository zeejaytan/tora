"""U10 ticket 08: wear (or jitter) the break faces of the U10 corpus, nothing else.

Tora ticket `.scratch/u10-juglet-ceiling/issues/08-worn-generic-corpus.md`. Reads the two
files `write_u10_trainset.py` wrote (`u10_generic.hdf5`, `u10_ceiling.hdf5`) and writes
ONE pooled file per arm:

  worn   break-face recession: every vertex of a break face (CSC's per-face `_break`
         flag, read from the corpus npz) moves back along the break face's own smoothed
         normal by the dose, THEN `recede_and_chip(recession_frac=0)` with dish chips on
         the same break vertices. Doses are wear v3's (build_bbad_vessel_trainset.py,
         WEAR_LEVELS), light and moderate per breakage.
  noise  the cruder baseline O7 asks for: independent Gaussian jitter on the same break
         vertices, scaled so its RMS displacement equals the worn variant's for that
         breakage and level. Same two levels.

WHY NOT WEAR V3'S `recede_surface`. It finds the contact band by distance (`_band_mask`,
2% of the diagonal) and pushes along the sherd's outward direction. On these 1.6-2.5 mm
walls the band covers 45-100% of each sherd, and both sides of a join move together:
the wall thins by ~0.25 mm per side while the join stays shut (gap 0.003-0.02% of the
diagonal). Rendered in artifacts/u10/r08/section_g00_{6_7,0_1}.png; the break-face
version opens the join by ~2x the dose with the skins untouched
(section_breakface_{6_7,0_1}.png).

WHAT DOES NOT CHANGE. Vessels, breakages, sherd count, split (train / val by vessel) and the
coordinate frame: vertices are written back in the source file's normalised frame with no
re-centring, so the only difference between arms is the break surface. No sherd is dropped.

FRESH IS NOT WRITTEN. The fresh corpus is the source files themselves; wear v3 kept fresh
out of its worn arm because exactly-coincident joins teach lookup, not assembly
(build_bbad_vessel_trainset.py, change 2). A worn variant that still shares a vertex with a
neighbour is dropped and counted, as there.

MEASURED PER VARIANT (manifest json, and group attrs): coincident share, RMS displacement
of the break vertices, and two gaps as % of the object's bounding-box diagonal (p10/p50/p90):
  break_gap    break vertices only, to the nearest vertex of another sherd (needs flags);
  contact_gap  every vertex within `--gap-cut` of another sherd -- the ruler that needs no
               flags, so `--measure` applies the same one to the Juglet for the reference.

    python scripts/write_u10_worn.py --src <dir with u10_{generic,ceiling}.hdf5>         --csc <CSC u10 corpus dir> --mode worn --out <dir> [--workers 32] [--limit N]
    python scripts/write_u10_worn.py --measure <file.hdf5> --dataset juglet_gt

DOSE SWEEP (ticket 09). `--scale-pct P` writes ONE level instead of the two: the whole light
operator scaled by P/100 -- recession 0.15% x P/100 and chip radius 0.22% x P/100, still 2
chips -- so every level is the same wear shape at a different strength (fixed light chips
would outweigh a quarter-strength recession). Noise stays RMS-matched to worn at that level.
Dataset and file are named u10_<mode>_d<PPP>, e.g. u10_noise_d050.
"""
import argparse
import json
import sys
import zlib
from multiprocessing import Pool
from pathlib import Path

import h5py
import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wear_ops import recede_and_chip  # noqa: E402
from compare_wear_severity import coincident_frac  # noqa: E402
from sherd_worn.labelled import (  # noqa: E402
    diag,
    point_triangle,
    surface_dist,
    contact_gap,
    recede_break,
    band_rms,
    jitter,
)

# wear v3's two trainable levels, verbatim (build_bbad_vessel_trainset.py, WEAR_LEVELS)
LEVELS = [("light", 0.0015, 2, 0.0022), ("moderate", 0.0030, 3, 0.0025)]
SOURCES = ("u10_generic", "u10_ceiling")


def break_gap(pieces, vflags):
    """p10/p50/p90 (% of diagonal) of break-vertex-to-other-sherd surface distance."""
    D = diag(pieces)
    trees = [cKDTree(v) for v, _ in pieces]
    ds = []
    for i, ((v, _), b) in enumerate(zip(pieces, vflags)):
        best = np.full(int(b.sum()), np.inf)
        for j, (t, (vj, fj)) in enumerate(zip(trees, pieces)):
            if i != j:
                best = np.minimum(best, surface_dist(v[b], vj, fj, t))
        ds.append(best)
    d = np.concatenate(ds) / D * 100.0
    return [round(float(x), 4) for x in np.percentile(d, [10, 50, 90])] + [int(len(d))]


def load_flags(npz, k, pieces):
    """CSC's per-FACE break flag for breakage k -> (face flags, vertex flags) per sherd."""
    z = np.load(npz)
    fflags, vflags = [], []
    for i, (v, f) in enumerate(pieces):
        fb = z[f"f{k}_p{i}_break"].astype(bool)
        if len(fb) != len(f) or len(z[f"f{k}_p{i}_V"]) != len(v):
            raise RuntimeError(f"{npz} f{k} p{i}: mesh does not match the hdf5 sherd")
        vb = np.zeros(len(v), bool)
        vb[f[fb].ravel()] = True
        fflags.append(fb)
        vflags.append(vb)
    return fflags, vflags


def work(job):
    key, pieces, mode, seed, cut, npz, k, levels = job
    rng = np.random.default_rng(seed)
    fflags, vflags = load_flags(npz, k, pieces)
    masks = [(b, b.astype(float)) for b in vflags]
    D = diag(pieces)
    res = {"key": key, "coincident_fresh": coincident_frac([v for v, _ in pieces]),
           "break_share": float(np.mean(np.concatenate(vflags))),
           "gap_fresh": contact_gap(pieces, cut), "break_gap_fresh": break_gap(pieces, vflags),
           "variants": []}
    for name, dose, n_chip, chip_sz in levels:
        worn = recede_break(pieces, fflags, vflags, dose)
        worn = recede_and_chip(worn, recession_frac=0.0, chip_count=n_chip,
                               chip_frac=chip_sz, seed=int(rng.integers(1 << 30)),
                               masks=masks, chip_method="dish")
        rms = band_rms(pieces, worn, vflags)
        out = worn if mode == "worn" else jitter(pieces, vflags, rms, rng)
        skin = max(float(np.linalg.norm(o[~b] - v[~b], axis=1).max(initial=0.0))
                   for (v, _), (o, _), b in zip(pieces, out, vflags))
        coin = coincident_frac([v for v, _ in out])
        res["variants"].append({
            "level": name, "dose": dose, "chips": n_chip, "chip_size": chip_sz,
            "band_rms_pct": rms / D * 100.0,
            "band_rms_out_pct": band_rms(pieces, out, vflags) / D * 100.0,
            "skin_move_max_pct": skin / D * 100.0,
            "coincident": coin, "gap": contact_gap(out, cut),
            "break_gap": break_gap(out, vflags),
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


def csc_index(csc, vessel, fracture, cache={}):
    """(npz path, k) for one breakage: k is its index in <vessel>_fracture.json per_fracture."""
    if vessel not in cache:
        pf = json.loads((csc / f"{vessel}_fracture.json").read_text())["per_fracture"]
        cache[vessel] = {r["fracture"]: k for k, r in enumerate(pf)}
    return str(csc / f"{vessel}_sherds.npz"), cache[vessel][fracture]


def jobs(src, csc, mode, limit, cut, levels):
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
                npz, k = csc_index(csc, attrs["vessel"], attrs["fracture"])
                seed = zlib.crc32(f"{s}/{tag}".encode())  # hash() of str varies per run
                yield (f"{s}/{tag}", read_obj(g), mode, seed, cut, npz, k, levels), \
                    (s, tag, sp, attrs)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--src")
    ap.add_argument("--csc", help="CSC u10 corpus dir (<vessel>_sherds.npz, _fracture.json)")
    ap.add_argument("--mode", choices=("worn", "noise"))
    ap.add_argument("--out")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int, default=0, help="per source file, for a dry run")
    ap.add_argument("--gap-cut", type=float, default=0.02, help="fraction of diagonal")
    ap.add_argument("--scale-pct", type=int, default=0,
                    help="dose sweep: one level, the light operator x P/100 (see docstring)")
    ap.add_argument("--no-chips", action="store_true",
                    help="with --scale-pct: recession only, no chips (dataset suffix 'nc')")
    ap.add_argument("--measure")
    ap.add_argument("--dataset")
    a = ap.parse_args()
    if a.measure:
        return measure(a.measure, a.dataset, a.gap_cut)

    src, out = Path(a.src), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    ds = f"u10_{a.mode}"
    levels = LEVELS
    if a.scale_pct:
        k = a.scale_pct / 100.0
        name, dose, n_chip, chip_sz = LEVELS[0]
        nc = "nc" if a.no_chips else ""
        levels = [(f"d{a.scale_pct:03d}{nc}", dose * k, 0 if nc else n_chip, chip_sz * k)]
        ds = f"u10_{a.mode}_d{a.scale_pct:03d}{nc}"
    path = out / f"{ds}.hdf5"
    pairs = list(jobs(src, Path(a.csc), a.mode, a.limit, a.gap_cut, levels))
    meta = {p[0][0]: p[1] for p in pairs}
    members = {"train": [], "val": [], "test": []}
    manifest, dropped = {}, 0
    vlen = h5py.special_dtype(vlen=bytes)
    with h5py.File(path, "w") as fo, Pool(a.workers) as pool:
        fo.attrs.update(mode=a.mode, levels=json.dumps(levels), sources=json.dumps(SOURCES),
                        gap_cut=a.gap_cut, ticket="tora u10-juglet-ceiling/08")
        dg = fo.create_group(ds)
        for res in pool.imap_unordered(work, (p[0] for p in pairs), chunksize=1):
            s, tag, sp, attrs = meta[res["key"]]
            for var in res["variants"]:
                rec = {k: v for k, v in var.items() if k != "pieces"}
                rec.update(coincident_fresh=res["coincident_fresh"], gap_fresh=res["gap_fresh"],
                           break_gap_fresh=res["break_gap_fresh"],
                           break_share=res["break_share"], split=sp)
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
                                gap=json.dumps(var["gap"]),
                                break_gap=json.dumps(var["break_gap"]),
                                skin_move_max_pct=var["skin_move_max_pct"],
                                operator="break-face recession + dish chips")
                members[sp].append(f"{ds}/{name}")
            print(f"{res['key']}: break gap fresh {res['break_gap_fresh']} -> "
                  + ", ".join(f"{v['level']} {v['break_gap']} (contact {v['gap']}) "
                              f"rms {v['band_rms_out_pct']:.3f}% skin {v['skin_move_max_pct']:.3f}%"
                              for v in res["variants"]), flush=True)
        sg = fo.create_group("data_split").create_group(ds)
        for sp, mem in members.items():
            sg.create_dataset(sp, dtype=vlen, data=np.array([m.encode() for m in sorted(mem)],
                                                            dtype=object))
    (out / f"{ds}.manifest.json").write_text(json.dumps(manifest, indent=1))
    print(f"wrote {path}: train {len(members['train'])}, val {len(members['val'])}, "
          f"dropped {dropped}", flush=True)


if __name__ == "__main__":
    main()
