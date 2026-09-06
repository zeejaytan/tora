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

THE TWO ARMS ARE MATCHED SHERD FOR SHERD, and that is the second correction. The
first version averaged the whole arm over every placed sherd and the dropped arm
over the survivors -- a mean over n sherds against a mean over n-1 DIFFERENT
ones. That alone moves the answer: drop a well-placed sherd and the survivors'
average rises with nothing having happened to them, drop a badly-placed one and
it falls. `narrow_bottle3` read 14.4% CLOSER under that arithmetic. The dropped
sherd is now left out of both sides.

Matching cannot go through part ids, because `_omit_fragment` deletes a mesh and
re-numbers what is left: `pink_bowl` part 1 in the rank-2 run is part 1 of three
in the whole run, but `plate` part 1 is not. It goes through AREA RANK, which
both arms agree on because `_sample_points` allots points by area share. The
mapping is then GATED, not assumed: each paired sherd's covariance eigenvalue
ratios must agree to SHAPE_TOL, a signature that survives the re-centring and
re-normalising but not a swap for a different sherd. A pot that fails the gate is
refused a row rather than given a caveat.

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
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np

from readout import chamfer, clouds_by_object, read_run, unit_box_scale


def shape_of(pts):
    """A frame-free signature of one sherd: its covariance eigenvalue ratios.

    The two arms centre and normalise the pot differently, so nothing absolute
    survives the crossing. Removing the sherd's own centroid kills the shift, and
    dividing the eigenvalues by the largest kills the uniform rescale, so what is
    left describes the sherd's shape alone. Two re-samplings of the same mesh
    agree on it; two different sherds do not.
    """
    q = pts - pts.mean(0)
    e = np.linalg.eigvalsh(np.cov(q.T))
    e = np.sort(e)[::-1]
    return e[1:] / max(e[0], 1e-12)


def per_part(run_dir):
    """{pot: {"disp": {area rank: per-draw displacement}, "shape": {...}, ...}}.

    Displacement is how far a sherd's points ended up from its OWN reference
    points, as a percentage of the pot's longest dimension.

    `readout.chamfer` returns the sum of two MEAN SQUARED nearest-neighbour
    distances, because that is what the evaluator thresholds. A squared quantity
    cannot be quoted as a distance, and reporting it as one exaggerates large
    errors and cannot be translated into millimetres. sqrt(c / 2) puts it back
    into the same units as the object, and dividing by the bounding box makes it
    a fraction of the pot.

    KEYED BY AREA RANK, NOT BY PART ID, and that is the point of this function.
    `dataset._omit_fragment` deletes a mesh and the survivors are re-numbered, so
    part 1 in a dropped run is NOT part 1 in the whole run. Ranking by point
    count recovers the correspondence, because `_sample_points` hands out the
    5000-point budget as area over total area -- monotone in area, which is the
    same order `_omit_fragment` ranks by. Rank 1 is the anchor.
    """
    out = {}
    for name, path in clouds_by_object(run_dir).items():
        d = np.load(path, allow_pickle=True)
        if "generations_proposed" not in d:
            continue
        gt, ids = d["pts_gt"], d["part_ids"]
        unit = unit_box_scale(gt)
        parts = sorted(set(ids.tolist()))
        order = sorted(parts, key=lambda p: -int((ids == p).sum()))
        disp, shape = {}, {}
        for rank, p in enumerate(order, start=1):
            m = ids == p
            shape[rank] = shape_of(gt[m])
            if rank == 1:
                continue                  # the anchor is handed over seated
            disp[rank] = np.array([
                100.0 * float(np.sqrt(max(chamfer(gt[m] / unit, g[m] / unit), 0.0) / 2.0))
                for g in d["generations_proposed"]])
        if not disp:
            continue
        out[name.split("/")[-1]] = {"disp": disp, "shape": shape,
                                    "n_frags": len(parts)}
    return out


def match(whole, drop, k):
    """Line the two arms up sherd for sherd, or refuse.

    The dropped arm lost the sherd at area rank `k`, so its ranks 2..n-1 are the
    whole arm's ranks 2..n with `k` taken out, in the same order. Returns
    (whole draws, dropped draws, worst shape disagreement) with the means taken
    over THE SAME SHERDS on both sides -- without which the comparison is
    between a mean over n sherds and a mean over n-1 different ones, and
    dropping a well-placed sherd raises the survivors' average by itself.
    """
    w_ranks = [r for r in sorted(whole["disp"]) if r != k]
    d_ranks = sorted(drop["disp"])
    if len(w_ranks) != len(d_ranks):
        return None, None, float("inf")
    gaps = [float(np.max(np.abs(whole["shape"][wr] - drop["shape"][dr])))
            for wr, dr in zip([1] + w_ranks, [1] + d_ranks)]
    wm = np.mean([whole["disp"][r] for r in w_ranks], axis=0)
    dm = np.mean([drop["disp"][r] for r in d_ranks], axis=0)
    return wm, dm, gaps


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

