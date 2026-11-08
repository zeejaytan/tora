"""Ruler check for TORA's whole-pot path (pr-workspace wear-beyond-juglet 21, 2026-11-08).

On saved TORA clouds of a sherds-missing set (whole-pot frame, anchor-fixed, paired), per object:
  1. the tolerance in mm: own_place's whole-pot unit, put back into mm with the cloud's `scale` and
     copies.csv mm_per_unit, must be 7.07% of copies.csv pot_mm (the bug: it was pot_mm * scale);
  2. the truth through the scorer (pred = pts_gt) must place and orient every kept sherd;
  3. every non-anchor sherd moved rigidly along its own thin axis (normal to the wall) by half
     the tolerance must stay own place, and by twice it must leave (only the anchor stays).
     With scale about 0.43 (these pots), half the new tolerance is 1.16 of the old one.
    python scripts/check_whole_pot_ruler.py --copies copies.csv RUN_DIR...     (exit 1 on any miss)
"""
import argparse
import csv
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from own_place import read_pot_sizes, score_draw  # noqa: E402
from readout import TAU, clouds_by_object, part_slices, unit_box_scale  # noqa: E402

SEAT = float(np.sqrt(TAU / 2))  # 0.0707: a rigid shift of d gives chamfer <= 2 d^2


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--copies", type=Path, required=True)
    ap.add_argument("runs", type=Path, nargs="+")
    a = ap.parse_args()
    sizes = read_pot_sizes(a.copies)
    meta = {}
    for r in csv.DictReader(open(a.copies)):
        meta[r["card"]] = (float(r["pot_mm"]), float(r["mm_per_unit"]))
    bad, n_obj = [], 0
    for run in a.runs:
        for name, npz in sorted(clouds_by_object(run).items()):
            d = np.load(npz, allow_pickle=True)
            card = name.split("/")[-1]
            pot_mm, mmu = meta[card]
            scale = float(np.asarray(d["scale"]).reshape(-1)[0])
            gt, ppp = d["pts_gt"].astype(float), d["points_per_part"]
            size = sizes[card] / scale                     # what own_place now uses
            mm_per_cloud = scale * mmu
            tol_new, tol_old = SEAT * size * mm_per_cloud, SEAT * sizes[card] * mm_per_cloud
            truth_mm = unit_box_scale(gt) * mm_per_cloud
            ok1 = abs(tol_new - 0.0707 * pot_mm) < 0.01 * pot_mm * 0.0707 + 1e-6
            t = score_draw(gt, gt, ppp, sizes[card] / scale)
            ok2 = t.own == t.n and t.oriented == t.n and t.oriented_strict == t.n
            sl = part_slices(ppp)
            anchor = int(np.argmax([b - a_ for a_, b in sl]))
            moved = {}
            for f in (0.5, 2.0):
                p = gt.copy()
                for j, (a_, b) in enumerate(sl):
                    if j != anchor:
                        q = gt[a_:b] - gt[a_:b].mean(0)
                        v = np.linalg.svd(q, full_matrices=False)[2][-1]   # thinnest axis
                        p[a_:b] += v * f * SEAT * size
                moved[f] = score_draw(gt, p, ppp, size).own
            ok3 = moved[0.5] == t.n and moved[2.0] == 1
            n_obj += 1
            print(f"{run.name} {card}: pot {pot_mm:.1f} mm, truth's longest side {truth_mm:.1f} mm; "
                  f"tolerance {tol_new:.2f} mm (was {tol_old:.2f}); truth own {t.own}/{t.n} "
                  f"right way {t.oriented}/{t.n}; moved 0.5x own {moved[0.5]}, 2x own {moved[2.0]}"
                  f"{'' if ok1 and ok2 and ok3 else '  <-- MISS'}")
            if not (ok1 and ok2 and ok3):
                bad.append(f"{run.name} {card}")
    print(f"\n{n_obj} objects; {len(bad)} miss(es)")
    for b in bad:
        print("   ", b)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
