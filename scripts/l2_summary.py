"""Per pot: how far GARF's attempts sit from a correct join, in % of pot size (no labels).

Reads l2_measure.py outputs (<pot>_l2.json) and the true-assembly floors (l2_truth.py).

Usage: python scripts/l2_summary.py --dir DIR
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dir", required=True, type=Path)
    a = ap.parse_args()
    truth = {}
    for f in a.dir.glob("*_truth.json"):
        for obj, rows in json.loads(f.read_text()).items():
            truth[obj.split("/")[-1].replace("Juglet-000", "juglet")] = rows
    print(f"{'pot':15} {'sherds':>6} {'wall%':>6} {'true gap%':>9} | attempts: sherd gap% "
          f"q25/q50/q75 | worst sherd q25/q50/q75 | nudge at limit")
    for f in sorted(a.dir.glob("*_l2.json")):
        pot = f.name[: -len("_l2.json")]
        d = json.loads(f.read_text())
        t = truth.get(pot, [])
        tg = np.median([r["gap"] for r in t if r["gap"] is not None]) if t else np.nan
        wall = np.median([s["wall_pct"] for s in d["sherd_info"]])
        g = np.array([s["gap"] for r in d["attempts"] for s in r["sherds"] if s["gap"] is not None])
        worst = np.array([max((s["gap"] if s["gap"] is not None else np.inf) for s in r["sherds"])
                          for r in d["attempts"]])
        lim = np.mean([s["nudge_pct"] > 0.95 * d["settings"]["NUDGE_PCT"]
                       or s["nudge_deg"] > 0.95 * d["settings"]["NUDGE_DEG"]
                       for r in d["attempts"] for s in r["sherds"]])
        q = lambda x: "/".join(f"{v:.2f}" for v in np.percentile(x[np.isfinite(x)], [25, 50, 75]))
        print(f"{pot:15} {len(d['sherd_info']):>6} {wall:6.2f} {tg:9.2f} | {q(g):>17} | "
              f"{q(worst):>17} | {100 * lim:4.0f}%   (no-contact attempts: {int(np.isinf(worst).sum())})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
