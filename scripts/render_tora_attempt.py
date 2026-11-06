"""Draw TORA's best attempt on a pot against the truth, and the input TORA was given
(wear-beyond-juglet 06/07, U3). Same layout as GARF's scripts/render_garf_attempt.py.

Per pot, three columns in two views (side, top):
  1. the input as the network receives it (clouds/*.npz `pts_input`: each sherd centred and
     turned at random), so an assembled pot here would mean the pose leaked into the input;
  2. the truth (`pts_gt`, the sampled points at home);
  3. the attempt (`generations_proposed`, the solid sherds own_place.py counts) coloured by
     sherd over the truth in grey; the anchor (largest sherd, as own_place names it) in black.
Per sherd: the attempt's centre offset from its true centre (mm), its turn from the true
orientation (degrees, best rotation on the same points), and the input's median distance from
the true place (mm).

Best attempt = the most sherds own place AND right way round (own_place.json `oriented`, solid
block), then the most own place, then the first by seed and draw; the picture says which
seed/draw it is and how many attempts tie.

Units: the loader divides each object by its largest |coordinate| (tora/data/dataset.py:451-454,
stored as `scale` in the npz), and the CSC HDF5 times copies.csv mm_per_unit is mm, so
mm per loader unit = scale * mm_per_unit. The script prints the truth's longest side in mm
against copies.csv pot_mm as a cross-check.

    python scripts/render_tora_attempt.py --runs RUN_DIR... --copies copies.csv \
        --cards p142_d00 p132_d00 --label "rough 1x" --out OUT_DIR
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path

import numpy as np


def turn_deg(a, b):
    a0, b0 = a - a.mean(0), b - b.mean(0)
    u, _, vt = np.linalg.svd(a0.T @ b0)
    d = np.sign(np.linalg.det(vt.T @ u.T))
    R = vt.T @ np.diag([1, 1, d]) @ u.T
    return float(np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1))))


def seed_of(run: Path) -> int:
    m = re.search(r"_s(\d+)_\d+$", run.name)
    return int(m.group(1)) if m else 42


def gather(runs, card):
    """(seed, draw, oriented, own, run, npz path) for every attempt on this card."""
    out = []
    for run in runs:
        scores = json.loads((run / "own_place.json").read_text())
        key = next((k for k in scores if k.split("/")[-1] == card), None)
        if key is None:
            continue
        npz = next(f for f in (run / "clouds").glob("*.npz")
                   if str(np.load(f, allow_pickle=True)["name"]).split("/")[-1] == card)
        for k, d in enumerate(scores[key]["solid"]):
            out.append((seed_of(run), k, d["oriented"], d["own"], d["n"], run, npz))
    return out


def per_sherd(d, k, mmu):
    ppp = d["points_per_part"]
    ppp = ppp[ppp > 0]  # the loader pads to max_parts (20) with empty slots; drop them
    cuts = np.concatenate([[0], np.cumsum(ppp)])
    gt = d["pts_gt"].astype(float)
    inp = d["pts_input"].astype(float)
    pred = d["generations_proposed"][k].astype(float)
    rows = []
    for i in range(len(ppp)):
        a, b = cuts[i], cuts[i + 1]
        rows.append(dict(
            sherd=i, points=int(ppp[i]),
            centre_mm=float(np.linalg.norm(pred[a:b].mean(0) - gt[a:b].mean(0)) * mmu),
            turn_deg=turn_deg(gt[a:b], pred[a:b]),
            input_from_true_mm=float(np.median(np.linalg.norm(inp[a:b] - gt[a:b], axis=1)) * mmu),
        ))
    return gt, pred, inp, cuts, rows


def draw(gt, pred, inp, cuts, anchor, rows, path, title):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    cmap = plt.get_cmap("tab10")
    n = len(cuts) - 1
    rng = np.random.default_rng(0)
    views = [(15, -60, "side"), (90, -90, "top")]
    fig = plt.figure(figsize=(15, 10))
    lim = max(np.abs(gt).max(), np.abs(pred).max()) * 1.05
    ilim = np.abs(inp).max() * 1.05
    for r, (el, az, vname) in enumerate(views):
        for c, label in enumerate(["input as TORA receives it", "truth", "attempt (colour) over truth (grey)"]):
            ax = fig.add_subplot(2, 3, r * 3 + c + 1, projection="3d")
            for i in range(n):
                a, b = cuts[i], cuts[i + 1]
                k = rng.permutation(b - a)[:1500] + a
                col = "black" if i == anchor else cmap(i % 10)
                if c == 0:
                    ax.scatter(*inp[k].T, s=0.6, color=col)
                elif c == 1:
                    ax.scatter(*gt[k].T, s=0.6, color=col)
                else:
                    ax.scatter(*gt[k].T, s=0.4, color="0.8")
                    ax.scatter(*pred[k].T, s=0.6, color=col)
            L = ilim if c == 0 else lim
            ax.set_xlim(-L, L); ax.set_ylim(-L, L); ax.set_zlim(-L, L)
            ax.view_init(elev=el, azim=az)
            ax.set_title(f"{label} ({vname})", fontsize=9)
            ax.set_xticks([]); ax.set_yticks([]); ax.set_zticks([])
    txt = "sherd  points  centre off mm  turn deg  input-from-true mm\n" + "\n".join(
        f"{x['sherd']:>5}{'*' if x['sherd'] == anchor else ' '} {x['points']:>6}  {x['centre_mm']:>12.2f}"
        f"  {x['turn_deg']:>8.2f}  {x['input_from_true_mm']:>12.1f}" for x in rows)
    fig.text(0.01, 0.01, txt + "\n* anchor (largest sherd; black)", family="monospace", fontsize=8)
    fig.suptitle(title, fontsize=11)
    fig.tight_layout(rect=(0, 0.16, 1, 0.96))
    fig.savefig(path, dpi=110)
    plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", type=Path, required=True)
    ap.add_argument("--copies", type=Path, required=True)
    ap.add_argument("--cards", nargs="+", required=True)
    ap.add_argument("--label", required=True, help="model label for titles and file names")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    meta = {(r["card"], r["condition"]): r for r in csv.DictReader(open(a.copies))}
    tag = re.sub(r"\W+", "", a.label)
    for card in a.cards:
        att = gather(a.runs, card)
        if not att:
            print(f"{card}: not in these runs"); return 1
        best = max(att, key=lambda t: (t[2], t[3], -t[0], -t[1]))
        ties = sum((t[2], t[3]) == (best[2], best[3]) for t in att)
        seed, k, ori, own, n, run, npzf = best
        d = np.load(npzf, allow_pickle=True)
        cond = re.sub(r"^csc_whole\d*_", "", str(d["name"]).split("/")[0])
        m = meta[(card, cond)]
        mmu = float(d["scale"]) * float(m["mm_per_unit"])
        gt, pred, inp, cuts, rows = per_sherd(d, k, mmu)
        anchor = int(np.argmax(d["points_per_part"]))  # padding slots are 0, never the max
        side = float((gt.max(0) - gt.min(0)).max()) * mmu
        print(f"== {card} ({cond}) {a.label}: best of {len(att)} attempts = seed {seed} draw {k + 1} (1-based): "
              f"{ori} of {n} right way round, {own} own place ({ties} attempts tie on both); "
              f"run {run.name}; pot_mm {m['pot_mm']} vs truth's longest side {side:.1f} mm (sampled, "
              f"any orientation)")
        for x in rows:
            print(f"   sherd {x['sherd']}{'*' if x['sherd'] == anchor else ' '} centre {x['centre_mm']:.2f} mm, "
                  f"turn {x['turn_deg']:.2f} deg; input {x['input_from_true_mm']:.1f} mm from true place")
        p = a.out / f"tora_best_{cond}_{tag}_{card}.png"
        draw(gt, pred, inp, cuts, anchor, rows, p,
             f"{card} {cond}, TORA {a.label}: best attempt (seed {seed}, draw {k + 1}; {ori}/{n} right way "
             f"round, {own}/{n} own place; {ties} of {len(att)} attempts tie), pot {m['pot_mm']} mm")
        print(f"   picture {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
