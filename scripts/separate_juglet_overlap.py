"""Move the Juglet's reference sherds apart where the hand reassembly set them
into each other -- rigidly, all at once, and as little as possible. Writes
SEPARATE copies; the reference file is only ever opened for reading.

WHY. Job 30420351 found a third of the Juglet's join dots (33.2% of 21,675)
inside the neighbouring sherd, and 61.7% of the 8,247 dots where a break face
meets its twin. Job 30420961 drew it: at the worst join (sherds 3 and 6) the
neighbour's break face runs 0.2-0.5 mm inside; at a typical one (6 and 5) the
two faces lie on top of each other and cross back and forth within ~0.1 mm.
The conservator's reading: the sherds do match, but by hand they were set a
little too close. This script tests that reading and, if it holds, gives a
reference with no clay inside clay, so the break-face selection can be judged
on data that meets its assumption (wear-ruler grilling Q13 waits on this).

METHOD -- the standard one for this job. Reassembly pipelines end with a
simultaneous, non-penetrating rigid registration of all fragments (Huang et
al. 2006, "Reassembling fractured objects by geometric matching", ACM TOG
25(3); the 2025 survey arXiv 2410.14770 lists later ones). Here:
  * the largest sherd is held still; every other sherd gets one small turn
    and shift, all solved together, so pushing one sherd out of a neighbour
    cannot silently push it into another;
  * every dot within R_MM of a neighbouring sherd is a constraint: its signed
    distance to that sherd's surface (minus = inside) must end at or above a
    target. A dot already clear costs nothing, so real gaps are never pulled
    shut;
  * of the moves that meet the constraints, the one taken moves the sherds'
    surfaces least, counted from the ORIGINAL pose (mean squared vertex
    displacement);
  * solved by linearising, stepping at most MAX_STEP_MM, then re-measuring
    exactly (winding number for inside/outside, exact point-to-triangle
    distance), repeated until nothing is below target.

TWO TARGETS, both written:
  strict    no dot inside a neighbour (target 0 mm);
  tolerant  overlap up to one point spacing allowed -- a crossing that small
            is what the scan cannot tell apart from two faces touching.

WHAT A RIGID MOVE CAN AND CANNOT DO. It removes a sherd pushed in as a whole
(the 3-6 join). It cannot remove two rough scanned faces crossing back and
forth at one point spacing without opening a gap about that wide somewhere
else; the report prints how far each join opens, as the price. Near the rim
of a join the nearest way out of a neighbour can be through its skin, so a
sherd may also slide a little along the wall; the render shows whether the
skins still line up.

GATES, before any file is written:
  G0 (laptop) scripts/selftest_separate_juglet.py -- boxes with exact answers;
  G1 run again from the strict result: nothing may move more than 0.01 mm;
  G2 one sherd pushed 0.2 mm into its neighbour, the rest held: it must come
     back to within 0.05 mm of where the strict run put it.
"""

import argparse
import json
import multiprocessing
import os
import shutil
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import h5py
import matplotlib
import numpy as np
import trimesh
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation

matplotlib.use("Agg")
import matplotlib.pyplot as plt                                 # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from diagnose_juglet_selection import (ANTI_DOT,               # noqa: E402
                                       closest_on_triangle, join_frame,
                                       rule_masks, terms, vessel_scale,
                                       winding)
from wear_fracture_spectrum import load_sherds                  # noqa: E402

R_MM = 1.2          # dots this near a neighbour are constrained. A dot inside
                    # one sits at most half the 1.79 mm wall from its surface,
                    # and a dot further out cannot get inside in one step.
MAX_STEP_MM = 0.2   # per iteration, so the linearised turn stays accurate
TOL_MM = 0.005      # "at the target": a fortieth of a point spacing
MOVE_TOL_MM = 0.001 # converged when no vertex moves more than this in a step
REG = 0.1           # weight of "move as little as possible", in dots
PUSH_MM = 0.2       # G2's known displacement
CHUNK = 1500
_G = {}             # set before the pool forks: current vertices, triangles


