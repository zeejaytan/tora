"""Are Breaking Bad's vessel breaks reassembly problems, or one pot plus chips?

Gate B turned up 375 vessel objects already fractured in a file we hold, each
with about a hundred fracture instances. Piece COUNT looked promising -- nearly
a tenth of instances have five or more. Then rendering them showed something the
count cannot: almost every panel is one dominant piece with a few slivers at the
rim.

That distinction decides whether the corpus is worth anything to us. A break that
is 97% one remnant plus three chips is a chip-detection problem, not a
reassembly. The Juglet is nine sherds of broadly comparable size, and that is the
problem we are trying to solve.

So this measures balance rather than counting pieces:

  largest share   how much of the object the biggest fragment holds. Near 100%
                  and there is nothing to reassemble.
  effective count 1 / sum(share^2), the inverse Simpson index. It says how many
                  pieces the break behaves like: four equal quarters gives 4.0,
                  one remnant with three slivers gives close to 1.0. This is the
                  number that should be compared with the Juglet's nine.

Measured by vertex count rather than volume. These meshes are fairly uniformly
sampled, and volume needs watertightness that fragments do not have.

Usage:
  python scripts/measure_bbad_balance.py --src dataset/breaking_bad_vol.hdf5
"""

import argparse
import collections

import h5py
import numpy as np

CATS = ["Bottle", "Vase", "Mug", "Bowl", "Cup", "Teapot", "Plate", "WineBottle",
        "BeerBottle", "Teacup", "PillBottle", "WineGlass", "DrinkBottle",
        "DrinkingUtensil"]


def sizes_of(grp):
    out = []
    for k in grp.keys():
        node = grp[k]
        v = node["vertices"] if "vertices" in node else node
        out.append(int(v.shape[0]))
    return np.array(out, dtype=float)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", required=True)
    ap.add_argument("--dataset", default="everyday")
    ap.add_argument("--objects-per-cat", type=int, default=8)
    ap.add_argument("--instances", type=int, default=40)
    ap.add_argument("--min-pieces", type=int, default=3)
    args = ap.parse_args()

    h = h5py.File(args.src, "r")
    ev = h[args.dataset]

    rows = []
    eff_hist = collections.Counter()
    for c in CATS:
        if c not in ev:
            continue
        objs = sorted(ev[c].keys())
        step = max(1, len(objs) // args.objects_per_cat)
        biggest, effs, n_inst = [], [], 0
        for o in objs[::step][:args.objects_per_cat]:
            node = ev[c][o]
            for fr in sorted(node.keys())[:args.instances]:
                sz = sizes_of(node[fr])
                if len(sz) < args.min_pieces or sz.sum() <= 0:
                    continue
                share = sz / sz.sum()
                biggest.append(share.max())
                e = 1.0 / float((share ** 2).sum())
                effs.append(e)
                eff_hist[round(e)] += 1
                n_inst += 1
        if n_inst:
            rows.append((c, n_inst, 100 * np.mean(biggest),
                         float(np.mean(effs)), float(np.max(effs))))

    print(f"Instances with at least {args.min_pieces} pieces")
    print(f"  {'category':<18s} {'instances':>10s} {'largest share':>14s} "
          f"{'effective pieces':>18s} {'best':>7s}")
    print("  " + "-" * 72)
    for c, n, big, eff, mx in sorted(rows, key=lambda r: -r[3]):
        print(f"  {c:<18s} {n:>10d} {big:>13.1f}% {eff:>18.2f} {mx:>7.2f}")

    if rows:
        allbig = np.mean([r[2] for r in rows])
        alleff = np.mean([r[3] for r in rows])
        print("  " + "-" * 72)
        print(f"  {'MEAN':<18s} {'':>10s} {allbig:>13.1f}% {alleff:>18.2f}")

    print("\n  effective piece count, distribution over instances")
    tot = sum(eff_hist.values())
    for k in sorted(eff_hist):
        share = 100 * eff_hist[k] / tot
        print(f"    ~{k} pieces  {eff_hist[k]:>6d}  {share:>5.1f}%  "
              f"{'#' * int(share / 2)}")

    print("\n  The Juglet is nine sherds of broadly comparable size, so its")
    print("  effective count is close to nine. An effective count near 1 means")
    print("  one remnant and some chips -- a different problem entirely, and")
    print("  not the one we need to train.")


if __name__ == "__main__":
    main()
