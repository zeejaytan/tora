"""Why the Juglet's break-face selection comes back as a scatter.

LOCAL RESULT, 2026-09-11, BEFORE THE JUGLET WAS READ: at the Juglet's geometry
the CURRENT rule (v2) passes -- 95.9-100% pure, 96.8-100% recall, ribbon as
continuous as the truth -- and the candidate replacement is the WORSE one,
recall 85.2-86.8% once normals are re-estimated from the points. So the rule
is not what makes the Juglet a scatter; this script's job became naming what
in the real data does.

JOB 30419474 (COMPLETED 0:0) named it. The files are sound -- all nine sherds
closed and wound outward -- and the gap alone finds one continuous ribbon per
face (largest piece 99.8%, median 50 mm). What scatters it is the FACING test:
on the join dots its value runs from -0.79 to +0.74 (10th to 90th percentile),
so for a tenth of them the neighbour sits squarely behind the break face.
`overlap` asks whether that is the reassembly setting sherds into each other.

WHY THIS EXISTS. Job 30386546 walked the Juglet's break faces as a graph, and
the render of that walk (job 30386693) showed it threading a sparse scatter
rather than a continuous ribbon: `wear_fracture_spectrum.mating_faces` kept
4,187 of 25,534 near points, and the largest connected piece of a face held
24% of its points against 34-59% on the simulated pots. Until the selection
holds the whole break face, nothing measured on the Juglet can be quoted, and
the Juglet is the reference (wear-ruler grilling Q4).

The current rule keeps a point that is (1) within 2% of the object diagonal of
another sherd and (2) FACING it: its normal points at the mean of its 8 nearest
points on the other sherd (dot > 0.5). The candidate replacement, proven exact
on a labelled synthetic pot (docs/notes/WEAR_SPECTRUM_GATE_A_30356470.md,
99.5-99.8% recall), is a gap within 3 point spacings AND an opposite-facing
partner: the nearest point on the other sherd has a normal pointing back
(dot < -0.7). A break face has its twin a gap away pointing back at it; outer
wall beside the join has the neighbour's outer wall pointing the same way.

That proof was on a 4.5 mm wall, a 0.10 mm gap and exact normals. The Juglet
differs on all three: a 1.79 mm wall (job 30385552); gaps of 0.21-0.28 mm
typical and 0.44-0.52 mm at the worst tenth, one to two point spacings
(.scratch/juglet-cause/issues/10); and normals averaged from a coarse mesh,
which tilt wherever the break face meets the wall -- on a wall about eight
points across, that is a large share of the face. So the proof is first redone
at the Juglet's geometry (--synthetic), with normals both exact and
re-estimated from the points, which brackets what a mesh gives. The original
geometry is rerun alongside as a control: if this harness does not reproduce
the proven 99%+ recall there, nothing it says about the Juglet counts. Then the
real Juglet is read term by term (--juglet), so the test doing the rejecting is
named from the data rather than guessed.

FOUR RULES, side by side:
  v2     near (2% of diagonal) + facing      -- what job 30386546 used
  tight  gap < 3 spacings, no normal test    -- what the normal tests buy
  tfa    tight + facing + opposite partner   -- the candidate as proven
  ta     tight + opposite partner            -- drops the facing test

THE RENDER resolves the wall. A slab 1 mm thick is cut ACROSS the break and
drawn at equal aspect so the 1.8 mm wall spans well over 100 px (the pixel
figure is measured from the drawn axes and printed, not assumed). A correct
rule paints the break face as one line across the full wall and leaves the
outer and inner skins grey. A second row looks straight at the break face over
12 mm of its length, to show whether the kept points form a ribbon or a
scatter.
"""

import argparse
import json
import sys
from pathlib import Path

import h5py
import matplotlib
import numpy as np
import trimesh
from scipy.spatial import cKDTree

matplotlib.use("Agg")
import matplotlib.pyplot as plt                                 # noqa: E402

sys.path.insert(0, __file__.rsplit("scripts", 1)[0] + "scripts")
import selftest_wear_spectrum_pot as pot                        # noqa: E402
from measure_strip_feasibility import traceable_length          # noqa: E402
from wear_fracture_spectrum import (BAND_FRAC, MATING_DOT,      # noqa: E402
                                    MATING_K, load_sherds)

TIGHT_SPACINGS = pot.TIGHT_SPACINGS     # 3.0, as proven
ANTI_DOT = pot.ANTI_DOT                 # -0.70, as proven
MIN_FACE = 400                          # same floor as mating_faces
PASS_PCT = 90.0                         # purity and recall both at least this
RULES = [("v2", "v2: near 2% diag + facing"),
         ("tight", "gap < 3 spacings only"),
         ("tfa", "gap + facing + opposite"),
         ("ta", "gap + opposite partner")]


