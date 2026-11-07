"""Spartan check for the whole-pot frame (pr-workspace wear-beyond-juglet 20, U3). CPU only.

  1. complete pots (round 2's set): option on (whole file = the same file) against off, both
     with presentation_seed: pointclouds, pointclouds_gt, scales, rotations, translations byte
     for byte, every pot;
  2. sherds missing (round 3's set) against the complete file: per pot, `scales` off (the kept
     sherds' own half-span), on, and the whole pot's (the complete set, option off); and for each
     kept sherd its extent in the input times `scales` over its true extent (mesh, file units);
  3. one picture: the pot as TORA is handed it, whole / sherds missing off / on, at one scale.

    python scripts/check_whole_pot_frame.py --whole C.hdf5 --whole-name csc_whole20_worn4 \
        --miss M.hdf5 --miss-name csc_whole20miss_worn4 --seed 3 --cards p132_d00 p148_d00 p390_d03 \
        --render p148_d00 --out OUT_DIR
"""
import argparse
import sys
from pathlib import Path

import h5py
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tora.data.dataset import PointCloudDataset  # noqa: E402

KEYS = ("pointclouds", "pointclouds_gt", "scales", "rotations", "translations", "points_per_part")


def ds(path, name, seed, whole=None):
    return PointCloudDataset(split="val", data_path=path, dataset_name=name, max_parts=64, up_axis="y",   # csc_whole.yaml sets no up_axis: "y" (no turn)
                             
                             anchor_free=True, presentation_seed=seed, whole_pot_path=whole)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--whole", required=True); ap.add_argument("--whole-name", required=True)
    ap.add_argument("--miss", required=True); ap.add_argument("--miss-name", required=True)
    ap.add_argument("--seed", type=int, default=3)
    ap.add_argument("--cards", nargs="+", required=True)
    ap.add_argument("--render", default=None)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    bad = 0

    off, on = ds(a.whole, a.whole_name, a.seed), ds(a.whole, a.whole_name, a.seed, a.whole)
    n_same = 0
    for i in range(len(off)):
        x, y = off[i], on[i]
        same = all(np.asarray(x[k]).tobytes() == np.asarray(y[k]).tobytes() for k in KEYS)
        n_same += same
        if not same:
            print(f"1. DIFFERS: {x['name']}")
    print(f"1. complete pots ({a.whole_name}, seed {a.seed}): on == off byte for byte on {n_same} of {len(off)}")
    bad += n_same != len(off)

    moff, mon, whole = ds(a.miss, a.miss_name, a.seed), ds(a.miss, a.miss_name, a.seed, a.whole), off
    idx = {n.split("/")[-1]: i for i, n in enumerate(moff.fragments)}
    widx = {n.split("/")[-1]: i for i, n in enumerate(whole.fragments)}
    pics = {}
    with h5py.File(a.miss, "r") as f:
        for card in a.cards:
            i = idx[card]; xo, xn = moff[i], mon[i]; xw = whole[widx[card]]
            n = int(xn["num_parts"]); ppp = xn["points_per_part"][:n]; o = np.concatenate([[0], np.cumsum(ppp)])
            grp = f[xn["name"]]; grp = grp["pieces"] if "pieces" in grp else grp
            true = [float(np.ptp(grp[p]["vertices"][()], axis=0).max()) for p in sorted(grp)]
            r = [float(np.ptp(xn["pointclouds_gt"][o[j]:o[j + 1]], axis=0).max()) * float(xn["scales"]) / t
                 for j, t in enumerate(true)]
            print(f"2. {card}: {n} kept sherds; scales off {float(xo['scales']):.4f}, on {float(xn['scales']):.4f}, "
                  f"whole pot {float(xw['scales']):.4f} (on/whole {float(xn['scales']) / float(xw['scales']):.4f}); "
                  f"input extent x scales / true extent: min {min(r):.3f} median {np.median(r):.3f} max {max(r):.3f}")
            if card == a.render:
                pics = dict(whole=xw, off=xo, on=xn)
    if pics:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axs = plt.subplots(2, 3, figsize=(15, 10.5))
        titles = dict(whole="whole pot (round 2), as TORA receives it",
                      off="sherds missing, option OFF (own frame)",
                      on="sherds missing, option ON (whole pot's frame)")
        for row, (c0, c1, view) in enumerate(((0, 1, "x-y"), (0, 2, "x-z"))):
          for k, axx in zip(("whole", "off", "on"), axs[row]):
            x = pics[k]; n = int(x["num_parts"]); ppp = x["points_per_part"][:n]
            o = np.concatenate([[0], np.cumsum(ppp)]); p = x["pointclouds_gt"]
            for j in range(n):
                axx.scatter(p[o[j]:o[j + 1], c0], p[o[j]:o[j + 1], c1], s=1, color=plt.cm.tab20(j % 20))
            axx.add_patch(plt.Rectangle((-1, -1), 2, 2, fill=False, ls="--", color="grey"))
            axx.set_xlim(-1.15, 1.15); axx.set_ylim(-1.15, 1.15); axx.set_aspect("equal")
            axx.set_title(f"{titles[k]} ({view})\nscales {float(x['scales']):.3f}, {n} sherds", fontsize=10)
        fig.suptitle(f"{a.render}: what TORA is handed (network units; dashed = the [-1, 1] box). "
                     f"seed {a.seed}", fontsize=11)
        fig.tight_layout()
        f = a.out / f"whole_pot_frame_{a.render}.png"; fig.savefig(f, dpi=110); print(f"3. picture {f}")

    try:
        ds(a.miss, a.miss_name, None, a.whole); print("4. no presentation_seed: NOT refused"); bad += 1
    except ValueError:
        print("4. no presentation_seed: refused")
    print("ALL OK" if not bad else f"{bad} FAILED")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
