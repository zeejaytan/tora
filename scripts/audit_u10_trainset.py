"""U10 stage 1: audit the finished training files -- spec seam 1, tora ticket 02.

Reads ONLY the files `write_u10_trainset.py` produced (and the Juglet's own file, for the
size comparison). Nothing the writer computed about the geometry is trusted: break faces
are found again here, walls are measured again, and the sherd count is the number of
meshes actually in the file. Exits 1 and names every reason if any of these hold:

  sherds      a breakage outside 3-64 sherds, or with exactly 9 (the Juglet's count);
  open        a sherd that is not closed;
  bodies      a sherd in more than one piece of clay;
  wall        a vessel whose median sherd wall is outside 1.6-2.5 mm, or a sherd more
              than 2.5 times its vessel's median (a solid lump);
  recipe      a recipe value outside the frozen ranges, a recipe that is not the one in
              the frozen list, or a list whose hash is not the frozen one;
  split       a vessel in both splits, in both arms, or an object not in exactly one split;
  arms        the two arms' training breakage counts differ;
  size        the size TORA will see as a label is outside 0.9-1.1 x the Juglet's.

WHY THE WALL IS JUDGED PER VESSEL. The measure is twice the volume over the outer skin
area (C2's). On a whole wall it reads the wall; on one small sherd it is thrown off by the
sherd's edges, and on a handle rod or a rounded lip it reads the rod, not a wall. On CSC
ticket 04's corpus, every vessel built at 1.6-2.5 mm, 432 of 9,715 sherds read 1.44-4.21
mm; per vessel the median lands within 0.07 mm of the built wall. So a per-sherd range
would fail the corpus on the ruler. The lump rule catches what a per-sherd rule was for:
the thickest real sherd, a handle rod, is 2.0 x its vessel's median.

WHY BREAK FACES ARE FOUND BY COINCIDENCE. fracture-modes cuts every sherd from one mesh,
so a break face is a triangle whose three corners sit exactly on another sherd's
vertices. The same test gives the coincident share, reported, never failed on: every
join is a perfect fit by design (spec, "Every join is a perfect fit").

THE SIZE LABEL is what tora/data/dataset.py passes as `scales`: max |coord| after
centring. The loader centres on sampled surface points, i.e. the area-weighted surface
centroid; that centroid is used here, for the Juglet and for every breakage alike, so the
comparison is deterministic. (Training then multiplies it by 0.75-1.25 at random.)

    python scripts/audit_u10_trainset.py --juglet <juglet_gt.hdf5> --out <report.json> \
        <u10_ceiling.hdf5> <u10_generic.hdf5> [--workers 16]
"""
import argparse
import hashlib
import json
import sys
from collections import defaultdict
from multiprocessing import Pool

import h5py
import numpy as np
import trimesh
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

FROZEN = "422081368edc75f4d67016ba34ff705d09ff091ce69e41ac48e777aa8d41f424"
RANGES = {"height_to_girth": (0.85, 1.15), "neck_length": (0.85, 1.15),
          "neck_width": (0.85, 1.15), "handle_loop": (0.75, 1.25),
          "handle_strap": (0.75, 1.25), "wall_mm": (1.6, 2.5)}
SHERDS = (3, 64)
NEVER = 9
WALL_MM = (1.6, 2.5)
LUMP = 2.5
SIZE = (0.9, 1.1)
COINCIDE_MM = 1e-4


def recipe_hash(recipes):
    return hashlib.sha256(json.dumps(recipes, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def pieces_of(group):
    g = group["pieces"] if "pieces" in group else group
    return [(np.asarray(g[k]["vertices"][:], np.float64), np.asarray(g[k]["faces"][:], np.int64))
            for k in sorted(g.keys())]


def surface_centroid(pieces):
    c, a = [], []
    for V, F in pieces:
        t = V[F]
        ar = 0.5 * np.linalg.norm(np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]), axis=1)
        c.append((t.mean(1) * ar[:, None]).sum(0))
        a.append(ar.sum())
    return np.sum(c, 0) / np.sum(a)


def size_label(pieces):
    c = surface_centroid(pieces)
    return float(max(np.abs(V - c).max() for V, _ in pieces))


def n_bodies(F, nv):
    e = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    g = coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(nv, nv))
    n, lab = connected_components(g, directed=False)
    return len(np.unique(lab[np.unique(F)]))