def terms(sherds):
    """Per sherd and per point: gap, facing dot, partner-normal dot."""
    out = []
    for i, (v, n) in enumerate(sherds):
        others = np.concatenate([w for j, (w, _) in enumerate(sherds)
                                 if j != i])
        onrm = np.concatenate([m for j, (_, m) in enumerate(sherds) if j != i])
        own = np.concatenate([np.full(len(w), j)
                              for j, (w, _) in enumerate(sherds) if j != i])
        d, idx = cKDTree(others).query(v, k=MATING_K, workers=-1)
        u = others[idx].mean(axis=1) - v
        u /= np.linalg.norm(u, axis=1, keepdims=True) + 1e-12
        out.append(dict(gap=d[:, 0], facing=np.sum(n * u, axis=1),
                        partner=np.sum(n * onrm[idx[:, 0]], axis=1),
                        owner=own[idx[:, 0]], foot=others[idx[:, 0]]))
        del others, onrm, own
    return out


def rule_masks(t, diag, sp):
    tight = t["gap"] < TIGHT_SPACINGS * sp
    face = t["facing"] > MATING_DOT
    anti = t["partner"] < ANTI_DOT
    return dict(v2=(t["gap"] < BAND_FRAC * diag) & face, tight=tight,
                tfa=tight & face & anti, ta=tight & anti)


def continuity(sherds, masks, sp, scale):
    """Per face a rule keeps: (points, largest connected share, arc mm)."""
    rows = []
    for (v, _n), m in zip(sherds, masks):
        if int(m.sum()) < MIN_FACE:
            continue
        run, _nc, frac = traceable_length(v[m], sp, scale)
        rows.append((int(m.sum()), float(frac), float(run)))
    return rows


def pca_normals(pts, ref, k=8):
    """Normals re-estimated from the points alone, signed to agree with ref.

    Blurs across the corner where the break face meets the wall, which is what
    a coarse mesh's averaged vertex normals do too. This is the harsher side of
    the bracket: k = 8 neighbours reach about 0.35 mm at 0.22 mm spacing, so
    more of the face is tilted than on a mesh, where only the crease row is.
    """
    _d, idx = cKDTree(pts).query(pts, k=k, workers=-1)
    nb = pts[idx] - pts[idx].mean(axis=1, keepdims=True)
    _w, vec = np.linalg.eigh(np.einsum("nki,nkj->nij", nb, nb))
    n = vec[:, :, 0]
    return n * np.sign(np.sum(n * ref, axis=1) + 1e-12)[:, None]


