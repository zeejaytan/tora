"""Does "part accuracy" mean a fragment was placed correctly? Audit it per object.

Written after the Juglet exposed the problem and a render confirmed it. Against
the conservator's own reassembly the model scored part_accuracy 0.80 -- eight
fragments in ten "correctly placed" -- while the mean rotation error was 52.9
degrees and not one fragment of nine sat within ten degrees of correct. Drawing
the attempt settled it: the pot is not reassembled. The sherds fan outwards and
never close into a vessel.

part_accuracy passes a fragment on CHAMFER DISTANCE against a fixed threshold,
and chamfer distance stays small for a sherd sitting roughly in the right region
however it is turned. That is generous in a way that matters: a sherd rotated a
third of a right angle is visibly, uselessly wrong to anyone holding it, and
still passes.

This checks every other object, because the same measure is the headline for all
of them and two rounds of conclusions rest on it.

REWIRED 2026-09-05, AND ONE COLUMN WITHDRAWN. Every number now comes from
scripts/readout.py, the one place a run is read.

  turned moved. It was the stored `rotation_error`, which is summed over the
  non-anchor fragments and divided by all of them, so it carried a free zero.
  The correction is n/(n-1) -- x2.000 on a two-fragment object, x1.125 on the
  nine-sherd Juglet -- so it is a different factor in every row of a table
  built to compare objects. Reconciliation: docs/notes/READOUT_RECONCILIATION.md.

  within10 WAS DESCRIBED WRONGLY HERE, and the wrong description travelled.
  This file's docstring called it "fraction of fragments within ten degrees of
  correct orientation". It is nothing of the kind.
  `Evaluator._recall_at_thresholds` (tora/eval/evaluator.py:205) does
  `(metrics <= threshold).float()` on a per-OBJECT mean of shape (B,). So it is
  0 or 1 for a whole object on one draw: "did this pot's average turn come in
  under ten degrees?" -- and the average it thresholds is the diluted one, so
  the bar is easier to clear than it looks. Averaged over draws it is the SHARE
  OF ATTEMPTS in which the whole pot came in under ten degrees. It can never
  tell you how many sherds were oriented well, and a nine-sherd pot with eight
  sherds perfect and one turned 90 degrees scores 0. It is printed below as
  `pot<10d` for that reason.

  DISAGREEMENT is withdrawn. It subtracted within10 from part_accuracy: a
  per-object 0/1 taken away from a fraction of fragments. Those are not the
  same quantity and the difference was not a number. Anything quoting it should
  be reread -- docs/notes/WEAR_TEST_RESULTS.md quotes "recall@10 degrees flat at
  0.000" from this script, which is true as printed but does NOT mean "no
  fragment was within ten degrees"; it means no pot AVERAGED under ten degrees.
  The honest columns are seated (a count, with its free anchor named) and turned
  (degrees on the fragments the model had to place), and they are what this now
  compares models on.

WHAT IS REPORTED:

  seated      fragments seated, as a count, out of the fragment total
  free        fragments handed to the model already correct; it earns nothing
              for these, and a pot scoring exactly `free` placed nothing
  turned      mean turn in degrees on the fragments it had to place
  pot<10d     share of draws in which the WHOLE pot averaged under ten degrees
  gap         mean offset, as a fraction of the object

Ten degrees is not a strict bar. It is roughly the angle at which a sherd's join
visibly stops following the curve of the pot. A model within ten degrees on most
fragments would be genuinely useful to a conservator; one averaging thirty is
not.

Usage:
  python scripts/audit_placement_metrics.py --runs /path/to/eval_runs --job 29308186
"""

import argparse
import collections
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from readout import format_flags, read_run, weight  # noqa: E402


def mean(xs):
    xs = [x for x in xs if x == x]
    return sum(xs) / len(xs) if xs else float("nan")


