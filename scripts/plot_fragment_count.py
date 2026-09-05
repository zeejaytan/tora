"""Does the Juglet do worse than its fragment count predicts?

Ticket .scratch/juglet-cause/issues/02-is-nine-fragments-enough.md.

The eight fresh ceramics of job 29891327 arm B, all normalised to the same stored
size (0.500, inside the trained band) and all run anchor-fixed with ten draws, are
plotted against fragment count, with the Juglet's twenty pooled baseline draws
overlaid. Everything is read through scripts/readout.py so the non-anchor
x n/(n-1) correction is applied once, in one place.

Two things this plot has to be honest about, both drawn on it:

  * Ticket 01's readable-difference threshold. On this material a gap below 17 deg
    between two runs is sampler noise, not a result. The band is drawn so a reader
    cannot eyeball a difference the instrument cannot resolve.
  * The Juglet is run anchor-free and the eight ceramics anchor-fixed. Job 28228263
    ran six real pots both ways and the median difference was -2.2 deg, well inside
    the 17 deg threshold, so the mismatch does not explain a gap -- but it is stated
    on the figure rather than left in a note.

Usage:
  python scripts/plot_fragment_count.py --out artifacts/fragment_count.png
"""

import argparse
import statistics as st
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, "scripts")
import readout  # noqa: E402

FRESH = "artifacts/notes_recheck/scaleladder_B_normalized_29891327"
JUGLET_RUNS = [
    "artifacts/juglet_runs/lorav_juglet_baseline_29527496",
    "artifacts/juglet_runs/lorav_juglet_baseline_29623885",
    "artifacts/juglet_runs/lorav3_juglet_baseline_29880370",
    "artifacts/juglet_runs/wearft2_jugletgt_baseline_29308186",
]
READABLE_DEG = 17.0  # ticket 01


def by_object(run):
    out = {}
    for r in readout.read_run(run):
        out.setdefault(r.object_name, []).append(r)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="artifacts/fragment_count.png")
    a = ap.parse_args()

    fresh = []
    for name, recs in by_object(FRESH).items():
        turns = [r.turn_deg for r in recs]
        fresh.append((recs[0].n_fragments, st.median(turns), min(turns), max(turns),
                      st.median([r.seated for r in recs]), name.split("/")[-1]))
    fresh.sort()

    jug = []
    for run in JUGLET_RUNS:
        jug.extend(readout.read_run(run))
    jt = [r.turn_deg for r in jug]
    j_n = jug[0].n_fragments
    j_med, j_lo, j_hi = st.median(jt), min(jt), max(jt)
    j_seat = st.median([r.seated for r in jug])

    fig, axs = plt.subplots(1, 2, figsize=(12, 5.2))

    ax = axs[0]
    ax.axhspan(j_med - READABLE_DEG, j_med + READABLE_DEG, color="#f0c419", alpha=0.16,
               zorder=0,
               label="within %g° of the Juglet = no difference detected" % READABLE_DEG)
    for n, med, lo, hi, _seat, label in fresh:
        ax.vlines(n, lo, hi, color="#9aa5b1", lw=1.2, zorder=2)
        ax.plot(n, med, "o", ms=7, color="#1f4e79", zorder=3)
        ax.annotate(label, (n, med), textcoords="offset points", xytext=(8, -3),
                    fontsize=7.5, color="#33475b")
    ax.vlines(j_n, j_lo, j_hi, color="#c1440e", lw=1.6, zorder=4)
    ax.plot(j_n, j_med, "D", ms=9, color="#c1440e", zorder=5, label="the Juglet")
    ax.plot([], [], "o", color="#1f4e79", label="fresh ceramics (10 draws each)")
    ax.set_xlabel("fragments in the pot")
    ax.set_ylabel("how far misplaced sherds are turned (degrees)")
    ax.set_title("Fragment count does not predict the error", fontsize=10)
    ax.set_ylim(0, 100)
    ax.grid(alpha=0.25, lw=0.6)
    ax.legend(fontsize=7.5, loc="upper left")

    ax = axs[1]
    # Several pots seat every sherd, so their markers coincide at 1.0; stagger the
    # labels rather than letting them print on top of one another.
    used = []
    for n, _med, _lo, _hi, seat, label in fresh:
        y = seat / n
        dy = -3
        while any(abs(n - un) < 3 and abs(y - uy) < 0.04 and abs(dy - udy) < 11
                  for un, uy, udy in used):
            dy -= 11
        used.append((n, y, dy))
        ax.plot(n, y, "o", ms=7, color="#1f4e79", zorder=3)
        ax.annotate(label, (n, y), textcoords="offset points", xytext=(8, dy),
                    fontsize=7.5, color="#33475b")
    ax.plot(j_n, j_seat / j_n, "D", ms=9, color="#c1440e", zorder=5)
    ax.annotate("the Juglet", (j_n, j_seat / j_n), textcoords="offset points",
                xytext=(8, -3), fontsize=8, color="#c1440e")
    ax.set_xlabel("fragments in the pot")
    ax.set_ylabel("fraction of sherds seated in the right place")
    ax.set_title("Seating falls away with fragment count", fontsize=10)
    ax.set_ylim(0, 1.05)
    ax.grid(alpha=0.25, lw=0.6)

    fig.suptitle("The Juglet against fresh ceramics at the same stored size, "
                 "by fragment count", fontsize=12)
    fig.text(0.5, 0.015,
             "Fresh ceramics: job 29891327 arm B, all normalised to 0.500, anchor-fixed, "
             "10 draws. Juglet: 20 pooled baseline draws, scale 0.511, anchor-free.\n"
             "Job 28228263 ran six real pots in both anchor modes; the median difference "
             "was -2.2°, inside the 17° threshold, so the mode mismatch cannot "
             "account for a readable gap.",
             ha="center", fontsize=7.5, color="#555")
    fig.tight_layout(rect=(0, 0.09, 1, 0.93))
    fig.savefig(a.out, dpi=170)
    print("wrote", a.out)

    print("\nfragments  turn(med)   seated      object")
    for n, med, lo, hi, seat, label in fresh:
        print("   %2d      %6.1f   %4.1f/%-2d    %s  [%.1f-%.1f]"
              % (n, med, seat, n, label, lo, hi))
    print("   %2d      %6.1f   %4.1f/%-2d    THE JUGLET  [%.1f-%.1f]"
          % (j_n, j_med, j_seat, j_n, j_lo, j_hi))

    # Does fragment count predict the error at all?
    xs = [n for n, *_ in fresh]
    ys = [m for _n, m, *_ in fresh]
    mx, my = st.mean(xs), st.mean(ys)
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sx = sum((x - mx) ** 2 for x in xs) ** 0.5
    sy = sum((y - my) ** 2 for y in ys) ** 0.5
    print("\nfresh ceramics only, fragment count vs turn: r = %.2f over %d pots"
          % (cov / (sx * sy), len(xs)))


if __name__ == "__main__":
    main()
