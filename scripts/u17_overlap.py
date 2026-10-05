"""U17 Revision 4: set the overlap cut-off on GARF's calibration pots, then re-rank (key side).

Rule and read-outs fixed in .scratch/attempt-ranker/preregistration-overlap.md, whose
commit this prints. Revision 3 (Layer 1 profile 0.873%, near joins, unjudged fails) is
kept exactly; Revision 4 adds one gate: an attempt fails if any sherd has more than the
cut-off share of its surface inside another sherd (overlap_measure.py).

Cut-off: per calibration pot, the 99th percentile over genuine attempts of the worst
sherd's inside share; the cut-off is the largest of those (as Revision 3 set its own).

Every pot is then ranked twice, Revision 3 and Revision 4:
  order  Layer 1 pass (and overlap pass, Rev 4), then worst-sherd gap, then profile.

Usage: python scripts/u17_overlap.py --prereg PREREG --profile-pct 0.873 --out out.json
    --calib-pots ROOT LABELS OVDIR blue_pot narrow_bottle2 ...   (GARF calibration)
    --pots NAME ROOT LABELS OVDIR pot [pot ...]                   (repeatable; seen pots)
  ROOT/<pot>/ranks.json, ROOT/<pot>_l2.json, ROOT/<pot>/key/idmap.json; OVDIR/<pot>_overlap.json
"""
import argparse
import json
import sys
from math import comb
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import u17_calibrate as C  # noqa: E402
from rank_report import prereg_commit  # noqa: E402

K = 5


def rows_for(root, labels_path, ovdir, pot, profile_pct):
    labels = {(r["pot"], r["run"], r["attempt"]): r
              for r in json.loads(Path(labels_path).read_text())}
    rs = C.pot_rows(Path(root), pot, labels, 100.0)
    ov = {r["id"]: r for r in json.loads((Path(ovdir) / f"{pot}_overlap.json")
                                         .read_text())["attempts"]}
    for r in rs:
        s = ov[r["id"]]["sherds"]
        r["inside"] = max(x["inside_pct"] for x in s)
        r["inside_sherd"] = int(np.argmax([x["inside_pct"] for x in s]))
        r["pass"] = C.l1_ok(r, profile_pct)
    return rs


def rank(rs, cut):
    ok = (lambda r: r["pass"]) if cut is None else (lambda r: r["pass"] and r["inside"] <= cut)
    order = sorted(rs, key=lambda r: (not ok(r), r["worst"], r["profile"]))
    gen = [i for i, r in enumerate(order, 1) if r["cls"] == "genuine"]
    near = [i for i, r in enumerate(order, 1) if r["cls"] == "near"]
    best = min(gen, default=None)
    return dict(kept=sum(ok(r) for r in rs), best_genuine=best,
                best_genuine_id=order[best - 1]["id"] if best else None,
                top5_ids=[r["id"] for r in order[:K]],
                top5_hit=bool(best and best <= K), top5=[r["cls"] for r in order[:K]],
                near_above=sum(n < best for n in near) if best else None,
                top5_inside=[round(r["inside"], 2) for r in order[:K]])


def q(xs, p):
    return round(float(np.percentile(xs, p)), 3) if len(xs) else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--prereg", required=True, type=Path)
    ap.add_argument("--profile-pct", required=True, type=float)
    ap.add_argument("--calib-pots", required=True, nargs="+")
    ap.add_argument("--pots", action="append", nargs="+", default=[])
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    commit = prereg_commit(a.prereg)
    C.IO_GATE, C.UNJ_FAIL = False, True
    print(f"pre-registration {a.prereg} @ {commit}; Revision 3 Layer 1 at {a.profile_pct}%")

    root, labels, ovdir, *cal = a.calib_pots
    sets = [("garf-calibration", root, labels, ovdir, cal)]
    sets += [(s[0], s[1], s[2], s[3], s[4:]) for s in a.pots]
    rows = {(name, p): rows_for(r, lab, ov, p, a.profile_pct)
            for name, r, lab, ov, pots in sets for p in pots}

    per = {}
    print("\n### overlap on GARF's calibration pots: worst sherd's surface inside another, %")
    print(f"{'pot':16} {'class':8} {'n':>5} {'median':>7} {'q90':>7} {'q99':>7} {'max':>7}")
    for p in cal:
        rs = rows[("garf-calibration", p)]
        for cls in ("genuine", "near", "other"):
            xs = [r["inside"] for r in rs if r["cls"] == cls]
            print(f"{p:16} {cls:8} {len(xs):>5} {q(xs, 50)!s:>7} {q(xs, 90)!s:>7} "
                  f"{q(xs, 99)!s:>7} {max(xs, default=0):>7.2f}")
        per[p] = q([r["inside"] for r in rs if r["cls"] == "genuine"], 99)
    cut = max(per.values())
    print(f"\nRevision 4 overlap cut-off: {cut}% of a sherd's surface (q99 genuine per pot: {per})")

    out = dict(prereg_commit=commit, profile_pct=a.profile_pct, overlap_cut=cut,
               per_pot_q99=per, pots={})
    print(f"\n{'set':18} {'pot':15} {'n':>4} {'gen':>4} {'rand5':>6}  "
          f"{'rev':3} {'kept':>5} {'best':>5} {'top5?':5} {'near>':>5}  top 5 (inside %)")
    for (name, p), rs in rows.items():
        n, g = len(rs), sum(r["cls"] == "genuine" for r in rs)
        base = 1 - comb(n - g, K) / comb(n, K) if g else 0.0
        r3, r4 = rank(rs, None), rank(rs, cut)
        gen = [r for r in rs if r["cls"] == "genuine"]
        failed = [r for r in gen if r["inside"] > cut]
        out["pots"][f"{name}/{p}"] = dict(n=n, genuine=g, random_top5=round(base, 4),
                                          rev3=r3, rev4=r4, genuine_failed_overlap=len(failed),
                                          genuine_failed_why=[dict(id=r["id"], inside=r["inside"],
                                                                   sherd=r["inside_sherd"])
                                                              for r in failed[:10]])
        for tag, r in (("3", r3), ("4", r4)):
            print(f"{name:18} {p:15} {n:>4} {g:>4} {100 * base:>5.1f}%  {tag:>3} {r['kept']:>5} "
                  f"{r['best_genuine']!s:>5} {'YES' if r['top5_hit'] else 'no':5} "
                  f"{r['near_above']!s:>5}  {list(zip(r['top5'], r['top5_inside']))}")
        if failed:
            print(f"  genuine failed by overlap: {len(failed)} of {g}: "
                  f"{[(r['id'], r['inside'], r['inside_sherd']) for r in failed[:5]]}")
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(out, indent=1))
    print(f"-> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