def load_run(d):
    """Per-object means over the draws of one evaluation run, via the module."""
    per = collections.defaultdict(list)
    for rec in read_run(Path(d)):
        per[rec.object_name].append(rec)
    out = {}
    for name, recs in per.items():
        out[name] = dict(
            n_parts=recs[0].n_fragments,
            free=recs[0].floor,
            n_gen=len(recs),
            seated=mean([r.seated for r in recs]),
            turned=mean([r.turn_deg for r in recs]),
            # a per-object 0/1, so its mean over draws is a share of ATTEMPTS
            pot10=mean([r.pot_under(10) for r in recs]),
            gap=mean([r.gap_object_fraction for r in recs]),
            records=recs,
        )
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", required=True)
    ap.add_argument("--job", required=True)
    args = ap.parse_args()

    sets = [("FRESH held-out objects", "fresh"),
            ("WORN sweep", "sweep"),
            ("THE JUGLET vs the hand assembly", "jugletgt")]
    models = ["baseline", "wear_v1", "wear_v2"]

    seen_dirs = []
    for label, key in sets:
        print()
        print("=" * 100)
        print(label)
        print("=" * 100)
        data = {}
        for mdl in models:
            d = Path(args.runs) / ("wearft2_" + key + "_" + mdl + "_" + args.job)
            if d.exists():
                data[mdl] = load_run(d)
                seen_dirs.append(d)
        if not data:
            print("  no runs found")
            continue

        objs = sorted({o for v in data.values() for o in v})
        head = ("  {:<32s} {:>5s} {:<10s} {:>8s} {:>5s} {:>8s} {:>9s} {:>8s}"
                .format("object", "parts", "model", "seated", "free", "turned",
                        "pot<10d", "gap"))
        print(head)
        print("  " + "-" * 96)
        for o in objs:
            for mdl in models:
                r = data.get(mdl, {}).get(o)
                if not r:
                    continue
                print("  {:<32s} {:>5d} {:<10s} {:>8.1f} {:>5d} {:>7.1f}d {:>9.3f} "
                      "{:>8.3f}".format(
                          o.split("/")[-1][:31], r["n_parts"], mdl,
                          r["seated"], r["free"], r["turned"],
                          r["pot10"], r["gap"]))
            print()

        print("  MEAN over objects")
        for mdl in models:
            v = data.get(mdl)
            if not v:
                continue
            print("    {:<10s} seated {:.1f} of {:.1f} ({:.1f} free)   "
                  "turned {:.1f}d   pot<10d {:.3f}".format(
                      mdl,
                      mean([x["seated"] for x in v.values()]),
                      mean([float(x["n_parts"]) for x in v.values()]),
                      mean([float(x["free"]) for x in v.values()]),
                      mean([x["turned"] for x in v.values()]),
                      mean([x["pot10"] for x in v.values()])))

        pooled = [rec for v in data.values() for x in v.values()
                  for rec in x["records"]]
        for line in format_flags(pooled):
            print(f"  !! {line}")
        print(f"  Weight: {weight(pooled)}.")

    print()
    print("=" * 100)
    print("HOW TO READ THIS")
    print("  seated is a COUNT of fragments, with the free anchor named beside")
    print("  it. A pot whose seated count equals its free count had nothing")
    print("  placed by the model at all.")
    print()
    print("  pot<10d is per POT, not per fragment: the share of attempts in")
    print("  which the whole pot averaged under ten degrees. Zero does not mean")
    print("  no fragment was close; it means no attempt averaged close.")
    print()
    print("  Compare models on SEATED and TURNED. Those are physical quantities")
    print("  a threshold cannot inflate.")
    print()
    print("  Then draw them. A table of degrees is an index to a picture:")
    for d in seen_dirs:
        print(f"    python scripts/render_assembly_grid.py \\")
        print(f'        --runs "{d.name}={d.as_posix()}/clouds" \\')
        print(f"        --out artifacts/{d.name}.png")
    print()


if __name__ == "__main__":
    main()
