"""Gate on the inside-out rule again, with a sherd-size guard (U17 ticket 11, key side).

The inside-out rule (check_inside_out.rule_flag, juglet-cause 14) caught both flipped
sherds the conservator saw on TORA's narrow_bottle3 top 5 and nothing else, but Revision 3
only reports it, because on correct attempts it misfires on a sherd that is most of the pot
(narrow_bottle4) and on small chips. Here the flag counts only on sherds whose share of the
pot's surface lies inside a size band, the band chosen on GARF's calibration pots by the
rule fixed in .scratch/attempt-ranker/preregistration-io-guard.md (its commit is printed),
then applied unchanged to every other pot.

Reads Layer 1 ranks (their `inside_out` lists, computed already), Layer 2 gaps, the id map,
the labels (with the turn limit, ticket 10) and each pot's sherds.npz for sherd sizes.

Usage: python scripts/u17_io_guard.py --prereg P --profile-pct 0.873 --calib garf-calibration \\
    --set garf-calibration ROOT BUNDLES LABELS blue_pot ... --set garf-test ... --out out.json
  ROOT/<pot>/ranks.json, ROOT/<pot>_l2.json, ROOT/<pot>/key/idmap.json; BUNDLES/<pot>/bundles/sherds.npz
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
LOS = (0.0, 2.0, 5.0, 10.0)            # % of the pot's surface
HIS = (20.0, 25.0, 30.0, 40.0, 50.0, 100.0)
MISFIRE = 1.0                           # % of genuine attempts a guarded flag may reject, per pot


def shares(npz):
    z = np.load(npz)
    area = []
    for j in range(int(z["k"])):
        v, f = z[f"v{j}"].astype(float), z[f"f{j}"]
        area.append(0.5 * np.linalg.norm(np.cross(v[f[:, 1]] - v[f[:, 0]],
                                                  v[f[:, 2]] - v[f[:, 0]]), axis=1).sum())
    area = np.array(area)
    return 100.0 * area / area.sum()


def load(root, bundles, labels_path, pot, profile_pct):
    labels = {(r["pot"], r["run"], r["attempt"]): r
              for r in json.loads(Path(labels_path).read_text())}
    rs = C.pot_rows(Path(root), pot, labels, 100.0)
    io = {r["id"]: r["inside_out"]
          for r in json.loads((Path(root) / pot / "ranks.json").read_text())["attempts"]}
    for r in rs:
        r["io_list"] = io[r["id"]]
        r["pass"] = C.l1_ok(r, profile_pct)
    return rs, shares(Path(bundles) / pot / "bundles" / "sherds.npz")


def flagged(r, sh, band):
    lo, hi = band
    return any(lo <= sh[j] <= hi for j in r["io_list"])


def rank(rs, sh, band):
    ok = (lambda r: r["pass"]) if band is None else (lambda r: r["pass"] and not flagged(r, sh, band))
    order = sorted(rs, key=lambda r: (not ok(r), r["worst"], r["profile"]))
    gen = [i for i, r in enumerate(order, 1) if r["cls"] == "genuine"]
    best = min(gen, default=None)
    return dict(kept=sum(ok(r) for r in rs), best_genuine=best,
                top5_hit=bool(best and best <= K), top5=[r["cls"] for r in order[:K]],
                top5_ids=[r["id"] for r in order[:K]],
                genuine_rejected=sum(r["cls"] == "genuine" and not ok(r) and r["pass"] for r in rs),
                near_rejected=sum(r["cls"] == "near" and not ok(r) and r["pass"] for r in rs))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--prereg", required=True, type=Path)
    ap.add_argument("--profile-pct", required=True, type=float)
    ap.add_argument("--calib", required=True, help="name of the --set that is calibration")
    ap.add_argument("--set", action="append", nargs="+", required=True,
                    help="NAME ROOT BUNDLES LABELS pot [pot ...]")
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    commit = prereg_commit(a.prereg)
    C.IO_GATE, C.UNJ_FAIL = False, True
    data = {(s[0], p): load(s[1], s[2], s[3], p, a.profile_pct) for s in a.set for p in s[4:]}
    print(f"pre-registration {a.prereg} @ {commit}; Revision 3 Layer 1 at {a.profile_pct}%")

    print("\n### calibration pots: sherd size (% of the pot's surface) and how often the rule "
          "flags it on genuine attempts")
    cal = {p: v for (n, p), v in data.items() if n == a.calib}
    for p, (rs, sh) in cal.items():
        gen = [r for r in rs if r["cls"] == "genuine"]
        rate = [100.0 * np.mean([j in r["io_list"] for r in gen]) if gen else float("nan")
                for j in range(len(sh))]
        print(f"{p:16} {len(gen):>5} genuine; " + "  ".join(
            f"{j}:{s:.0f}%/{x:.0f}%" for j, (s, x) in enumerate(zip(sh, rate))))

    grid = []
    for lo in LOS:
        for hi in HIS:
            worst = max(100.0 * np.mean([flagged(r, sh, (lo, hi)) for r in rs if r["cls"] == "genuine"])
                        for rs, sh in cal.values())
            judged = sum(int(((sh >= lo) & (sh <= hi)).sum()) for _, sh in cal.values())
            grid.append(dict(lo=lo, hi=hi, worst_misfire_pct=round(worst, 2), judged=judged))
    ok = [g for g in grid if g["worst_misfire_pct"] <= MISFIRE]
    band = None
    if ok:
        g = max(ok, key=lambda g: (g["judged"], g["hi"] - g["lo"]))
        band = (g["lo"], g["hi"])
    print(f"\nsize band chosen on calibration (misfire <= {MISFIRE}% of genuine on every pot, "
          f"most sherds judged): {band}")

    out = dict(prereg_commit=commit, band=band, grid=grid, pots={})
    print(f"\n{'set':18} {'pot':15} {'n':>4} {'gen':>4} {'rand5':>6}  {'rev':4} {'kept':>5} "
          f"{'best':>5} {'top5?':5} {'gen-x':>5} {'near-x':>6}  top 5")
    for (name, p), (rs, sh) in data.items():
        n, g = len(rs), sum(r["cls"] == "genuine" for r in rs)
        base = 1 - comb(n - g, K) / comb(n, K) if g else 0.0
        r3 = rank(rs, sh, None)
        rg = rank(rs, sh, band) if band else None
        out["pots"][f"{name}/{p}"] = dict(n=n, genuine=g, random_top5=round(base, 4),
                                          sherd_share_pct=[round(float(x), 1) for x in sh],
                                          rev3=r3, io_guard=rg)
        for tag, r in (("3", r3), ("io", rg)):
            if r is None:
                continue
            print(f"{name:18} {p:15} {n:>4} {g:>4} {100 * base:>5.1f}%  {tag:4} {r['kept']:>5} "
                  f"{r['best_genuine']!s:>5} {'YES' if r['top5_hit'] else 'no':5} "
                  f"{r['genuine_rejected']:>5} {r['near_rejected']:>6}  {r['top5']}")
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(out, indent=1))
    print(f"-> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