# Two re-samplings of the same mesh agree on shape_of to ~1e-3; two
# different sherds of the same pot differ by tenths. Anything in between
# means the rank mapping is not doing what this script claims it does.
SHAPE_TOL = 0.05


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

    whole = per_part(Path(a.whole))
    reseed = per_part(Path(a.reseed))
    dropped = {Path(d).name: per_part(Path(d)) for d in a.dropped}
    turn_w = turn(Path(a.whole))
    turn_d = {Path(d).name: turn(Path(d)) for d in a.dropped}

    print("HOW FAR THE PLACED SHERDS ENDED UP FROM WHERE THEY BELONG")
    print("as a percentage of the pot's longest dimension. The anchor is excluded:")
    print("it is handed over already seated. Under about 1% the seam is closed;")
    print("30% is a sherd sitting a third of the pot away from its socket.\n")

    print("Control -- the same whole pot, nothing removed, run twice.")
    print("This is what 'no change' looks like, POT BY POT.\n")
    # The shape-gap column CALIBRATES the gate. Nothing is dropped here, so the
    # sherd-to-sherd mapping is known to be right, and whatever gap it produces
    # is the gap re-sampling alone can manufacture. A dropped arm has to be
    # judged against this number, not against zero.
    print("%-16s %6s %8s %8s %7s %9s %10s" %
          ("pot", "placed", "run A", "run B", "move", "BAR USED", "shape gap"))
    print("-" * 72)
    moves, bars = {}, {}
    for name in sorted(whole):
        if name not in reseed:
            continue
        # Nothing is dropped in either control arm, so k=None matches every
        # sherd to itself -- the same code path the real comparison uses.
        wa, wb, gaps = match(whole[name], reseed[name], None)
        if wa is None:
            continue
        ma, mb = float(np.median(wa)), float(np.median(wb))
        mv = abs(ma - mb)
        moves[name] = mv
        bars[name] = bar_for(wa, wb, mv)
        print("%-16s %6d %8.2f %8.2f %7.2f %9.2f %10.4f"
              % (name, len(whole[name]["disp"]), ma, mb, mv, bars[name],
                 max(gaps)))
    if not bars:
        raise SystemExit("no pot appears in both the whole and reseed runs")
    print("\nThe bar runs from %.2f to %.2f percent of pot size depending on the pot."
          % (min(bars.values()), max(bars.values())))
    print("A change smaller than a pot's own bar has not been shown to move that pot.\n")

    verdicts = {}
    for label, tab in sorted(dropped.items()):
        k = int(re.search(r"rank(\d+)", label).group(1))
        print("=" * 78)
        print("%s: the rank-%d sherd by area removed. The whole column is the SAME"
              % (label, k))
        print("sherds in the whole run -- the dropped one is left out of both sides."
              )
        print("=" * 78)
        print("%-16s %9s %8s %8s %8s %8s %13s" %
              ("pot", "scored", "whole", "kept", "change", "its bar", "reading"))
        print("-" * 78)
        rows = []
        for name in sorted(tab):
            if name not in whole or name not in bars:
                continue
            wm, dm, gaps = match(whole[name], tab[name], k)
            if wm is None:
                print("%-16s   REFUSED: sherd counts do not line up" % name)
                continue
            bad = max(gaps)
            if bad > SHAPE_TOL:
                # The gate, not a caveat. If the sherds do not pair up by shape
                # the rank mapping is wrong, and every number in the row would be
                # one sherd compared against a different sherd.
                print("%-16s   REFUSED: shape gaps %s -- mapping unsafe"
                      % (name, " ".join("%.3f" % g for g in gaps)))
                continue
            mw, md = float(np.median(wm)), float(np.median(dm))
            ch = md - mw
            b = bar_for(wm, dm, moves[name])
            r = reading_of(ch, b)
            rows.append((name, ch, r))
            print("%-16s %9d %8.2f %8.2f %+8.2f %8.2f %13s"
                  % (name, len(tab[name]["disp"]),
                     mw, md, ch, b, r))
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
