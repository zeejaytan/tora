"""Does abrasion make a pot fail the way the Juglet fails?

Written 2026-09-09 for juglet-cause ticket 09.

THE QUESTION. Wear demonstrably breaks reassembly on pots we abraded ourselves
(ticket 05). Nothing carries that to the Juglet, because the Juglet's own wear
cannot be seen at the resolution it was scanned (Gate A). This asks the bridge
question that needs no finer scan: does wear produce the KIND of failure the
Juglet is having?

Two kinds, and `scripts/check_identity_swap.py` tells them apart:

  exchange    the pieces are roughly in the right places wearing the wrong
              names. The same renaming wins every attempt. This is what a
              DISCRIMINATION failure looks like -- the model could not tell two
              fragments apart.
  scattering  the pieces are genuinely nowhere near where they belong. A
              different renaming wins nearly every attempt and none of them
              rescues the assembly.

The intuitive account of wear -- abrasion eats the break edges so the model can
no longer tell one sherd from another -- is a discrimination story, and predicts
EXCHANGE. The Juglet scatters (ticket 08). So this test can go either way.

WHAT IT READS. The erosion ladder, job 30190268's baseline arm: six objects at
five abrasion levels (e000 unworn through e100), ten attempts each, same pieces
and same correct answer at every rung. Only the break surfaces differ.

THE CONTROL IS e000, and it is the row that makes the rest readable. At zero
abrasion the instrument must pick the identity naming outright on the pots this
model assembles. If it does not, the instrument is wrong on this data and there
is no signature to track.

WHY e100 IS NOT READ. Once a pot has collapsed completely, no renaming can
rescue it and "scattering" is what the instrument MUST report whatever the
mechanism. The signature has to be taken where seating is still partly intact.
This script prints every rung; the reading is stated for the low and middle ones.

WHY ONLY WITHIN-POT COMPARISONS COUNT. "How many of ten attempts agree on one
renaming" is not comparable between pots with different numbers of sherds. A
three-sherd pot has six possible renamings and lands on the same one by luck; a
ten-sherd pot has 3.6 million and repeats almost nothing. This script measures
that confound rather than arguing about it -- see the CONFOUND block, which
correlates sherd count against agreement across all thirty variants -- and the
reading below is stated per pot, up its own ladder, where the sherd count is
constant and only the abrasion changes.

Usage:
  python scripts/check_wear_failure_shape.py --clouds artifacts/wearsig
"""

import argparse
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_identity_swap import cost_matrix, pct  # noqa: E402
from readout import unit_box_scale  # noqa: E402

try:
    from scipy.optimize import linear_sum_assignment
except ImportError:  # pragma: no cover
    linear_sum_assignment = None

# A pot whose worst loose sherd sits inside this is assembled, not failed.
# 2-3% is what a correct assembly reads (ticket 07, 08); 5% is the same bar
# check_identity_swap.py already uses.
ASSEMBLED_PCT = 5.0
# How many of the ten attempts must agree on one renaming before it counts as a
# repeated pattern rather than chance. narrow_bottle3, the corpus's one real
# exchange, agrees 10 of 10; the Juglet's best is 4 of 20.
REPEAT_MIN = 7


def variant(name: str):
    """'erosion_sweep/blue_pot_e050' -> ('blue_pot', 50)."""
    tag = str(name).split("/")[-1]
    obj, _, rung = tag.rpartition("_e")
    return obj, int(rung)


def analyse(path: Path, rng):
    d = np.load(path, allow_pickle=True)
    obj, rung = variant(d["name"])
    gt, ids, props = d["pts_gt"], d["part_ids"], d["generations_proposed"]
    parts = sorted(set(ids.tolist()))
    unit = unit_box_scale(gt)
    anchor = max(parts, key=lambda p: int((ids == p).sum()))
    free = [i for i, p in enumerate(parts) if p != anchor]

    worst_id, worst_best, perms = [], [], []
    for k in range(len(props)):
        C = cost_matrix(gt, props[k], ids, parts, unit, rng)
        _, best = linear_sum_assignment(C)
        worst_id.append(max((pct(C[i, i]) for i in free), default=0.0))
        worst_best.append(max((pct(C[i, best[i]]) for i in free), default=0.0))
        perms.append(tuple(int(x) for x in best))

    counts = Counter(perms)
    top_perm, top_n = counts.most_common(1)[0]
    identity = tuple(range(len(parts)))
    return {
        "object": obj, "rung": rung, "sherds": len(parts), "draws": len(props),
        "worst_id": float(np.median(worst_id)),
        "worst_best": float(np.median(worst_best)),
        "distinct": len(counts),
        "top_n": top_n,
        "top_is_identity": top_perm == identity,
        "identity_wins": sum(1 for p in perms if p == identity),
    }


def shape(r):
    """Which of the two failure kinds -- or neither, because it worked."""
    if r["worst_id"] < ASSEMBLED_PCT:
        return "assembled"
    if r["top_is_identity"]:
        # no renaming beats the true one: mis-placed, and not even a spurious
        # permutation to point at
        return "scattered"
    if r["top_n"] >= REPEAT_MIN:
        return "EXCHANGE-like"
    return "scattered"


