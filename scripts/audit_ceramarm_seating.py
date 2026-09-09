"""Own-place vs relabelled seating for the three-arm ceramics run, per pot per rung.

Job 30337242 evaluated eight real Fractura pots at five wear rungs on three
arms (adapter_on / adapter_off / baseline), 20 draws each.

Why this exists. The seating figure the job prints comes from
`compute_part_acc`, which runs the Hungarian assignment over the sherd-to-sherd
chamfer matrix: sherds may be RELABELLED to whichever pairing passes most of
them, so a sherd standing in another sherd's place is credited. That is the
published number and it is not wrong, but it is not what a conservator means by
"that piece is in the right place". This script prints both, plus the free
anchor, so the three can never be quoted as one number.

No pooled mean: every row is one pot at one rung (intent/O2).

Usage:
    python scripts/audit_ceramarm_seating.py --runs artifacts/ceramarm_30337242
"""
import sys, argparse, json
from pathlib import Path
import numpy as np
from scipy.optimize import linear_sum_assignment
sys.path.insert(0, "scripts")
from readout import chamfer, unit_box_scale, TAU
from check_identity_swap import pct

ARMS = ["adapter_on", "adapter_off", "baseline"]

ap = argparse.ArgumentParser(description=__doc__,
                             formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--runs", type=Path, default=Path("artifacts/ceramarm_30337242"))
ap.add_argument("--json-out", type=Path,
                default=Path("artifacts/ceramarm_30337242/seating_audit.json"))
ap.add_argument("--rungs", default="e000,e100",
                help="which rungs to score; the two ends are enough to show relabelling")
ap.add_argument("--cap", type=int, default=500,
                help="points per sherd. 500 reproduces the 1200-point verdict on "
                     "blue_pot and pink_bowl and runs ~6x faster.")
args = ap.parse_args()
CAP = args.cap
RUNGS = tuple(args.rungs.split(","))

def score(npz):
    z = np.load(npz, allow_pickle=True)
    gt, ids, pred = z["pts_gt"], z["part_ids"], z["generations_pred"]
    unit = unit_box_scale(gt)
    parts = sorted(set(ids.tolist()))
    anchor = max(parts, key=lambda p: int((ids == p).sum()))
    G = [gt[ids == p][:CAP] / unit for p in parts]
    own, hung = [], []
    for d in range(pred.shape[0]):
        Q = [pred[d][ids == p][:CAP] / unit for p in parts]
        C = np.array([[chamfer(G[i], Q[j]) for j in range(len(parts))]
                      for i in range(len(parts))])
        own.append(int(sum(C[i, i] < TAU for i in range(len(parts)))))
        r, c = linear_sum_assignment((C >= TAU).astype(float))
        hung.append(int((C[r, c] < TAU).sum()))
    return dict(name=str(z["name"]), n=len(parts), anchor=int(anchor),
                own=own, hung=hung, scale=float(z["scale"]))

rows = {}
for arm in ARMS:
    for npz in sorted((args.runs / arm / "clouds").glob("*.npz")):
        # read only the label first: scoring every rung costs hours and the two
        # ends of a ladder are what the relabelling question needs.
        if not str(np.load(npz, allow_pickle=True)["name"]).endswith(RUNGS):
            continue
        r = score(npz)
        rows.setdefault(r["name"].split("/")[-1], {})[arm] = r

print(f"seated = both sherds within {pct(TAU):.2f}% of pot size (tau={TAU}, unit box)")
print("own  = sherd p judged against sherd p, the conservator's question")
print("hung = Hungarian relabelling, the number the job prints")
print("both include the ONE free anchor, held at truth\n")
print(f"{'pot / rung':24s} {'n':>2s} {'':>3s} " +
      "  ".join(f"{a:>16s}" for a in ARMS))
print(f"{'':24s} {'':>2s} {'':>3s} " + "  ".join(f"{'own  hung':>16s}" for a in ARMS))
for pot in sorted(rows):
    r = rows[pot]
    cells = []
    for a in ARMS:
        if a in r:
            cells.append(f"{np.median(r[a]['own']):5.1f}{np.median(r[a]['hung']):7.1f}   ")
        else:
            cells.append(f"{'--':>16s}")
    n = r[ARMS[0]]["n"]
    print(f"{pot:24s} {n:2d} {'':>3s} " + "".join(cells))

args.json_out.parent.mkdir(parents=True, exist_ok=True)
args.json_out.write_text(json.dumps(rows, indent=1))
print(f"\nwritten: {args.json_out}")
