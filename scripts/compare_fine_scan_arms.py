#!/usr/bin/env python3
"""What does taking the sherd-worn fix change in the fine-scan wear? Vertex by vertex.

Written for sherd-worn ticket 05. The package departs from TORA's wear in one
function, `_proud_height`: its fit keeps every point instead of thinning to 60000
(FIX 07b), a fit steeper than 1 reports nothing (FIX 07), and `blunt_asperities`
caps a height at the cutoff R. Rebuilding wear_trainset_v2 cannot show the effect:
that build rescales each object by its largest offset and does not store the
factor, so one moved vertex shifts every number in the object. So this calls
`apply_wear` with the build's own VARIANTS, chips and seeds, and compares before
that step.

Four arms on one object, from the same chips and contact bands:

    A  master
    B  master with the thinning off (A to B is the thinning alone)
    C  the package (B to C is the guards alone)
    D  the package, with the exposure heights taken from B

D is there because of one line of `blunt_asperities`. It divides every vertex's
exposure by the standard deviation of ALL the exposure heights on the piece, so a
guard that zeroes one vertex's exposure height changes that divisor, and through
it every vertex whose removed fraction is below 1. That reach is the whole piece,
so B to C cannot be held to a distance rule. B to D can: with exposure shared, a
change can only spread from a caught vertex by refitting on the moved surface.

`blunt_asperities`'s output is what is classed, because `band_limit` runs after
it on the scan variants and spreads any change to its neighbours. Final output
is reported too.

CAUGHT means: inside arm C or D, master's unthinned `_proud_height` and the
package's were called on the same input and differ, or the package's exceeds the
radius. A changed vertex is then caught, a neighbour (within 4R of a caught vertex
on the blunting input), or neither.

Exit 0 only if all of these hold:
  - wear_context and the input to blunting match across arms;
  - fresh and fresh_scan, which never blunt, match across arms;
  - A to B changes nothing on a piece of 60000 vertices or fewer;
  - B to D has no vertex in "neither";
  - B to C has no vertex in "neither" on a piece whose exposure divisor did not change;
  - no vertex moves further than R in blunting in C or D.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
import time
from pathlib import Path

import h5py
import numpy as np
from scipy.spatial import cKDTree


MAX_REF = 60000
NEAR = 4.0                      # the neighbour rule, in cutoffs
COMPARISONS = (("A", "B"), ("B", "C"), ("B", "D"), ("A", "C"))
CLASSED = {("B", "C"): "C", ("B", "D"): "D"}
TOP = 3


def load_libs(master_scripts):
    """Master's modules by name, and the package's. Master's path must come first."""
    sys.path.insert(0, str(Path(master_scripts).resolve()))
    old = importlib.import_module("wear_ops")
    build = importlib.import_module("build_wear_trainset_v2")
    # not `import sherd_worn.wear as w`: the attribute `wear` is the function wear()
    sw = importlib.import_module("sherd_worn.wear")
    assert old._proud_height.__module__ == "wear_ops", "master's wear_ops is not master's"
    assert inspect.signature(old._proud_height).parameters["max_ref"].default == MAX_REF
    assert inspect.signature(sw._proud_height).parameters["max_ref"].default == np.inf
    return old, build, sw


def load_pieces(src, dataset, obj):
    with h5py.File(src, "r") as f:
        grp = f[dataset][obj]
        g = grp["pieces"] if "pieces" in grp else grp
        keys = sorted(g.keys(), key=lambda s: int(s) if s.isdigit() else s)
        return [(np.asarray(g[k]["vertices"][:], dtype=np.float64),
                 np.asarray(g[k]["faces"][:], dtype=np.int64)) for k in keys]


def make_plan(old, build, seed):
    """Each variant's arguments, with its chips drawn once so every arm gets the same."""
    rng = np.random.default_rng(seed)
    plan = []
    for vi, (vname, kw) in enumerate(build.VARIANTS):
        kw = dict(kw)
        if kw.pop("_chips", True):
            _, chip_kw = old.sample_chip_level(rng)
        else:
            chip_kw = dict(chip_count=0, chip_size=0.0)
        plan.append((vname, dict(kw, **chip_kw, seed=seed + vi)))
    return plan


