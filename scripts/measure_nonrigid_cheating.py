"""Does the model already have the pot's shape, and lose it when the sherds go rigid?

Conservator's observation, 2026-08-10: for wear_v2 on the Juglet, generation05
looks like a convincing closed vessel while proposed_assembly05 -- the same
attempt with the sherds kept rigid -- splays apart. The nicer picture is the
less trustworthy one. Ticket .scratch/juglet-cause/issues/12 turns that into a
measurement.

The flow model moves every point independently; nothing requires a fragment to
stay rigid. So it can assemble a plausible pot by stretching and bending sherds
into place. The rigid step (`fit_transformations`, a best fit of each sherd's
true shape to wherever its points ended up) then asks the only physically
possible question: with each sherd at its true, unaltered shape, where does it
go?

Three things are measured, per draw, on the FREE sherds (the largest sherd is
pinned to its true place in every run here, so it is reported apart):

    outline    how close the cloud sits to the true vessel, ignoring which sherd
               each point belongs to. Split into `cover` (is every part of the
               true surface reached?) and `stray` (are there points off it?).
               Raw output and rigid assembly, each against the truth.

    own place  how far each sherd sits from its OWN home, matched by identity,
               never relabelled. Raw and rigid.

    bending    how far each raw point sits from the rigid placement of its own
               sherd -- exactly the best-fit residual, because point i is the
               same surface point in every cloud. Also against the sherd's own
               size, so a small sherd bent badly is not hidden by a large one
               placed well.

    mirror     what the bending IS. A sherd no solid turn fits, but which a turn
               plus a reflection fits to within the run's own jitter, came out as
               its own mirror image -- not bent at all. The rigid step cannot
               reflect (`tora/procrustes.py:30-33` forces det = +1), so it has to
               pick the nearest real orientation, and the sherd sticks out.
               Found on the Juglet 2026-09-12: every bent sherd there is a mirror.

All distances are % of pot size: the longest side of the TRUE object's box
(`readout.unit_box_scale(pts_gt)`), never the prediction's.

FIXED 2026-09-12 (ticket 12). The first version, never run, had three faults:
its ruler was the box of the PREDICTION, so a splayed assembly read as less bent
the worse it was; its verdict was a fixed 2% cut-off with no control, the fault
that once faked a whole finding here; and it counted the pinned anchor, which
reads as "not bent" by construction. There is no verdict line now. Read the
numbers against the control pots (`--npz artifacts/nb3/whole/*.npz`).

Usage:
  python scripts/measure_nonrigid_cheating.py --npz artifacts/nb3/whole/*.npz
  python scripts/measure_nonrigid_cheating.py \
      --npz artifacts/jugdraw/jugdraw_baseline_30130049/clouds/*.npz
"""

import argparse
import glob
import json
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))

from readout import TAU, chamfer, chamfer_fast, unit_box_scale  # noqa: E402

# Pots this model rebuilds when complete and unworn (ticket 04). Their numbers are
# the floor: what a CORRECT assembly carries in bending and outline error.
FLOOR_POTS = ("blue_pot", "narrow_bottle2", "narrow_bottle4", "pink_bowl")

# The evaluator's tolerance (chamfer < TAU in the unit box), as % of pot size.
SEAT_PCT = 100.0 * float(np.sqrt(TAU / 2.0))

# A sherd whose raw points sit further than this (% of pot size, mean) from every solid
# placement of it is "bent": clearly above the jitter (0.1-0.6%), below point spacing.
BENT_PCT = 1.0


def pct(c: float) -> float:
    """Chamfer in the unit-box frame -> percent of pot size."""
    return 100.0 * float(np.sqrt(max(c, 0.0) / 2.0))


def rms(d: np.ndarray) -> float:
    return 100.0 * float(np.sqrt((d ** 2).mean()))


def point_spacing(gt: np.ndarray, unit: float) -> float:
    """Mean distance from each true point to its nearest neighbour, % of pot size."""
    d, _ = cKDTree(gt).query(gt, k=2)
    return 100.0 * float(d[:, 1].mean()) / unit


def anchor_of(ids: np.ndarray) -> int:
    """The largest sherd by point count -- not part id 0, which is not size-ordered."""
    parts = sorted(set(ids.tolist()))
    return max(parts, key=lambda p: int((ids == p).sum()))


