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

Usage:
  python scripts/summarise_juglet_draws.py --runs <run_dir> [<run_dir> ...]

A run_dir is an eval_runs/<name> folder; the script reads <run_dir>/results/.
"""

import argparse
import json
from collections import Counter
from pathlib import Path


def load_draws(run_dir: Path) -> list[dict]:
    res = run_dir / "results"
    if not res.is_dir():
        raise SystemExit(f"no results/ under {run_dir}")
    out = []
    for p in sorted(res.glob("*_generation*.json")):
        out.append(json.loads(p.read_text()))
    if not out:
        raise SystemExit(f"no per-draw json in {res}")
    return out


def median(xs: list[float]) -> float:
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True)
    a = ap.parse_args()

    rows = []
    for r in a.runs:
        d = Path(r)
        draws = load_draws(d)
        n_parts = draws[0]["num_parts"]
        # part_accuracy is a fraction of fragments; turn it back into a count so
        # the quantisation is visible instead of hidden behind three decimals.
        seated = [round(x["part_accuracy"] * n_parts) for x in draws]
        rot = [x["rotation_error"] for x in draws]
        rows.append({
            "name": d.name,
            "n": len(draws),
            "parts": n_parts,
            "seated": seated,
            "rot": rot,
        })

    parts = rows[0]["parts"]
    print(f"\nThe Juglet: {parts} fragments, one of them missing from the pot.")
    print("A reconstruction that leaves that gap open is correct.\n")

    w = max(len(r["name"]) for r in rows)
    print(f"{'arm':{w}s}  draws   sherds seated (of {parts})            "
          f"median  best  worst   turn")
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

    print("\nNow open the renders. This is one pot; the picture is the")
    print("instrument and the table is the index to it.\n")


if __name__ == "__main__":
    main()
