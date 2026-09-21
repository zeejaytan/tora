"""The U10 training-file audit fails each deliberately broken file, naming why -- ticket 02.

Builds a small clean pair of files from the real ones (three breakages per arm: two
training vessels and one choosing vessel), checks the audit passes it, then breaks one
thing at a time and checks the audit fails, with the named reason among its failures.
The faults are made in the geometry wherever the rule reads geometry:

  two_sherds   a breakage cut down to 2 of its sherds
  nine         a breakage cut down to 9 sherds
  open         one face removed from a sherd
  two_body     two sherds stored as one mesh
  solid        a sherd replaced by a solid ball of its own width -- a lump of clay. (Not
               its convex hull: a gently curved sherd's hull is barely thicker than
               its wall, and would pass the lump rule for the wrong reason)
  thin_wall    one vessel restated so its wall reads 1.2 mm. The stored geometry is
               normalised, so a wall is in mm only through `mm_per_unit`; the fault is
               made there, and is the same pot at a scale where its wall is 1.2 mm
  both_splits  a training breakage also listed as choosing
  recipe       a recipe's wall set to 2.8 mm, outside 1.6-2.5
  hash         the recipe list in the file edited
  unequal      one training breakage removed from one arm
  size         a breakage's geometry halved, so TORA's size label halves

Exits non-zero on the first fixture that passes, or on a clean file that fails.

    python scripts/test_u10_audit.py --juglet <juglet_gt.hdf5> <u10_ceiling.hdf5> <u10_generic.hdf5>
"""
import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

import h5py
import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_u10_trainset import audit  # noqa: E402

VL = h5py.special_dtype(vlen=bytes)


def set_split(f, ds, sp, names):
    g = f["data_split"][ds]
    del g[sp]
    g.create_dataset(sp, data=np.array([n.encode() for n in names], dtype=object), dtype=VL)


def split(f, ds, sp):
    return [n.decode() for n in f["data_split"][ds][sp][:]]


def mini(src, dst):
    """Two training vessels and one choosing vessel; the first has 11-30 sherds."""
    with h5py.File(src, "r") as fi, h5py.File(dst, "w") as fo:
        for k, v in fi.attrs.items():
            fo.attrs[k] = v
        ds = [k for k in fi.keys() if k != "data_split"][0]
        train, val = split(fi, ds, "train"), split(fi, ds, "val")
        first = next(n for n in train if 11 <= fi[n].attrs["sherds"] <= 30)
        second = next(n for n in train if fi[n].attrs["vessel"] != fi[first].attrs["vessel"])
        keep = {"train": [first, second], "val": val[:1], "test": []}
        fo.create_group(ds)
        for n in keep["train"] + keep["val"]:
            fi.copy(fi[n], fo[ds], name=n.split("/", 1)[1])
        g = fo.create_group("data_split").create_group(ds)
        for sp, names in keep.items():
            g.create_dataset(sp, data=np.array([n.encode() for n in names], dtype=object),
                             dtype=VL)
    return ds, keep


def pieces(f, n):
    return f[n]["pieces"]


def rewrite(pg, key, V, F):
    del pg[key]
    s = pg.create_group(key)
    s.create_dataset("vertices", data=V.astype(np.float32))
    s.create_dataset("faces", data=F.astype(np.int32))


def keep_first(f, n, k):
    pg = pieces(f, n)
    for key in sorted(pg.keys())[k:]:
        del pg[key]
    f[n].attrs["sherds"] = k


def fault(name, f, ds, keep):
    b0, b1 = keep["train"]
    pg = pieces(f, b0)
    keys = sorted(pg.keys())
    if name == "two_sherds":
        keep_first(f, b0, 2)
    elif name == "nine":
        keep_first(f, b0, 9)
    elif name == "open":
        V, F = pg[keys[0]]["vertices"][:], pg[keys[0]]["faces"][:]
        rewrite(pg, keys[0], V, F[:-1])
    elif name == "two_body":
        V0, F0 = pg[keys[0]]["vertices"][:], pg[keys[0]]["faces"][:]
        V1, F1 = pg[keys[1]]["vertices"][:], pg[keys[1]]["faces"][:]
        rewrite(pg, keys[0], np.concatenate([V0, V1]), np.concatenate([F0, F1 + len(V0)]))
        del pg[keys[1]]
        f[b0].attrs["sherds"] = len(keys) - 1
    elif name == "solid":
        big = max(keys, key=lambda k: len(pg[k]["faces"]))
        V = pg[big]["vertices"][:]
        ball = trimesh.creation.icosphere(subdivisions=3, radius=0.5 * float(np.ptp(V, 0).max()))
        rewrite(pg, big, np.asarray(ball.vertices) + V.mean(0), np.asarray(ball.faces))
    elif name == "thin_wall":
        rec = json.loads(f[b0].attrs["recipe"])
        f[b0].attrs["mm_per_unit"] = f[b0].attrs["mm_per_unit"] * 1.2 / rec["wall_mm"]
    elif name == "both_splits":
        set_split(f, ds, "val", split(f, ds, "val") + [b0])
    elif name == "recipe":
        rec = json.loads(f[b0].attrs["recipe"])
        rec["wall_mm"] = 2.8
        f[b0].attrs["recipe"] = json.dumps(rec, sort_keys=True)
    elif name == "hash":
        rs = json.loads(f.attrs["recipes"])
        rs[0]["seed"] += 1
        f.attrs["recipes"] = json.dumps(rs, sort_keys=True, separators=(",", ":"))
    elif name == "unequal":
        del f[b1]
        set_split(f, ds, "train", [b0])
    elif name == "size":
        for k in keys:
            V, F = pg[k]["vertices"][:], pg[k]["faces"][:]
            rewrite(pg, k, V * 0.5, F)


EXPECT = {"two_sherds": "sherds", "nine": "sherds", "open": "open", "two_body": "bodies",
          "solid": "wall", "thin_wall": "wall", "both_splits": "split", "recipe": "recipe",
          "hash": "recipe", "unequal": "arms", "size": "size"}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("ceiling")
    ap.add_argument("generic")
    ap.add_argument("--juglet", required=True)
    args = ap.parse_args()
    tmp = Path(tempfile.mkdtemp(prefix="u10_audit_"))
    ok = True
    try:
        cz, gz = tmp / "u10_ceiling.hdf5", tmp / "u10_generic.hdf5"
        ds, keep = mini(args.ceiling, cz)
        mini(args.generic, gz)
        fails, _, _ = audit([str(cz), str(gz)], args.juglet, workers=4)
        print(f"clean       {'PASS' if not fails else 'FAIL'}  {fails[:3]}")
        ok &= not fails
        for name, kind in EXPECT.items():
            bad = tmp / f"bad_{name}.hdf5"
            shutil.copy(cz, bad)
            with h5py.File(bad, "r+") as f:
                fault(name, f, ds, keep)
            fails, _, _ = audit([str(bad), str(gz)], args.juglet, workers=4)
            named = [m for m in fails if m.startswith(kind + ":")]
            print(f"{name:<11s} {'fails, named' if named else 'NOT CAUGHT':<13s} "
                  f"{named[0] if named else fails}")
            ok &= bool(named)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("ALL FIXTURES BEHAVE" if ok else "FIXTURE TEST FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
