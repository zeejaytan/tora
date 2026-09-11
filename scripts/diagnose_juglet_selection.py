"""Why the Juglet's break-face selection comes back as a scatter.

LOCAL RESULT, 2026-09-11, BEFORE THE JUGLET WAS READ: at the Juglet's geometry
the CURRENT rule (v2) passes -- 95.9-100% pure, 96.8-100% recall, ribbon as
continuous as the truth -- and the candidate replacement is the WORSE one,
recall 85.2-86.8% once normals are re-estimated from the points. So the rule
is not what makes the Juglet a scatter; this script's job became naming what
in the real data does.

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


def frame_at(sherd, t, tmask, jf):
    """A point in the middle of the break, and the along/across/normal axes.

    Taken from the gap-only points, so the frame does not depend on the normal
    tests being compared.
    """
    v, _n = sherd
    P = v[tmask]
    c = P[np.argmin(np.linalg.norm(P - np.median(P, axis=0), axis=1))]
    r = np.linalg.norm(P - c, axis=1)
    loc = P[r < 1.2 / jf] - c
    _w, vec = np.linalg.eigh(loc.T @ loc)
    n0 = vec[:, 0]
    if np.mean((t["foot"][tmask][r < 1.2 / jf] - c) @ n0) < 0:
        n0 = -n0
    loc3 = P[r < 3.0 / jf] - c
    loc3 = loc3 - np.outer(loc3 @ n0, n0)
    _w3, v3 = np.linalg.eigh(loc3.T @ loc3)
    e_al = v3[:, 2]
    e_ac = np.cross(n0, e_al)
    return c, np.column_stack([e_al, e_ac, n0])


def render(sherds, T, M, jf, wall_mm, out_png):
    i = int(np.argmax([int(mm["tight"].sum()) for mm in M]))
    c, F = frame_at(sherds[i], T[i], M[i]["tight"], jf)
    q = [(v - c) @ F * jf for v, _n in sherds]
    qi = q[i]
    half = wall_mm / 2.0 + 0.8

    fig, axes = plt.subplots(2, 4, figsize=(19, 9.2))
    px = []
    for col, (key, name) in enumerate(RULES):
        m = M[i][key]
        ax = axes[0, col]
        s = np.abs(qi[:, 0]) < 0.5
        s &= (np.abs(qi[:, 1]) < half + 0.6) & (np.abs(qi[:, 2]) < 4.0)
        for j in range(len(q)):
            if j == i:
                continue
            o = q[j]
            so = (np.abs(o[:, 0]) < 0.5) & (np.abs(o[:, 1]) < half + 0.6) & \
                (np.abs(o[:, 2]) < 4.0)
            ax.scatter(o[so, 2], o[so, 1], s=5, c="#5b8fd6", lw=0)
        ax.scatter(qi[s & ~m, 2], qi[s & ~m, 1], s=7, c="#9a9a9a", lw=0)
        ax.scatter(qi[s & m, 2], qi[s & m, 1], s=9, c="#c0392b", lw=0)
        ax.set_xlim(-4.0, 4.0)
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
        px.append(bb.width / 8.0)
    fig.savefig(out_png, dpi=fig.dpi, facecolor="white")
    ppm = float(np.median(px))
    print("")
    print("render: sherd " + str(i) + ", " + format(ppm, ".0f") +
          " px per mm in the top row, so the " + format(wall_mm, ".2f") +
          " mm wall spans " + format(ppm * wall_mm, ".0f") + " px and one "
          "point spacing about " + format(ppm * 0.22, ".0f") + " px")
    print("  RESOLVES THE WALL" if ppm * wall_mm >= 100 else
          "  DOES NOT RESOLVE THE WALL -- do not read the picture")
    print("wrote " + out_png)
    return dict(sherd=i, px_per_mm=ppm)


def run_juglet(path, group, juglet_mm, max_pts, out_png):
    rng = np.random.default_rng(0)
    with h5py.File(path, "r") as h:
        lo, hi = np.full(3, np.inf), np.full(3, -np.inf)
        for tg in h[group]:
            if "pieces" not in h[group][tg]:
                continue
            for k in h[group][tg]["pieces"]:
                v = np.asarray(h[group][tg]["pieces"][k]["vertices"][:],
                               dtype=np.float64)
                lo, hi = np.minimum(lo, v.min(0)), np.maximum(hi, v.max(0))
        jf = juglet_mm / float((hi - lo).max())
        tag = sorted(tg for tg in h[group] if "pieces" in h[group][tg])[0]
        g = h[group][tag]["pieces"]
        keys = sorted(g.keys(), key=lambda s: (len(s), s))
        info, walls = [], []
        for k in keys:
            m = trimesh.Trimesh(
                vertices=np.asarray(g[k]["vertices"][:], dtype=np.float64),
                faces=np.asarray(g[k]["faces"][:], dtype=np.int64),
                process=False)
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
    res["render"] = render(sherds, T, M, jf, wall_mm, out_png)
    return res


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--synthetic", action="store_true")
    p.add_argument("--juglet")
    p.add_argument("--group", default="juglet_gt")
    p.add_argument("--juglet-mm", type=float, default=65.0)
    p.add_argument("--max-pts", type=int, default=200000)
    p.add_argument("--out-json", default="artifacts/juglet_selection.json")
    p.add_argument("--out-png", default="artifacts/juglet_selection.png")
    a = p.parse_args()

    out, ok = {}, True
    if a.synthetic:
        out["synthetic"], ok = run_synthetic()
    if a.juglet and ok:
        out["juglet"] = run_juglet(a.juglet, a.group, a.juglet_mm, a.max_pts,
                                   a.out_png)
    Path(a.out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out_json).write_text(json.dumps(out, indent=2, default=float))
    print("wrote " + a.out_json)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
