"""Known-answer gate (G0) for separate_juglet_overlap.py.

The separation moves sherds apart by the least that stops any of them sitting
inside another. Before it touches the Juglet it has to get boxes right, where
the right move is exact:

  * one box 0.1 mm into a held one must come out 0.1 mm, straight, unturned;
  * boxes 0.1 mm apart, or exactly touching, must not move at all -- this is
    the case that could fail: a solver that always pushed apart passes the
    first test and would open every real gap on the Juglet;
  * three boxes in a row, each 0.1 mm into the next, the first held: the
    middle one must move 0.1 and the far one 0.2, which only happens if all
    are solved together;
  * with 0.05 mm of overlap allowed, the first pair must move 0.05;
  * a box turned 3 degrees into its neighbour must come clear while moving
    no more, on average, than the plain shift that would clear it.

The boxes in each set differ in height so no edge lies exactly on another
box's side, where inside and outside would be a tie.

    python scripts/selftest_separate_juglet.py     # exit 0 = all pass
"""
import sys
from pathlib import Path

import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parent))
from separate_juglet_overlap import moves, separate            # noqa: E402

fails = 0


def check(name, got, want, tol):
    global fails
    got, want = np.asarray(got, float), np.asarray(want, float)
    ok = bool(np.all(np.abs(got - want) <= tol))
    fails += not ok
    print(("PASS " if ok else "FAIL ") + name + "\n   got  " +
          np.array2string(got, precision=4) + "\n   want " +
          np.array2string(want, precision=4))


def box(cx, e, turn_deg=0.0):
    m = trimesh.creation.box(extents=[2, e, e])
    m = m.subdivide().subdivide().subdivide().subdivide()
    m.apply_translation([cx, 0, 0])
    if turn_deg:
        m.apply_transform(trimesh.transformations.rotation_matrix(
            np.radians(turn_deg), [0, 0, 1], point=[cx - 1.0, 0, 0]))
    return m


def run(boxes, movable, tau=0.0):
    V0 = [np.asarray(m.vertices, dtype=np.float64) for m in boxes]
    F = [np.asarray(m.faces, dtype=np.int64) for m in boxes]
    r = separate(V0, F, movable, tau, 1.0, 1, "  test", max_iter=20)
    dx = [float((v.mean(0) @ R.T + t - v.mean(0))[0])
          for v, R, t in zip(V0, r["Rm"], r["tr"])]
    return r, moves(V0, r["Rm"], r["tr"], 1.0), dx


def main():
    r, mv, dx = run([box(0.0, 2.0), box(1.9, 1.8)], [1])
    check("0.1 into a held box: comes out 0.1 mm", dx[1], 0.1, 2e-3)
    check("  ... unturned", mv[1]["turn_deg"], 0.0, 0.05)
    check("  ... target met, converged", [r["met"], r["converged"]], [1, 1], 0)
    check("  ... held box untouched", mv[0]["max_mm"], 0.0, 1e-12)

    for sep in (0.1, 0.0):
        r, mv, dx = run([box(0.0, 2.0), box(2.0 + sep, 1.8)], [1])
        check("boxes " + format(sep, ".1f") + " apart: nothing moves",
              mv[1]["max_mm"], 0.0, 1e-3)

    r, mv, dx = run([box(0.0, 2.0), box(1.9, 1.8), box(3.8, 1.6)], [1, 2])
    check("three in a row: middle 0.1, far 0.2", dx[1:], [0.1, 0.2], 3e-3)
    check("  ... target met", [r["met"]], [1], 0)

    r, mv, dx = run([box(0.0, 2.0), box(1.9, 1.8)], [1], tau=-0.05)
    check("0.05 mm overlap allowed: comes out 0.05 mm", dx[1], 0.05, 2e-3)

    r, mv, dx = run([box(0.0, 2.0), box(2.0, 1.8, turn_deg=3.0)], [1])
    shift = 0.9 * np.sin(np.radians(3.0))
    check("turned 3 deg into its neighbour: cleared", [r["met"]], [1], 0)
    check("  ... mean move no more than the plain shift " +
          format(shift, ".4f") + " mm", max(mv[1]["mean_mm"], shift), shift,
          1e-3)

    print("\nALL PASS" if not fails else "\n" + str(fails) + " FAILED")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