def measure(job):
    """One breakage, from the file alone."""
    path, name = job
    with h5py.File(path, "r") as f:
        grp = f[name]
        pieces = pieces_of(grp)
        mm = float(grp.attrs["mm_per_unit"])
    tol = COINCIDE_MM / mm
    trees = [cKDTree(V) for V, _ in pieces]
    out = []
    hit = tot = 0
    for i, (V, F) in enumerate(pieces):
        on = np.zeros(len(V), bool)
        for j, t in enumerate(trees):
            if j != i:
                d, _ = t.query(V, distance_upper_bound=tol)
                on |= np.isfinite(d)
        brk = on[F].all(1)
        vid = np.unique(F[brk])
        hit += int(on[vid].sum())
        tot += len(vid)
        m = trimesh.Trimesh(V, F, process=False)
        closed = bool(m.is_watertight)
        t = V[F]
        ar = 0.5 * np.linalg.norm(np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]), axis=1)
        skin = float(ar[~brk].sum())
        vol = abs(float(m.volume)) if closed else float("nan")
        wall = 2 * vol / skin * mm if (closed and skin > 0) else float("nan")
        out.append(dict(closed=closed, bodies=n_bodies(F, len(V)), wall_mm=wall,
                        volume_mm3=vol * mm ** 3, break_share=float(ar[brk].sum() / ar.sum())))
    return dict(name=name, path=path, sherds=out, size_label=size_label(pieces),
                coincident_share=hit / tot if tot else float("nan"))