def winding(q, tri, budget=2_000_000):
    """Generalised winding number of points q about a closed triangle mesh.

    About 1 inside and 0 outside, from the solid angle each triangle subtends
    (Van Oosterom-Strackee). Needs no normals and no ray library -- the tora
    env has neither rtree nor embree, so trimesh's `contains` cannot run there.
    Exact for a closed mesh, and all nine Juglet sherds are closed.
    """
    w = np.empty(len(q))
    step = max(1, budget // len(tri))
    for s in range(0, len(q), step):
        d = tri[None] - q[s:s + step, None, None, :]
        a, b, c = d[:, :, 0], d[:, :, 1], d[:, :, 2]
        la, lb, lc = (np.linalg.norm(x, axis=2) for x in (a, b, c))
        num = np.einsum("mfi,mfi->mf", a, np.cross(b, c))
        den = (la * lb * lc + np.einsum("mfi,mfi->mf", a, b) * lc +
               np.einsum("mfi,mfi->mf", b, c) * la +
               np.einsum("mfi,mfi->mf", c, a) * lb)
        w[s:s + step] = np.arctan2(num, den).sum(axis=1) / (2.0 * np.pi)
    return w


def closest_on_triangle(p, a, b, c):
    """Closest point on each triangle to each point (Ericson, RTCD 5.1.5)."""
    ab, ac = b - a, c - a
    dot = lambda x, y: np.sum(x * y, axis=1)                    # noqa: E731
    d1, d2 = dot(ab, p - a), dot(ac, p - a)
    d3, d4 = dot(ab, p - b), dot(ac, p - b)
    d5, d6 = dot(ab, p - c), dot(ac, p - c)
    va, vb, vc = d3 * d6 - d5 * d4, d5 * d2 - d1 * d6, d1 * d4 - d3 * d2
    with np.errstate(divide="ignore", invalid="ignore"):
        den = va + vb + vc
        out = a + ab * (vb / den)[:, None] + ac * (vc / den)[:, None]
        # Regions in reverse priority, so the earlier tests in Ericson win.
        m = (va <= 0) & (d4 - d3 >= 0) & (d5 - d6 >= 0)
        t = (d4 - d3) / ((d4 - d3) + (d5 - d6))
        out[m] = b[m] + t[m, None] * (c - b)[m]
        m = (vb <= 0) & (d2 >= 0) & (d6 <= 0)
        t = d2 / (d2 - d6)
        out[m] = a[m] + t[m, None] * ac[m]
        m = (d6 >= 0) & (d5 <= d6)
        out[m] = c[m]
        m = (vc <= 0) & (d1 >= 0) & (d3 <= 0)
        t = d1 / (d1 - d3)
        out[m] = a[m] + t[m, None] * ab[m]
        m = (d3 >= 0) & (d4 <= d3)
        out[m] = b[m]
        m = (d1 <= 0) & (d2 <= 0)
        out[m] = a[m]
    return out


def surface_distance(q, tri, k=16):
    """Exact distance from each point to the nearest of a mesh's triangles.

    Nearest-vertex distance would not do: the overlaps in question are about
    one point spacing deep, the same size as that shortcut's error.
    """
    _d, idx = cKDTree(tri.mean(axis=1)).query(q, k=min(k, len(tri)),
                                              workers=-1)
    idx = idx.reshape(len(q), -1)
    best = np.full(len(q), np.inf)
    for col in range(idx.shape[1]):
        t = tri[idx[:, col]]
        best = np.minimum(best, np.linalg.norm(
            q - closest_on_triangle(q, t[:, 0], t[:, 1], t[:, 2]), axis=1))
    return best


def overlap(sherds, tris, T, M, jf, push_mm=0.05, n_ctrl=500):
    """Does the hand reassembly put clay inside clay?

    WHY. On the Juglet's join points the facing test is spread almost evenly
    from -1 to +1 (job 30419474): for a tenth of them the neighbour sits
    squarely BEHIND the break face. One reading is that the reassembly sets
    neighbouring sherds slightly into each other, and ticket 10's gaps of
    0.21-0.28 mm could not show it, because a nearest-dot distance has no sign.
    This asks the question without normals: is each join dot inside the closed
    neighbouring sherd, and how far from its surface.

    PREDICTION, WRITTEN BEFORE THE RUN. If overlap is the cause, a third or more
    of the join dots lie inside the neighbour, and far more of them where the
    facing test fails (dot <= 0) than where it passes (dot > 0.5). If under 5%
    are inside, overlap is refuted and the mesh's surface directions are the
    suspect instead.

    CONTROL FIRST. Each sherd's own dots pushed push_mm inward along their
    normals must read inside, and pushed outward must read outside, at 95% or
    more -- else the inside test is not trusted and nothing below it is printed.
    """
    rng = np.random.default_rng(1)
    push = push_mm / jf
    ins_ok, out_ok = [], []
    for (v, n), tri in zip(sherds, tris):
        s = rng.choice(len(v), min(n_ctrl, len(v)), replace=False)
        ins_ok.append(winding(v[s] - push * n[s], tri) > 0.5)
        out_ok.append(winding(v[s] + push * n[s], tri) < 0.5)
    p_in = 100 * np.mean(np.concatenate(ins_ok))
    p_out = 100 * np.mean(np.concatenate(out_ok))
    trusted = p_in >= 95.0 and p_out >= 95.0
    print("")
    print("  OVERLAP -- is the neighbouring sherd's clay behind the break face?")
    print("  prediction: overlap is the cause if >= 1/3 of join dots are inside "
          "the neighbour, mostly where facing fails; refuted if < 5%")
    print("  control: own dots pushed " + format(push_mm, ".2f") + " mm in read "
          "inside " + format(p_in, ".1f") + "%, pushed out read outside " +
          format(p_out, ".1f") + "%  -> " +
          ("TRUSTED" if trusted else "NOT TRUSTED -- reading withheld"))
    res = dict(control_inside_pct=p_in, control_outside_pct=p_out,
               trusted=bool(trusted))
    if not trusted:
        return res

    sg, fac, par, pair = [], [], [], []
    SG = [np.full(len(v), np.nan) for v, _ in sherds]
    for i, ((v, _n), t, mm) in enumerate(zip(sherds, T, M)):
        tight = mm["tight"]
        for j in np.unique(t["owner"][tight]):
            sel = tight & (t["owner"] == j)
            q = v[sel]
            inside = winding(q, tris[j]) > 0.5
            dist = surface_distance(q, tris[j]) * jf
            SG[i][sel] = np.where(inside, -dist, dist)
            sg.append(SG[i][sel])
            fac.append(t["facing"][sel])
            par.append(t["partner"][sel])
            pair.append(np.full(int(sel.sum()), i * 100 + int(j)))
    sg, fac, par, pair = map(np.concatenate, (sg, fac, par, pair))
    ins = sg < 0
    pc = [10, 25, 50, 75, 90]
    fail, ok, opp = fac <= 0.0, fac > MATING_DOT, par < ANTI_DOT

    def pct(m):
        return 100 * np.sum(ins & m) / max(int(m.sum()), 1)

    def pcts(x):
        return np.percentile(x, pc) if len(x) else np.full(len(pc), np.nan)

    print("  on the " + str(len(sg)) + " join dots (gap < 3 spacings): " +
          format(100 * ins.mean(), ".1f") + "% lie INSIDE the neighbouring "
          "sherd")
    print("    signed gap, mm (minus = overlap), percentiles " + str(pc) + ": " +
          "  ".join(format(x, "6.3f") for x in np.percentile(sg, pc)))
    print("    where facing FAILS (dot <= 0, " + str(int(fail.sum())) +
          " dots): " + format(pct(fail), ".1f") + "% inside;  where it PASSES "
          "(dot > " + format(MATING_DOT, ".2f") + ", " + str(int(ok.sum())) +
          " dots): " + format(pct(ok), ".1f") + "% inside")
    print("    break face against its twin (partner dot < " +
          format(ANTI_DOT, ".2f") + ", " + str(int(opp.sum())) + " dots): " +
          format(pct(opp), ".1f") + "% inside; signed gap " +
          "  ".join(format(x, "6.3f") for x in pcts(sg[opp])))
    print("    per join, sherd against sherd (>= 200 dots): dots, % inside, "
          "median and 10th-percentile signed gap mm")
    rows = []
    for key in np.unique(pair):
        m = pair == key
        if m.sum() < 200:
            continue
        r = (int(key // 100), int(key % 100), int(m.sum()),
             float(100 * ins[m].mean()), float(np.median(sg[m])),
             float(np.percentile(sg[m], 10)))
        rows.append(r)
        print("      " + format(r[0], "2d") + " vs " + format(r[1], "2d") +
              format(r[2], "7d") + format(r[3], "8.1f") + "%" +
              format(r[4], "9.3f") + format(r[5], "9.3f"))
    res.update(dots=int(len(sg)), inside_pct=float(100 * ins.mean()),
               signed_gap_pct=dict(zip(map(str, pc),
                                       map(float, np.percentile(sg, pc)))),
               inside_where_facing_fails_pct=float(pct(fail)),
               inside_where_facing_passes_pct=float(pct(ok)),
               inside_on_twin_faces_pct=float(pct(opp)), joins=rows,
               _sg=SG)     # per-dot, for render_overlap; popped before JSON
    return res


def med(xs):
    xs = [x for x in xs if np.isfinite(x)]
    return float(np.median(xs)) if xs else float("nan")


def synthetic_case(wall, gap, step, label, H=0.5):
    """One labelled pot. Returns {normal mode: {rule: stats}}."""
    pot.WALL, pot.GAP, pot.STEP = wall, gap, step
    rough = pot.rough_field(H)
    built = [pot.shell(+1.0, rough), pot.shell(-1.0, rough)]
    allv = np.concatenate([v for v, _, _ in built])
    rng = np.random.default_rng(0)
    sp = float(np.median(cKDTree(allv).query(
        allv[rng.choice(len(allv), 20000, replace=False)],
        k=2, workers=-1)[0][:, 1]))
    diag = float(np.linalg.norm(allv.max(0) - allv.min(0)))
    labs = [lab for _, _, lab in built]

    print("")
    print("=" * 78)
    print(label + ": wall " + format(wall, ".2f") + " mm, gap " +
          format(gap, ".2f") + " mm, point spacing " + format(sp, ".3f") +
          " mm (gap = " + format(gap / sp, ".1f") + " spacings)")
    print("  v2 band " + format(BAND_FRAC * diag, ".2f") + " mm; tight gate " +
          format(TIGHT_SPACINGS * sp, ".2f") + " mm")

    (vA, nA, lA), (vB, nB, lB) = built
    dd, ii = cKDTree(vB[lB == 4]).query(vA[lA == 4], k=1, workers=-1)
    pdot = np.sum(nA[lA == 4] * nB[lB == 4][ii], axis=1)
    print("  geometry: face-to-face gap median " +
          format(float(np.median(dd)), ".3f") + " mm, partner dot median " +
          format(float(np.median(pdot)), ".3f") + " (must be ~ -1)")
    if np.median(pdot) > -0.9:
        print("  GEOMETRY INVALID -- the two faces are not one surface pulled "
              "apart. Nothing below counts for this case.")
        return None

    res = {}
    for mode in ("exact", "estimated"):
        sherds = [(v, n if mode == "exact" else pca_normals(v, n))
                  for v, n, _ in built]
        T = terms(sherds)
        M = [rule_masks(t, diag, sp) for t in T]
        truth = [lab == 4 for lab in labs]
        tr = continuity(sherds, truth, sp, 1.0)
        onb = np.concatenate([t["facing"][lab == 4] for t, lab in zip(T, labs)])
        opb = np.concatenate([t["partner"][lab == 4] for t, lab in zip(T, labs)])
        gpb = np.concatenate([t["gap"][lab == 4] for t, lab in zip(T, labs)])
        print("")
        print("  normals " + mode.upper() + ".  On the true break face: gap < "
              "3 spacings " + format(100 * np.mean(gpb < TIGHT_SPACINGS * sp),
                                     "5.1f") + "%, facing " +
              format(100 * np.mean(onb > MATING_DOT), "5.1f") +
              "%, opposite partner " +
              format(100 * np.mean(opb < ANTI_DOT), "5.1f") + "%")
        print("    " + "rule".ljust(28) + "purity".rjust(8) + "recall".rjust(8) +
              "kept".rjust(8) + "largest piece".rjust(15) + "arc mm".rjust(9))
        print("    " + "TRUTH".ljust(28) + "".rjust(24) +
              format(100 * med([r[1] for r in tr]), "14.1f") + "%" +
              format(med([r[2] for r in tr]), "9.2f"))
        res[mode] = {}
        for key, name in RULES:
            masks = [mm[key] for mm in M]
            tp = sum(int(((lab == 4) & m).sum()) for lab, m in zip(labs, masks))
            sel = sum(int(m.sum()) for m in masks)
            tot = sum(int((lab == 4).sum()) for lab in labs)
            pur = 100.0 * tp / sel if sel else float("nan")
            rec = 100.0 * tp / tot if tot else float("nan")
            rows = continuity(sherds, masks, sp, 1.0)
            ok = pur >= PASS_PCT and rec >= PASS_PCT
            print("    " + name.ljust(28) + format(pur, "7.1f") + "%" +
                  format(rec, "7.1f") + "%" + format(sel, "8d") +
                  format(100 * med([r[1] for r in rows]), "14.1f") + "%" +
                  format(med([r[2] for r in rows]), "9.2f") +
                  ("   pass" if ok else "   FAIL"))
            res[mode][key] = dict(purity=pur, recall=rec, kept=sel,
                                  largest=med([r[1] for r in rows]),
                                  arc=med([r[2] for r in rows]), ok=ok)
    return res


def run_synthetic():
    out = {}
    ctl = synthetic_case(4.5, 0.10, 0.20, "CONTROL -- the geometry the rule "
                         "was proven on")
    out["control"] = ctl
    good = (ctl is not None and ctl["exact"]["tfa"]["recall"] >= 99.0
            and ctl["exact"]["tfa"]["purity"] >= 99.0)
    print("")
    if not good:
        print("CONTROL FAILED -- this harness does not reproduce the proven "
              "99%+ recall. Nothing it says about the Juglet counts.")
        return out, False
    print("CONTROL PASSED -- the harness reproduces the proven result.")
    out["juglet_typical"] = synthetic_case(
        1.79, 0.24, 0.22, "JUGLET GEOMETRY, typical join gap")
    out["juglet_worst"] = synthetic_case(
        1.79, 0.48, 0.22, "JUGLET GEOMETRY, worst-tenth join gap")
    return out, True


def join_frame(v, n, D, jf, wall_mm, max_rms=0.3):
    """Local frame on ONE join, from its face-to-face dots D, with a check.

    Replaces frame_at, which centred on the middle of every gap-only dot on the
    sherd. On a sherd with three joins that can land at a corner, and within
    1.2 mm on a 1.79 mm wall the gap-only dots include both skins, so its plane
    fit tilted: job 30420351's picture showed a "face" running 3 mm across a
    1.79 mm wall. It resolved the scale and showed the wrong thing.

    D here is one join's twins (partner dot < -0.7). The frame passes only if
    those dots within 3 mm lie on a plane (rms <= max_rms mm; a skin mixed in
    gives about 1 mm) and, in a 1 mm slice, span 0.5-1.5 walls across it.
    Columns of F: along the break, across the wall, out of the face (toward
    the neighbour).
    """
    P, N = v[D], n[D]
    c = P[np.argmin(np.linalg.norm(P - np.median(P, axis=0), axis=1))]
    near = np.linalg.norm(P - c, axis=1) < 3.0 / jf
    loc = P[near] - P[near].mean(axis=0)
    _w, vec = np.linalg.eigh(loc.T @ loc)
    n0, e_al = vec[:, 0], vec[:, 2]
    if np.mean(N[near] @ n0) < 0:
        n0 = -n0
    F = np.column_stack([e_al, np.cross(n0, e_al), n0])
    q = (P[near] - c) @ F * jf
    rms = float(np.sqrt(np.mean((q[:, 2] - q[:, 2].mean()) ** 2)))
    slab = np.abs(q[:, 0]) < 0.5
    span = float(np.ptp(q[slab, 1])) if slab.sum() >= 3 else float("nan")
    ok = bool(rms <= max_rms and 0.5 * wall_mm <= span <= 1.5 * wall_mm)
    return c, F, dict(dots=int(near.sum()), rms_mm=rms, span_mm=span, ok=ok)


def render(sherds, T, M, jf, wall_mm, out_png):
    i = int(np.argmax([int(mm["tight"].sum()) for mm in M]))
    t, tt = T[i], M[i]["tight"]
    j = int(np.bincount(t["owner"][tt]).argmax())
    # The frame only sets the viewing angle; it does not decide what is red.
    c, F, chk = join_frame(sherds[i][0], sherds[i][1],
                           tt & (t["owner"] == j) & (t["partner"] < ANTI_DOT),
                           jf, wall_mm)
    q = [(v - c) @ F * jf for v, _n in sherds]
    qi = q[i]
    half = wall_mm / 2.0 + 0.8
    X = 2.5     # mm either side of the join; +-4 gave 95 px across the wall

    fig, axes = plt.subplots(2, 4, figsize=(19, 9.2))
    px = []
    for col, (key, name) in enumerate(RULES):
        m = M[i][key]
        ax = axes[0, col]
        s = np.abs(qi[:, 0]) < 0.5
        s &= (np.abs(qi[:, 1]) < half + 0.6) & (np.abs(qi[:, 2]) < X)
        for j in range(len(q)):
            if j == i:
                continue
            o = q[j]
            so = (np.abs(o[:, 0]) < 0.5) & (np.abs(o[:, 1]) < half + 0.6) & \
                (np.abs(o[:, 2]) < X)
            ax.scatter(o[so, 2], o[so, 1], s=5, c="#5b8fd6", lw=0)
        ax.scatter(qi[s & ~m, 2], qi[s & ~m, 1], s=7, c="#9a9a9a", lw=0)
        ax.scatter(qi[s & m, 2], qi[s & m, 1], s=9, c="#c0392b", lw=0)
        ax.set_xlim(-X, X)
        ax.set_ylim(-(half + 0.6), half + 0.6)
        ax.set_aspect("equal")
        ax.axhline(wall_mm / 2, color="k", lw=0.5, ls=":")
        ax.axhline(-wall_mm / 2, color="k", lw=0.5, ls=":")
        ax.set_title(name + "\nkept on this sherd: " + str(int(m.sum())),
                     fontsize=10)
        ax.set_xlabel("mm, across the join (this sherd left, blue = "
                      "neighbour)", fontsize=8)
        if col == 0:
            ax.set_ylabel("mm, across the wall\n(dotted = measured wall " +
                          format(wall_mm, ".2f") + " mm)", fontsize=8)
        ax.tick_params(labelsize=7)

        ax2 = axes[1, col]
        s2 = (np.abs(qi[:, 0]) < 6.0) & (np.abs(qi[:, 1]) < half + 0.6) & \
            (qi[:, 2] > -1.0) & (qi[:, 2] < 0.6)
        ax2.scatter(qi[s2 & ~m, 0], qi[s2 & ~m, 1], s=6, c="#9a9a9a", lw=0)
        ax2.scatter(qi[s2 & m, 0], qi[s2 & m, 1], s=8, c="#c0392b", lw=0)
        ax2.set_xlim(-6.0, 6.0)
        ax2.set_ylim(-(half + 0.6), half + 0.6)
        ax2.set_aspect("equal")
        ax2.set_xlabel("mm, along the break (looking straight at the face)",
                       fontsize=8)
        if col == 0:
            ax2.set_ylabel("mm, across the wall", fontsize=8)
        ax2.tick_params(labelsize=7)

    fig.suptitle("Juglet sherd " + str(i) + ": which points each rule keeps "
                 "as break face (red). Top: a 1 mm slice cut across the join -- "
                 "a correct rule paints one red line spanning the wall at the "
                 "gap, and\nleaves the outer and inner skins (the horizontal "
                 "grey rows) grey. Bottom: looking straight at the break face "
                 "over 12 mm -- a correct rule gives a continuous red ribbon.",
                 fontsize=10.5)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.canvas.draw()
    for ax in axes[0]:
        bb = ax.get_window_extent()
        px.append(bb.width / (2.0 * X))
    fig.savefig(out_png, dpi=fig.dpi, facecolor="white")
    ppm = float(np.median(px))
    print("")
    print("render: sherd " + str(i) + ", " + format(ppm, ".0f") +
          " px per mm in the top row, so the " + format(wall_mm, ".2f") +
          " mm wall spans " + format(ppm * wall_mm, ".0f") + " px and one "
          "point spacing about " + format(ppm * 0.22, ".0f") + " px")
    print("  RESOLVES THE WALL" if ppm * wall_mm >= 100 else
          "  DOES NOT RESOLVE THE WALL -- do not read the picture")
    print("  frame on the join with sherd " + str(j) + ": twins within 3 mm "
          "lie " + format(chk["rms_mm"], ".2f") + " mm rms off one plane and "
          "span " + format(chk["span_mm"], ".2f") + " mm across the wall  -> " +
          ("FRAME OK" if chk["ok"] else
           "FRAME FAILED ITS CHECK -- do not read the picture"))
    print("wrote " + out_png)
    return dict(sherd=i, neighbour=j, px_per_mm=ppm, frame=chk)


def render_overlap(meshes, sherds, T, M, SG, jf, wall_mm, joins, out_png):
    """Draw the overlap itself: the most overlapped join and a typical one.

    Three cuts straight across the join, 2 mm apart along it, through BOTH
    meshes -- the triangles, not the dots, so a crossing smaller than one
    point spacing still shows. Black is this sherd's surface, blue the
    neighbour's. Where the blue line runs to the left of the black one, the
    reassembly has put the neighbour's clay inside this sherd. The fourth
    panel looks straight at the break face and colours every join dot by its
    measured signed gap (red inside the neighbour, blue clear of it).
    """
    from matplotlib.collections import LineCollection
    by_pct = sorted(joins, key=lambda r: r[3])
    pick = [by_pct[-1], by_pct[len(by_pct) // 2]]
    X, H = 1.5, wall_mm / 2.0 + 0.8
    fig, axes = plt.subplots(2, 4, figsize=(20, 10.5))
    rows_out = []
    for row, (i, j, ndots, pin, msg, p10) in enumerate(pick):
        v, n = sherds[i]
        t, tt = T[i], M[i]["tight"]
        c, F, chk = join_frame(v, n, tt & (t["owner"] == j) &
                               (t["partner"] < ANTI_DOT), jf, wall_mm)
        warn = "" if chk["ok"] else "\nFRAME FAILED ITS CHECK -- do not read"
        for col, a in enumerate((-2.0, 0.0, 2.0)):
            ax = axes[row, col]
            for mesh, colour in ((meshes[i], "k"), (meshes[j], "#2e6fd1")):
                seg = trimesh.intersections.mesh_plane(
                    mesh, F[:, 0], c + F[:, 0] * (a / jf))
                if len(seg) == 0:
                    continue
                s2 = (np.asarray(seg) - c) @ F * jf
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
            ax.set_title("sherd " + str(i) + " (black) against " + str(j) +
                         " (blue), cut at " + format(a, "+.0f") +
                         " mm along the join" + warn, fontsize=9.5)
            ax.set_xlabel("mm, out of this sherd's break face ->", fontsize=8)
            if col == 0:
                ax.set_ylabel("mm, across the wall (dotted: " +
                              format(wall_mm, ".2f") + " mm wall)", fontsize=8)
            ax.tick_params(labelsize=7)
        ax = axes[row, 3]
        sel = tt & (t["owner"] == j)
        q = (v[sel] - c) @ F * jf
        w = (np.abs(q[:, 0]) < 6.0) & (np.abs(q[:, 1]) < H) & \
            (np.abs(q[:, 2]) < 1.0)
        sc = ax.scatter(q[w, 0], q[w, 1], c=SG[i][sel][w], cmap="RdBu",
                        vmin=-0.3, vmax=0.3, s=12, lw=0)
        ax.set_xlim(-6.0, 6.0)
        ax.set_ylim(-H, H)
        ax.set_aspect("equal")
        ax.set_title("face-on, 12 mm of the break: " + format(pin, ".0f") +
                     "% of dots\ninside the neighbour, median " +
                     format(msg, "+.3f") + " mm" + warn, fontsize=9.5)
        ax.set_xlabel("mm, along the break", fontsize=8)
        ax.tick_params(labelsize=7)
        fig.colorbar(sc, ax=ax, shrink=0.6,
                     label="signed gap, mm (red = inside the neighbour)")
        rows_out.append(dict(sherd=i, neighbour=j, frame=chk))
        print("  overlap render row " + str(row) + ": sherd " + str(i) +
              " vs " + str(j) + ", frame rms " + format(chk["rms_mm"], ".2f") +
              " mm, span " + format(chk["span_mm"], ".2f") + " mm -> " +
              ("FRAME OK" if chk["ok"] else "FRAME FAILED -- do not read"))
    fig.suptitle("Juglet: do the reassembled sherds sit inside each other? "
                 "Each cut goes straight across a join through both sherds' "
                 "surfaces. Top row: the most overlapped join. Bottom: a "
                 "typical one.", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.canvas.draw()
    ppm = float(np.median([ax.get_window_extent().width / (2 * X)
                           for ax in axes[:, :3].ravel()]))
    fig.savefig(out_png, dpi=fig.dpi, facecolor="white")
    print("  overlap render: " + format(ppm, ".0f") + " px per mm, so 0.1 mm "
          "is " + format(0.1 * ppm, ".0f") + " px -> " +
          ("RESOLVES 0.1 mm" if 0.1 * ppm >= 10 else
           "DOES NOT RESOLVE 0.1 mm -- do not read"))
    print("wrote " + out_png)
    return dict(px_per_mm=ppm, rows=rows_out)


def vessel_scale(path, group, juglet_mm):
    """File units to mm: the vessel's longest extent is juglet_mm."""
    lo, hi = np.full(3, np.inf), np.full(3, -np.inf)
    with h5py.File(path, "r") as h:
        for tg in h[group]:
            if "pieces" not in h[group][tg]:
                continue
            for k in h[group][tg]["pieces"]:
                v = np.asarray(h[group][tg]["pieces"][k]["vertices"][:],
                               dtype=np.float64)
                lo, hi = np.minimum(lo, v.min(0)), np.maximum(hi, v.max(0))
    return juglet_mm / float((hi - lo).max())


def run_juglet(path, group, juglet_mm, max_pts, out_png, scale_from=None):
    rng = np.random.default_rng(0)
    # A separated copy is a fraction of a mm wider; --scale-from keeps it on
    # the original's ruler, so before and after read in the same millimetres.
    jf = vessel_scale(scale_from or path, group, juglet_mm)
    with h5py.File(path, "r") as h:
        tag = sorted(tg for tg in h[group] if "pieces" in h[group][tg])[0]
        g = h[group][tag]["pieces"]
        keys = sorted(g.keys(), key=lambda s: (len(s), s))
        info, walls, tris, meshes = [], [], [], []
        for k in keys:
            m = trimesh.Trimesh(
                vertices=np.asarray(g[k]["vertices"][:], dtype=np.float64),
                faces=np.asarray(g[k]["faces"][:], dtype=np.int64),
                process=False)
            tris.append(np.asarray(m.vertices)[np.asarray(m.faces)])
            meshes.append(m)
            vol = float(m.volume)
            info.append(dict(sherd=k, verts=int(len(m.vertices)),
                             volume_sign=int(np.sign(vol)),
                             watertight=bool(m.is_watertight),
                             winding_consistent=bool(m.is_winding_consistent)))
            if m.area > 0:
                walls.append(2.0 * abs(vol) / float(m.area) * jf)
        sherds = load_sherds(h, group, tag, max_pts, rng)
    wall_mm = float(np.median(walls))
    allv = np.concatenate([v for v, _ in sherds])
    sp = float(np.median(cKDTree(allv).query(
        allv[rng.choice(len(allv), min(20000, len(allv)), replace=False)],
        k=2, workers=-1)[0][:, 1]))
    diag = float(np.linalg.norm(allv.max(0) - allv.min(0)))
    T = terms(sherds)
    M = [rule_masks(t, diag, sp) for t in T]

    print("")
    print("=" * 78)
    print("REAL JUGLET " + tag + ": " + str(len(sherds)) + " sherds, x" +
          format(jf, ".4f") + " to a " + format(juglet_mm, ".0f") +
          " mm vessel, wall " + format(wall_mm, ".2f") + " mm, spacing " +
          format(sp * jf, ".3f") + " mm")
    print("  v2 band " + format(BAND_FRAC * diag * jf, ".2f") +
          " mm; tight gate " + format(TIGHT_SPACINGS * sp * jf, ".2f") + " mm")
    print("")
    print("  sherd  verts  winding  closed   gap<3sp  of those: facing  "
          "opposite   kept v2  tight   tfa    ta")
    for s, (inf, t, mm) in enumerate(zip(info, T, M)):
        tt = mm["tight"]
        nt = max(int(tt.sum()), 1)
        print("  " + inf["sherd"].rjust(5) + format(inf["verts"], "7d") +
              ("  outward" if inf["volume_sign"] > 0 else "  INWARD ") +
              ("  yes  " if inf["watertight"] else "  no   ") +
              format(int(tt.sum()), "9d") +
              format(100 * np.sum(t["facing"][tt] > MATING_DOT) / nt, "15.1f") +
              "%" + format(100 * np.sum(t["partner"][tt] < ANTI_DOT) / nt,
                           "9.1f") + "%" +
              format(int(mm["v2"].sum()), "10d") +
              format(int(mm["tight"].sum()), "7d") +
              format(int(mm["tfa"].sum()), "6d") +
              format(int(mm["ta"].sum()), "6d"))

    fac = np.concatenate([t["facing"][mm["tight"]] for t, mm in zip(T, M)])
    par = np.concatenate([t["partner"][mm["tight"]] for t, mm in zip(T, M)])
    pc = [10, 25, 50, 75, 90]
    print("")
    print("  on the gap<3sp points, percentiles " + str(pc) + ":")
    print("    facing dot   (kept if > " + format(MATING_DOT, ".2f") + ")  " +
          "  ".join(format(x, "6.2f") for x in np.percentile(fac, pc)))
    print("    partner dot  (kept if < " + format(ANTI_DOT, ".2f") + ")  " +
          "  ".join(format(x, "6.2f") for x in np.percentile(par, pc)))

    res = dict(scale=jf, wall_mm=wall_mm, spacing_mm=sp * jf, sherds=info,
               rules={})
    print("")
    print("  " + "rule".ljust(28) + "kept".rjust(8) + "faces".rjust(7) +
          "largest piece".rjust(15) + "arc mm, median".rjust(16) +
          "   per face arc mm")
    for key, name in RULES:
        masks = [mm[key] for mm in M]
        rows = continuity(sherds, masks, sp, jf)
        kept = sum(int(m.sum()) for m in masks)
        print("  " + name.ljust(28) + format(kept, "8d") +
              format(len(rows), "7d") +
              format(100 * med([r[1] for r in rows]), "14.1f") + "%" +
              format(med([r[2] for r in rows]), "16.2f") + "   " +
              " ".join(format(r[2], ".1f") for r in sorted(rows,
                                                           key=lambda r: r[2])))
        res["rules"][key] = dict(kept=kept, faces=[list(r) for r in rows])
    # The inside test needs each sherd's dots to be its mesh's own vertices.
    assert [len(v) for v, _ in sherds] == [x["verts"] for x in info], \
        "load_sherds subsampled; raise --max-pts"
    res["overlap"] = overlap(sherds, tris, T, M, jf)
    SG = res["overlap"].pop("_sg", None)
    res["render"] = render(sherds, T, M, jf, wall_mm, out_png)
    if SG is not None and res["overlap"].get("joins"):
        res["overlap_render"] = render_overlap(
            meshes, sherds, T, M, SG, jf, wall_mm, res["overlap"]["joins"],
            str(Path(out_png).with_name(Path(out_png).stem + "_overlap.png")))
    return res


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--synthetic", action="store_true")
    p.add_argument("--juglet")
    p.add_argument("--group", default="juglet_gt")
    p.add_argument("--juglet-mm", type=float, default=65.0)
    p.add_argument("--max-pts", type=int, default=200000)
    p.add_argument("--scale-from", help="take the mm scale from this file "
                   "(the original reference, when reading a separated copy)")
    p.add_argument("--out-json", default="artifacts/juglet_selection.json")
    p.add_argument("--out-png", default="artifacts/juglet_selection.png")
    a = p.parse_args()

    out, ok = {}, True
    if a.synthetic:
        out["synthetic"], ok = run_synthetic()
    if a.juglet and ok:
        out["juglet"] = run_juglet(a.juglet, a.group, a.juglet_mm, a.max_pts,
                                   a.out_png, a.scale_from)
    Path(a.out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out_json).write_text(json.dumps(out, indent=2, default=float))
    print("wrote " + a.out_json)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