def run_arm(arm, lib, old_height, pieces, masks, dirs, plan):
    """One arm over all variants: blunting's input and output, final output, what was caught."""
    orig_blunt, orig_height = lib.blunt_asperities, lib._proud_height
    state = {}

    def height_b(v, idx, nrm, radius, **kw):
        return orig_height(v, idx, nrm, radius, **dict(kw, max_ref=np.inf))

    def height_checked(v, idx, nrm, radius, **kw):
        h_new = orig_height(v, idx, nrm, radius, **kw)
        t0 = time.perf_counter()
        h_old = old_height(v, idx, nrm, radius, **dict(kw, max_ref=np.inf))
        state["check_seconds"] += time.perf_counter() - t0
        # blunting takes the pieces in order, and each starts with its one exposure call
        exposure_call = radius > 1.5 * state["R"]
        if exposure_call:
            state["cursor"] += 1
        i = state["order"][state["cursor"]]
        assert len(v) == len(state["caught"][i]) and np.array_equal(idx, state["bands"][i])
        if exposure_call:
            state["s"][i] = [float(np.std(h_old)), float(np.std(h_new))]
            if arm == "D":
                return h_old
        state["caught"][i][idx[(h_new != h_old) | (h_new > radius)]] = True
        return h_new

    def blunt_recorded(cur, cut_frac=0.004, **kw):
        state["input"] = [v.copy() for v, _ in cur]
        state["faces"] = [f.copy() for _, f in cur]
        state["R"] = cut_frac * (np.linalg.norm(np.concatenate(state["input"]).max(0)
                                                - np.concatenate(state["input"]).min(0)) + 1e-9)
        state["bands"] = [np.where(kw["masks"][i][1] > 0.02)[0] for i in range(len(cur))]
        state["order"] = [i for i, band in enumerate(state["bands"]) if len(band)]
        state["cursor"] = -1
        out = orig_blunt(cur, cut_frac=cut_frac, **kw)
        state["blunted"] = [v.copy() for v, _ in out]
        return out

    lib.blunt_asperities = blunt_recorded
    if arm == "B":
        lib._proud_height = height_b
    elif arm in ("C", "D"):
        lib._proud_height = height_checked
    results = {}
    try:
        for vname, kw in plan:
            state.update(input=None, blunted=None, faces=None, R=None, check_seconds=0.0,
                         s=[None] * len(pieces),
                         caught=[np.zeros(len(v), dtype=bool) for v, _ in pieces])
            t0 = time.perf_counter()
            out = lib.apply_wear(pieces, masks=masks, dirs=dirs, **kw)
            seconds = time.perf_counter() - t0 - state["check_seconds"]
            results[vname] = dict(input=state["input"], blunted=state["blunted"],
                                  faces=state["faces"], R=state["R"],
                                  final=[v.copy() for v, _ in out], seconds=seconds,
                                  caught=state["caught"], s=state["s"])
            print(f"  arm {arm} {vname}: {seconds:.1f} s net"
                  f" (check {state['check_seconds']:.1f} s)", flush=True)
    finally:
        lib.blunt_asperities, lib._proud_height = orig_blunt, orig_height
    return results


def same_arrays(xs, ys):
    return len(xs) == len(ys) and all(x.tobytes() == y.tobytes() for x, y in zip(xs, ys))


def classify(left, right, base, caught, R):
    """Changed vertices of one piece, split into caught, neighbour and neither."""
    changed = np.any(left != right, axis=1)
    near = np.zeros(len(base), dtype=bool)
    if caught.any() and changed.any():
        d, _ = cKDTree(base[caught]).query(base[changed], k=1)
        near[np.where(changed)[0]] = d <= NEAR * R
    is_caught = changed & caught
    neighbour = changed & ~caught & near
    neither = changed & ~caught & ~near
    return int(is_caught.sum()), int(neighbour.sum()), int(neither.sum()), neither