def fit_leftover(src: np.ndarray, dst: np.ndarray, allow_mirror: bool) -> float:
    """Mean distance left after the best fit of `src` onto `dst`, point i to point i.

    Kabsch. With `allow_mirror=False` it is a solid turn (det = +1), the same fit
    `fit_transformations` makes; with True it may also reflect.
    """
    a, b = src - src.mean(0), dst - dst.mean(0)
    U, _, Vt = np.linalg.svd(a.T @ b)
    D = np.eye(3)
    if not allow_mirror:
        D[2, 2] = np.sign(np.linalg.det(U @ Vt))
    return float(np.linalg.norm(a @ (U @ D @ Vt) - b, axis=1).mean())


def measure_draw(gt, pred, prop, ids):
    """Outline, own place and bending for one draw. Everything in % of pot size."""
    unit = unit_box_scale(gt)
    parts = sorted(set(ids.tolist()))
    anchor = anchor_of(ids)
    free = ids != anchor
    g, r, q = gt / unit, pred / unit, prop / unit

    out = {"anchor": anchor, "parts": parts}
    for tag, x in (("raw", r), ("rigid", q)):
        cover, _ = cKDTree(x[free]).query(g[free])
        stray, _ = cKDTree(g[free]).query(x[free])
        out[f"{tag}_cover"] = rms(cover)
        out[f"{tag}_stray"] = rms(stray)
        out[f"{tag}_outline"] = pct((cover ** 2).mean() + (stray ** 2).mean())
        out[f"{tag}_outline_whole"] = pct(chamfer_fast(g, x))
        own = {p: pct(chamfer_fast(g[ids == p], x[ids == p])) for p in parts}
        out[f"{tag}_own"] = own
        fv = [own[p] for p in parts if p != anchor]
        out[f"{tag}_own_mean"] = float(np.mean(fv))
        out[f"{tag}_own_worst"] = float(np.max(fv))
        out[f"{tag}_seated"] = int(sum(v < SEAT_PCT for v in fv))

    bend_pt = 100.0 * np.linalg.norm(r - q, axis=1)          # per point, % pot
    out["bend_point"] = bend_pt
    out["bend"] = {p: float(bend_pt[ids == p].mean()) for p in parts}
    out["bend_rel"] = {
        p: 100.0 * float(np.linalg.norm(pred[ids == p] - prop[ids == p], axis=1).mean())
        / unit_box_scale(gt[ids == p])
        for p in parts
    }
    # `bend` is already the solid-fit leftover (prop is that fit); this is the same fit
    # allowed to reflect. The true sherd is a solid copy of the input sherd, so either
    # can be the source.
    out["mirror_left"] = {p: 100.0 * fit_leftover(g[ids == p], r[ids == p], True)
                          for p in parts}
    fb = [out["bend"][p] for p in parts if p != anchor]
    fr = [out["bend_rel"][p] for p in parts if p != anchor]
    out["bend_mean"] = float(np.mean(fb))
    out["bend_worst"] = float(np.max(fb))
    out["bend_rel_worst"] = float(np.max(fr))
    out["anchor_bend"] = out["bend"][anchor]
    out["anchor_raw_own"] = out["raw_own"][anchor]
    return out


