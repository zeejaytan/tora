"""Join TORA pairwise-oracle eval results with true-mate/non-mate adjacency labels.

Reads the per-pair result JSONs from a `sample.py` run against a pairs HDF5
built by `build_control_pairs_hdf5.py`, matches each sample's `name` field
(e.g. "pairs_synth/mode_5__p0102") against that build's adjacency JSON
(keyed "mode_5__p0102"), and reports true-mate vs. non-mate rotation_error /
part_accuracy — the assembly-level pairwise mating oracle, GARF Exp 6 style.

Usage:
  python scripts/analyze_pairwise_oracle.py \\
    --results-dir eval_runs/pairs_synth_XXXXX/results \\
    --adjacency logs_pairs_synth_adjacency.json \\
    --label synthetic
"""

import argparse
import glob
import json
from collections import defaultdict

import numpy as np


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results-dir", required=True)
    ap.add_argument("--adjacency", required=True)
    ap.add_argument("--label", default="")
    args = ap.parse_args()

    with open(args.adjacency) as f:
        adjacency = json.load(f)["pairs"]

    by_pair = defaultdict(list)
    files = sorted(glob.glob(f"{args.results_dir}/*.json"))
    for fp in files:
        with open(fp) as f:
            d = json.load(f)
        name = d["name"]  # e.g. "pairs_synth/mode_5__p0102"
        pair_key = name.split("/")[-1]  # "mode_5__p0102"
        by_pair[pair_key].append(d)

    mate_rot, nonmate_rot = [], []
    mate_pa, nonmate_pa = [], []
    n_missing = 0
    for pair_key, samples in by_pair.items():
        if pair_key not in adjacency:
            n_missing += 1
            continue
        is_mate = adjacency[pair_key]["true_mate"]
        # best-of-N across generations for this pair (lower rot_err = better)
        best_rot = min(s["rotation_error"] for s in samples)
        best_pa = max(s["part_accuracy"] for s in samples)
        (mate_rot if is_mate else nonmate_rot).append(best_rot)
        (mate_pa if is_mate else nonmate_pa).append(best_pa)

    def stats(x):
        return (np.mean(x), np.median(x)) if x else (float("nan"), float("nan"))

    mr_mean, mr_med = stats(mate_rot)
    nr_mean, nr_med = stats(nonmate_rot)
    mp_mean, mp_med = stats(mate_pa)
    np_mean, np_med = stats(nonmate_pa)

    print(f"\n=== Pairwise oracle: {args.label or args.results_dir} ===")
    print(f"  n pairs scored: {len(mate_rot) + len(nonmate_rot)} (missing from adjacency: {n_missing})")
    print(f"  true mates    (n={len(mate_rot):3d}): rot_err mean={mr_mean:6.2f} med={mr_med:6.2f}  part_acc mean={mp_mean:.3f} med={mp_med:.3f}")
    print(f"  non-mates     (n={len(nonmate_rot):3d}): rot_err mean={nr_mean:6.2f} med={nr_med:6.2f}  part_acc mean={np_mean:.3f} med={np_med:.3f}")
    if mate_rot and nonmate_rot:
        sep = nr_mean / mr_mean if mr_mean > 0 else float("inf")
        print(f"  separation (non-mate mean / true-mate mean rot_err): {sep:.2f}x")
        print(f"  {'DISCRIMINATES' if sep > 1.25 else 'NO CLEAR DISCRIMINATION'} (gate: >1.25x, mirroring GARF Exp 6/6b)")


if __name__ == "__main__":
    main()
