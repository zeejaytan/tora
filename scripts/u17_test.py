"""Score the U17 ranker on the held-out Fractura pots, cut-offs fixed (key side).

Read-outs and success rule are fixed in .scratch/attempt-ranker/preregistration-test.md,
whose commit this prints. The cut-offs come from the calibration run (calib.json) and must
equal the ones written in that file; nothing is tuned here. Reads per test pot: Layer 1
ranks (rank_attempts.py), Layer 2 gaps (l2_measure.py), the converter's id map, labels.

TORA (ticket 06): --method tora allows any pot; the cut-offs stay GARF's calibration.

Usage: python scripts/u17_test.py --root DIR --labels labels.json --calib calib.json
    --profile-pct 0.873 --unfixable-pct 2.31 --pots narrow_bottle3 galli_pot
    --pot-mm 100 --prereg preregistration-test.md --out test.json
  DIR/<pot>/ranks.json, DIR/<pot>_l2.json, DIR/<pot>/key/idmap.json
"""
import argparse
import json
import sys
from math import comb
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import u17_calibrate as C  # noqa: E402
from l2_report import auc  # noqa: E402
from rank_report import prereg_commit  # noqa: E402

TEST_POTS = C.TEST_POTS
K = 5


def order(rows, key):
    return [r for r in sorted(rows, key=key)]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", required=True, type=Path)
    ap.add_argument("--labels", required=True, type=Path)
    ap.add_argument("--calib", required=True, type=Path)
    ap.add_argument("--profile-pct", required=True, type=float)
    ap.add_argument("--unfixable-pct", required=True, type=float)
    ap.add_argument("--pots", required=True, nargs="+")
    ap.add_argument("--pot-mm", type=float, required=True)
    ap.add_argument("--prereg", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--method", choices=("garf", "tora"), default="garf",
                    help="tora: any pot (the cut-offs were set on GARF's attempts only)")
    a = ap.parse_args()
    if a.method == "garf" and set(a.pots) - TEST_POTS:
        sys.exit(f"not test pots: {set(a.pots) - TEST_POTS}")
    commit = prereg_commit(a.prereg)
    cal = json.loads(a.calib.read_text())
    if (round(cal["profile_pct"], 3) != round(a.profile_pct, 3)
            or round(cal["unfixable_pct"], 2) != round(a.unfixable_pct, 2)):
        sys.exit(f"cut-offs differ from the calibration: {cal['profile_pct']}, "
                 f"{cal['unfixable_pct']} vs {a.profile_pct}, {a.unfixable_pct}")
    if not (cal["unjudged_fail"] and not cal["io_gate"]):
        sys.exit("calibration was not run with --unjudged fail --io-gate off")
    C.IO_GATE, C.UNJ_FAIL = False, True
    labels = {(r["pot"], r["run"], r["attempt"]): r
              for r in json.loads(a.labels.read_text())}

    print(f"pre-registration {a.prereg} @ {commit}; method {a.method}")
    print(f"cut-offs (fixed): Layer 1 profile {a.profile_pct}% of pot; "
          f"unfixable gap {a.unfixable_pct}% of pot; calibration {a.calib}")
    out = dict(prereg_commit=commit, method=a.method, profile_pct=a.profile_pct,
               unfixable_pct=a.unfixable_pct, k=K, pots={})
    for p in a.pots:
        rs = C.pot_rows(a.root, p, labels, a.pot_mm)
        n = len(rs)
        gen = [r for r in rs if r["cls"] == "genuine"]
        near = [r for r in rs if r["cls"] == "near"]
        for r in rs:
            r["pass"] = C.l1_ok(r, a.profile_pct)
        l1 = order(rs, lambda r: (not r["pass"], r["profile"]))
        l12 = order(rs, lambda r: (not r["pass"], r["worst"], r["profile"]))
        rank1 = {r["id"]: i for i, r in enumerate(l1, 1)}
        rank12 = {r["id"]: i for i, r in enumerate(l12, 1)}
        base = 1 - comb(n - len(gen), K) / comb(n, K) if gen else 0.0
        best1 = min((rank1[r["id"]] for r in gen), default=None)
        best12 = min((rank12[r["id"]] for r in gen), default=None)
        top12 = [r["cls"] for r in l12[:K]]
        d = dict(
            n=n, genuine=len(gen), near_miss=len(near), random_top5=round(base, 4),
            layer1_kept=sum(r["pass"] for r in rs),
            genuine_failed_l1=sum(not r["pass"] for r in gen),
            genuine_failed_l1_why=[dict(id=r["id"], profile=round(r["profile"], 3),
                                        unjudged=r["unj"]) for r in gen if not r["pass"]],
            genuine_unjudged_share=round(float(np.mean([r["unj"] > 0 for r in gen])), 3)
            if gen else None,
            genuine_inside_out_share=round(float(np.mean([r["io"] > 0 for r in gen])), 3)
            if gen else None,
            best_genuine_rank_l1=best1, best_genuine_rank_l12=best12,
            top5_hit_l1=bool(best1 and best1 <= K), top5_hit_l12=bool(best12 and best12 <= K),
            top5_l12_classes=top12,
            near_above_best_genuine_l12=sum(rank12[r["id"]] < best12 for r in near)
            if best12 else None,
            auc_near_vs_genuine_worst=round(auc([r["worst"] for r in near],
                                                [r["worst"] for r in gen]), 3),
            genuine_flagged_unfixable=round(float(np.mean(
                [r["worst"] > a.unfixable_pct for r in gen])), 3) if gen else None,
            genuine_ranks_l12=sorted(rank12[r["id"]] for r in gen))
        out["pots"][p] = d
        print(f"\n### {p}: {n} attempts, {len(gen)} genuine, {len(near)} near-miss; "
              f"random top {K}: {100 * base:.1f}%")
        print(f"Layer 1 kept {d['layer1_kept']}; genuine failed by Layer 1: "
              f"{d['genuine_failed_l1']} (unjudged share {d['genuine_unjudged_share']}, "
              f"inside-out reported {d['genuine_inside_out_share']})")
        for w in d["genuine_failed_l1_why"][:10]:
            print(f"  failed genuine {w['id']}: profile {w['profile']}% unjudged {w['unjudged']}")
        print(f"best genuine rank: Layer 1 {best1}, Layers 1+2 {best12} of {n}; "
              f"top {K}: L1 {'YES' if d['top5_hit_l1'] else 'no'}, "
              f"L1+2 {'YES' if d['top5_hit_l12'] else 'no'}")
        print(f"top {K} under Layers 1+2: {top12}")
        print(f"near-misses above best genuine (L1+2): {d['near_above_best_genuine_l12']} "
              f"of {len(near)}; near vs genuine worst-gap AUC {d['auc_near_vs_genuine_worst']}")
        print(f"genuine flagged unfixable: {d['genuine_flagged_unfixable']}")
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(out, indent=1))
    print(f"-> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
