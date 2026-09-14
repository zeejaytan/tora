"""Does the own-place scorer count what U10 says it counts? Seconds on CPU.

Ticket `.scratch/u10-juglet-ceiling/issues/01`. Every draw here is built by hand,
so the right answer is known before the scorer runs:

  1. a perfect draw reads 9 of 9 on both counts;
  2. two look-alike sherds exchanged read 9 of 9 swap-allowed and 7 of 9 own
     place -- the whole reason the second count exists;
  3. one sherd in its neighbour's place and the neighbour lost reads 8 swap-allowed
     and 7 own place, and names the first "swapped" and the second "off";
  4. every sherd displaced reads 0 on both, each no further off than it was moved
     and further off the further it was moved;
  5. one sherd displaced reads 8 and 8, and only that sherd is "off";
  6. nothing changes when the pot is made 7.3 times bigger (the ruler is the unit
     box; a size-dependent chamfer once faked a whole finding here);
  7. the swap-allowed count equals readout.part_acc, the existing count;
  8. score_batch gives what score_draw gives;
  9. the anchor check notices an anchor off its home;
 10. U10's decision rule reads the right way, including the +1 boundary.

Run:  python scripts/test_own_place.py     (exits 1 on any failure)
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from own_place import SEAT_PCT, anchor_note, decide, score_batch, score_draw  # noqa: E402
from readout import TAU, part_acc, part_slices, unit_box_scale  # noqa: E402

FAILS = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(("PASS  " if ok else "FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        FAILS.append(name)


def pot(rng):
    """A juglet-proportioned cylinder (radius 0.5, height 1.8) cut into 9 sherds,
    3 bands by 3 sectors, padded to 20 parts as saved runs are. Sherd 0 is the
    largest (the anchor). Sherds 4 and 5 are the same size and sit side by side,
    so they can be exchanged."""
    pts, ppp = [], []
    for s in range(9):
        band, sector = divmod(s, 3)
        n = 500 if s == 0 else 300
        th = rng.uniform(sector * 2 * np.pi / 3, (sector + 1) * 2 * np.pi / 3, n)
        z = rng.uniform(band * 0.6, (band + 1) * 0.6, n)
        pts.append(np.c_[0.5 * np.cos(th), 0.5 * np.sin(th), z])
        ppp.append(n)
    return np.concatenate(pts), np.array(ppp + [0] * 11)


def moved(gt, ppp, shifts):
    """Each sherd pushed straight out from the pot's axis by shifts[s] (% of pot size).
    Outward is empty space, so a moved sherd cannot land on another sherd's home."""
    pred, unit = gt.copy(), unit_box_scale(gt)
    for s, (a, b) in enumerate(part_slices(ppp)):
        if shifts.get(s):
            c = gt[a:b, :2].mean(0)
            pred[a:b, :2] += shifts[s] / 100 * unit * c / np.linalg.norm(c)
    return pred


def exchanged(gt, ppp, i, j):
    """Sherd i drawn where sherd j belongs and j where i belongs."""
    sl = part_slices(ppp)
    pred = gt.copy()
    (a, b), (c, d) = sl[i], sl[j]
    pred[a:b], pred[c:d] = gt[c:d], gt[a:b]
    return pred


