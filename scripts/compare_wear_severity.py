"""Put the training wear and the evaluation wear on ONE ruler: gap ratio.

The conservator's model (docs/notes/WEAR_SIMULATION.md §2) is that wear is
material loss at three scales -- asperities (reads as smoothing), the mating
surface (reads as joins opening), chunks (chipping) -- and that these are ONE
severity axis, not different kinds of damage. `wear_ops.wear_to_loss` encodes
exactly that: it smooths first, then RECEDES to reach a target gap ratio, "so an
object whose surface will not smooth any further still reaches the intended
degree of wear, via loss at a larger scale."

If that is the model, then severity has one unit -- how far the joins have opened
-- and both datasets can be placed on it.

They never were. They were dosed on different rulers and never compared:

  bbad_vessels   dosed by RECESSION FRACTION (0.0005, 0.0010), checked against
                 the relief curve
  erosion_sweep  dosed by MOLLIFIER STRENGTH (0..1), calibrated by relief_p90
                 in erosion_sweep.calibration.json

Neither file records a gap ratio, so nobody has ever been able to say whether
the adapter was trained harder or softer than it was tested. That is what this
measures, with `joint_gap` lifted unchanged from `diagnose_recession.py` so the
instrument is the one already used on this question.

Reports gap in PERCENT OF OBJECT SIZE, and the ratio worn/fresh, which is the
unit `wear_to_loss(target_gap_ratio=...)` is written in.

Usage:
  python scripts/compare_wear_severity.py \
      --src dataset/bbad_vessels.hdf5   --dataset bbad_vessels   --limit 12 \
      --src dataset/erosion_sweep.hdf5  --dataset erosion_sweep  --limit 12
"""

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

import h5py
import numpy as np
from scipy.spatial import cKDTree


def load_parts(grp):
    pg = grp["pieces"]
    keys = sorted(pg.keys(), key=lambda s: int(s) if s.isdigit() else s)
    return [np.asarray(pg[k]["vertices"][:], dtype=np.float64) for k in keys]


def joint_gap(parts, max_pts=40000, seed=0):
    """10th-percentile distance from each piece to its nearest neighbour piece.

    Lifted from diagnose_recession.py unchanged. The 10th percentile picks the
    CONTACT, not the far side of the sherd.
    """
    rng = np.random.default_rng(seed)
    subs = [v if len(v) <= max_pts else v[rng.choice(len(v), max_pts, replace=False)]
            for v in parts]
    trees = [cKDTree(s) for s in subs]
    out = []
    for i, s in enumerate(subs):
        best = np.full(len(s), np.inf)
        for j, t in enumerate(trees):
            if i != j:
                d, _ = t.query(s, workers=-1)
                best = np.minimum(best, d)
        out.append(float(np.percentile(best, 10)))
    return float(np.mean(out))


def coincident_frac(parts, max_pts=40000, seed=0, tol=1e-9):
    """Fraction of each piece's vertices lying EXACTLY on another piece.

    Fragments cut from a single mesh share their mating vertices, so this is
    roughly the contact band. Fragments from separate real scans never do, so
    this is 0 and the join carries genuine slop. It is the cleanest single
    number for "was this break simulated by cutting, or observed".
    """
    rng = np.random.default_rng(seed)
    subs = [v if len(v) <= max_pts else v[rng.choice(len(v), max_pts, replace=False)]
            for v in parts]
    trees = [cKDTree(s) for s in subs]
    out = []
    for i, s in enumerate(subs):
        best = np.full(len(s), np.inf)
        for j, t in enumerate(trees):
            if i != j:
                d, _ = t.query(s, workers=-1)
                best = np.minimum(best, d)
        out.append(float(np.mean(best <= tol)))
    return float(np.mean(out))


def object_size(parts):
    allv = np.concatenate(parts, axis=0)
    return float(np.linalg.norm(allv.max(0) - allv.min(0))) + 1e-12