def closest(q, tri, k=16):
    """Nearest point on a mesh's surface to each q, and on which triangle.

    Same search as diagnose_juglet_selection.surface_distance, so distances
    here and there agree.
    """
    _d, idx = cKDTree(tri.mean(axis=1)).query(q, k=min(k, len(tri)))
    idx = idx.reshape(len(q), -1)
    best = np.full(len(q), np.inf)
    cp, ti = np.zeros_like(q), np.zeros(len(q), dtype=np.int64)
    for col in range(idx.shape[1]):
        t = tri[idx[:, col]]
        c = closest_on_triangle(q, t[:, 0], t[:, 1], t[:, 2])
        d = np.linalg.norm(q - c, axis=1)
        b = d < best
        best[b], cp[b], ti[b] = d[b], c[b], idx[b, col]
    return best, cp, ti


def _job(task):
    """Signed distance of some of sherd i's dots to sherd j's surface.

    Also the direction in which that distance grows fastest -- what a small
    move of either sherd changes it by. Outside it points away from j's
    surface, inside it points back toward it; on the surface it is the
    triangle's outward normal (all nine sherds are wound outward).
    """
    i, j, idx = task
    q, tri = _G["V"][i][idx], _G["TRI"][j]
    d, cp, ti = closest(q, tri)
    s = np.where(winding(q, tri) > 0.5, -d, d)
    fn = np.cross(tri[ti, 1] - tri[ti, 0], tri[ti, 2] - tri[ti, 0])
    fn /= np.linalg.norm(fn, axis=1, keepdims=True) + 1e-300
    far = np.abs(s) > _G["eps"]
    gv = fn.copy()
    gv[far] = (q[far] - cp[far]) / s[far, None]
    return i, j, idx, s, cp, gv


def measure(V, TRI, pairs, workers, eps):
    """{(i, j): [dot indices, signed distance, closest point, gradient]}."""
    tasks = [(i, j, idx[a:a + CHUNK]) for (i, j), idx in pairs.items()
             for a in range(0, len(idx), CHUNK)]
    _G.update(V=V, TRI=TRI, eps=eps)
    if workers > 1:
        ctx = multiprocessing.get_context("fork")
        with ProcessPoolExecutor(workers, mp_context=ctx) as ex:
            res = list(ex.map(_job, tasks))
    else:
        res = [_job(t) for t in tasks]
    out = {}
    for i, j, *rest in res:
        out.setdefault((i, j), []).append(rest)
    return {k: [np.concatenate(z) for z in zip(*v)] for k, v in out.items()}


def candidates(V, r, movable):
    """Each sherd's dots within r of another sherd (nearest vertex)."""
    trees = [cKDTree(v) for v in V]
    pairs = {}
    for i in range(len(V)):
        for j in range(len(V)):
            if i == j or (i not in movable and j not in movable):
                continue
            d, _ = trees[j].query(V[i], k=1, distance_upper_bound=r)
            idx = np.flatnonzero(np.isfinite(d))
            if len(idx):
                pairs[(i, j)] = idx
    return pairs


def posed(V0, Rm, tr):
    return [v @ R.T + t for v, R, t in zip(V0, Rm, tr)]


