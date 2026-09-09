"""Paired per-object comparison of the three arms. No pooled mean (intent/O2).

For each object we ask a question that survives differing fragment counts:
did this arm seat MORE of this object's sherds than that arm, fewer, or the same?
Then count objects. A sign test on the objects that changed.

Usage:
    python scripts/compare_lorav3_arms.py --runs artifacts/lorav3_29880370/runs
"""
import sys, math
from pathlib import Path
from collections import defaultdict
import numpy as np
sys.path.insert(0, "scripts")
from readout import read_run

import argparse
_ap = argparse.ArgumentParser(description=__doc__,
                              formatter_class=argparse.RawDescriptionHelpFormatter)
_ap.add_argument("--runs", type=Path,
                 default=Path("artifacts/lorav3_29880370/runs"),
                 help="directory holding the twelve fetched lorav3_* run dirs")
RUNS = _ap.parse_args().runs
ARMS = ["baseline", "adapter_off", "adapter_on"]
BONES = {"coxae", "limb3", "vert9"}

def per_object(dataset):
    out = {}
    for a in ARMS:
        d = defaultdict(list)
        for r in read_run(RUNS / f"lorav3_{dataset}_{a}_29880370"):
            d[r.object_name.split("/")[-1]].append(r)
        out[a] = {k: (float(np.mean([x.seated for x in v if x.seated >= 0])),
                      float(np.mean([x.turn_deg for x in v if not math.isnan(x.turn_deg)])),
                      v[0].n_fragments)
                  for k, v in d.items()}
    return out

def signtest(w, l):
    """two-sided exact binomial p at q=0.5 over the objects that changed"""
    n = w + l
    if n == 0: return float("nan")
    k = min(w, l)
    p = sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n
    return min(1.0, 2 * p)

for dataset, drop_bones in (("vessels", False), ("sweep", True), ("fresh", True)):
    P = per_object(dataset)
    names = sorted(P["baseline"])
    if drop_bones:
        names = [n for n in names if n.rpartition("_")[0] not in BONES and n not in BONES]
    print(f"\n{dataset.upper()}  ({len(names)} objects"
          + (", bones excluded)" if drop_bones else ")"))
    print(f"{'comparison':<28}{'better':>8}{'worse':>7}{'same':>6}{'sign p':>9}"
          f"{'mean turn change':>19}")
    for a, b in (("adapter_on", "baseline"), ("adapter_off", "baseline"),
                 ("adapter_on", "adapter_off")):
        w = l = s = 0; dturn = []
        for n in names:
            sa, ta, _ = P[a][n]; sb, tb, _ = P[b][n]
            if sa > sb + 1e-9: w += 1
            elif sa < sb - 1e-9: l += 1
            else: s += 1
            if not (math.isnan(ta) or math.isnan(tb)): dturn.append(ta - tb)
        print(f"{a+' vs '+b:<28}{w:>8}{l:>7}{s:>6}{signtest(w,l):>9.3f}"
              f"{np.mean(dturn):>+18.1f}d")