def compare_variant(obj, vname, arms, pieces, failures, worst):
    rows = []
    any_arm = arms["A"][vname]
    blunts = any_arm["blunted"] is not None
    R = any_arm["R"]
    for stage in ("blunted", "final"):
        if stage == "blunted" and not blunts:
            continue
        for la, ra in COMPARISONS:
            for i, (v0, _) in enumerate(pieces):
                left, right = arms[la][vname][stage][i], arms[ra][vname][stage][i]
                move = np.linalg.norm(left - right, axis=1)
                row = dict(object=obj, variant=vname, stage=stage, comparison=f"{la}-{ra}",
                           piece=i, vertices=len(v0), changed=int(np.any(left != right, axis=1).sum()),
                           largest_move=float(move.max()) if len(move) else 0.0,
                           R=R, largest_move_in_R=float(move.max() / R) if R else None)
                if stage == "blunted" and (la, ra) in CLASSED:
                    src = arms[CLASSED[(la, ra)]][vname]
                    caught, near, neither, neither_mask = classify(
                        left, right, src["input"][i], src["caught"][i], R)
                    row.update(caught=caught, neighbour=near, neither=neither,
                               caught_in_all=int(src["caught"][i].sum()),
                               largest_move_neither=float(move[neither_mask].max()) if neither else 0.0)
                    s = arms["C"][vname]["s"][i]
                    row["exposure_divisor_changed"] = bool(s is not None and s[0] != s[1])
                    if neither and (ra == "D" or not row["exposure_divisor_changed"]):
                        failures.append(f"{obj} {vname} piece {i} {la}-{ra}: {neither} in neither")
                # blunted only: band_limit's scale is the whole object, so a thinned piece
                # can reach a small one's final output through the object's extent
                if stage == "blunted" and (la, ra) == ("A", "B") and len(v0) <= MAX_REF and row["changed"]:
                    failures.append(f"{obj} {vname} piece {i} ({len(v0)} vertices) A-B: "
                                    f"{row['changed']} changed with no thinning to remove")
                if stage == "blunted" and row["changed"] and f"{la}-{ra}" != "B-D":
                    key = f"{la}-{ra}"
                    for j in np.argsort(move)[::-1][:TOP]:
                        worst.setdefault(key, []).append(
                            (float(move[j]), vname, i, int(j)))
                    worst[key] = sorted(worst[key], reverse=True)[:TOP]
                rows.append(row)
    if blunts:
        for arm in "ABCD":
            a = arms[arm][vname]
            for i, (v0, _) in enumerate(pieces):
                m = np.linalg.norm(a["input"][i] - a["blunted"][i], axis=1)
                rows.append(dict(object=obj, variant=vname, stage="blunting", comparison=arm,
                                 piece=i, vertices=len(v0), moved_past_R=int((m > R).sum()),
                                 largest_move=float(m.max()), R=R,
                                 largest_move_in_R=float(m.max() / R)))
                if arm in "CD" and m.max() > R * (1 + 1e-9):
                    failures.append(f"{obj} {vname} piece {i} arm {arm}: moved {m.max() / R:.3f} R")
    return rows