def rank_draws(per: list[dict]) -> tuple[int, int]:
    """(median draw, worst draw), ranked on how far the RIGID free sherds sit from home.

    That is the assembly every score in the map is read off, so "median" here is
    the median of what the model actually delivers.
    """
    order = sorted(range(len(per)), key=lambda k: per[k]["rigid_own_mean"])
    return order[len(order) // 2], order[-1]


def mirror_flags(per: list[dict]) -> tuple[float, list[dict]]:
    """(jitter, per draw {free sherd: "solid" | "mirror" | "deformed"}).

    Jitter is the median solid-fit leftover of the unbent free sherds in this run: what
    a sherd carries when nothing is wrong with it. It differs by arm (~0.1% of pot size
    untouched, 0.5-0.6% with an adapter), so a fixed cut-off misreads the adapter arms
    -- a 0.5% cut first called every adapter_off mirror "deformed". A bent sherd is a
    mirror when the reflecting fit leaves under three times the jitter.
    """
    anchor = per[0]["anchor"]
    free = [p for p in per[0]["parts"] if p != anchor]
    calm = [d["bend"][p] for d in per for p in free if d["bend"][p] <= BENT_PCT]
    jitter = float(np.median(calm)) if calm else float("nan")

    def kind(d, p):
        if d["bend"][p] <= BENT_PCT:
            return "solid"
        return "mirror" if d["mirror_left"][p] < 3.0 * jitter else "deformed"

    return jitter, [{p: kind(d, p) for p in free} for d in per]


def load_object(path: str) -> dict:
    d = np.load(path, allow_pickle=True)
    for key in ("generations_pred", "generations_proposed", "pts_gt", "part_ids"):
        if key not in d.files:
            raise SystemExit(f"{path} has no {key}; saved keys: {d.files}")
    return {
        "path": path,
        "name": str(d["name"]).split("/")[-1],
        "gt": d["pts_gt"],
        "ids": d["part_ids"],
        "pred": d["generations_pred"],
        "prop": d["generations_proposed"],
    }


def check_ruler(obj: dict) -> float:
    """chamfer_fast must equal readout.chamfer. Checked on a subsample, every file."""
    rng = np.random.default_rng(0)
    gt, pred = obj["gt"], obj["pred"][0]
    unit = unit_box_scale(gt)
    i = rng.choice(len(gt), size=min(800, len(gt)), replace=False)
    a, b = gt[i] / unit, pred[i] / unit
    ref, fast = chamfer(a, b), chamfer_fast(a, b)
    # The clouds are stored float32 and the dense version stays in float32, so the
    # two agree to ~1e-8 relative, not to double precision.
    if not np.isclose(ref, fast, rtol=1e-5, atol=1e-12):
        raise SystemExit(f"chamfer_fast {fast} disagrees with readout.chamfer {ref}")
    return abs(ref - fast)


def summarise(per: list[dict], key: str) -> str:
    v = np.array([p[key] for p in per], dtype=float)
    return f"{np.median(v):6.2f} [{v.min():5.2f}-{v.max():5.2f}]"


def report(obj: dict, label: str = "") -> dict:
    gt, ids = obj["gt"], obj["ids"]
    unit = unit_box_scale(gt)
    check_ruler(obj)
    per = [measure_draw(gt, obj["pred"][k], obj["prop"][k], ids)
           for k in range(len(obj["pred"]))]
    med, worst = rank_draws(per)
    anchor = per[0]["anchor"]
    n_free = len(per[0]["parts"]) - 1
    spacing = point_spacing(gt, unit)
    floor = " (floor pot)" if obj["name"] in FLOOR_POTS else ""

    print(f"\n{label or obj['name']}{floor}: {len(per[0]['parts'])} sherds "
          f"({n_free} free; sherd {anchor} is the pinned anchor), {len(per)} draws. "
          f"Points sit {spacing:.2f}% of pot size apart.")
    print(f"  {'draw':>4s} | {'outline raw':>11s} {'rigid':>6s} | "
          f"{'own place raw':>13s} {'rigid':>6s} | {'seated raw':>10s} {'rigid':>5s} | "
          f"{'bent mean':>9s} {'worst':>6s} {'worst/sherd':>11s}")
    for k, p in enumerate(per):
        tag = "  <- median" if k == med else ("  <- worst" if k == worst else "")
        print(f"  {k:>4d} | {p['raw_outline']:10.2f}% {p['rigid_outline']:5.2f}% | "
              f"{p['raw_own_mean']:12.2f}% {p['rigid_own_mean']:5.2f}% | "
              f"{p['raw_seated']:>5d}/{n_free:<4d} {p['rigid_seated']:>2d}/{n_free:<2d} | "
              f"{p['bend_mean']:8.2f}% {p['bend_worst']:5.2f}% {p['bend_rel_worst']:10.1f}%"
              f"{tag}")
    print("  median [range] over draws, % of pot size:")
    for key, what in (
        ("raw_outline", "outline, raw   "), ("rigid_outline", "outline, rigid "),
        ("raw_cover", "  cover, raw   "), ("rigid_cover", "  cover, rigid "),
        ("raw_stray", "  stray, raw   "), ("rigid_stray", "  stray, rigid "),
        ("raw_own_mean", "own place, raw "), ("rigid_own_mean", "own place, rigid"),
        ("bend_mean", "bent, mean     "), ("bend_worst", "bent, worst    "),
    ):
        print(f"    {what} {summarise(per, key)}")
    print(f"    anchor: bent {summarise(per, 'anchor_bend')}, "
          f"raw from home {summarise(per, 'anchor_raw_own')}")

    jitter, flags = mirror_flags(per)
    kinds = [f[s] for f in flags for s in f]
    print(f"  what the bending is, over {len(kinds)} free sherd-draws: "
          f"{kinds.count('mirror')} mirror images of the real sherd, "
          f"{kinds.count('deformed')} bent out of shape, {kinds.count('solid')} solid "
          f"(within {BENT_PCT:.0f}% of some turn of the real sherd; their jitter "
          f"{jitter:.2f}%)")
    for tag in ("mirror", "solid"):
        h = [per[k]["rigid_own"][s] for k, f in enumerate(flags) for s in f if f[s] == tag]
        if h:
            print(f"    {tag:6s} sherds after the rigid step: from home median "
                  f"{np.median(h):5.1f}%, seated {100 * np.mean([v < SEAT_PCT for v in h]):3.0f}%")

    p = per[med]
    print(f"  per sherd, median draw {med} (% of pot size; bent/sherd = % of the sherd's "
          f"own size):")
    for s in p["parts"]:
        n = int((ids == s).sum())
        tag = ("  <- anchor" if s == anchor else
               f"  mirror in {sum(f[s] == 'mirror' for f in flags)}/{len(per)} draws")
        print(f"     sherd {s:>2d} ({n:>4d} pts, {100 * unit_box_scale(gt[ids == s]) / unit:4.1f}% "
              f"of pot): home raw {p['raw_own'][s]:6.2f}%  rigid {p['rigid_own'][s]:6.2f}%  "
              f"bent {p['bend'][s]:5.2f}%  bent/sherd {p['bend_rel'][s]:5.1f}%{tag}")

    keep = ("raw_outline", "rigid_outline", "raw_cover", "rigid_cover", "raw_stray",
            "rigid_stray", "raw_own_mean", "rigid_own_mean", "raw_seated",
            "rigid_seated", "bend_mean", "bend_worst", "bend_rel_worst", "anchor_bend")
    return {
        "name": obj["name"], "path": obj["path"], "floor_pot": bool(floor),
        "n_free": n_free, "anchor": anchor, "spacing_pct": spacing,
        "median_draw": med, "worst_draw": worst,
        "mirror_jitter": jitter,
        "sherd_draws": {t: kinds.count(t) for t in ("solid", "mirror", "deformed")},
        "draws": [{**{k: p[k] for k in keep}, "kind": {str(s): v for s, v in f.items()}}
                  for p, f in zip(per, flags)],
        "median_per_sherd": {str(s): {"raw_own": per[med]["raw_own"][s],
                                      "rigid_own": per[med]["rigid_own"][s],
                                      "bend": per[med]["bend"][s],
                                      "bend_rel": per[med]["bend_rel"][s]}
                             for s in per[med]["parts"]},
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--npz", required=True, nargs="+", help="saved clouds (globs allowed)")
    ap.add_argument("--label", default="")
    ap.add_argument("--json", default=None, help="write every number here too")
    args = ap.parse_args()

    paths = []
    for p in args.npz:
        paths.extend(sorted(glob.glob(p)))
    if not paths:
        raise SystemExit("no npz files matched")

    print(f"All distances are % of pot size (longest side of the TRUE object's box). "
          f"Seated = own place under {SEAT_PCT:.2f}%, the evaluator's tolerance, "
          f"matched by identity (no relabelling).")
    rows = [report(load_object(p), args.label) for p in paths]

    floor = [r for r in rows if r["floor_pot"]]
    if floor:
        print("\nFLOOR -- pots this model rebuilds. Median over draws, per pot:")
        print(f"  {'pot':16s} {'outline raw':>11s} {'rigid':>6s} {'own raw':>8s} "
              f"{'rigid':>6s} {'bent mean':>9s} {'worst':>6s}")
        for r in floor:
            m = {k: float(np.median([d[k] for d in r["draws"]]))
                 for k in ("raw_outline", "rigid_outline", "raw_own_mean",
                           "rigid_own_mean", "bend_mean", "bend_worst")}
            print(f"  {r['name']:16s} {m['raw_outline']:10.2f}% {m['rigid_outline']:5.2f}% "
                  f"{m['raw_own_mean']:7.2f}% {m['rigid_own_mean']:5.2f}% "
                  f"{m['bend_mean']:8.2f}% {m['bend_worst']:5.2f}%")

    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(rows, indent=1))
        print("\nwrote", args.json)


if __name__ == "__main__":
    main()
