"""What the turn limit changes in the answer key (U17 ticket 10, key side).

Reads label files written by label_attempts.py after the turn limit (each row carries
`oriented`, with the limit, and `oriented_point`, offset only as before), and optionally
the old label file of the same attempts, to confirm `oriented_point` reproduces it.
Per pot: genuine and near-miss counts before and after, and the attempts that changed.

Usage: python scripts/u17_relabel_diff.py --new NEW.json [--old OLD.json] [--name NAME]
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path


def cls(r, key):
    return ("genuine" if r[key] == r["n"] else "near" if r["own"] == r["n"] else "other")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--new", required=True, type=Path)
    ap.add_argument("--old", type=Path)
    ap.add_argument("--name", default="")
    a = ap.parse_args()
    new = json.loads(a.new.read_text())
    if a.old:
        old = {(r["pot"], r["run"], r["attempt"]): r for r in json.loads(a.old.read_text())}
        keys = {(r["pot"], r["run"], r["attempt"]) for r in new}
        bad = [k for k in keys if k not in old] + \
              [k for r in new for k in [(r["pot"], r["run"], r["attempt"])]
               if k in old and old[k]["oriented"] != r["oriented_point"]]
        print(f"{a.name}: offset-only labels reproduce the old file: "
              f"{'yes' if not bad else f'NO, {len(bad)} differ or are missing'} "
              f"({len(new)} attempts, old file {len(old)})")
    by = defaultdict(list)
    for r in new:
        by[r["pot"].split("/")[-1]].append(r)
    print(f"{'pot':16} {'n':>5} {'genuine old->new':>17} {'near old->new':>14}  changed (run#attempt)")
    for p, rs in sorted(by.items()):
        g0 = sum(cls(r, "oriented_point") == "genuine" for r in rs)
        g1 = sum(cls(r, "oriented") == "genuine" for r in rs)
        n0 = sum(cls(r, "oriented_point") == "near" for r in rs)
        n1 = sum(cls(r, "oriented") == "near" for r in rs)
        ch = [f"{r['run']}#{r['attempt']}" for r in rs if cls(r, "oriented") != cls(r, "oriented_point")]
        print(f"{p:16} {len(rs):>5} {g0:>8} -> {g1:<6} {n0:>6} -> {n1:<5}  {len(ch)}: {ch[:6]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
