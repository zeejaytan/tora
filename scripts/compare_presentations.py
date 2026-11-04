"""Does one sampling seed hand every run the same presentation? (wear-beyond-juglet 06, U3)

A presentation is what the model is given: the points sampled on each sherd and each
sherd's random input turn. sample.py's FlowVisualizationCallback saves both per object in
<run>/clouds/<object>.npz: pts_gt (sampled points at home, in the order fed) and pts_input
(the same points after centring and the input turn). This compares run A against each
other run, object by object, and reports:
  - byte-identical: pts_gt, pts_input, points_per_part equal to the last bit;
  - max point difference, index for index (as fed), in the npz's normalised units and
    times the stored `scale` (the HDF5's units; CSC sets are in mm);
  - as sets: the largest nearest-neighbour distance of B's pts_gt from A's, which is ~0
    when the same points come in a different order and ~one point spacing when resampled;
  - the attempts' own-place counts (solid block) from each run's own_place.json, equal or not.
Reports only; it decides nothing.

  python scripts/compare_presentations.py RUN_A RUN_B [RUN_C ...] [--objects p328_d01 ...]
"""
import argparse, json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree


def clouds(run: Path) -> dict:
    return {str(np.load(f, allow_pickle=True)["name"]).split("/")[-1]: f
            for f in sorted(run.glob("**/clouds/*.npz"))}


def owns(run: Path) -> dict:
    f = run / "own_place.json"
    if not f.exists():
        return {}
    return {k.split("/")[-1]: [d["own"] for d in v["solid"]] for k, v in json.loads(f.read_text()).items()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+", type=Path)
    ap.add_argument("--objects", nargs="*", default=None)
    a = ap.parse_args()
    base, others = a.runs[0], a.runs[1:]
    ca, oa = clouds(base), owns(base)
    names = a.objects or sorted(ca)
    print(f"A = {base}")
    for run in others:
        cb, ob = clouds(run), owns(run)
        print(f"\nB = {run}")
        print("  object     pts_gt=  pts_input=  ppp=  max|dgt| (x scale)    max|din| (x scale)    "
              "set NN max (x scale)   own counts equal")
        tally = {"gt": 0, "in": 0, "own": 0, "n": 0}
        for n in names:
            if n not in ca or n not in cb:
                print(f"  {n:<10} missing in {'A' if n not in ca else 'B'}")
                continue
            A, B = np.load(ca[n], allow_pickle=True), np.load(cb[n], allow_pickle=True)
            s = float(A["scale"]) if "scale" in A.files else 1.0
            same_ppp = np.array_equal(A["points_per_part"], B["points_per_part"])
            eq_gt = same_ppp and np.array_equal(A["pts_gt"], B["pts_gt"])
            eq_in = same_ppp and np.array_equal(A["pts_input"], B["pts_input"])
            if A["pts_gt"].shape == B["pts_gt"].shape:
                dgt = float(np.abs(A["pts_gt"] - B["pts_gt"]).max())
                din = float(np.abs(A["pts_input"] - B["pts_input"]).max())
            else:
                dgt = din = float("nan")
            nn = float(cKDTree(A["pts_gt"]).query(B["pts_gt"])[0].max())
            own_eq = (oa.get(n) == ob.get(n)) if n in oa and n in ob else None
            tally["gt"] += eq_gt; tally["in"] += eq_in; tally["own"] += bool(own_eq); tally["n"] += 1
            print(f"  {n:<10} {str(eq_gt):<7}  {str(eq_in):<10}  {str(same_ppp):<5} "
                  f"{dgt:.3g} ({dgt * s:.3g})   {din:.3g} ({din * s:.3g})   {nn:.3g} ({nn * s:.3g})   "
                  f"{own_eq}")
        print(f"  summary: pts_gt identical {tally['gt']}/{tally['n']}, pts_input identical "
              f"{tally['in']}/{tally['n']}, own counts equal {tally['own']}/{tally['n']}")
        if names:
            s = float(np.load(ca[names[0]], allow_pickle=True).get("scale", 1.0))
            g = np.load(ca[names[0]], allow_pickle=True)["pts_gt"]
            print(f"  units check: {names[0]} pts_gt longest side {np.ptp(g, axis=0).max() * s:.1f} "
                  f"(x scale {s:.4g})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
