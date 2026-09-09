"""Read job 29880370 -- the wear v3 adapter -- through `readout.py`.

WHY THIS EXISTS. The job trained the adapter and printed twelve summary tables, and
then nobody read them for a week. The printed tables cannot be quoted as they stand,
for two reasons this script fixes and one it can only report:

  1. The free anchor. Every `part_accuracy` in those tables counts the anchor
     fragment -- clamped at ground truth by construction -- as a fragment the model
     placed. On the nine-sherd Juglet that is a free ninth on every arm. `readout.py`
     reports seating as a COUNT with the floor named, so the free one cannot be
     mistaken for earned.

  2. The pooled mean. `avg/part_accuracy` averages six objects of different fragment
     counts into one number. intent/O2 records what that costs: it reported a real
     two-thirds reduction in the wear penalty as no effect. Everything here is
     per object, and the sweep is per object per rung.

  3. What it cannot fix, and prints instead: the `erosion_sweep` and `real_heldout`
     arms are the SIX-object `real_heldout_norm` file, THREE of them bones. That is
     the same defect ticket 11 found in the ticket-09 sweep. Half of the column the
     adapter was bought for is not pottery.

Usage:
    python scripts/summarise_lorav3.py --runs artifacts/lorav3_29880370/runs
"""

from __future__ import annotations

import argparse
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

from readout import format_flags, read_run, weight

ARMS = ["baseline", "adapter_off", "adapter_on"]
SETS = ["vessels", "sweep", "fresh", "juglet"]

# real_heldout_norm's six objects. The three bones are why a pooled figure over this
# file says little about pottery -- named here so the split is visible, not inferred.
BONES = {"coxae", "limb3", "vert9"}

SET_TITLES = {
    "vessels": "synthetic vessel shapes the adapter trained on (bbad_vessels_v3 val)",
    "sweep":   "the erosion sweep -- the gain the adapter was bought for",
    "fresh":   "real unworn pots -- what we might be paying with",
    "juglet":  "the Juglet, against the hand reassembly",
}


def short(name: str) -> str:
    """Object name without its dataset prefix."""
    return name.split("/")[-1]


def load(runs: Path, arm: str, dataset: str) -> list:
    d = runs / f"lorav3_{dataset}_{arm}_29880370"
    if not d.is_dir():
        raise SystemExit(f"missing run directory: {d}")
    return read_run(d)


def by_object(records) -> dict[str, list]:
    out = defaultdict(list)
    for r in records:
        out[short(r.object_name)].append(r)
    return out


def mean_seated(recs) -> float:
    """Mean fragments seated over the draws of ONE object. Never across objects."""
    vals = [r.seated for r in recs if r.seated >= 0]
    return float(np.mean(vals)) if vals else float("nan")


def mean_turn(recs) -> float:
    vals = [r.turn_deg for r in recs if not math.isnan(r.turn_deg)]
    return float(np.mean(vals)) if vals else float("nan")


def table(title: str, rows: list[tuple], arms_present: list[str]) -> None:
    print()
    print(title)
    print("-" * len(title))
    head = f"{'object':<26}{'sherds':>8}{'free':>6}   " + "".join(
        f"{a:>22}" for a in arms_present)
    print(head)
    for name, n_frag, floor, cells in rows:
        line = f"{short(name):<26}{n_frag:>8}{floor:>6}   "
        for c in cells:
            line += f"{c:>22}"
        print(line)


def cell(seated: float, n_frag: int, turn: float) -> str:
    if math.isnan(seated):
        return "-".rjust(22)
    return f"{seated:.1f}/{n_frag} seated {turn:.0f}d"


def run_set(runs: Path, dataset: str, limit_objects: int | None = None) -> list:
    """Print one set's per-object table across the three arms. Returns all records."""
    per_arm = {a: by_object(load(runs, a, dataset)) for a in ARMS}
    names = sorted(per_arm[ARMS[0]].keys())
    if limit_objects is not None and len(names) > limit_objects:
        shown = names[:limit_objects]
    else:
        shown = names

    rows = []
    for nm in shown:
        recs0 = per_arm[ARMS[0]][nm]
        n_frag = recs0[0].n_fragments
        floor = recs0[0].floor
        cells = []
        for a in ARMS:
            recs = per_arm[a].get(nm, [])
            cells.append(cell(mean_seated(recs), n_frag, mean_turn(recs)) if recs
                         else "-".rjust(22))
        rows.append((nm, n_frag, floor, cells))

    table(f"{dataset.upper()} -- {SET_TITLES[dataset]}", rows, ARMS)
    if limit_objects is not None and len(names) > limit_objects:
        print(f"    ... {len(names) - limit_objects} more objects not shown "
              f"(pass --all-vessels)")

    allrecs = [r for a in ARMS for rs in per_arm[a].values() for r in rs]
    return allrecs


def run_sweep(runs: Path) -> list:
    """The sweep, per pot per rung, ceramics and bones kept apart."""
    per_arm = {a: by_object(load(runs, a, "sweep")) for a in ARMS}
    names = sorted(per_arm[ARMS[0]].keys())

    pots = defaultdict(list)
    for nm in names:
        pot, _, rung = nm.rpartition("_")
        pots[pot].append((rung, nm))

    for group, keep in (("CERAMICS", False), ("BONES -- not pottery, reported apart", True)):
        print()
        print(f"SWEEP / {group}")
        print("-" * (8 + len(group)))
        print(f"{'pot':<18}{'sherds':>7}{'free':>5}  {'rung':>6}   "
              + "".join(f"{a:>20}" for a in ARMS))
        for pot in sorted(pots):
            if (pot in BONES) != keep:
                continue
            for rung, nm in sorted(pots[pot]):
                recs0 = per_arm[ARMS[0]][nm]
                n_frag, floor = recs0[0].n_fragments, recs0[0].floor
                line = f"{pot:<18}{n_frag:>7}{floor:>5}  {rung:>6}   "
                for a in ARMS:
                    recs = per_arm[a].get(nm, [])
                    s, t = mean_seated(recs), mean_turn(recs)
                    line += (f"{s:.1f}/{n_frag} {t:.0f}d".rjust(20) if recs
                             else "-".rjust(20))
                print(line)

    return [r for a in ARMS for rs in per_arm[a].values() for r in rs]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", type=Path,
                    default=Path("artifacts/lorav3_29880370/runs"))
    ap.add_argument("--all-vessels", action="store_true",
                    help="print all 107 synthetic vessel shapes, not the first 12")
    args = ap.parse_args()

    print("=" * 78)
    print("job 29880370 -- wear v3 adapter, read through readout.py")
    print("seating is a COUNT with the free anchor named; turn is corrected for it")
    print("no pooled mean anywhere: intent/O2 records what one costs")
    print("=" * 78)

    everything = []
    everything += run_set(args.runs, "vessels",
                          limit_objects=None if args.all_vessels else 12)
    everything += run_sweep(args.runs)
    everything += run_set(args.runs, "fresh")
    everything += run_set(args.runs, "juglet")

    print()
    print("WEIGHT")
    print("------")
    for dataset in SETS:
        recs = [r for r in everything if dataset in r.run]
        print(f"  {dataset:<9} {weight(recs)}")

    print()
    print("HEALTH WARNINGS")
    print("---------------")
    for f in format_flags(everything):
        print(f"  - {f}")
    print("  - erosion_sweep and real_heldout are the SIX-object real_heldout_norm "
          "file;\n    three of the six (coxae, limb3, vert9) are BONES. Ticket 11.")


if __name__ == "__main__":
    main()
