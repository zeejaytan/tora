"""Can a coarse mesh carry wear? Separate blunting from opening the joins.

The conservator's challenge, 2026-08-19: "I don't understand how a coarse model
stops you making it worn. Wear is blunting of its fracture surface and reducing
the contact surface between the break."

The claim being tested is mine, and it was too strong. I wrote that Breaking
Bad's vessels are too coarsely sampled to carry wear, from the fact that their
spacing (0.232-0.283% of object) sits barely below the blunting cutoff
(0.30-0.50%). That argument only covers ONE of the two things wear does.

  BLUNTING removes what stands proud of the local surface. It needs fine texture
  to exist in the mesh. At 0.25% sampling nothing below about 0.5% is
  represented, so there may be no teeth there to remove -- not because the tool
  fails but because the geometry was never recorded.

  OPENING THE JOINS reduces the contact between mating pieces. It needs no fine
  detail whatever. A surface can be retreated on a coarse mesh as easily as a
  fine one.

And the second may matter more. Gate A found real archaeological scans carry no
fracture texture at these scales either, so for training data meant to resemble
real material, the joins opening is the effect that survives digitisation.

WHAT IS MEASURED, on Breaking Bad vessels against blue_pot as the fine-mesh
control:

  available    mean height standing proud of the local surface at the cutoff.
               If this is near zero on the coarse meshes, blunting has nothing
               to work with and that half of my claim holds.
  blunting     what blunting actually removes, and what it does to the join.
  recession    what a small retreat does to the join, and to the curve.

Usage:
  python scripts/test_wear_on_coarse.py --bbad dataset/breaking_bad_vol.hdf5 \
      --fine dataset/real_heldout_norm.hdf5
"""

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wear_ops import (_band_mask, _outward_directions, _proud_height,  # noqa: E402
                      blunt_asperities, recede_surface)


def effective_pieces(sizes):
    s = np.asarray(sizes, dtype=float)
    p = s / s.sum()
    return 1.0 / float((p ** 2).sum())


def load_bbad(path, cats, want=3, min_eff=4.0):
    """Balanced multi-piece vessel breaks, since most instances are chips."""
    out = []
    with h5py.File(path, "r") as h:
        ev = h["everyday"]
        for c in cats:
            if c not in ev:
                continue
            for o in sorted(ev[c].keys()):
                node = ev[c][o]
                for fr in sorted(node.keys()):
                    grp = node[fr]
                    keys = sorted(grp.keys())
                    if len(keys) < 3:
                        continue
                    sz = [grp[k]["vertices"].shape[0] for k in keys]
                    if effective_pieces(sz) < min_eff:
                        continue
                    pieces = [(np.asarray(grp[k]["vertices"][:], dtype=np.float64),
                               np.asarray(grp[k]["faces"][:], dtype=np.int64))
                              for k in keys]
                    out.append((f"{c}/{o[:8]}/{fr}", pieces))
                    break
                if len(out) >= want:
                    break
            if len(out) >= want:
                break
    return out


def load_fine(path, dsname, obj):
    with h5py.File(path, "r") as h:
        grp = h[dsname][obj]
        g = grp["pieces"] if "pieces" in grp else grp
        keys = sorted(g.keys(), key=lambda s: int(s) if s.isdigit() else s)
        return [(np.asarray(g[k]["vertices"][:], dtype=np.float64),
                 np.asarray(g[k]["faces"][:], dtype=np.int64)) for k in keys]


def gap_pct(pieces, max_pts=60000, seed=0):
    """Mean separation at the joins, as a percentage of object size."""
    rng = np.random.default_rng(seed)
    allv = np.concatenate([v for v, _ in pieces], axis=0)
    size = float(np.linalg.norm(allv.max(0) - allv.min(0)))
    tau = 0.02 * size
    gaps = []
    for i, (vi, _) in enumerate(pieces):
        for j, (vj, _) in enumerate(pieces):
            if j <= i:
                continue
            a = vi if len(vi) <= max_pts else vi[rng.choice(len(vi), max_pts, False)]
            b = vj if len(vj) <= max_pts else vj[rng.choice(len(vj), max_pts, False)]
            d, _ = cKDTree(b).query(a, workers=-1)
            sel = d < tau
            if sel.sum() > 200:
                gaps.append(float(d[sel].mean()) / size * 100)
    return float(np.mean(gaps)) if gaps else float("nan")


def report(name, pieces, cut=0.004):
    allv = np.concatenate([v for v, _ in pieces], axis=0)
    size = float(np.linalg.norm(allv.max(0) - allv.min(0)))
    v0 = pieces[0][0]
    d, _ = cKDTree(v0).query(v0, k=2, workers=-1)
    spacing = float(np.median(d[:, 1])) / size * 100

    masks = [_band_mask(pieces, i, pieces[i][0]) for i in range(len(pieces))]
    idx = np.where(masks[0][1] > 0.02)[0]
    if len(idx) < 200:
        print(f"  {name:<28s} too few band vertices")
        return
    nrm = _outward_directions(pieces[0][0], idx, size)
    proud = _proud_height(pieces[0][0], idx, nrm, cut * size)
    avail = float(np.maximum(proud, 0).mean()) / size * 100

    g0 = gap_pct(pieces)
    blunted = blunt_asperities(pieces, cut_frac=cut, strength=1.0, passes=3,
                               masks=masks)
    gb = gap_pct(blunted)
    moved_b = float(np.abs(blunted[0][0] - pieces[0][0]).max()) / size * 100

    receded = recede_surface(pieces, recession_frac=0.0005, masks=masks)
    gr = gap_pct(receded)
    moved_r = float(np.abs(receded[0][0] - pieces[0][0]).max()) / size * 100

    print(f"  {name:<28s} {spacing:>8.3f}% {avail:>11.4f}% "
          f"{moved_b:>10.4f}% {100 * (gb / g0 - 1):>9.1f}% "
          f"{moved_r:>10.4f}% {100 * (gr / g0 - 1):>10.1f}%")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bbad", required=True)
    ap.add_argument("--fine", required=True)
    ap.add_argument("--fine-dataset", default="real_heldout_norm")
    args = ap.parse_args()

    print("Can a coarse mesh carry wear? Blunting and join-opening measured apart.")
    print()
    print(f"  {'object':<28s} {'spacing':>8s} {'available':>12s} "
          f"{'blunt moved':>11s} {'gap':>10s} {'rec moved':>10s} {'gap':>11s}")
    print("  " + "-" * 88)

    for name, pieces in load_bbad(args.bbad, ["Vase", "Bowl", "Cup"]):
        report(f"bbad {name}", pieces)

    for obj in ["blue_pot", "plate"]:
        report(f"fine {obj}", load_fine(args.fine, args.fine_dataset, obj))

    print()
    print("  available   how much stands proud at the cutoff. Near zero means")
    print("              there are no teeth in the mesh to blunt.")
    print("  blunt/rec moved  the largest vertex displacement each caused.")
    print("  gap         change in mean separation at the joins.")
    print()
    print("  If blunting moves nothing on the coarse meshes but recession opens")
    print("  their joins, then coarse meshes CAN carry wear -- just not the")
    print("  blunting half -- and recession should be un-retired for them.")


if __name__ == "__main__":
    main()
