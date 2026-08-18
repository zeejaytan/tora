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

WHAT IS REPORTED:

  seated      part_accuracy, the measure under suspicion
  turned      mean rotation error in degrees -- the physical quantity
  within10    fraction of fragments within ten degrees of correct orientation
  gap         mean translation error

  DISAGREEMENT is the column that matters: the "seated" figure minus the share
  actually oriented correctly. Near zero and the headline describes placement.
  Near the headline value itself and it describes almost nothing -- the
  fragments passed on chamfer distance while being turned the wrong way.

Ten degrees is not a strict bar. It is roughly the angle at which a sherd's join
visibly stops following the curve of the pot. A model within ten degrees on most
fragments would be genuinely useful to a conservator; one averaging thirty is
not.

Usage:
  python scripts/audit_placement_metrics.py --runs /path/to/eval_runs --job 29308186
"""

import argparse
import collections
import json
from pathlib import Path


def load_run(d):
    """Per-object means over the generations of one evaluation run."""
    per = collections.defaultdict(list)
    for f in sorted(Path(d).glob("results/*.json")):
        try:
            r = json.load(open(f))
        except Exception:
            continue
        per[r.get("name", f.stem)].append(r)
    out = {}
    for name, rs in per.items():
        def m(k):
            v = [r[k] for r in rs if k in r and r[k] is not None]
            return sum(v) / len(v) if v else float("nan")
        out[name] = dict(n_parts=rs[0].get("num_parts", 0), n_gen=len(rs),
                         seated=m("part_accuracy"), turned=m("rotation_error"),
                         within10=m("recall_at_10deg"), within5=m("recall_at_5deg"),
                         gap=m("translation_error"), cd=m("object_chamfer"))
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
        if not data:
            print("  no runs found")
            continue

        objs = sorted({o for v in data.values() for o in v})
        head = ("  {:<32s} {:>5s} {:<10s} {:>8s} {:>8s} {:>9s} {:>8s} {:>13s}"
                .format("object", "parts", "model", "seated", "turned",
                        "within10", "gap", "DISAGREEMENT"))
        print(head)
        print("  " + "-" * 96)
        for o in objs:
            for mdl in models:
                r = data.get(mdl, {}).get(o)
                if not r:
                    continue
                dis = r["seated"] - r["within10"]
                print("  {:<32s} {:>5d} {:<10s} {:>8.3f} {:>7.1f}d {:>9.3f} "
                      "{:>8.3f} {:>13.3f}".format(
                          o.split("/")[-1][:31], r["n_parts"], mdl,
                          r["seated"], r["turned"], r["within10"],
                          r["gap"], dis))
            print()

        print("  MEAN over objects")
        for mdl in models:
            v = data.get(mdl)
            if not v:
                continue
            n = len(v)
            s = sum(x["seated"] for x in v.values()) / n
            t = sum(x["turned"] for x in v.values()) / n
            w = sum(x["within10"] for x in v.values()) / n
            print("    {:<10s} seated {:.3f}   turned {:.1f}d   "
                  "within10 {:.3f}   DISAGREEMENT {:.3f}".format(
                      mdl, s, t, w, s - w))

    print()
    print("=" * 100)
    print("HOW TO READ THIS")
    print("  DISAGREEMENT is the share of fragments counted as correctly placed")
    print("  minus the share actually oriented within ten degrees. Near zero and")
    print("  the headline number describes placement. Near the headline value")
    print("  itself and it describes almost nothing.")
    print()
    print("  Compare models on TURNED and WITHIN10, not on SEATED. Those are")
    print("  physical quantities a threshold cannot inflate.")


if __name__ == "__main__":
    main()
