"""TORA's own loader admits every U10 breakage, and one looks right as the network sees it.

Tora ticket `u10-juglet-ceiling/02`, the loader box. The audit reads the file; this reads
it the way training will, through tora/data/dataset.py, with the settings training will
use: max_parts 64 (sherds reach 36; the Juglet's eval config says 20 and would silently
drop every breakage above it), anchor_free false with the largest sherd held in place
(what bbad_everyday and wear v3 trained with), up_axis z (CSC's pots stand on z).

Fails if the loader keeps fewer breakages than a split lists -- a part-count filter
dropping them without a word is exactly what this is for. Then loads one sample per arm
with augmentation off and draws it twice: assembled (pointclouds_gt) and as handed to the
network (pointclouds: each sherd centred and turned, the anchor where it belongs). The
Juglet goes through the same loader with the same settings, so its `scales` -- the size
label the model is conditioned on -- is compared like for like.

    python scripts/check_u10_loader.py --juglet <juglet_gt.hdf5> --out <png> \
        <u10_ceiling.hdf5> <u10_generic.hdf5>
"""
import argparse
import json
import sys
from pathlib import Path

import h5py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tora.data.dataset import PointCloudDataset  # noqa: E402

SETTINGS = dict(max_parts=64, min_parts=2, anchor_free=False, up_axis="z",
                num_points_to_sample=5000, min_points_per_part=20,
                disable_augmentation=True, num_threads=4)


def dataset_name(path):
    with h5py.File(path, "r") as f:
        return next(iter(f["data_split"]))


def listed(path, ds, split):
    with h5py.File(path, "r") as f:
        return len(f["data_split"][ds][split][:])


def draw(ax, pts, ppp, anchor, title):
    st = 0
    for i, n in enumerate(ppp):
        if n == 0:
            continue
        p = pts[st:st + n]
        ax.scatter(p[:, 0], p[:, 2], p[:, 1], s=0.6, lw=0,
                   color="k" if anchor[i] else plt.cm.tab20(i % 20))
        st += n
    ax.set_box_aspect((1, 1, 1))
    for f in (ax.set_xlim, ax.set_ylim, ax.set_zlim):
        f(-1, 1)
    ax.set_title(title, fontsize=8)
    ax.view_init(elev=12, azim=-60)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--juglet", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    ok, report = True, {}
    fig = plt.figure(figsize=(5 * len(args.files), 10))
    for col, path in enumerate(args.files):
        ds = dataset_name(path)
        for split in ("train", "val"):
            d = PointCloudDataset(split=split, data_path=path, dataset_name=ds, **SETTINGS)
            want = listed(path, ds, split)
            report[f"{ds}/{split}"] = dict(listed=want, loaded=len(d),
                                           sherds=[int(d.min_part_count), int(d.max_part_count)])
            print(f"{ds:12s} {split:5s} listed {want:4d} loaded {len(d):4d} "
                  f"sherds {d.min_part_count}-{d.max_part_count}", flush=True)
            if len(d) != want:
                print(f"FAIL {ds}/{split}: the loader dropped {want - len(d)} breakages")
                ok = False
        d = PointCloudDataset(split="train", data_path=path, dataset_name=ds, **SETTINGS)
        s = d[0]
        ppp = np.asarray(s["points_per_part"])
        anc = np.asarray(s["anchor_parts"])
        report[f"{ds}/sample"] = dict(name=s["name"], parts=int((ppp > 0).sum()),
                                      scales=float(np.asarray(s["scales"]).ravel()[0]),
                                      anchor=int(np.argmax(anc)))
        head = f"{s['name']}\n{int((ppp > 0).sum())} sherds, anchor (black) = sherd {np.argmax(anc)}"
        draw(fig.add_subplot(2, len(args.files), col + 1, projection="3d"),
             np.asarray(s["pointclouds_gt"]), ppp, anc, "assembled, as stored\n" + head)
        draw(fig.add_subplot(2, len(args.files), len(args.files) + col + 1, projection="3d"),
             np.asarray(s["pointclouds"]), ppp, anc,
             "as handed to the network: each sherd centred and turned,\n"
             "the largest (black) held where it belongs")

    jds = dataset_name(args.juglet)
    js = [n.decode() for n in h5py.File(args.juglet, "r")["data_split"][jds]["val"][:]]
    jsplit = "val" if js else "test"
    j = PointCloudDataset(split=jsplit, data_path=args.juglet, dataset_name=jds, **SETTINGS)
    jl = float(np.asarray(j[0]["scales"]).ravel()[0])
    report["juglet"] = dict(split=jsplit, loaded=len(j), scales=jl)
    for k, v in report.items():
        if k.endswith("/sample"):
            v["scales_over_juglet"] = v["scales"] / jl
            print(f"{k}: size label {v['scales']:.4f}, {v['scales'] / jl:.3f} x the Juglet's "
                  f"{jl:.4f}")
    fig.suptitle("TORA's loader, training settings (max_parts 64, largest sherd anchored, "
                 "z up), augmentation off", fontsize=10)
    fig.tight_layout()
    fig.savefig(args.out, dpi=150)
    Path(args.out).with_suffix(".json").write_text(json.dumps(report, indent=1))
    print("wrote", args.out)
    print("LOADER ADMITS EVERY BREAKAGE" if ok else "LOADER CHECK FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
