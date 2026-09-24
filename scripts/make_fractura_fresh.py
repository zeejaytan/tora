"""The eight Fractura pots with no applied wear, as their own evaluation file.

U10 ticket 05 scores every arm on the eight real broken pots, pot by pot. They exist
already as the `_e000` rung of `erosion_ceramics.hdf5` (ticket 11): normalised once to
max|v| = 0.5 before the ladder was built, erosion strength 0. The loader reads every
object a file's split lists and has no rung filter, so the rung is copied out rather
than filtered in -- otherwise the other 32 worn variants would be scored with it.

Usage (login node is fine, it copies 8 objects):
  python scripts/make_fractura_fresh.py --src dataset/erosion_ceramics.hdf5 \
      --dst dataset/fractura_fresh.hdf5
"""

import argparse

import h5py

SRC_GROUP = "erosion_ceramics"
DST_GROUP = "fractura_fresh"
RUNG = "_e000"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--src", required=True)
    ap.add_argument("--dst", required=True)
    a = ap.parse_args()

    with h5py.File(a.src, "r") as src, h5py.File(a.dst, "w-") as dst:
        tags = sorted(t for t in src[SRC_GROUP].keys() if t.endswith(RUNG))
        if len(tags) != 8:
            raise SystemExit(f"expected 8 {RUNG} pots, found {len(tags)}: {tags}")
        g = dst.create_group(DST_GROUP)
        names = []
        for t in tags:
            pot = t[: -len(RUNG)]
            src.copy(src[SRC_GROUP][t], g, name=pot)
            names.append(f"{DST_GROUP}/{pot}")
        split = dst.create_group("data_split").create_group(DST_GROUP)
        for s in ("train", "val", "test"):
            split.create_dataset(s, data=[n.encode() for n in names])
        for t in tags:
            pieces = g[t[: -len(RUNG)]]["pieces"]
            print(f"{t[: -len(RUNG)]:16s} {len(pieces)} sherds")
    print(f"wrote {len(names)} pots to {a.dst}")


if __name__ == "__main__":
    main()
