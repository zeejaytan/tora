"""Set the U17 ranker's cut-offs on the set-aside Fractura pots (key side).

Rules fixed in .scratch/attempt-ranker/calibration-fractura.md before this runs. Reads
per calibration pot: Layer 1 ranks (rank_attempts.py, raw profile deviation), Layer 2
gaps (l2_measure.py), the converter's id map, and the labels (label_attempts.py). Writes
the cut-offs and the development read-outs. Never reads a test pot.

  genuine    every sherd in its own place and the right way round
  near-miss  every sherd in its own place, at least one turned
  other      at least one sherd out of place

Usage: python scripts/u17_calibrate.py --root DIR --labels labels.json --pots P [P ...]
    --pot-mm 100 --rule calibration-fractura.md --out calib.json
  DIR/<pot>/ranks.json, DIR/<pot>_l2.json, DIR/<pot>/key/idmap.json
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from l2_report import auc, gaps  # noqa: E402
from rank_report import prereg_commit  # noqa: E402

TEST_POTS = {"narrow_bottle3", "galli_pot"}
Q = 99          # percentile of genuine attempts a cut-off must let through
IO_GATE = True  # --io-gate off: inside-out sherds reported, not failing (job 32159300)
UNJ_FAIL = False  # --unjudged fail: a sherd touching no neighbour fails (Revision 3)


def q(x, p):
    x = np.asarray(x, float)
    return round(float(np.percentile(x, p)), 3) if len(x) else None


def pot_rows(root, pot, labels, pot_mm):
    rk = {r["id"]: r for r in json.loads((root / pot / "ranks.json").read_text())["attempts"]}
    l2 = {r["id"]: r for r in json.loads((root / f"{pot}_l2.json").read_text())["attempts"]}
    idmap = json.loads((root / pot / "key" / "idmap.json").read_text())
    rows = []
    for aid, m in idmap.items():
        run = Path(m["run"]).parts[-4]
        lab = labels[(f"fractura_fresh/{pot}", run, m["attempt"])]
        cls = ("genuine" if lab["oriented"] == lab["n"] else
               "near" if lab["own"] == lab["n"] else "other")
        g = gaps(l2[aid])
        rows.append(dict(id=aid, cls=cls, profile=100 * rk[aid]["profile_mm"] / pot_mm,
                         io=len(rk[aid]["inside_out"]), unj=len(rk[aid].get("unjudged", [])),
                         gaps=g, worst=max(g)))
    return rows


def l1_ok(r, profile_pct):
    return (r["profile"] <= profile_pct and not (IO_GATE and r["io"])
            and not (UNJ_FAIL and r["unj"]))


def ranks(rows, key):
    order = sorted(rows, key=key)
    return [i for i, r in enumerate(order, 1) if r["cls"] == "genuine"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", required=True, type=Path)
    ap.add_argument("--labels", required=True, type=Path)
    ap.add_argument("--pots", required=True, nargs="+")
    ap.add_argument("--pot-mm", type=float, required=True)
    ap.add_argument("--rule", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--io-gate", choices=("on", "off"), default="on")
    ap.add_argument("--unjudged", choices=("report", "fail"), default="report")
    a = ap.parse_args()
    global IO_GATE, UNJ_FAIL
    IO_GATE, UNJ_FAIL = a.io_gate == "on", a.unjudged == "fail"
    if TEST_POTS & set(a.pots):
        sys.exit(f"test pots {TEST_POTS & set(a.pots)} must not be calibrated on")
    labels = {(r["pot"], r["run"], r["attempt"]): r
              for r in json.loads(a.labels.read_text())}
    pots = {p: pot_rows(a.root, p, labels, a.pot_mm) for p in a.pots}

    # the cut-offs, by the rule
    prof_q = {p: q([r["profile"] for r in rs if r["cls"] == "genuine" and np.isfinite(r["profile"])], Q)
              for p, rs in pots.items()}
    gap_q = {p: q([g for r in rs if r["cls"] == "genuine" for g in r["gaps"] if np.isfinite(g)], Q)
             for p, rs in pots.items()}
    profile_pct = max(v for v in prof_q.values() if v is not None)
    unfixable_pct = max(v for v in gap_q.values() if v is not None)
    print(f"rule {a.rule} @ {prereg_commit(a.rule)}")
    print(f"Layer 1 profile cut-off: {profile_pct:.2f}% of pot (per pot q{Q} of genuine: {prof_q})")
    print(f"Layer 2 unfixable cut-off: {unfixable_pct:.2f}% of pot (per pot q{Q}: {gap_q})")

    out = dict(io_gate=IO_GATE, unjudged_fail=UNJ_FAIL, rule=str(a.rule), rule_commit=prereg_commit(a.rule), q=Q,
               profile_pct=profile_pct, unfixable_pct=unfixable_pct,
               per_pot_profile_q=prof_q, per_pot_gap_q=gap_q, pots={})
    print(f"\n{'pot':15} cls      n   profile% q50/q90   inside-out  worst gap q50/q90  "
          f"pass L1  any unfixable")
    for p, rs in pots.items():
        d = {}
        for cls in ("genuine", "near", "other"):
            s = [r for r in rs if r["cls"] == cls]
            if not s:
                continue
            pf = [r["profile"] for r in s]
            wo = [r["worst"] for r in s]
            passed = [l1_ok(r, profile_pct) for r in s]
            unfix = [r["worst"] > unfixable_pct for r in s]
            d[cls] = dict(n=len(s), profile_q50=q(pf, 50), profile_q90=q(pf, 90),
                          inside_out_share=round(float(np.mean([r["io"] > 0 for r in s])), 3),
                          unjudged_share=round(float(np.mean([r["unj"] > 0 for r in s])), 3),
                          worst_q50=q(wo, 50), worst_q90=q(wo, 90),
                          pass_l1=round(float(np.mean(passed)), 3),
                          unfixable=round(float(np.mean(unfix)), 3))
            x = d[cls]
            print(f"{p:15} {cls:7} {x['n']:5}  {x['profile_q50']:6.2f} {x['profile_q90']:6.2f}"
                  f"      {x['inside_out_share']:5.3f}     {x['worst_q50']:6.2f} {x['worst_q90']:6.2f}"
                  f"     {x['pass_l1']:5.3f}   {x['unfixable']:5.3f}   unjudged {x['unjudged_share']:5.3f}")
        gen = [r["worst"] for r in rs if r["cls"] == "genuine"]
        near = [r["worst"] for r in rs if r["cls"] == "near"]
        d["auc_near_vs_genuine_worst"] = round(auc(near, gen), 3)
        l1 = ranks(rs, lambda r: (not l1_ok(r, profile_pct), r["profile"]))
        l12 = ranks(rs, lambda r: (not l1_ok(r, profile_pct), r["worst"], r["profile"]))
        d["best_genuine_rank_l1"], d["best_genuine_rank_l12"] = l1[0], l12[0]
        print(f"{'':15} near-miss vs genuine worst gap AUC {d['auc_near_vs_genuine_worst']}; "
              f"best genuine rank L1 {l1[0]}, L1+2 {l12[0]} of {len(rs)}")
        out["pots"][p] = d
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(out, indent=1))
    print(f"-> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
