"""Manufactured truth for `measure_strip_feasibility.traceable_length`.

The rule in AGENTS.md is that manufactured truth gets its own geometry gate
before any scoring, and version 1 of the strip-feasibility check (job
30386369) is why: it read 0.0% on every object at every length because the
quantity it measured was bounded by the size of the window it measured it in.
A three-case gate would have caught that in seconds.

Three cases, each with an arc length known by construction:

  1. A CURVED RIBBON -- an arc of a circle, radius 30 mm, sweeping 60 degrees,
     1.8 mm wide (a Juglet wall), sampled at 0.2 mm. True arc length
     30 x pi/3 = 31.42 mm. The measurement must recover THAT and not the
     straight chord between its ends (30 mm), because a straight ruler is
     what v1 got wrong.

  2. A FLAT SQUARE PATCH, 20 x 20 mm -- the control against saturation. The
     answer must be the diagonal, about 28.3 mm. If a bounded window has crept
     back into the code this comes back near the window size instead.

  3. A BROKEN RIBBON -- the same arc with a 3 mm gap cut out of it at 40% of
     its length. The longer surviving piece is about 18.9 mm. The measurement
     must report the longer piece and NOT credit itself for jumping the gap,
     because a profile filter cannot run across missing data either.

Run locally; needs only numpy and scipy.
"""

import sys

import numpy as np

sys.path.insert(0, __file__.rsplit("scripts", 1)[0] + "scripts")
from measure_strip_feasibility import traceable_length  # noqa: E402

TOL = 0.06   # 6% -- a graph walk on a point cloud steps slightly short


def arc_ribbon(radius, sweep_deg, width, spacing, cut=None):
    """Points on an arc-shaped ribbon lying in the xy-plane, mm."""
    sweep = np.deg2rad(sweep_deg)
    n_along = int(radius * sweep / spacing) + 1
    n_across = max(int(width / spacing) + 1, 2)
    t = np.linspace(0.0, sweep, n_along)
    u = np.linspace(-width / 2.0, width / 2.0, n_across)
    T, U = np.meshgrid(t, u, indexing="ij")
    R = radius + U
    pts = np.column_stack([(R * np.cos(T)).ravel(), (R * np.sin(T)).ravel(),
                           np.zeros(R.size)])
    if cut is not None:
        lo, hi = cut
        s = (T.ravel() * radius)            # arc length from the start
        pts = pts[(s < lo) | (s > hi)]
    return pts


def check(name, pts, expect, spacing):
    got, ncomp, frac = traceable_length(pts, spacing, 1.0)
    err = abs(got - expect) / expect
    ok = err <= TOL
    print(("PASS " if ok else "FAIL ") + name)
    print("     expected " + format(expect, "7.2f") + " mm    measured " +
          format(got, "7.2f") + " mm    error " +
          format(100.0 * err, "5.1f") + "%    pieces " + str(ncomp) +
          "    largest holds " + format(100.0 * frac, ".1f") + "%")
    return ok


def main():
    sp = 0.2
    ok = []

    r, sweep, w = 30.0, 60.0, 1.8
    true_arc = r * np.deg2rad(sweep)
    chord = 2.0 * r * np.sin(np.deg2rad(sweep) / 2.0)
    print("case 1: curved ribbon, arc " + format(true_arc, ".2f") +
          " mm, straight chord between its ends " + format(chord, ".2f") +
          " mm -- the arc is the right answer")
    ok.append(check("curved ribbon follows the curve",
                    arc_ribbon(r, sweep, w, sp), true_arc, sp))

    print("")
    print("case 2: flat 20 x 20 mm patch -- control, must reach the diagonal")
    g = np.arange(0.0, 20.0 + sp, sp)
    X, Y = np.meshgrid(g, g, indexing="ij")
    flat = np.column_stack([X.ravel(), Y.ravel(), np.zeros(X.size)])
    ok.append(check("flat patch reaches its diagonal",
                    flat, 20.0 * np.sqrt(2.0), sp))

    print("")
    gap_at = 0.40 * true_arc
    gap = 3.0
    longer = max(gap_at, true_arc - (gap_at + gap))
    print("case 3: same ribbon with a " + format(gap, ".1f") +
          " mm gap cut at " + format(gap_at, ".2f") +
          " mm along -- must report the longer piece, " +
          format(longer, ".2f") + " mm, not the whole arc")
    ok.append(check("gap is not jumped",
                    arc_ribbon(r, sweep, w, sp, cut=(gap_at, gap_at + gap)),
                    longer, sp))

    print("")
    if all(ok):
        print("ALL THREE PASS -- the measurement recovers a known arc length,")
        print("does not saturate on an open patch, and does not cross a hole.")
        return 0
    print("GATE FAILED -- do not submit the job or quote its numbers.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