def main() -> int:
    rng = np.random.default_rng(0)
    gt, ppp = pot(rng)

    d = score_draw(gt, gt.copy(), ppp)
    check("perfect draw: 9 of 9 on both counts", (d.own, d.swap, d.n) == (9, 9, 9),
          f"own {d.own}, swap {d.swap}, n {d.n}")

    swap = exchanged(gt, ppp, 4, 5)
    d = score_draw(gt, swap, ppp)
    check("two sherds exchanged: 9 swap-allowed, 7 own place", (d.own, d.swap) == (7, 9),
          f"own {d.own}, swap {d.swap}")
    check("  ... and those two, only, are named 'swapped'",
          [s for s in range(9) if d.status[s] == "swapped"] == [4, 5], str(d.status))

    half = moved(exchanged(gt, ppp, 4, 5), ppp, {5: 30})   # 4 sits in 5's home; 5 is lost
    d = score_draw(gt, half, ppp)
    check("one in its neighbour's place, neighbour lost: 8 swap-allowed, 7 own",
          (d.own, d.swap) == (7, 8), f"own {d.own}, swap {d.swap}")
    check("  ... first is 'swapped', second is 'off'",
          (d.status[4], d.status[5]) == ("swapped", "off"), str(d.status))

    shifts = {s: 20 + 5 * s for s in range(9)}
    d = score_draw(gt, moved(gt, ppp, shifts), ppp)
    check("everything displaced: 0 on both counts", (d.own, d.swap) == (0, 0),
          f"own {d.own}, swap {d.swap}")
    check("  ... every sherd 'off'", set(d.status) == {"off"}, str(d.status))
    far = d.home_pct
    check("  ... each off by more than the tolerance and no more than it was moved",
          all(SEAT_PCT < far[s] <= shifts[s] + 1e-9 for s in range(9)),
          " ".join(f"{far[s]:.1f}/{shifts[s]}" for s in range(9)))
    check("  ... the further moved, the further off",
          all(far[s] < far[s + 1] for s in range(8)))
    check("  ... the anchor check says the anchor is OFF", "OFF" in anchor_note([d]),
          anchor_note([d]))

    one = score_draw(gt, moved(gt, ppp, {7: 30}), ppp)
    check("one sherd displaced: 8 and 8", (one.own, one.swap) == (8, 8),
          f"own {one.own}, swap {one.swap}")
    check("  ... only that sherd is 'off'",
          [s for s in range(9) if one.status[s] != "own"] == [7], str(one.status))
    check("  ... and the anchor check says pinned", "pinned" in anchor_note([one]),
          anchor_note([one]))

    for label, pred in (("exchange", swap), ("one displaced", moved(gt, ppp, {7: 30}))):
        a, b = score_draw(gt, pred, ppp), score_draw(7.3 * gt, 7.3 * pred, ppp)
        check(f"7.3x bigger pot, {label}: same counts and distances",
              (a.own, a.swap, a.status) == (b.own, b.swap, b.status)
              and np.allclose(a.home_pct, b.home_pct),
              f"{a.own}/{a.swap} vs {b.own}/{b.swap}")

    unit = unit_box_scale(gt)
    for label, pred in (("perfect", gt), ("exchange", swap), ("half", half),
                        ("one displaced", moved(gt, ppp, {7: 30})),
                        ("all displaced", moved(gt, ppp, shifts))):
        acc, n = part_acc(gt / unit, pred / unit, ppp, TAU)
        mine = score_draw(gt, pred, ppp).swap
        check(f"swap-allowed = readout.part_acc, {label}", mine == round(acc * n),
              f"scorer {mine}, readout {round(acc * n)}")

    batch = score_batch(np.stack([gt, gt]), np.stack([gt, swap]), np.stack([ppp, ppp]))
    check("score_batch = score_draw",
          [(x.own, x.swap) for x in batch] == [(9, 9), (7, 9)],
          str([(x.own, x.swap) for x in batch]))

    v = decide([5] * 20, [5] * 20, [6] * 20)
    check("rule: ceiling 6, generic 5 -> ceiling wins", v["reading"] == "ceiling_wins")
    v = decide([5] * 20, [4] * 20, [5] * 20)
    check("rule: margin exactly +1 -> ceiling wins", v["reading"] == "ceiling_wins")
    v = decide([5] * 20, [5] * 20, [5, 6] * 10)
    check("rule: ceiling median 5.5 vs 5 -> ceiling loses, no C4 line",
          (v["reading"], v["c4"]) == ("ceiling_loses", False), f"margin {v['margin']}")
    v = decide([4] * 20, [6] * 20, [6] * 20)
    check("rule: generic as good as ceiling, both beat untouched -> loses + C4 line",
          (v["reading"], v["c4"]) == ("ceiling_loses", True))

    print(f"\n{len(FAILS)} failure(s)" if FAILS else "\nall checks pass")
    return 1 if FAILS else 0


if __name__ == "__main__":
    raise SystemExit(main())
