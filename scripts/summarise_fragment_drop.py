"""Did the sherds we KEPT still go to the right place when one sherd was gone?

Ticket .scratch/juglet-cause/issues/04. The Juglet is missing a piece; none of
the eight Fractura pots TORA reassembles is missing anything. This reads the
runs that test whether that difference matters.

WHAT IS NOT REPORTED, AND WHY. No whole-assembly score. A missing fragment
deflates any score computed over the whole pot automatically, and quoting that
would confuse absence with failure. Every column here is over the fragments
that were present in that run, scored against their own reference poses.

EVERY POT GETS ITS OWN BAR. This is the correction that matters, and the first
version of this script got it wrong. A single pooled threshold is useless here
because run-to-run spread is wildly different from pot to pot: on job 30167044
two draws of the same UNCHANGED pot moved `narrow_bottle3` by 35.6 degrees and
`pink_bowl` by 0.2. Judging both against one median floor of 4.2 degrees called
half the table readable when it was not. So each pot's change is judged against
a threshold built from that pot's own draws, the same way tickets 01 and 06
built the 17 and 9.1 degree rules:

    sd of the pot's draws in each arm -> SE of a median = sd / sqrt(n)
    difference of two medians          -> sqrt(SE_a^2 + SE_b^2)
    readable                           -> 2 x that

and then, because the sampler is re-drawn between runs and that is a source of
variation the within-run draws never see, the bar is raised to the RESEED arm's
observed move for that pot whenever the reseed move is larger. Whichever
instrument is blunter wins; that is the honest direction to err in.

THE CONFOUND, NAMED. Removing a fragment does not leave the others untouched:
the 5000-point budget is shared out by area, so every kept sherd is re-sampled,
and the pot is re-centred and re-normalised on what remains. Two things bound
that. `scripts/check_fragment_omission.py` measures it before any GPU time (on
job 30167044: kept sherds came back 0.92% different in shape against a 1.08%
re-sampling floor, so they are the same sherds; the pot's FRAME moved 8.92% of
its size). And re-centring and re-scaling are a translation and a uniform
scale, neither of which can change an angle -- which is why the turn column is
the one to read, and displacement is not reported here at all.

AND THE DIRECTION CARRIES THE ARGUMENT. Removing a sherd also removes a sherd
to place, and fewer pieces is an EASIER task, so the confound pushes towards a
better score:

  graceful degradation -> the kept sherds score the SAME or BETTER.
  destabilisation      -> the kept sherds score WORSE, even though the job got
                          smaller. Absence actively misplaces what is present.

Only the second is a reason to make generative completion load-bearing.

RANKS ARE NOT COMPARABLE TO EACH OTHER UNLESS THE POT SET IS HELD FIXED. Rank 5
only exists on pots with five or more fragments, so a rank-5 table is computed
over the big pots alone -- and the big pots are the ones that were already doing
badly. The per-rank summary therefore reports its own pot set, and the
cross-rank summary at the end is restricted to pots present at every rank.

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
    """{object: {"turn": median, "draws": [...], "n_frags": int}}."""
    out = {}
    for r in read_run(Path(run_dir)):
        out.setdefault(r.object_name, []).append(r)
    return {
        name: {
            "turn": float(np.median([r.turn_deg for r in rs])),
            "draws": np.array([r.turn_deg for r in rs], dtype=float),
            "n_frags": rs[0].n_fragments,
        }
        for name, rs in out.items()
    }


def se_median(draws):
    """Standard error of a median, the way tickets 01 and 06 computed it."""
    n = len(draws)
    if n < 2:
        return float("inf")
    return float(np.std(draws, ddof=1) / np.sqrt(n))


def bar_for(a, b, reseed_move):
    """How far two medians must differ on this pot before it is readable.

    Two independent estimates, and the blunter one wins: the spread of the draws
    inside each run, and the move actually observed between two runs of the
    unchanged pot (which also carries the sampler being re-drawn).
    """
    stat = 2.0 * float(np.hypot(se_median(a), se_median(b)))
    return max(stat, reseed_move), stat


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

    print("Control -- the same whole pot, nothing removed, run twice.")
    print("This is what 'no change' looks like, POT BY POT. It is not one number:")
    print("some of these pots are far noisier than others, and a pooled floor")
    print("would call their noise a finding.\n")
    print(f"{'pot':18s} {'frags':>5s} {'turn A':>8s} {'turn B':>8s} {'move':>7s} "
          f"{'draw sd':>8s} {'stat bar':>9s} {'BAR USED':>9s}")
    print("-" * 82)

    reseed_move, bars = {}, {}
    for name in sorted(whole):
        if name not in reseed:
            continue
        wa, wb = whole[name], reseed[name]
        mv = abs(wa["turn"] - wb["turn"])
        reseed_move[name] = mv
        b, stat = bar_for(wa["draws"], wb["draws"], mv)
        bars[name] = b
        print(f"{short(name):18s} {wa['n_frags']:5d} {wa['turn']:8.1f} "
              f"{wb['turn']:8.1f} {mv:7.1f} {np.std(wa['draws'], ddof=1):8.1f} "
              f"{stat:9.1f} {b:9.1f}")

    if not bars:
        raise SystemExit("no pot appears in both the whole and reseed runs")
    print(f"\nThe bar runs from {min(bars.values()):.1f} to "
          f"{max(bars.values()):.1f} degrees depending on the pot. Anything")
    print("smaller than a pot's own bar has not been shown to move that pot.\n")

    verdicts = {}
    for label, tab in dropped.items():
        print("=" * 88)
        print(f"{label}: one sherd removed. Scored on the sherds that REMAIN.")
        print("=" * 88)
        print(f"{'pot':18s} {'frags':>5s} {'->':>3s} {'whole':>7s} {'kept':>7s} "
              f"{'change':>8s} {'its bar':>8s} {'reading':>12s}")
        print("-" * 88)
        rows = []
        for name in sorted(tab):
            if name not in whole or name not in bars:
                continue
            tw, td = whole[name], tab[name]
            d = td["turn"] - tw["turn"]
            b, _ = bar_for(tw["draws"], td["draws"], reseed_move[name])
            if abs(d) < b:
                reading = "not readable"
            elif d > 0:
                reading = "WORSE"
            else:
                reading = "better"
            rows.append((name, d, b, reading))
            print(f"{short(name):18s} {tw['n_frags']:5d} {td['n_frags']:3d} "
                  f"{tw['turn']:7.1f} {td['turn']:7.1f} {d:+8.1f} {b:8.1f} "
                  f"{reading:>12s}")
        if not rows:
            print("  no pot in common with the whole run")
            continue
        verdicts[label] = {n: (d, b, r) for n, d, b, r in rows}
        n_worse = sum(1 for *_, r in rows if r == "WORSE")
        n_better = sum(1 for *_, r in rows if r == "better")
        n_flat = len(rows) - n_worse - n_better
        med = float(np.median([d for _, d, _, _ in rows]))
        print(f"\n  {len(rows)} pots: {n_worse} readably worse, {n_better} "
              f"readably better, {n_flat} not readable. Median change "
              f"{med:+.1f} deg.")
        if n_worse > n_better and n_worse > n_flat:
            print("  READING: DESTABILISATION on most pots -- kept sherds went to")
            print("  worse places even though losing a fragment made the task smaller.")
        elif n_flat >= n_worse + n_better:
            print("  READING: GRACEFUL DEGRADATION. On most pots losing a sherd did")
            print("  not readably move the ones that remain.")
        elif n_better >= n_worse:
            print("  READING: GRACEFUL DEGRADATION, and the task got easier -- the")
            print("  kept sherds improved, which is what one fewer piece buys.")
        else:
            print("  READING: MIXED. Report pot by pot; there is no majority.")
        print()

    # Cross-rank, on a fixed pot set only. Ranks differ in which pots can supply
    # them, and the pots that survive to high ranks are the ones with the most
    # fragments -- which are also the ones already doing worst.
    if len(verdicts) > 1:
        common = set.intersection(*(set(v) for v in verdicts.values()))
        print("=" * 88)
        print("Across ranks, on the pots that appear at EVERY rank")
        print("=" * 88)
        if not common:
            print("no pot survives every rank; the ranks cannot be compared.")
        else:
            print("Ranks remove progressively smaller sherds. If absence")
            print("destabilises, removing a BIGGER sherd should hurt more.\n")
            print(f"{'pot':18s} " + " ".join(f"{k.split('_')[1]:>9s}"
                                             for k in sorted(verdicts)))
            print("-" * (19 + 10 * len(verdicts)))
            for name in sorted(common):
                cells = []
                for k in sorted(verdicts):
                    d, b, r = verdicts[k][name]
                    mark = "*" if r != "not readable" else " "
                    cells.append(f"{d:+8.1f}{mark}")
                print(f"{short(name):18s} " + " ".join(cells))
            print("\n* = readable against that pot's own bar. Rank 2 is the "
                  "largest droppable sherd,")
            print("higher ranks are smaller ones. A rising trend left to right "
                  "would mean the")
            print("opposite of the prediction: small sherds hurting more than big ones.")

    print()
    print("Before quoting any of this, LOOK at the renders: whether the vessel")
    print("still closes is not in any of these columns.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