def separate(V0, F, movable, tau_mm, jf, workers, label, max_iter=40):
    """Smallest rigid moves of the movable sherds that clear the target.

    Unknowns per movable sherd: a turn w (rotation vector) and a shift t about
    its current centre g. A dot p of sherd i whose nearest point on sherd j is
    c, with signed distance s and gradient n, changes to about
        s + n . (w_i x (p - g_i) + t_i) - n . (w_j x (c - g_j) + t_j).
    Every dot whose predicted value is below the target is pulled to the
    target (squared hinge, solved by repeating until the set of such dots
    stops changing); the rest are free. REG adds the mean squared displacement
    of each sherd's vertices from the ORIGINAL pose, which fixes the moves the
    constraints leave free (sliding along a join) at zero and lets a sherd
    return toward where the conservator put it whenever it can.
    """
    n = len(V0)
    Rm, tr = [np.eye(3) for _ in range(n)], [np.zeros(3) for _ in range(n)]
    g0 = [v.mean(axis=0) for v in V0]
    col = {k: c for c, k in enumerate(movable)}
    m = 6 * len(movable)
    tau, tol = tau_mm / jf, TOL_MM / jf
    allv = np.concatenate(V0)
    eps = 1e-7 * float(np.linalg.norm(allv.max(0) - allv.min(0)))
    log, converged, deepest = [], False, float("nan")
    t0 = time.time()
    for it in range(max_iter + 1):
        V = posed(V0, Rm, tr)
        TRI = [v[f] for v, f in zip(V, F)]
        meas = measure(V, TRI, candidates(V, R_MM / jf, col), workers, eps)
        A, b = [], []
        for (i, j), (idx, s, cp, gv) in meas.items():
            a = np.zeros((len(idx), m))
            if i in col:
                o = 6 * col[i]
                a[:, o:o + 3] = np.cross(V[i][idx] - V[i].mean(axis=0), gv)
                a[:, o + 3:o + 6] = gv
            if j in col:
                o = 6 * col[j]
                a[:, o:o + 3] = -np.cross(cp - V[j].mean(axis=0), gv)
                a[:, o + 3:o + 6] = -gv
            A.append(a)
            b.append(tau - s)
        A, b = np.concatenate(A), np.concatenate(b)
        deepest = float(b.max() * jf)

        D, c = np.zeros((m, m)), np.zeros(m)
        for k, cc in col.items():
            rr = V[k] - V[k].mean(axis=0)
            o = 6 * cc
            D[o:o + 3, o:o + 3] = (np.mean(np.sum(rr * rr, axis=1)) * np.eye(3)
                                   - rr.T @ rr / len(rr))
            D[o + 3:o + 6, o + 3:o + 6] = np.eye(3)
            c[o:o + 3] = Rotation.from_matrix(Rm[k]).as_rotvec()
            c[o + 3:o + 6] = V[k].mean(axis=0) - g0[k]
        act = b > 0
        for _ in range(50):
            Aa = A[act]
            x = np.linalg.solve(Aa.T @ Aa + REG * D,
                                Aa.T @ b[act] - REG * D @ c)
            new = A @ x < b
            if np.array_equal(new, act):
                break
            act = new

        reach = [np.linalg.norm(V[k] - V[k].mean(axis=0), axis=1).max()
                 for k in col]
        step = max(np.linalg.norm(x[6 * cc + 3:6 * cc + 6]) +
                   np.linalg.norm(x[6 * cc:6 * cc + 3]) * reach[cc]
                   for cc in col.values())
        below = int((b > tol).sum())
        log.append(dict(it=it, below=below, deepest_mm=deepest,
                        step_mm=float(step * jf)))
        print("  " + label + " it " + format(it, "2d") + ": " +
              format(below, "6d") + " dots below target, deepest " +
              format(deepest, "+.3f") + " mm, next step " +
              format(step * jf, ".4f") + " mm, " +
              format(time.time() - t0, ".0f") + " s", flush=True)
        if step * jf < MOVE_TOL_MM or it == max_iter:
            converged = step * jf < MOVE_TOL_MM
            break
        if step > MAX_STEP_MM / jf:
            x *= (MAX_STEP_MM / jf) / step
        for k, cc in col.items():
            o = 6 * cc
            Rs = Rotation.from_rotvec(x[o:o + 3]).as_matrix()
            g = V[k].mean(axis=0)
            Rm[k] = Rs @ Rm[k]
            tr[k] = Rs @ (tr[k] - g) + g + x[o + 3:o + 6]
    met = deepest <= TOL_MM
    print("  " + label + ": " + ("converged" if converged else
                                 "NOT CONVERGED in " + str(max_iter)) +
          ", target " + ("MET" if met else "NOT MET") + " (deepest " +
          format(deepest, "+.3f") + " mm below it)", flush=True)
    return dict(Rm=Rm, tr=tr, log=log, converged=converged, met=bool(met),
                deepest_mm=deepest)


