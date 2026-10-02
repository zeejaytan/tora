"""Join the U17 ranker's order to the answer key, after ranking (ticket 01).

The only step that reads labels. Labels are recomputed here with own_place.score_draw
on each run's rigid ("solid") attempt, the cloud the bundles were made from:

  genuine    all sherds in their own place AND the right way round
  near-miss  all sherds in their own place, at least one not the right way round

Writes a JSON and prints the plain read-out: rank of every genuine attempt, whether
one is in the top K, the random baseline, how many attempts Layer 1 drops, and where
the near-misses land. Prints the commit of the pre-registration file.

Usage: python scripts/rank_report.py --ranks ranks.json --key KEY/idmap.json \\
           --prereg .scratch/attempt-ranker/preregistration.md --out report.json \\
           [--expect-genuine 2 --expect-near 19] [--k 5]
"""
import argparse
import json
import subprocess
import sys
from math import comb
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from own_place import SEAT_PCT, score_draw  # noqa: E402


def prereg_commit(path: Path) -> str:
    """Commit of the pre-registration; refuse if it has uncommitted changes."""
    root = path.resolve().parent
    dirty = subprocess.run(["git", "status", "--porcelain", "--", str(path.resolve())],
                           cwd=root, capture_output=True, text=True).stdout.strip()
    h = subprocess.run(["git", "log", "-1", "--format=%h %cs", "--", str(path.resolve())],
                       cwd=root, capture_output=True, text=True).stdout.strip()
    if dirty or not h:
        sys.exit(f"pre-registration {path} is not committed as it stands")
    return h


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ranks", required=True, type=Path)
    ap.add_argument("--key", required=True, type=Path)
    ap.add_argument("--prereg", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--expect-genuine", type=int)
    ap.add_argument("--expect-near", type=int)
    a = ap.parse_args()

    commit = prereg_commit(a.prereg)
    ranks = json.loads(a.ranks.read_text())
    rows = ranks["attempts"]
    idmap = json.loads(a.key.read_text())

    by_run = {}
    for aid, v in idmap.items():
        by_run.setdefault(v["run"], []).append((v["attempt"], aid))
    label = {}
    for run, items in sorted(by_run.items()):
        d = np.load(run, allow_pickle=True)
        gt, ppp = d["pts_gt"].astype(float), d["points_per_part"]
        for t, aid in items:
            dr = score_draw(gt, d["generations_proposed"][t].astype(float), ppp)
            wrong = [tn for tn, pp in zip(dr.turn_deg, dr.point_pct) if pp >= SEAT_PCT]
            label[aid] = dict(run=run, attempt=t, own=dr.own, oriented=dr.oriented, n=dr.n,
                              worst_turn_deg=round(max(wrong), 1) if wrong else 0.0)

    n = len(rows)
    for r in rows:
        r.update(label[r["id"]])
        r["kind"] = ("genuine" if r["oriented"] == r["n"] else
                     "near-miss" if r["own"] == r["n"] else "other")
    gen = [r for r in rows if r["kind"] == "genuine"]
    near = [r for r in rows if r["kind"] == "near-miss"]
    if (a.expect_genuine is not None and len(gen) != a.expect_genuine) or \
       (a.expect_near is not None and len(near) != a.expect_near):
        sys.exit(f"labels changed: {len(gen)} genuine, {len(near)} near-miss, expected "
                 f"{a.expect_genuine}, {a.expect_near}. The ruler moved; stop here.")
    baseline = 1 - comb(n - len(gen), a.k) / comb(n, a.k) if gen else 0.0
    hit = any(r["rank"] <= a.k for r in gen)
    passed = sum(r["layer1_pass"] for r in rows)

    def place(r):
        return dict(rank=r["rank"], run=Path(r["run"]).parts[-4] if len(Path(r["run"]).parts) >= 4
                    else r["run"], attempt=r["attempt"], pass_=r["layer1_pass"],
                    profile_mm=r["profile_mm"], inside_out=r["inside_out"],
                    least_sure=r["least_sure"], worst_turn_deg=r["worst_turn_deg"])

    out = dict(prereg_commit=commit, layer=ranks.get("layer"), cutoffs=ranks.get("cutoffs"),
               n_attempts=n, k=a.k, random_baseline=round(baseline, 4), top_k_hit=hit,
               layer1_pass=passed, layer1_dropped=n - passed,
               genuine=[place(r) for r in gen],
               near_miss=sorted((place(r) for r in near), key=lambda x: x["rank"]),
               near_miss_above_best_genuine=sum(r["rank"] < min((g["rank"] for g in gen),
                                                                 default=n + 1) for r in near))
    a.out.write_text(json.dumps(out, indent=1))

    print(f"pre-registration {commit}; Layer {out['layer']}; {n} attempts")
    print(f"Layer 1 kept {passed}, dropped {n - passed} ({100 * (n - passed) / n:.0f}%)")
    for g in out["genuine"]:
        print(f"genuine {g['run']} #{g['attempt']}: rank {g['rank']} of {n} "
              f"(deviation {g['profile_mm']} mm, {'kept' if g['pass_'] else 'DROPPED'})")
    print(f"genuine in top {a.k}: {'YES' if hit else 'no'}  (random choice: "
          f"{100 * baseline:.2f}%)")
    print(f"near-misses ranked above the best genuine: {out['near_miss_above_best_genuine']}"
          f" of {len(near)}")
    for r in out["near_miss"]:
        print(f"  near-miss {r['run']} #{r['attempt']}: rank {r['rank']}, worst turn "
              f"{r['worst_turn_deg']} deg, {'kept' if r['pass_'] else 'dropped'}")
    print(f"-> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