# tag -> (object_key, variant). Fresh variant sorts first by construction.
PATTERNS = [
    re.compile(r"^(?P<obj>.+)_e(?P<lvl>\d{3})$"),        # erosion_sweep
    re.compile(r"^(?P<obj>.+?)__(?P<lvl>fresh|worn_\w+?)(?:__.*)?$"),  # bbad
]


def split_tag(tag):
    for p in PATTERNS:
        m = p.match(tag)
        if m:
            return m.group("obj"), m.group("lvl")
    return None, None


def run(src, dataset, limit):
    h = h5py.File(src, "r")
    dg = h[dataset]
    groups = defaultdict(dict)
    for tag in dg.keys():
        obj, lvl = split_tag(tag)
        if obj is None:
            continue
        groups[obj].setdefault(lvl, tag)

    usable = [o for o, v in groups.items()
              if ("fresh" in v or "000" in v) and len(v) > 1]
    usable.sort()
    if limit and len(usable) > limit:
        step = max(1, len(usable) // limit)
        usable = usable[::step][:limit]

    print(f"\n{'='*74}\n{dataset}   ({len(groups)} objects, measuring {len(usable)})\n{'='*74}")
    rows = defaultdict(list)
    for n, obj in enumerate(usable):
        v = groups[obj]
        base_lvl = "fresh" if "fresh" in v else "000"
        try:
            parts0 = load_parts(dg[v[base_lvl]])
            if len(parts0) < 2:
                continue
            size = object_size(parts0)
            g0 = joint_gap(parts0)
            c0 = coincident_frac(parts0)
        except Exception as e:                       # noqa: BLE001
            print(f"  skip {obj}: {e}")
            continue
        for lvl, tag in sorted(v.items()):
            if lvl == base_lvl:
                rows[lvl].append((100 * g0 / size, 1.0, c0))
                continue
            try:
                parts = load_parts(dg[tag])
                g = joint_gap(parts)
            except Exception as e:                   # noqa: BLE001
                print(f"  skip {obj}/{lvl}: {e}")
                continue
            ratio = (g / g0) if g0 > 1e-12 else float("nan")
            rows[lvl].append((100 * g / size, ratio, coincident_frac(parts)))
        if (n + 1) % 5 == 0:
            print(f"  {n + 1}/{len(usable)}", flush=True)

    print(f"\n  {'level':<16} {'n':>3}  {'gap % of object':>16}  {'ratio':>9}  {'coincident':>12}")
    print(f"  {'-'*16} {'-'*3}  {'-'*16}  {'-'*9}  {'-'*12}")
    for lvl in sorted(rows):
        pct = np.array([r[0] for r in rows[lvl]])
        rat = np.array([r[1] for r in rows[lvl]])
        coi = np.array([r[2] for r in rows[lvl]])
        rs = "undefined" if np.all(np.isnan(rat)) else f"{np.nanmedian(rat):.3f}"
        print(f"  {lvl:<16} {len(pct):>3}  {np.median(pct):>12.4f}    "
              f"  {rs:>9}  {100*np.median(coi):>10.2f} %")
    print("\n  ratio is undefined where the fresh gap is exactly 0 -- fragments cut")
    print("  from one mesh share their mating vertices, so there is no gap to open")
    print("  RELATIVE to. Compare the absolute column in that case.")
    h.close()
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", action="append", required=True)
    ap.add_argument("--dataset", action="append", required=True)
    ap.add_argument("--limit", type=int, default=12)
    args = ap.parse_args()
    if len(args.src) != len(args.dataset):
        sys.exit("--src and --dataset must be given the same number of times")
    for s, d in zip(args.src, args.dataset):
        if not Path(s).exists():
            print(f"missing: {s}")
            continue
        run(s, d, args.limit)
    print("\nGap ratio is the unit wear_to_loss(target_gap_ratio=...) is written "
          "in.\nIf the two sets sit at different ratios, they are different "
          "SEVERITIES of\nthe same wear, and the adapter was not tested at the "
          "level it was trained at.")


if __name__ == "__main__":
    main()
