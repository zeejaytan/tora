"""Did the sherds we KEPT still go to the right place when one sherd was gone?

Ticket .scratch/juglet-cause/issues/04. The Juglet is missing a piece; none of
the eight Fractura pots TORA reassembles is missing anything. This reads the
runs that test whether that difference matters.

WHAT IS NOT REPORTED, AND WHY. No whole-assembly score. A missing fragment
deflates any score computed over the whole pot automatically, and quoting that
would confuse absence with failure. Every column here is over the fragments
that were present in that run, scored against their own reference poses.

THE CONFOUND, NAMED. Removing a fragment does not leave the others untouched:
the 5000-point budget is shared out by area, so every kept sherd is re-sampled,
and the pot is re-centred and re-normalised on what remains. That is not a bug
to be suppressed -- it is what a genuinely incomplete pot does -- but it means
"dropped differs from whole" is not by itself a finding. Two controls bound it:

  reseed   the same whole pot, drawn again with a different sampler seed. Any
           difference here is the sampler, not the missing sherd. This is the
           floor a real effect has to clear.
  size     removing a sherd also removes a sherd to place, and fewer pieces is
           an EASIER task. So the direction is what carries the argument:

             graceful degradation -> the kept sherds score the SAME or BETTER,
                                     because the job got smaller.
             destabilisation      -> the kept sherds score WORSE, even though
                                     the job got smaller. Absence actively
                                     misplaces pieces that are present.

Only the second is a reason to make generative completion load-bearing.

Usage:
  python scripts/summarise_fragment_drop.py \
      --whole eval_runs/drop_whole_<jobid> \
      --reseed eval_runs/drop_reseed_<jobid> \
      --dropped eval_runs/drop_rank2_<jobid> eval_runs/drop_rank3_<jobid>
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np

from readout import read_run


def by_object(run_dir):
    """{object: (median turn, median earned-seated, n fragments, n draws)}."""
    recs = read_run(Path(run_dir))
    out = {}
    for r in recs:
        out.setdefault(r.object_name, []).append(r)
    return {
        name: (
            float(np.median([r.turn_deg for r in rs])),
            float(np.median([r.seated - r.n_anchors for r in rs])),
            rs[0].n_fragments,
            len(rs),
        )
        for name, rs in out.items()
    }


def short(name):
    return str(name).split("/")[-1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--whole", required=True)
    ap.add_argument("--reseed", required=True)
    ap.add_argument("--dropped", nargs="+", required=True)
    a = ap.parse_args()

    whole = by_object(a.whole)
    reseed = by_object(a.reseed)
    dropped = {Path(d).name: by_object(d) for d in a.dropped}

    # The noise floor: the same pot, nothing removed, drawn twice.
    floor = []
    print("Control -- the same whole pot, sampled twice. Nothing was removed,")
    print("so every difference below is the sampler and sets the floor.\n")
    print(f"{'pot':22s} {'frags':>5s} {'turn A':>8s} {'turn B':>8s} {'move':>8s}")
    print("-" * 56)
    for name in sorted(whole):
        if name not in reseed:
            continue
        ta, tb = whole[name][0], reseed[name][0]
        floor.append(abs(ta - tb))
        print(f"{short(name):22s} {whole[name][2]:5d} {ta:8.1f} {tb:8.1f} "
              f"{abs(ta - tb):8.1f}")
    if not floor:
        raise SystemExit("no pot appears in both the whole and reseed runs")
    bar = float(np.median(floor))
    worst = float(np.max(floor))
    print(f"\nnoise floor: median {bar:.1f} deg between two draws of the same "
          f"unchanged pot, worst {worst:.1f} deg")
    print("A drop that moves a pot less than this has not been shown to move "
          "it at all.\n")

    for label, tab in dropped.items():
        print("=" * 96)
        print(f"{label}: one sherd removed. Scored on the sherds that REMAIN.")
        print("=" * 96)
        print(f"{'pot':22s} {'frags':>5s} {'->':>3s} {'turn whole':>11s} "
              f"{'turn kept':>10s} {'change':>8s} {'reading':>16s}")
        print("-" * 96)
        deltas = []
        for name in sorted(tab):
            if name not in whole:
                continue
            tw, sw, nw, _ = whole[name]
            td, sd, nd, _ = tab[name]
            d = td - tw
            deltas.append(d)
            if abs(d) < bar:
                reading = "no change"
            elif d > 0:
                reading = "WORSE"
            else:
                reading = "better"
            print(f"{short(name):22s} {nw:5d} {nd:3d} {tw:11.1f} {td:10.1f} "
                  f"{d:+8.1f} {reading:>16s}")
        if not deltas:
            print("  no pot in common with the whole run")
            continue
        deltas = np.array(deltas)
        med = float(np.median(deltas))
        n_worse = int((deltas > bar).sum())
        n_better = int((deltas < -bar).sum())
        print(f"\n  median change {med:+.1f} deg against a {bar:.1f} deg floor; "
              f"{n_worse} pots worse, {n_better} better, "
              f"{len(deltas) - n_worse - n_better} unmoved")
        if med > bar and n_worse > n_better:
            print("  READING: DESTABILISATION. The kept sherds went to worse")
            print("  places even though losing a fragment made the task smaller.")
        elif abs(med) <= bar:
            print("  READING: GRACEFUL DEGRADATION. Losing a sherd did not move")
            print("  the ones that remain; the model seats what it has.")
        else:
            print("  READING: GRACEFUL DEGRADATION, and the task got easier --")
            print("  the kept sherds improved, which is what one fewer piece to")
            print("  place buys. Absence did not misplace what was present.")
        print()

    print("Before quoting any of this, LOOK at the renders: whether the vessel")
    print("still closes is not in any of these columns.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
