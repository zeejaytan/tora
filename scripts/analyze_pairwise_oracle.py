"""Join TORA pairwise-oracle eval results with true-mate/non-mate adjacency labels.

Reads the per-pair result JSONs from a `sample.py` run against a pairs HDF5
built by `build_control_pairs_hdf5.py`, matches each sample's `name` field
(e.g. "pairs_synth/mode_5__p0102") against that build's adjacency JSON
(keyed "mode_5__p0102"), and reports true-mate vs. non-mate rotation_error /
part_accuracy — the assembly-level pairwise mating oracle, GARF Exp 6 style.

REWIRED 2026-09-05. The rotation errors now come from scripts/readout.py, the
one place a run is read. WHAT MOVED, and what did not:

  the absolute degrees DOUBLED. Every sample here is a PAIR, so k = 2, and
  `rotation_error` is summed over the non-anchor fragments and divided by all
  of them -- one free zero out of two. The stored figure is exactly half the
  turn on the fragment the model actually had to place. A "true mates mean
  rot_err 21" printed by the old version of this script was 42 degrees on the
  loose piece.

  the separation ratio did NOT move. It is a ratio of two rotation errors at
  the same k, so the x2.000 cancels exactly. Any DISCRIMINATES / NO CLEAR
  DISCRIMINATION verdict this script has ever printed still stands.

That is the distinction worth keeping straight: the ruler was wrong, and the
comparison it was used for happened to be immune. Reconciliation:
docs/notes/READOUT_RECONCILIATION.md.

Usage:
  python scripts/analyze_pairwise_oracle.py \\
    --results-dir eval_runs/pairs_synth_XXXXX/results \\
    --adjacency logs_pairs_synth_adjacency.json \\
    --label synthetic
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from readout import format_flags, read_run, weight  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results-dir", required=True)
    ap.add_argument("--adjacency", required=True)
    ap.add_argument("--label", default="")
    args = ap.parse_args()

    with open(args.adjacency) as f:
        adjacency = json.load(f)["pairs"]

    run_dir = Path(args.results_dir)
    if run_dir.name == "results":
        run_dir = run_dir.parent
    records = read_run(run_dir)
    if not records:
        raise SystemExit(f"no per-draw json under {run_dir}/results")

    by_pair = defaultdict(list)
    for rec in records:
        # names arrive as "pairs_synth/mode_5__p0102"; the adjacency file is
        # keyed on the second half only
        by_pair[rec.object_name.split("/")[-1]].append(rec)

    mate_rot, nonmate_rot = [], []
    mate_pa, nonmate_pa = [], []
    n_missing = 0
    for pair_key, samples in by_pair.items():
        if pair_key not in adjacency:
            n_missing += 1
            continue
        is_mate = adjacency[pair_key]["true_mate"]
        # best-of-N across generations for this pair (lower rot_err = better).
        # turn_deg is the turn on the ONE piece the model had to place; the
        # stored rotation_error is that halved by the free anchor.
        best_rot = min(x.turn_deg for x in samples)
        best_pa = max(x.seated / x.n_fragments for x in samples)
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
        print("  rot_err is the turn on the loose piece; the separation is a")
        print("  ratio at fixed k, so the free-anchor correction cancels in it.")

    for line in format_flags(records):
        print(f"  !! {line}")
    print(f"  Weight: {weight(records)}.")
    print()
    print("  A separation ratio is an index to a picture. Draw the pairs before")
    print("  quoting it:")
    print(f"    python scripts/render_assembly_grid.py \\")
    print(f'        --runs "{run_dir.name}={run_dir.as_posix()}/clouds" \\')
    print(f"        --out artifacts/{run_dir.name}.png")
    print()


if __name__ == "__main__":
    main()
