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

REWIRED 2026-09-05. Every number here now comes from scripts/readout.py, the one
place a run is read. TWO COLUMNS MOVED:

  turn. The free anchor was subtracted from the seated count here but not from
  the rotation error, which is summed over the non-anchor fragments and divided
  by all of them. The correction is n/(n-1), so it is a DIFFERENT factor for
  every pot in the table -- x1.500 on the three-fragment pink_bowl, x1.091 on
  the twelve-fragment narrow_bottle1 -- which is exactly the shape that
  corrupts a pot-by-pot comparison. On the normalized scale-ladder rung the
  eight pots move like this: blue_pot 24.4 -> 30.5 deg, pink_bowl 1.6 -> 2.4
  deg, narrow_bottle1 57.1 -> 62.3 deg. Nothing changed rank; the pots with
  few fragments were being flattered most.

  offset. It was translation_error divided by the stored `scales`. A run scored
  after the unit-box fix stores translation_error_unit, already divided by the
  longest side of the ground truth box, which is the denominator the seating
  threshold uses. The read-out prefers that and names which one it used, so the
  column cannot silently mean two different things down one page.

Sherds seated did not move. Reconciliation: docs/notes/READOUT_RECONCILIATION.md.

Usage:
  python scripts/summarise_ceramics_arms.py --runs <run_dir> [<run_dir> ...]

A run_dir is an eval_runs/<name> folder; the script reads <run_dir>/results/.
"""

import argparse
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from readout import format_flags, read_run, weight  # noqa: E402


def median(xs):
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True)
    a = ap.parse_args()

    arms, all_records = {}, []
    for r in a.runs:
        d = Path(r)
        records = read_run(d)
        if not records:
            raise SystemExit(f"no per-draw json under {d}/results")
        all_records += records
        by_pot = defaultdict(list)
        for x in records:
            by_pot[x.object_name].append(x)
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
            n_parts = draws[0].n_fragments
            seated = [x.seated for x in draws]
            rot = [x.turn_deg for x in draws]
            # translation in object units is meaningless on its own; this is a
            # fraction of the pot, and gap_denominator says a fraction of what.
            off = [x.gap_object_fraction for x in draws]
            earned = [max(0, c - x.floor) for c, x in zip(seated, draws)]
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
        free = 0
        for pot, draws in by_pot.items():
            # pool the per-draw counts, so this is the AVERAGE attempt, not the
            # luckiest one. Best-of-N is not reported here on purpose.
            tot_seat += sum(x.seated for x in draws)
            tot_frag += sum(x.n_fragments for x in draws)
            free += sum(x.floor for x in draws)
            rots += [x.turn_deg for x in draws]
            n_draws += len(draws)
        # every draw gets its anchor for free, so the honest denominator and
        # numerator both drop by the fragments that were handed over.
        earned = tot_seat - free
        earn_frag = tot_frag - free
        pct = 100.0 * earned / earn_frag if earn_frag else float("nan")
        print(f"{arm:{aw}s}  {len(by_pot):4d}  {n_draws:5d}  {tot_seat:6d}  {earned:6d}"
              f"  {earn_frag:3d}  {pct:7.1f}  {median(rots):10.1f}d")

    dens = ", ".join(sorted({x.gap_denominator for x in all_records}))
    print(f"\noffset is a fraction of the pot: {dens}.")
    for line in format_flags(all_records):
        print(f"!! {line}")
    print(f"Weight: {weight(all_records)}.")

    print("\nA seated count is an index to a picture. Draw each arm before")
    print("quoting a row of this table:\n")
    for r in a.runs:
        print(f"  python scripts/render_assembly_grid.py \\")
        print(f'      --runs "{Path(r).name}={r}/clouds" \\')
        print(f"      --out artifacts/{Path(r).name}.png")

    print("\nThat percentage is fragments the model actually placed, on the")
    print("typical attempt -- not the best of them, and not counting the")
    print("anchor it was given. Zero earned means the pot fell apart.")
    print("A gap smaller than one fragment on one pot is not a result.")
    print("Eight pots is a lead, not a conclusion -- and they are modern")
    print("breaks with no wear, so they do not settle the buried-sherd case.\n")


if __name__ == "__main__":
    main()
