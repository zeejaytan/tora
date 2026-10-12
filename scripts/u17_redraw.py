"""Does the Juglet ranking survive a different point draw? (U17 ticket 03, re-draw test)

Layer 1 reads mesh vertices and has no random step; Layer 2 (l2_measure.py) resamples each
sherd's surface at random, by area. This re-orders the attempts exactly as the ranker does
(Layer 1 pass, then worst-sherd gap, then profile) once per Layer 2 point draw, and compares
each re-drawn top 5 with the original one. Read-outs and decision rule are fixed in
.scratch/attempt-ranker/preregistration-redraw.md, whose commit this prints.

The order is computed from the bundles' scores alone; the answer key (idmap + label report)
is read afterwards, only to say which places hold a genuine attempt.

Usage: python scripts/u17_redraw.py --ranks ranks.json --l2 ORIGINAL_l2.json
           --redraws seed3.json seed11.json ... --key idmap.json --report report.json
           --pot-mm 65 --prereg .scratch/attempt-ranker/preregistration-redraw.md --out redraw.json
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from l2_report import gaps, short  # noqa: E402
from rank_report import prereg_commit  # noqa: E402

K = 5


def order(rk, l2):
    worst = {i: max(gaps(r)) for i, r in l2.items()}
    ids = sorted(rk, key=lambda i: (not rk[i]["layer1_pass"], worst[i], rk[i]["profile_mm"]))
    return ids, worst


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    for k in ("ranks", "l2", "key", "report", "prereg", "out"):
        ap.add_argument(f"--{k}", required=True, type=Path)
    ap.add_argument("--redraws", required=True, nargs="+", type=Path)
    ap.add_argument("--pot-mm", type=float, required=True)
    a = ap.parse_args()
    commit = prereg_commit(a.prereg)

    rk = {r["id"]: r for r in json.loads(a.ranks.read_text())["attempts"]}

    def load(p):
        d = json.loads(p.read_text())
        l2 = {r["id"]: r for r in d["attempts"]}
        if set(l2) != set(rk):
            sys.exit(f"{p}: Layer 2 scores and Layer 1 ranks cover different attempts")
        return d.get("seed", 3), l2

    seed0, l2_0 = load(a.l2)
    ids0, w0 = order(rk, l2_0)
    top0 = ids0[:K]
    draws = []
    for p in a.redraws:
        seed, l2 = load(p)
        ids, w = order(rk, l2)
        pos = {i: n for n, i in enumerate(ids, 1)}
        common = [i for i in ids if i in w0 and np.isfinite(w[i]) and np.isfinite(w0[i])]
        dmm = np.abs(np.array([w[i] - w0[i] for i in common])) * a.pot_mm / 100.0
        draws.append(dict(file=str(p), seed=seed, top5=ids[:K],
                          shared_with_original=len(set(ids[:K]) & set(top0)),
                          original_top5_now_at=[pos[i] for i in top0],
                          worst_gap_change_mm=dict(median=round(float(np.median(dmm)), 4),
                                                   p90=round(float(np.percentile(dmm, 90)), 4),
                                                   max=round(float(dmm.max()), 4)),
                          _ids=ids))

    # key side, only now
    idmap = json.loads(a.key.read_text())
    rep = json.loads(a.report.read_text())
    where = {(short(v["run"]), v["attempt"]): aid for aid, v in idmap.items()}
    genuine = {where[(g["run"], g["attempt"])] for g in rep["genuine"]}

    def gen_read(ids):
        ranks = [n for n, i in enumerate(ids, 1) if i in genuine]
        return dict(genuine_ranks=ranks, top5_hit=bool(ranks and ranks[0] <= K),
                    top5_classes=["genuine" if i in genuine else "not" for i in ids[:K]])

    orig = dict(seed=seed0, top5=top0, **gen_read(ids0))
    for d in draws:
        d.update(gen_read(d.pop("_ids")))

    redrawn = [d for d in draws if d["seed"] != seed0]
    control = [d for d in draws if d["seed"] == seed0]
    control_ok = all(d["shared_with_original"] == K and d["top5"] == top0 for d in control)
    if not control_ok:
        verdict = "VOID: the same seed did not reproduce the original top 5 (broken measurement)"
    elif any(d["shared_with_original"] == 0 for d in redrawn):
        verdict = "REFUTED: a re-drawn top 5 shares nothing with the original (ranks the sampling)"
    elif all(d["shared_with_original"] >= 3 and d["top5_hit"] for d in redrawn):
        verdict = "PASS: every re-draw keeps >= 3 of the top 5 and a genuine attempt in it"
    else:
        verdict = "WEAKENED: neither pass nor refuted; see per-draw read-outs"

    out = dict(prereg=commit, pot_mm=a.pot_mm, units="mm", original=orig, draws=draws,
               control_reproduced=control_ok, verdict=verdict)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(out, indent=1))
    print(f"pre-registration {commit}")
    print(f"original (seed {seed0}): top 5 {orig['top5_classes']}, genuine ranks {orig['genuine_ranks']}")
    for d in draws:
        print(f"seed {d['seed']}: shared {d['shared_with_original']}/5, original top 5 now at "
              f"{d['original_top5_now_at']}, classes {d['top5_classes']}, genuine ranks "
              f"{d['genuine_ranks']}, worst-gap change mm {d['worst_gap_change_mm']}")
    print(verdict)
    return 0


if __name__ == "__main__":
    sys.exit(main())
