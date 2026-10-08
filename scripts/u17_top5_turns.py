"""How far each sherd sits from home in the ranker's top attempts (ticket 07, key side).

For each attempt in top.json (u17_top5_export.py): per sherd, the turn from its home
orientation in degrees (own_place.turn_deg) and the median point offset in mm and in % of
pot against the "right way round" limit (own_place.SEAT_PCT). Answers whether a sherd the
key calls turned is turned by enough for the eye to see.

Usage: python scripts/u17_top5_turns.py --top top.json --key idmap.json
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from own_place import SEAT_PCT, score_draw  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--top", required=True, type=Path)
ap.add_argument("--key", required=True, type=Path)
a = ap.parse_args()
top = json.loads(a.top.read_text())
idmap = json.loads(a.key.read_text())
pot = top["pot_mm"]
print(f"right-way limit {SEAT_PCT:.2f}% of pot = {SEAT_PCT * pot / 100:.2f} mm; colours "
      f"{top['sherd_colours']}")
for t in top["attempts"]:
    run, i = idmap[t["id"]]["run"], idmap[t["id"]]["attempt"]
    d = np.load(run, allow_pickle=True)
    dr = score_draw(d["pts_gt"].astype(float), d["generations_proposed"][i].astype(float),
                    d["points_per_part"])
    cells = [f"{j}:{dr.turn_deg[j]:5.1f}deg {dr.point_pct[j] * pot / 100:4.2f}mm"
             f"{'*' if dr.point_pct[j] >= SEAT_PCT else ''}" for j in range(dr.n)]
    print(f"pick {t['rank']}: " + "  ".join(cells))