def moves(V0, Rm, tr, jf):
    rows = []
    for k, (v, R, t) in enumerate(zip(V0, Rm, tr)):
        d = np.linalg.norm(v @ R.T + t - v, axis=1) * jf
        g = v.mean(axis=0)
        rows.append(dict(
            sherd=k, shift_mm=float(np.linalg.norm(g @ R.T + t - g) * jf),
            turn_deg=float(np.degrees(np.linalg.norm(
                Rotation.from_matrix(R).as_rotvec()))),
            mean_mm=float(d.mean()), max_mm=float(d.max())))
    return rows


def join_state(V, F, J, jf, workers):
    """Signed gap, mm, of the same join dots in a given pose."""
    TRI = [v[f] for v, f in zip(V, F)]
    allv = np.concatenate(V)
    eps = 1e-7 * float(np.linalg.norm(allv.max(0) - allv.min(0)))
    meas = measure(V, TRI, {k: idx for k, (idx, _tw) in J.items()},
                   workers, eps)
    return {k: meas[k][1] * jf for k in J}


def summarise(S, J, label):
    pc = [10, 25, 50, 75, 90]
    alls = np.concatenate([S[k] for k in J])
    tw = np.concatenate([S[k][J[k][1]] for k in J])
    # "Inside" means more than TOL_MM in: a dot the strict run leaves exactly
    # on the neighbour's surface reads -0.000001 mm and is contact, not
    # overlap. The plain below-zero share is kept for job 30420351's figures.
    r = dict(dots=int(len(alls)),
             inside_pct=float(100 * np.mean(alls < -TOL_MM)),
             below_zero_pct=float(100 * np.mean(alls < 0)),
             twin_dots=int(len(tw)),
             twin_inside_pct=float(100 * np.mean(tw < -TOL_MM)),
             twin_below_zero_pct=float(100 * np.mean(tw < 0)),
             all_gap_pct=dict(zip(map(str, pc),
                                  map(float, np.percentile(alls, pc)))),
             twin_gap_pct=dict(zip(map(str, pc),
                                   map(float, np.percentile(tw, pc)))))
    print("  " + label.ljust(9) + ": " + format(r["dots"], ",") +
          " join dots, " + format(r["inside_pct"], "5.1f") + "% inside (" +
          format(r["below_zero_pct"], ".1f") + "% below 0); " +
          format(r["twin_dots"], ",") + " face-to-face dots, " +
          format(r["twin_inside_pct"], "5.1f") + "% inside (" +
          format(r["twin_below_zero_pct"], ".1f") + "% below 0), gap mm " +
          str(pc) + ": " + "  ".join(format(x, "+.3f")
                                     for x in np.percentile(tw, pc)))
    return r


def join_table(S, J, states):
    """Per join (both directions pooled): % inside, median, 90th pct, mm."""
    keys = sorted({tuple(sorted(k)) for k in J})
    rows = []
    print("")
    print("  join    dots  | " + " | ".join(s.ljust(24) for s in states))
    print("                | " + " | ".join("inside  median     p90 "
                                            for _ in states))
    for a, b in keys:
        ks = [k for k in ((a, b), (b, a)) if k in J]
        if sum(len(J[k][0]) for k in ks) < 200:
            continue
        row = dict(join=[a, b], dots=int(sum(len(J[k][0]) for k in ks)))
        cells = []
        for st in states:
            s = np.concatenate([S[st][k] for k in ks])
            row[st] = dict(inside_pct=float(100 * np.mean(s < -TOL_MM)),
                           median_mm=float(np.median(s)),
                           p90_mm=float(np.percentile(s, 90)))
            cells.append(format(row[st]["inside_pct"], "5.1f") + "% " +
                         format(row[st]["median_mm"], "+.3f") + "  " +
                         format(row[st]["p90_mm"], "+.3f"))
        rows.append(row)
        print("  " + format(a, "d").rjust(2) + "-" + format(b, "d").ljust(2) +
              format(row["dots"], "7d") + "  | " + " | ".join(
                  c.ljust(24) for c in cells))
    return rows


