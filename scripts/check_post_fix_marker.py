"""Assert that a run's result files were scored by today's evaluator, not a stale one.

Written 2026-09-07, after the mistake it exists to prevent.

`part_accuracy` changed meaning on 2026-09-02 (commit `0d6a85f`): it had been a
fixed absolute chamfer threshold, which is generous in proportion to how small
the object is, and became a threshold in the unit-box frame, which is not. The
field kept its name. Nothing in a result file announced the change, and nothing
complained when a table built from 2026-08-17 runs was compared against a
2026-09-07 run as though the two numbers were the same quantity. They are not:
on `coxae` the same ten draws score 0.950 on the old ruler and 0.050 on the new.

`readout.py` already knows how to tell them apart -- `POST_FIX_MARKER =
"part_accuracy_absolute"`, a field only the post-fix evaluator writes. The flag
worked. It was bypassed because the comparison was made against a number quoted
in a document, which has no provenance attached to it at all.

So this is the gate version of that flag: run it inside the job, on the job's
own first output, before any GPU time goes into the remaining runs. A prose rule
did not stop this happening once; a check that exits non-zero will.

Usage:
    python scripts/check_post_fix_marker.py <run_dir>            # exits 1 on failure
    python scripts/check_post_fix_marker.py <run_dir> --warn     # reports, exits 0
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from readout import POST_FIX_MARKER  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("run_dir", help="an eval_runs/<name> directory")
    ap.add_argument("--warn", action="store_true",
                    help="report and exit 0 instead of failing the job")
    args = ap.parse_args()

    results = Path(args.run_dir) / "results"
    files = sorted(results.glob("*_generation*.json"))
    if not files:
        print(f"FAIL: no result files under {results} -- nothing to check")
        return 0 if args.warn else 1

    entry = json.loads(files[0].read_text())
    if POST_FIX_MARKER not in entry:
        print(f"FAIL: `{POST_FIX_MARKER}` missing from {files[0].name}.")
        print("      This run was scored by a PRE-0d6a85f evaluator, so its")
        print("      `part_accuracy` is the retired size-dependent score and is")
        print("      NOT comparable with anything measured since 2026-09-02.")
        return 0 if args.warn else 1

    new = float(entry.get("part_accuracy", float("nan")))
    old = float(entry.get(POST_FIX_MARKER, float("nan")))
    print(f"PASS: `{POST_FIX_MARKER}` present -- unit-box scoring is in force.")
    print(f"      {files[0].name}: part_accuracy {new:.4f}  "
          f"(old ruler would have said {old:.4f})")
    if old > new:
        print("      The old ruler is the more generous one here, as expected on "
              "a small object.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
