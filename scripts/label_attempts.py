"""Label every saved attempt as own place / right way round, per pot (U17 ticket 04).

For each run's clouds/*.npz (one pot per file), scores each attempt's rigid ("solid")
cloud, generations_proposed, with own_place.score_draw: the same cloud and ruler as the
Juglet labels (jug_t06_rescore.json; the U17 report reproduced its 2 genuine / 19
near-miss). Answer-key work: run it apart from the ranker.

  genuine    every sherd in its own place AND the right way round
  near-miss  every sherd in its own place, at least one not the right way round

Writes one JSON row per attempt and prints, per pot: attempts, near-misses, genuine,
and whether the pot qualifies for ranking (genuine rare but present).

Usage: python scripts/label_attempts.py --runs DIR [DIR ...] --out labels.json
           [--workers N]
"""
import argparse
import json
import os
import re
import sys
from collections import defaultdict
from math import comb
from multiprocessing import Pool
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from own_place import score_draw  # noqa: E402

RARE = 0.10   # a pot qualifies if 0 < genuine share <= RARE (spec: rare but present)


def label_file(path):
    d = np.load(path, allow_pickle=True)
    gt, ppp = d["pts_gt"].astype(float), d["points_per_part"]
    run = Path(path).parents[2].name
    m = re.match(r"rwlora_eval_(.+?)_ds(\d+)_", run)
    rows = []
    for t, pred in enumerate(d["generations_proposed"].astype(float)):
        dr = score_draw(gt, pred, ppp)
        rows.append(dict(pot=str(d["name"]), arm=m.group(1) if m else run,
                         ds=int(m.group(2)) if m else -1, run=run, file=Path(path).name,
                         attempt=t, n=dr.n, own=dr.own, oriented=dr.oriented))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--runs", required=True, nargs="+", type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--workers", type=int,
                    default=int(os.environ.get("SLURM_CPUS_PER_TASK", "1")))
    a = ap.parse_args()
    files = sorted(f for r in a.runs for f in (r / "version_0" / "clouds").glob("*.npz"))
    if not files:
        sys.exit("no clouds/*.npz under the given runs")
    with Pool(a.workers) as pool:
        rows = [x for part in pool.map(label_file, files, chunksize=1) for x in part]
    a.out.write_text(json.dumps(rows, indent=0))

    by = defaultdict(list)
    for r in rows:
        by[r["pot"]].append(r)
    print(f"{len(rows)} attempts, {len(files)} files, {len(a.runs)} runs -> {a.out}")
    print(f"{'pot':34} {'n':>3} {'attempts':>8} {'near-miss':>9} {'genuine':>7} "
          f"{'random top5':>11}  verdict")
    for pot, rs in sorted(by.items()):
        n = len(rs)
        gen = sum(r["oriented"] == r["n"] for r in rs)
        near = sum(r["own"] == r["n"] and r["oriented"] < r["n"] for r in rs)
        base = 1 - comb(n - gen, 5) / comb(n, 5) if gen else 0.0
        verdict = ("set aside: none right" if gen == 0 else
                   "set aside: right too often" if gen / n > RARE else "qualifies")
        print(f"{pot:34} {rs[0]['n']:>3} {n:>8} {near:>9} {gen:>7} {100 * base:>10.1f}%  "
              f"{verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