def audit(paths, juglet, workers=8):
    fails, facts = [], {}

    def fail(kind, msg):
        fails.append(f"{kind}: {msg}")

    with h5py.File(juglet, "r") as f:
        sp = f["data_split"][next(iter(f["data_split"]))]
        names = sorted({n.decode() for s in sp for n in sp[s][:]})
        if len(names) != 1:
            raise SystemExit(f"{juglet}: expected the one Juglet, found {names}")
        jlabel = size_label(pieces_of(f[names[0]]))
    facts["juglet_size_label"] = jlabel

    jobs, info = [], {}
    split_of = defaultdict(set)       # vessel -> {(arm, split)}
    train_count = {}
    for path in paths:
        with h5py.File(path, "r") as f:
            arm = str(f.attrs.get("arm", path))
            try:
                recipes = json.loads(f.attrs["recipes"])
            except KeyError:
                fail("recipe", f"{path}: no recipe list in the file")
                recipes = []
            h = recipe_hash(recipes)
            if h != FROZEN or f.attrs.get("recipe_hash") != FROZEN:
                fail("recipe", f"{path}: recipe list hash {h[:12]} is not the frozen {FROZEN[:12]}")
            listed = {r["name"]: r for r in recipes}
            ds = [k for k in f.keys() if k != "data_split"]
            if len(ds) != 1:
                fail("split", f"{path}: expected one dataset group, found {ds}")
                continue
            ds = ds[0]
            objs = set(f"{ds}/{o}" for o in f[ds].keys())
            seen = defaultdict(list)
            for sp in f["data_split"][ds].keys():
                for n in f["data_split"][ds][sp][:]:
                    seen[n.decode()].append(sp)
            for n in objs - set(seen):
                fail("split", f"{n} is in no split")
            for n, sps in seen.items():
                if n not in objs:
                    fail("split", f"{n} is listed in {sps} but not in the file")
                elif len(sps) != 1:
                    fail("split", f"{n} is listed in {sorted(sps)}")
            train_count[arm] = sum(1 for n, s in seen.items() if "train" in s and n in objs)
            for n in sorted(objs):
                a = f[n].attrs
                vessel = str(a.get("vessel", n))
                for sp in seen.get(n, []):
                    split_of[vessel].add((arm, sp))
                try:
                    rec = json.loads(a["recipe"])
                except KeyError:
                    fail("recipe", f"{n}: no recipe")
                    rec = {}
                if rec and listed.get(rec.get("name")) != rec:
                    fail("recipe", f"{n}: its recipe is not the frozen list's {rec.get('name')}")
                for k, (lo, hi) in RANGES.items():
                    if k in rec and not lo <= rec[k] <= hi:
                        fail("recipe", f"{n}: {k} {rec[k]} outside {lo}-{hi}")
                if rec and rec.get("arm") != arm:
                    fail("split", f"{n}: recipe arm {rec.get('arm')} in the {arm} file")
                info[n] = dict(vessel=vessel, arm=arm, split=seen.get(n, ["none"])[0],
                               stated_sherds=int(a.get("sherds", -1)))
                jobs.append((path, n))

    for vessel, where in split_of.items():
        if len({s for _, s in where}) > 1:
            fail("split", f"vessel {vessel} is in both splits: {sorted(where)}")
        if len({a for a, _ in where}) > 1:
            fail("split", f"vessel {vessel} is in both arms: {sorted(where)}")
    if len(set(train_count.values())) > 1:
        fail("arms", f"training breakages differ between arms: {train_count}")
    facts["training_breakages"] = train_count

    with Pool(workers) as pool:
        measured = pool.map(measure, jobs, chunksize=1)

    by_vessel = defaultdict(list)
    for r in measured:
        n = r["name"]
        k = len(r["sherds"])
        if not SHERDS[0] <= k <= SHERDS[1]:
            fail("sherds", f"{n}: {k} sherds, outside {SHERDS[0]}-{SHERDS[1]}")
        if k == NEVER:
            fail("sherds", f"{n}: exactly {NEVER} sherds, the Juglet's own count")
        if info[n]["stated_sherds"] != k:
            fail("sherds", f"{n}: says {info[n]['stated_sherds']} sherds, holds {k}")
        for i, s in enumerate(r["sherds"]):
            if not s["closed"]:
                fail("open", f"{n} sherd {i} is not closed")
            if s["bodies"] != 1:
                fail("bodies", f"{n} sherd {i} is {s['bodies']} separate bodies")
        lo, hi = SIZE[0] * jlabel, SIZE[1] * jlabel
        if not lo <= r["size_label"] <= hi:
            fail("size", f"{n}: size label {r['size_label']:.3f} outside the Juglet's "
                         f"{jlabel:.3f} x {SIZE[0]}-{SIZE[1]}")
        by_vessel[info[n]["vessel"]].append(r)

    walls = {}
    for vessel, rs in by_vessel.items():
        w = np.array([s["wall_mm"] for r in rs for s in r["sherds"]])
        w = w[np.isfinite(w)]
        if not len(w):
            fail("wall", f"vessel {vessel}: no sherd wall could be measured")
            continue
        med = float(np.median(w))
        walls[vessel] = dict(median=med, min=float(w.min()), max=float(w.max()),
                             max_over_median=float(w.max() / med))
        if not WALL_MM[0] <= med <= WALL_MM[1]:
            fail("wall", f"vessel {vessel}: median sherd wall {med:.2f} mm outside "
                         f"{WALL_MM[0]}-{WALL_MM[1]} mm")
        for r in rs:
            for i, s in enumerate(r["sherds"]):
                if np.isfinite(s["wall_mm"]) and s["wall_mm"] > LUMP * med:
                    fail("wall", f"{r['name']} sherd {i}: {s['wall_mm']:.2f} mm is "
                                 f"{s['wall_mm'] / med:.1f} x its vessel's {med:.2f} mm "
                                 "-- a solid lump, not a wall")

    cs = np.array([r["coincident_share"] for r in measured])
    labels = np.array([r["size_label"] for r in measured])
    allw = np.array([s["wall_mm"] for r in measured for s in r["sherds"]])
    facts.update(
        breakages=len(measured),
        sherds=int(sum(len(r["sherds"]) for r in measured)),
        coincident_share=dict(min=float(np.nanmin(cs)), median=float(np.nanmedian(cs)))
        if len(cs) else {},
        size_label=dict(min=float(labels.min()), max=float(labels.max())) if len(labels) else {},
        sherd_wall_mm=dict(zip(["p0", "p1", "p50", "p99", "p100"],
                               np.nanpercentile(allw, [0, 1, 50, 99, 100]).round(3).tolist()))
        if len(allw) else {},
        vessel_walls=walls,
    )
    return fails, facts, measured


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--juglet", required=True)
    ap.add_argument("--out")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()
    fails, facts, measured = audit(args.files, args.juglet, args.workers)
    summary = {k: v for k, v in facts.items() if k != "vessel_walls"}
    print(json.dumps(summary, indent=1))
    if args.out:
        with open(args.out, "w") as f:
            json.dump(dict(fails=fails, facts=facts, per_breakage=measured), f, indent=1)
    for m in fails:
        print("FAIL", m)
    print(f"{len(fails)} failures" if fails else "PASS")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