def render(meshes, V0, poses, J, S, normals, jf, wall_mm, sp_mm, mv,
           anchor, out_png):
    """Before and after on the same joins, seen from the sherd on the left.

    Each cut goes straight across the join through both meshes (triangles,
    not dots). Everything is drawn in the left sherd's own frame, so its
    black line is the same in all three columns and only the blue neighbour
    moves: the picture shows the move between the two sherds, which is what
    decides whether they overlap.
    """
    from matplotlib.collections import LineCollection
    ranked = sorted((100 * np.mean(S["before"][k] < 0), k) for k in J
                    if len(J[k][0]) >= 200)
    pick = [ranked[-1][1], ranked[len(ranked) // 2][1]]
    states = [("before", "as reassembled by hand"),
              ("strict", "strict: no overlap"),
              ("tolerant", "tolerant: overlap <= 1 spacing")]
    X, H = 1.5, wall_mm / 2.0 + 0.8
    fig = plt.figure(figsize=(21, 14))
    gs = fig.add_gridspec(3, 4, height_ratios=[1, 1, 0.55])
    cut_axes, frames = [], []
    for r, (i, j) in enumerate(pick):
        idx, tw = J[(i, j)]
        Dm = np.zeros(len(V0[i]), dtype=bool)
        Dm[idx[tw]] = True
        c, Fr, chk = join_frame(V0[i], normals[i], Dm, jf, wall_mm)
        frames.append(dict(sherd=i, neighbour=j, frame=chk))
        warn = "" if chk["ok"] else "\nFRAME FAILED ITS CHECK -- do not read"
        for col, (st, name) in enumerate(states):
            Rm, tr = poses[st]
            Vj = ((V0[j] @ Rm[j].T + tr[j]) - tr[i]) @ Rm[i]
            mj = trimesh.Trimesh(Vj, meshes[j].faces, process=False)
            ax = fig.add_subplot(gs[r, col])
            cut_axes.append(ax)
            for mesh, colour in ((meshes[i], "k"), (mj, "#2e6fd1")):
                seg = trimesh.intersections.mesh_plane(mesh, Fr[:, 0], c)
                if len(seg) == 0:
                    continue
                s2 = (np.asarray(seg) - c) @ Fr * jf
                keep = np.all((np.abs(s2[:, :, 2]) < X + 0.5) &
                              (np.abs(s2[:, :, 1]) < H + 0.5), axis=1)
                ax.add_collection(LineCollection(s2[keep][:, :, [2, 1]],
                                                 colors=colour, lw=1.3))
            ax.set_xlim(-X, X)
            ax.set_ylim(-H, H)
            ax.set_aspect("equal")
            for y in (-wall_mm / 2, wall_mm / 2):
                ax.axhline(y, color="0.6", lw=0.6, ls=":")
            ax.axvline(0, color="0.8", lw=0.6)
            s = S[st][(i, j)]
            ax.set_title(name + ": sherd " + str(i) + " (black) vs " +
                         str(j) + " (blue)\n" +
                         format(100 * np.mean(s < -TOL_MM), ".0f") +
                         "% of this join's dots inside, median " +
                         format(np.median(s), "+.3f") + " mm" + warn,
                         fontsize=9.5)
            ax.set_xlabel("mm, out of sherd " + str(i) + "'s break face ->",
                          fontsize=8)
            if col == 0:
                ax.set_ylabel("mm, across the wall (dotted: " +
                              format(wall_mm, ".2f") + " mm wall)", fontsize=8)
            ax.tick_params(labelsize=7)
        ax = fig.add_subplot(gs[r, 3])
        bins = np.linspace(-0.6, 0.8, 71)
        # "before" drawn widest, so it still shows where a copy did not move
        for (st, name), colour, lw in zip(states, ("0.6", "#c0392b",
                                                   "#27ae60"), (3.2, 1.4, 1.4)):
            ax.hist(S[st][(i, j)], bins, histtype="step", color=colour,
                    lw=lw, label=name)
        ax.axvline(0, color="k", lw=0.8)
        ax.axvline(-sp_mm, color="k", lw=0.8, ls=":")
        ax.set_xlabel("signed gap, mm (left of 0 = inside the neighbour; "
                      "dotted = one spacing)", fontsize=8)
        ax.set_ylabel("join dots", fontsize=8)
        ax.legend(fontsize=7.5)
        ax.tick_params(labelsize=7)
    ax = fig.add_subplot(gs[2, :])
    k = np.arange(len(V0))
    for off, st, colour in ((-0.2, "strict", "#c0392b"),
                            (0.2, "tolerant", "#27ae60")):
        ax.bar(k + off, [row["max_mm"] for row in mv[st]], 0.38,
               color=colour, label=st + ": furthest any point of the sherd "
               "moved")
    ax.set_xticks(k, [("sherd " + str(x) + "\n(held still)") if x == anchor
                      else "sherd " + str(x) for x in k], fontsize=8)
    ax.axhline(wall_mm / 2, color="k", lw=0.8, ls=":")
    ax.text(len(V0) - 0.5, wall_mm / 2, " half the wall", fontsize=8,
            va="bottom", ha="right")
    ax.set_ylabel("mm", fontsize=8)
    ax.legend(fontsize=8, loc="upper left")
    fig.suptitle("Juglet: the sherds moved apart just enough to stop them "
                 "sitting inside each other. Top: the most overlapped join. "
                 "Middle: a typical one. Bottom: how far each sherd moved.",
                 fontsize=11.5)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.canvas.draw()
    ppm = float(np.median([a.get_window_extent().width / (2 * X)
                           for a in cut_axes]))
    fig.savefig(out_png, dpi=fig.dpi, facecolor="white")
    print("")
    print("render: " + format(ppm, ".0f") + " px per mm, so 0.1 mm is " +
          format(0.1 * ppm, ".0f") + " px -> " +
          ("RESOLVES 0.1 mm" if 0.1 * ppm >= 10 else
           "DOES NOT RESOLVE 0.1 mm -- do not read"))
    for f in frames:
        print("  frame, sherd " + str(f["sherd"]) + " vs " +
              str(f["neighbour"]) + ": rms " +
              format(f["frame"]["rms_mm"], ".2f") + " mm, span " +
              format(f["frame"]["span_mm"], ".2f") + " mm -> " +
              ("FRAME OK" if f["frame"]["ok"] else
               "FRAME FAILED -- do not read"))
    print("wrote " + out_png)
    return dict(px_per_mm=ppm, rows=frames)


def write_copy(src, dst, group, tag, keys, V, attrs):
    if Path(dst).resolve() == Path(src).resolve():
        raise SystemExit("refusing to overwrite the reference " + src)
    shutil.copyfile(src, dst)
    with h5py.File(dst, "r+") as h:
        g = h[group][tag]["pieces"]
        for k, v in zip(keys, V):
            g[k]["vertices"][...] = v
        for a, val in attrs.items():
            g.attrs[a] = val
    print("wrote " + dst)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--juglet", required=True)
    p.add_argument("--group", default="juglet_gt")
    p.add_argument("--juglet-mm", type=float, default=65.0)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--workers", type=int,
                   default=int(os.environ.get("SLURM_CPUS_PER_TASK", "1")))
    a = p.parse_args()
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Same loading and spacing as diagnose_juglet_selection.run_juglet, so the
    # "before" numbers must reproduce job 30420351 exactly.
    jf = vessel_scale(a.juglet, a.group, a.juglet_mm)
    rng = np.random.default_rng(0)
    with h5py.File(a.juglet, "r") as h:
        tag = sorted(tg for tg in h[a.group] if "pieces" in h[a.group][tg])[0]
        g = h[a.group][tag]["pieces"]
        keys = sorted(g.keys(), key=lambda s: (len(s), s))
        V0 = [np.asarray(g[k]["vertices"][:], dtype=np.float64) for k in keys]
        F = [np.asarray(g[k]["faces"][:], dtype=np.int64) for k in keys]
        sherds = load_sherds(h, a.group, tag, 200000, rng)
    assert all(np.array_equal(v, s) for v, (s, _n) in zip(V0, sherds))
    meshes = [trimesh.Trimesh(v, f, process=False) for v, f in zip(V0, F)]
    wall_mm = float(np.median([2 * abs(m.volume) / m.area * jf
                               for m in meshes]))
    allv = np.concatenate(V0)
    sp = float(np.median(cKDTree(allv).query(
        allv[rng.choice(len(allv), min(20000, len(allv)), replace=False)],
        k=2, workers=-1)[0][:, 1]))
    diag = float(np.linalg.norm(allv.max(0) - allv.min(0)))
    T = terms(sherds)
    M = [rule_masks(t, diag, sp) for t in T]
    J = {}
    for i, (t, mm) in enumerate(zip(T, M)):
        for j in np.unique(t["owner"][mm["tight"]]):
            idx = np.flatnonzero(mm["tight"] & (t["owner"] == j))
            J[(i, int(j))] = (idx, t["partner"][idx] < ANTI_DOT)
    anchor = int(np.argmax([len(v) for v in V0]))
    movable = [k for k in range(len(V0)) if k != anchor]
    sp_mm = sp * jf

    print("=" * 78)
    print("JUGLET " + tag + ": " + str(len(V0)) + " sherds, x" +
          format(jf, ".4f") + " to a " + format(a.juglet_mm, ".0f") +
          " mm vessel, wall " + format(wall_mm, ".2f") + " mm, spacing " +
          format(sp_mm, ".3f") + " mm; sherd " + str(anchor) +
          " held still; " + str(a.workers) + " workers")
    print("")
    S = {"before": join_state(V0, F, J, jf, a.workers)}
    res = dict(scale=jf, wall_mm=wall_mm, spacing_mm=sp_mm, anchor=anchor,
               summary={}, targets={})
    res["summary"]["before"] = summarise(S["before"], J, "before")
    print("    (job 30420351 read 21,675 join dots 33.2% inside, 8,247 "
          "face-to-face dots 61.7% inside)")

    poses = {"before": ([np.eye(3)] * len(V0),
                        [np.zeros(3)] * len(V0))}
    mv = {}
    for name, tau in (("strict", 0.0), ("tolerant", -sp_mm)):
        print("")
        print(name.upper() + ": every dot at least " + format(tau, "+.3f") +
              " mm from the neighbour's surface")
        r = separate(V0, F, movable, tau, jf, a.workers, name)
        poses[name] = (r["Rm"], r["tr"])
        S[name] = join_state(posed(V0, r["Rm"], r["tr"]), F, J, jf,
                             a.workers)
        mv[name] = moves(V0, r["Rm"], r["tr"], jf)
        print("  sherd   shift mm   turn deg   mean mm    max mm")
        for row in mv[name]:
            print("  " + format(row["sherd"], "5d") +
                  format(row["shift_mm"], "11.3f") +
                  format(row["turn_deg"], "11.3f") +
                  format(row["mean_mm"], "10.3f") +
                  format(row["max_mm"], "10.3f") +
                  ("   held still" if row["sherd"] == anchor else "") +
                  ("   MORE THAN HALF THE WALL -- look before accepting"
                   if row["max_mm"] > wall_mm / 2 else ""))
        res["targets"][name] = dict(
            target_mm=tau, converged=r["converged"], met=r["met"],
            deepest_mm=r["deepest_mm"], iterations=r["log"], moves=mv[name],
            transforms=[np.vstack([np.column_stack([R, t]),
                                   [0, 0, 0, 1]]).tolist()
                        for R, t in zip(r["Rm"], r["tr"])])
        res["summary"][name] = summarise(S[name], J, name)

    print("")
    print("GATE G1 -- run again from the strict result; nothing may move "
          "more than 0.01 mm")
    Vs = posed(V0, *poses["strict"])
    r1 = separate(Vs, F, movable, 0.0, jf, a.workers, "G1")
    g1 = max(row["max_mm"] for row in moves(Vs, r1["Rm"], r1["tr"], jf))
    g1_ok = bool(g1 <= 0.01 and r1["met"])
    print("  G1: furthest move " + format(g1, ".4f") + " mm -> " +
          ("PASS" if g1_ok else "FAIL"))

    kj = max((k for k in J if k[0] != anchor), key=lambda k: int(J[k][1].sum()))
    k, j = kj
    Dm = np.zeros(len(V0[k]), dtype=bool)
    Dm[J[kj][0][J[kj][1]]] = True
    _c, Fr, _chk = join_frame(V0[k], sherds[k][1], Dm, jf, wall_mm)
    dirn = poses["strict"][0][k] @ Fr[:, 2]
    print("")
    print("GATE G2 -- sherd " + str(k) + " pushed " + format(PUSH_MM, ".2f") +
          " mm into sherd " + str(j) + ", the rest held; it must come back "
          "to within 0.05 mm")
    Vp = list(Vs)
    Vp[k] = Vs[k] + (PUSH_MM / jf) * dirn
    r2 = separate(Vp, F, [k], 0.0, jf, a.workers, "G2")
    Vk = posed(Vp, r2["Rm"], r2["tr"])[k]
    off = float(np.sqrt(np.mean(np.sum((Vk - Vs[k]) ** 2, axis=1))) * jf)
    back = float(np.mean((Vk - Vp[k]) @ dirn) * jf)
    g2_ok = bool(off <= 0.05 and r2["met"])
    print("  G2: came back " + format(-back, ".3f") + " mm along the push; "
          "left " + format(off, ".3f") + " mm (rms) from its strict place -> "
          + ("PASS" if g2_ok else "FAIL"))
    res["gates"] = dict(G1_max_move_mm=g1, G1_pass=g1_ok, G2_sherd=k,
                        G2_neighbour=j, G2_back_mm=-back, G2_off_mm=off,
                        G2_pass=g2_ok)

    res["joins"] = join_table(S, J, ["before", "strict", "tolerant"])
    res["render"] = render(meshes, V0, poses, J, S,
                           [n for _v, n in sherds], jf, wall_mm, sp_mm, mv,
                           anchor, str(out / "juglet_separation.png"))

    ok = g1_ok and g2_ok and all(res["targets"][t]["met"]
                                 for t in ("strict", "tolerant"))
    if ok:
        for name in ("strict", "tolerant"):
            write_copy(a.juglet, str(out / ("juglet_gt_separated_" + name +
                                            ".hdf5")),
                       a.group, tag, keys, posed(V0, *poses[name]),
                       dict(separated_from=str(a.juglet),
                            separation_target_mm=float(
                                res["targets"][name]["target_mm"]),
                            separation_script="scripts/"
                            "separate_juglet_overlap.py"))
    else:
        print("")
        print("A GATE OR A TARGET FAILED -- no separated file written")
    (out / "juglet_separation.json").write_text(
        json.dumps(res, indent=2, default=float))
    print("wrote " + str(out / "juglet_separation.json"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
