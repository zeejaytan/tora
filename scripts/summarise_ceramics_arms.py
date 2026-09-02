"""Report the Fractura ceramics arms pot by pot, in sherds seated.

Eight real broken pots, 3 to 12 fragments each. An average part-accuracy over
all eight hides the two things that matter: which pots the model can do at all,
and how much the answer moves between one attempt and the next on the same pot.
On the Juglet that movement was about a third of the vessel -- larger than any
difference between the arms being compared.

Two numbers in the per-draw json must NOT be quoted as they stand:

  object_chamfer and translation_error are in the object's own units. The
  ceramics run records scales around 77, so a chamfer of 167 means nothing
  until it is divided by that. This prints translation as a fraction of object
  scale and leaves raw chamfer out entirely.

  part_accuracy is a distance threshold per fragment, not an orientation
  check. A sherd sitting roughly in place but turned 20 degrees counts as
  seated. So the turn is printed beside the count, always.

ONE OF THE SEATED FRAGMENTS IS FREE. This config is anchor-fixed: one fragment
is handed to the model already in its correct place, and compute_part_acc
counts every part including that one. So a pot scoring exactly 1 seated had
nothing placed by the model at all. The baseline run 24342475 scored exactly 1
on all eight pots across all three draws -- a flat 17% that means zero. The
"earned" column subtracts the freebie so that cannot be misread again.

Usage:
  python scripts/summarise_ceramics_arms.py --runs <run_dir> [<run_dir> ...]

A run_dir is an eval_runs/<name> folder; the script reads <run_dir>/results/.
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path


def load_draws(run_dir: Path) -> list[dict]:
    res = run_dir / "results"
    if not res.is_dir():
        raise SystemExit(f"no results/ under {run_dir}")
    out = [json.loads(p.read_text()) for p in sorted(res.glob("*_generation*.json"))]
    if not out:
        raise SystemExit(f"no per-draw json in {res}")
    return out


def median(xs):
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True)
    a = ap.parse_args()

    arms = {}
    for r in a.runs:
        d = Path(r)
        by_pot = defaultdict(list)
        for x in load_draws(d):
            by_pot[x["name"]].append(x)
        arms[d.name] = by_pot

    pots = sorted({p for by_pot in arms.values() for p in by_pot})
    aw = max(len(k) for k in arms)
    pw = max(len(p) for p in pots)

    print("\nFractura ceramics: 8 pots that were really broken and scanned.")
    print("Real fracture surfaces, no burial wear. Ground truth confirmed by")
    print("the conservator, so a bad score here is the method, not the key.\n")

    print(f"{'pot':{pw}s}  {'arm':{aw}s}  frags  draws  seated  earned  best  worst   turn   offset")
    print("('earned' = seated minus the one anchor fragment handed over for free)\n")
    for pot in pots:
        for arm, by_pot in arms.items():
            draws = by_pot.get(pot)
            if not draws:
                continue
            n_parts = draws[0]["num_parts"]
            seated = [round(x["part_accuracy"] * n_parts) for x in draws]
            rot = [x["rotation_error"] for x in draws]
            # translation in object units is meaningless on its own; scale is
            # the object's own size, so trans/scale is a fraction of the pot.
            off = [x["translation_error"] / x["scales"] for x in draws if x.get("scales")]
            earned = [max(0, s - 1) for s in seated]
            print(f"{pot:{pw}s}  {arm:{aw}s}  {n_parts:5d}  {len(draws):5d}  "
                  f"{median(seated):6.1f}  {median(earned):6.1f}  "
                  f"{max(seated):4d}  {min(seated):5d}  "
                  f"{median(rot):5.1f}d  {median(off) if off else float('nan'):6.2f}")
        print()

    print("=" * 70)
    print("Whole subset, all 8 pots pooled:\n")
    print(f"{'arm':{aw}s}  pots  draws  seated  earned  of  earned %  median turn")
    for arm, by_pot in arms.items():
        tot_seat = tot_frag = 0
        rots = []
        n_draws = 0
        for pot, draws in by_pot.items():
            n_parts = draws[0]["num_parts"]
            # pool the per-draw counts, so this is the AVERAGE attempt, not the
            # luckiest one. Best-of-N is not reported here on purpose.
            tot_seat += sum(round(x["part_accuracy"] * n_parts) for x in draws)
            tot_frag += n_parts * len(draws)
            rots += [x["rotation_error"] for x in draws]
            n_draws += len(draws)
        # every draw gets one anchor for free, so the honest denominator and
        # numerator both drop by the number of draws.
        earned = tot_seat - n_draws
        earn_frag = tot_frag - n_draws
        pct = 100.0 * earned / earn_frag if earn_frag else float("nan")
        print(f"{arm:{aw}s}  {len(by_pot):4d}  {n_draws:5d}  {tot_seat:6d}  {earned:6d}"
              f"  {earn_frag:3d}  {pct:7.1f}  {median(rots):10.1f}d")

    print("\nThat percentage is fragments the model actually placed, on the")
    print("typical attempt -- not the best of them, and not counting the")
    print("anchor it was given. Zero earned means the pot fell apart.")
    print("A gap smaller than one fragment on one pot is not a result.")
    print("Eight pots is a lead, not a conclusion -- and they are modern")
    print("breaks with no wear, so they do not settle the buried-sherd case.\n")


if __name__ == "__main__":
    main()