def pearson(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    x, y = x - x.mean(), y - y.mean()
    d = np.linalg.norm(x) * np.linalg.norm(y)
    return float(x @ y / d) if d else float("nan")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--clouds", required=True)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    if linear_sum_assignment is None:
        raise SystemExit("scipy is required for the assignment step")

    rng = np.random.default_rng(a.seed)
    files = sorted(Path(a.clouds).glob("*.npz"))
    if not files:
        raise SystemExit(f"no clouds under {a.clouds}")

    rows = [analyse(f, rng) for f in files]
    by_obj = defaultdict(dict)
    for r in rows:
        by_obj[r["object"]][r["rung"]] = r

    print("Does abrasion make a pot fail the way the Juglet fails?")
    print("Erosion ladder, job 30190268 baseline arm. Same pots, same pieces, same")
    print("correct answer at every rung -- only the break surfaces are abraded.\n")
    print("  worst loose sherd = how far the worst free piece sits from home, percent")
    print("  of the pot's own size, median of ten attempts. 2-3% is a correct assembly.")
    print("  relabelled = the same figure if the pieces may swap names.")
    print("  same renaming = how many of the ten attempts agree on one renaming.")
    print("  An EXCHANGE repeats (narrow_bottle3: 10 of 10). A scattering does not")
    print(f"  (the Juglet: 4 of 20). Bar for 'repeats' here is {REPEAT_MIN} of 10.\n")

    hdr = (f"{'object':11s} {'wear':>5s} {'sherds':>6s} {'worst':>7s} {'relab':>7s} "
           f"{'same renaming':>14s} {'ident wins':>10s}  reading")
    print(hdr)
    print("-" * len(hdr))
    for obj in sorted(by_obj):
        for rung in sorted(by_obj[obj]):
            r = by_obj[obj][rung]
            same = f"{r['top_n']}/{r['draws']}" + ("*" if r["top_is_identity"] else "")
            print(f"{obj:11s} {rung:4d}% {r['sherds']:6d} {r['worst_id']:6.1f}% "
                  f"{r['worst_best']:6.1f}% {same:>14s} {r['identity_wins']:7d}/10"
                  f"  {shape(r)}")
        print()
    print("* the renaming that wins IS the true naming -- no relabelling beats it.\n")

    # --- the control, printed as its own statement --------------------------
    print("THE CONTROL -- at zero abrasion, does the instrument pick the true naming")
    print("on the pots this model assembles?")
    ok = True
    for obj in sorted(by_obj):
        r = by_obj[obj].get(0)
        if r is None:
            continue
        if r["worst_id"] < ASSEMBLED_PCT:
            held = r["top_is_identity"]
            ok &= held
            print(f"  {obj:11s} assembled at e000 ({r['worst_id']:.1f}%): "
                  f"true naming wins {'YES' if held else 'NO -- instrument suspect'}")
        else:
            print(f"  {obj:11s} not assembled at e000 ({r['worst_id']:.1f}%) "
                  f"-- carries no control signal")
    print(f"\n  control {'HOLDS' if ok else 'FAILS -- stop and report'}\n")

    # --- the confound, measured rather than argued --------------------------
    print("THE CONFOUND -- how many renamings a pot even has depends on how many")
    print("sherds it has, so 'the same renaming won again' is not comparable between")
    print("pots. Measured across all thirty variants:")
    r_conf = pearson([r["sherds"] for r in rows], [r["top_n"] for r in rows])
    for n in sorted({r["sherds"] for r in rows}):
        grp = [r for r in rows if r["sherds"] == n]
        objs = ", ".join(sorted({r["object"] for r in grp}))
        perms = math.factorial(n)
        print(f"  {n:2d} sherds, {perms:>9,d} possible renamings   "
              f"median agreement {int(np.median([r['top_n'] for r in grp]))}/10"
              f"   {objs}")
    print(f"\ncorrelation, sherd count vs agreement: r = {r_conf:+.2f}")
    print("  Fewer sherds, more agreement -- so a cross-pot 'EXCHANGE-like' label is")
    print("  partly reporting the sherd count. Only the within-pot ladders below are")
    print("  admissible: same pot, same pieces, same sherd count, only wear changes.\n")

    # --- the reading, low and middle rungs only -----------------------------
    print("THE READING -- per pot, up its own ladder. e100 is excluded: a pot that has")
    print("collapsed entirely must read as scattered whatever the mechanism.")
    for obj in sorted(by_obj):
        ctrl = by_obj[obj].get(0)
        if ctrl is None or ctrl["worst_id"] >= ASSEMBLED_PCT:
            print(f"  {obj:11s} no e000 control -- ladder not readable")
            continue
        steps = " -> ".join(
            f"e{rung:03d} {shape(by_obj[obj][rung])}"
            for rung in (0, 25, 50, 75) if rung in by_obj[obj])
        print(f"  {obj:11s} {steps}")
    print("\nA cross-pot tally is printed for completeness only; do not read it as a")
    print("  count of failure kinds.")
    tally = Counter()
    for obj in sorted(by_obj):
        for rung in (25, 50, 75):
            r = by_obj[obj].get(rung)
            if r is None:
                continue
            tally[shape(r)] += 1
    for k, v in tally.most_common():
        print(f"    {k:14s} {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
