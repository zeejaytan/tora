"""Did the sherds we KEPT still go to the right place when one sherd was gone?

Ticket .scratch/juglet-cause/issues/04. The Juglet is missing a piece; none of
the eight Fractura pots TORA reassembles is missing anything. This reads the
runs that test whether that difference matters.

WHAT IS NOT REPORTED, AND WHY. No whole-assembly score. A missing fragment
deflates any score computed over the whole pot automatically, and quoting that
would confuse absence with failure. Every column here is over the fragments that
were present in that run, scored against their own reference poses.

THE HEADLINE COLUMN IS DISPLACEMENT, NOT TURN, and that is a correction. Turn was
the obvious column and it is the wrong one, for two reasons found by rendering
job 30167044 and then probing what the render disagreed with:

  A sherd can read 177 degrees while sitting where it belongs. On `plate` a
  59-point sherd reads 177.4 deg at 1.0% of pot size from correct; on `blue_pot`
  a 131-point sherd reads 169.6 deg at 0.20%. Small sherds are near-planar and
  nearly symmetric, so a half-turn lands them back on themselves. The angle is a
  symmetry of the sherd, not a misplacement, and it inflates every mean that
  contains a small flat fragment.

  Turn ignores translation entirely. A sherd carried right across the pot with
  its orientation intact reads zero. On `galli_pot` at rank 2 the worst kept
  sherd ends up further from home than the pot is wide, and the turn column calls
  that change "not readable".

So the question "did the kept sherds go to the right PLACE" is answered by the
distance their points ended up from their own reference points, and turn is kept
only as a secondary column with this caveat attached to it.

THE ANCHOR IS THE LARGEST SHERD BY POINT COUNT, NOT part_id 0. `_transform` picks
`anchor_idx = np.argmax(counts)`, and part ids are not ordered by size -- on
`blue_pot` the anchor is part 1. Excluding part 0 instead of the real anchor
scores the free fragment and drops a real one, which is a way to make almost any
result appear.

EVERY POT GETS ITS OWN BAR. A single pooled threshold is useless here because
run-to-run spread differs wildly between pots. Each pot's change is judged
against a threshold built from that pot's own draws, the same way tickets 01 and
06 built the 17 and 9.1 degree rules:

    sd of the pot's draws in each arm -> SE of a median = sd / sqrt(n)
    difference of two medians          -> sqrt(SE_a^2 + SE_b^2)
    readable                           -> 2 x that

raised to the RESEED arm's observed move for that pot whenever that is larger,
because the sampler is re-drawn between runs and the within-run draws never see
that. The blunter instrument wins; that is the honest direction to err in.

THE CONFOUND, NAMED. Removing a fragment does not leave the others untouched: the
5000-point budget is shared out by area, so every kept sherd is re-sampled, and
the pot is re-centred and re-normalised on what remains.
`scripts/check_fragment_omission.py` bounds it before any GPU time (job 30167044:
kept sherds came back 0.92% different in shape against a 1.08% re-sampling floor,
so they are the same sherds; the pot's FRAME moved 8.92% of its size). The frame
shift does not leak into the columns here: each arm is scored against its OWN
reference, in its own frame, so both sides of every comparison moved together.

AND THE DIRECTION CARRIES THE ARGUMENT. Removing a sherd also removes a sherd to
place, and fewer pieces is an EASIER task, so the confound pushes towards a
better score:

  graceful degradation -> the kept sherds land the SAME or CLOSER to home.
  destabilisation      -> they land FURTHER from home, even though the job got
                          smaller. Absence actively misplaces what is present.

Only the second is a reason to make generative completion load-bearing.

RANKS ARE NOT COMPARABLE UNLESS THE POT SET IS HELD FIXED. Rank 5 exists only on
pots with five or more fragments, and those are the high-fragment-count pots that
were already scoring worst, so a rank-2-versus-rank-6 comparison across all
available pots compares two different populations. The cross-rank table at the
end is restricted to pots present at every rank.

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

from readout import chamfer, clouds_by_object, read_run, unit_box_scale


def displacement(run_dir):
    """{pot: {"draws": per-draw mean displacement, "worst": ..., "n_frags": int}}.

    Displacement is how far a sherd's points ended up from its OWN reference
    points, as a percentage of the pot's longest dimension, averaged over the
    sherds the model actually had to place.

    `readout.chamfer` returns the sum of two MEAN SQUARED nearest-neighbour
    distances, because that is what the evaluator thresholds. A squared quantity
    cannot be quoted as a distance, and reporting it as one exaggerates large
    errors and cannot be translated into millimetres. sqrt(c / 2) puts it back
    into the same units as the object, and dividing by the bounding box makes it
    a fraction of the pot.
    """
    out = {}
    for name, path in clouds_by_object(run_dir).items():
        d = np.load(path, allow_pickle=True)
        if "generations_proposed" not in d:
            continue
        gt, ids = d["pts_gt"], d["part_ids"]
        unit = unit_box_scale(gt)
        parts = sorted(set(ids.tolist()))
        # The anchor is handed over already seated, so it must not be scored.
        # It is the sherd with the most points -- dataset.py takes argmax(counts).
        anchor = max(parts, key=lambda p: int((ids == p).sum()))
        placed = [p for p in parts if p != anchor]
        if not placed:
            continue
        means, worsts = [], []
        for g in d["generations_proposed"]:
            per = []
            for p in placed:
                m = ids == p
                c = chamfer(gt[m] / unit, g[m] / unit)
                per.append(100.0 * float(np.sqrt(max(c, 0.0) / 2.0)))
            means.append(float(np.mean(per)))
            worsts.append(float(np.max(per)))
        out[name.split("/")[-1]] = {
            "draws": np.array(means),
            "median": float(np.median(means)),
            "worst": float(np.median(worsts)),
            "n_frags": len(parts),
            "n_placed": len(placed),
        }
    return out


def turn(run_dir):
    """{pot: median turn in degrees}. Secondary -- see the caveat in the header."""
    out = {}
    for r in read_run(Path(run_dir)):
        out.setdefault(r.object_name.split("/")[-1], []).append(r.turn_deg)
    return {k: float(np.median(v)) for k, v in out.items()}


def se_median(draws):
    n = len(draws)
    if n < 2:
        return float("inf")
    return float(np.std(draws, ddof=1) / np.sqrt(n))


def bar_for(a, b, reseed_move):
    stat = 2.0 * float(np.hypot(se_median(a), se_median(b)))
    return max(stat, reseed_move)


# A change has to clear TWO bars, not one. The statistical bar says the run
# noise cannot explain it. The seam floor says a conservator could see it.
# narrow_bottle2 is why: it moved +0.16% of pot size against a 0.05% bar --
# statistically solid, and on a 100 mm pot that is a sixth of a millimetre,
# which is inside the thickness of the glue line. Counting that as a pot
# "readably destabilised" alongside pink_bowl's +11.71% is how a table ends up
# saying something the pictures do not.
SEAM_FLOOR = 1.0            # percent of the pot's longest dimension


def reading_of(change, bar):
    if abs(change) < bar:
        return "not readable"
    if abs(change) < SEAM_FLOOR:
        return "below seam"
    return "FURTHER" if change > 0 else "closer"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--whole", required=True)
    ap.add_argument("--reseed", required=True)
    ap.add_argument("--dropped", nargs="+", required=True)
    a = ap.parse_args()

    whole = displacement(Path(a.whole))
    reseed = displacement(Path(a.reseed))
    dropped = {Path(d).name: displacement(Path(d)) for d in a.dropped}
    turn_w = turn(Path(a.whole))
    turn_d = {Path(d).name: turn(Path(d)) for d in a.dropped}

    print("HOW FAR THE PLACED SHERDS ENDED UP FROM WHERE THEY BELONG")
    print("as a percentage of the pot's longest dimension. The anchor is excluded:")
    print("it is handed over already seated. Under about 1% the seam is closed;")
    print("30% is a sherd sitting a third of the pot away from its socket.\n")

    print("Control -- the same whole pot, nothing removed, run twice.")
    print("This is what 'no change' looks like, POT BY POT.\n")
    print("%-16s %6s %8s %8s %7s %9s" %
          ("pot", "placed", "run A", "run B", "move", "BAR USED"))
    print("-" * 60)
    moves, bars = {}, {}
    for name in sorted(whole):
        if name not in reseed:
            continue
        wa, wb = whole[name], reseed[name]
        mv = abs(wa["median"] - wb["median"])
        moves[name] = mv
        bars[name] = bar_for(wa["draws"], wb["draws"], mv)
        print("%-16s %6d %8.2f %8.2f %7.2f %9.2f"
              % (name, wa["n_placed"], wa["median"], wb["median"], mv, bars[name]))
    if not bars:
        raise SystemExit("no pot appears in both the whole and reseed runs")
    print("\nThe bar runs from %.2f to %.2f percent of pot size depending on the pot."
          % (min(bars.values()), max(bars.values())))
    print("A change smaller than a pot's own bar has not been shown to move that pot.\n")

    verdicts = {}
    for label, tab in sorted(dropped.items()):
        print("=" * 78)
        print("%s: one sherd removed. Scored on the sherds that REMAIN." % label)
        print("=" * 78)
        print("%-16s %9s %8s %8s %8s %8s %13s" %
              ("pot", "placed", "whole", "kept", "change", "its bar", "reading"))
        print("-" * 78)
        rows = []
        for name in sorted(tab):
            if name not in whole or name not in bars:
                continue
            tw, td = whole[name], tab[name]
            ch = td["median"] - tw["median"]
            b = bar_for(tw["draws"], td["draws"], moves[name])
            r = reading_of(ch, b)
            rows.append((name, ch, r))
            print("%-16s %4d->%-4d %8.2f %8.2f %+8.2f %8.2f %13s"
                  % (name, tw["n_placed"], td["n_placed"],
                     tw["median"], td["median"], ch, b, r))
        if not rows:
            print("  no pot in common with the whole run")
            continue
        verdicts[label] = {n: (c, r) for n, c, r in rows}
        n_far = sum(1 for _, _, r in rows if r == "FURTHER")
        n_near = sum(1 for _, _, r in rows if r == "closer")
        n_flat = len(rows) - n_far - n_near
        med = float(np.median([c for _, c, _ in rows]))
        print("\n  %d pots: %d readably further from home, %d readably closer, "
              "%d with no change worth seeing." % (len(rows), n_far, n_near, n_flat))
        print("  Median change %+.2f%% of pot size." % med)
        # "Most" means most of the pots, not merely more than either other
        # column. Four of eight is not most; saying so once already turned a
        # split result into a verdict.
        if n_far > len(rows) / 2.0:
            print("  READING: DESTABILISATION on most pots -- the kept sherds landed")
            print("  further from home even though losing a fragment made the task smaller.")
        elif n_far and n_near:
            print("  READING: NO CONSISTENT DIRECTION. Some pots worse, some better, by")
            print("  amounts that do not point one way. This is pot-level noise, not an")
            print("  effect of absence -- report it as such, not as a majority verdict.")
        elif n_flat >= n_far + n_near:
            print("  READING: GRACEFUL DEGRADATION. On most pots losing a sherd did not")
            print("  readably move the ones that remain.")
        else:
            print("  READING: GRACEFUL DEGRADATION, and the task got easier -- the kept")
            print("  sherds improved, which is what one fewer piece buys.")

        print("\n  Secondary, and NOT to be quoted on its own -- median TURN, degrees.")
        print("  A near-planar sherd sitting where it belongs can read 177 degrees, and")
        print("  a sherd carried across the pot with its orientation intact reads zero.")
        print("  %-16s %8s %8s %8s" % ("pot", "whole", "kept", "change"))
        for name, _, _ in rows:
            tv, dv = turn_w.get(name), turn_d[label].get(name)
            if tv is None or dv is None:
                continue
            print("  %-16s %8.1f %8.1f %+8.1f" % (name, tv, dv, dv - tv))
        print()

    if len(verdicts) > 1:
        common = set.intersection(*(set(v) for v in verdicts.values()))
        print("=" * 78)
        print("Across ranks, on the pots that appear at EVERY rank")
        print("=" * 78)
        if not common:
            print("no pot survives every rank; the ranks cannot be compared.")
        else:
            print("Rank 2 removes the largest droppable sherd, higher ranks smaller ones.")
            print("The prediction was that removing a BIGGER sherd hurts more, so these")
            print("should FALL from left to right. Change in % of pot size.\n")
            keys = sorted(verdicts)
            print("%-16s " % "pot" + " ".join("%9s" % k.split("_")[1] for k in keys))
            print("-" * (17 + 10 * len(keys)))
            for name in sorted(common):
                cells = []
                for k in keys:
                    c, r = verdicts[k][name]
                    cells.append("%+8.2f%s" % (c, "*" if r in ("FURTHER", "closer") else " "))
                print("%-16s " % name + " ".join(cells))
            print("\n* = readable against that pot's own bar. These pots are the ones with")
            print("the most fragments, which are also the ones already reassembling worst,")
            print("so this table says nothing about the small pots that TORA gets right.")

    print()
    print("Before quoting any of this, LOOK at the renders. Whether the vessel still")
    print("closes is in none of these columns, and the render must be read against the")
    print("dropped arm's OWN reference -- with a sherd gone, a correct answer has a")
    print("hole in it too.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