def render_worst(obj, arms, worst, out):
    """Input, then both arms, side-on to the move. The coordinator looks; nothing is judged here."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    for key, items in worst.items():
        la, ra = key.split("-")
        for rank, (move, vname, i, j) in enumerate(items):
            a, b = arms[la][vname], arms[ra][vname]
            R = a["R"]
            base, left, right = a["input"][i], a["blunted"][i], b["blunted"][i]
            f = a["faces"][i]        # a chip's seal can change the faces, never the vertex count
            near = np.linalg.norm(base - base[j], axis=1) <= 6.0 * R
            crop = f[near[f].all(axis=1)]
            np.savez_compressed(out / f"worst_{obj}_{key}_{rank}.npz", faces=crop, vertex=j, R=R,
                                move=move, variant=vname, piece=i,
                                input=base[near], left=left[near], right=right[near],
                                kept=np.where(near)[0])
            d = right[j] - left[j]
            view = np.cross(d, [0.0, 0.0, 1.0])
            if np.linalg.norm(view) < 1e-12:
                view = np.array([1.0, 0.0, 0.0])
            view /= np.linalg.norm(view)
            elev = np.degrees(np.arcsin(view[2]))
            azim = np.degrees(np.arctan2(view[1], view[0]))
            fig = plt.figure(figsize=(15, 5))
            for k, (name, v) in enumerate((("before blunting", base),
                                           (f"arm {la}", left), (f"arm {ra}", right))):
                ax = fig.add_subplot(1, 3, k + 1, projection="3d")
                ax.add_collection3d(Poly3DCollection(v[crop], facecolor="0.8", edgecolor="0.3",
                                                     linewidths=0.2))
                ax.scatter(*v[j], color="red", s=20)
                c = base[j]
                ax.set_xlim(c[0] - 6 * R, c[0] + 6 * R)
                ax.set_ylim(c[1] - 6 * R, c[1] + 6 * R)
                ax.set_zlim(c[2] - 6 * R, c[2] + 6 * R)
                ax.set_box_aspect((1, 1, 1))
                ax.view_init(elev=elev, azim=azim)
                ax.set_title(name)
            fig.suptitle(f"{obj} {vname} piece {i} vertex {j}: {key} moved {move:.5g} = "
                         f"{move / R:.2f} R (red dot); box is 12 R wide")
            fig.savefig(out / f"worst_{obj}_{key}_{rank}.png", dpi=130)
            plt.close(fig)


def run_object(obj, args, old, build, sw, out):
    print(f"== {obj}", flush=True)
    pieces = load_pieces(args.src, args.src_dataset, obj)
    print(f"  piece vertex counts: {[len(v) for v, _ in pieces]}", flush=True)
    failures, rows = [], []

    t0 = time.perf_counter()
    masks_old, dirs_old = old.wear_context(pieces)
    context_seconds = time.perf_counter() - t0
    masks_new, dirs_new = sw.wear_context(pieces)
    for (h0, f0), (h1, f1) in zip(masks_old, masks_new):
        if not same_arrays([np.asarray(h0), np.asarray(f0)], [np.asarray(h1), np.asarray(f1)]):
            failures.append(f"{obj}: wear_context bands differ")
    if not same_arrays(dirs_old, dirs_new):
        failures.append(f"{obj}: wear_context directions differ")

    plan = make_plan(old, build, args.seed)
    arms = {}
    for arm, lib, masks, dirs in (("A", old, masks_old, dirs_old), ("B", old, masks_old, dirs_old),
                                  ("C", sw, masks_new, dirs_new), ("D", sw, masks_new, dirs_new)):
        arms[arm] = run_arm(arm, lib, old._proud_height, pieces, masks, dirs, plan)

    worst = {}
    for vname, _ in plan:
        ref = arms["A"][vname]
        for arm in "BCD":
            other = arms[arm][vname]
            if (ref["input"] is None) != (other["input"] is None):
                failures.append(f"{obj} {vname}: arm {arm} blunted and A did not, or the reverse")
            elif ref["input"] is not None and not same_arrays(ref["input"], other["input"]):
                failures.append(f"{obj} {vname}: input to blunting differs, A against {arm}")
            if ref["input"] is None and not same_arrays(ref["final"], other["final"]):
                failures.append(f"{obj} {vname}: never blunts, yet A and {arm} differ")
        rows += compare_variant(obj, vname, arms, pieces, failures, worst)

    render_worst(obj, arms, worst, out)
    times = {arm: sum(arms[arm][vname]["seconds"] for vname, _ in plan) for arm in "ABCD"}
    res = dict(object=obj, pieces=[len(v) for v, _ in pieces], seconds_per_arm=times,
               wear_context_seconds=context_seconds, failures=failures, rows=rows)
    (out / f"fine_scan_{obj}.json").write_text(json.dumps(res, indent=1))
    print(f"  seconds per arm: { {k: round(v) for k, v in times.items()} }", flush=True)
    print(f"  failures: {len(failures)}", flush=True)
    for line in failures[:20]:
        print(f"    {line}", flush=True)
    return res


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--master-scripts", required=True, help="scripts/ of TORA before the switch")
    ap.add_argument("--src", required=True)
    ap.add_argument("--src-dataset", default="real_finetune")
    ap.add_argument("--objects", nargs="+", required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    old, build, sw = load_libs(args.master_scripts)
    pkg = importlib.import_module("sherd_worn")
    print(f"master wear_ops: {old.__file__}\npackage: {pkg.__version__} {pkg.__file__}", flush=True)

    done = [run_object(obj, args, old, build, sw, out) for obj in args.objects]
    failures = [line for r in done for line in r["failures"]]
    summary = dict(passed=not failures, n_failures=len(failures), failures=failures[:200],
                   objects=args.objects, package_version=pkg.__version__,
                   seconds_per_arm={r["object"]: r["seconds_per_arm"] for r in done})
    (out / "fine_scan_summary.json").write_text(json.dumps(summary, indent=1))
    print(f"PASSED={summary['passed']} failures={len(failures)}", flush=True)
    raise SystemExit(0 if summary["passed"] else 1)


if __name__ == "__main__":
    main()
