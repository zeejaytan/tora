"""Report the Juglet arms as distributions of SHERDS SEATED, not as averages.

The Juglet has nine fragments, so every part-accuracy score it can produce is a
multiple of 1/9 = 0.111. Reporting 0.622 hides that this means "5.6 sherds on
average", and reporting only the average hides the thing that actually matters
on a single object: how much the answer moves between one attempt and the next.

Job 29623885 put 0.511, 0.622 and 0.644 in a table as if they were three
different results. In sherds that is 4.6, 5.6 and 5.8 out of 9, from five draws
each -- a gap of about one sherd, measured five times. This prints what that
table could not: the whole distribution, the median, and how often each arm
reaches a given number of sherds.

It reads the per-draw json that sample.py already writes; nothing needs to be
rerun to use it on an old run.

REWIRED 2026-09-05. Every number here now comes from scripts/readout.py, the one
place a run is read. WHAT MOVED: the turn column. This script used to print the
stored `rotation_error`, which is summed over the non-anchor fragments but
divided by all of them, so it carried a free zero. On the nine-sherd Juglet the
observed ratio is exactly 1.125000 on every draw -- the 55.7 deg once published
for lorav3_juglet_baseline_29880370 is 62.7 deg. Sherds seated did not move.
Reconciliation: docs/notes/READOUT_RECONCILIATION.md.

Usage:
  python scripts/summarise_juglet_draws.py --runs <run_dir> [<run_dir> ...]

A run_dir is an eval_runs/<name> folder; the script reads <run_dir>/results/.
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from readout import format_flags, read_run, weight  # noqa: E402


def median(xs: list[float]) -> float:
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True)
    a = ap.parse_args()

    rows, all_records = [], []
    for r in a.runs:
        d = Path(r)
        records = read_run(d)
        if not records:
            raise SystemExit(f"no per-draw json under {d}/results")
        all_records += records
        rows.append({
            "name": d.name,
            "n": len(records),
            "parts": records[0].n_fragments,
            "floor": records[0].floor,
            # seated is already a count of fragments, so the quantisation is
            # visible instead of hidden behind three decimals
            "seated": [x.seated for x in records],
            "rot": [x.turn_deg for x in records],
        })

    parts = rows[0]["parts"]
    print(f"\nThe Juglet: {parts} fragments, one of them missing from the pot.")
    print("A reconstruction that leaves that gap open is correct.\n")

    w = max(len(r["name"]) for r in rows)
    head = f"sherds seated (of {parts})"
    print(f"{'arm':{w}s}  draws  {head:34s}  median  best  worst   turn")
    for r in rows:
        c = Counter(r["seated"])
        hist = " ".join(f"{k}x{c[k]}" for k in sorted(c))
        print(f"{r['name']:{w}s}  {r['n']:5d}   {hist:34s}  "
              f"{median(r['seated']):6.1f}  {max(r['seated']):4d}  "
              f"{min(r['seated']):5d}  {median(r['rot']):5.1f} deg")

    print("\n'3x2' means two of the draws seated three sherds.")

    if len(rows) > 1:
        best = max(rows, key=lambda r: median(r["seated"]))
        others = [r for r in rows if r is not best]
        gap = min(median(best["seated"]) - median(o["seated"]) for o in others)
        print(f"\nBest median: {best['name']} at {median(best['seated']):.1f} "
              f"sherds, ahead of the next arm by {gap:.1f}.")
        if gap < 1.0:
            print("That is less than one sherd. On a single pot, with these")
            print("draws overlapping, it is not a difference worth acting on --")
            print("say so plainly rather than ranking the arms.")
        else:
            print("Check the overlap above before calling it a difference: if")
            print("the two distributions share most of their range, the medians")
            print("are further apart than the arms are.")

    print(f"\nOne of the {parts} is the anchor, placed correctly by construction:")
    print(f"the floor is {rows[0]['floor']} of {parts}, and the model earns nothing")
    print("for it. Turn is the mean over the fragments it had to place.")

    for line in format_flags(all_records):
        print(f"!! {line}")
    print(f"\nWeight: {weight(all_records)}.")

    print("\nNow open the renders. This is one pot; the picture is the")
    print("instrument and the table is the index to it. Draw them with:\n")
    for r in a.runs:
        print(f'  python scripts/render_assembly_grid.py \\')
        print(f'      --runs "{Path(r).name}={r}/clouds" \\')
        print(f'      --out artifacts/{Path(r).name}.png')
    print()


if __name__ == "__main__":
    main()
