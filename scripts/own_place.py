"""Sherds seated in THEIR OWN place -- the count U10 is decided on.

Ticket `.scratch/u10-juglet-ceiling/issues/01`; spec module 8 in the umbrella
`.scratch/u10-juglet-ceiling/spec.md`; question `intent/U10` (umbrella).

WHY A SECOND COUNT. The evaluator's part accuracy lets look-alike sherds swap. It
pairs predicted and true sherds by Hungarian matching on "is this pair within
tolerance", so a rim sherd sitting in its neighbour's place counts as seated.
That suits Breaking Bad, where many pieces are interchangeable. It does not suit
U10: a shape prior can make a pot look more like a juglet by filling places with
the wrong sherds (PF++ does exactly that, `puzzlefusion-plusplus/intent/P1`), and
the swap-allowed count would reward it. So sherd i counts here only if it sits
within tolerance of TRUE sherd i. Identity, never relabelled.

Both counts are always printed side by side, on one ruler:

    own place     sherd i within tolerance of its own home
    swap-allowed  the evaluator's count, reproduced exactly (`--reconcile` checks
                  it against the run's results/*.json, draw by draw)

THE RULER. Chamfer as pytorch3d 0.7.8 computes it (`readout.chamfer`), in the
unit box -- the object divided by the longest side of its TRUE bounding box --
under `readout.TAU` = 0.01. As a distance that is 7.1% of pot size, about 4.6 mm
on the 65 mm Juglet. "How far off" is the same chamfer as a % of pot size (`pct`,
the convention of `measure_nonrigid_cheating.py`). On the Juglet, pot size IS its
height: the longest side of its box is the upright axis.

WHICH CLOUD. A run saves two answers per draw, and both are scored:

    raw    `generations_pred`. The flow model's own output, every point moved on
           its own. The evaluator scores this one (`tora/modeling/tora.py`,
           test_step hands it the last step of the flow), so every Juglet number
           so far was read off it.
    solid  `generations_proposed`. Each TRUE sherd, unaltered, moved by the one
           rigid turn-and-shift that best fits where its points ended up: the
           only assembly a conservator could actually glue. It cannot reflect, so
           a sherd the raw output drew as its own mirror image (juglet-cause/12)
           can be seated raw and not solid.

U10 decides on SOLID, with raw reported beside it (conservator, 2026-09-14): a seat
nobody could glue does not count. `decide()` reads whichever counts it is handed;
`--decide` prints the deciding reading on solid first, then raw, and says so if
they differ.

THE ANCHOR is handled exactly as readout.py handles it: counted among the n
sherds ("5 of 9" includes it), never dropped. It is the largest sherd by point
count. In every Juglet run so far it is pinned -- its raw points equal its true
points to the bit -- so it is always seated and the contest is over the other
n-1. The scorer checks that per object and says so. If an anchor is ever off its
home, the evaluator (anchor-free mode) first fits it back by ICP
(`tora/eval/metrics.py`, align_anchor), which this scorer does not do; the object
is then flagged rather than left to disagree silently.

PER EPOCH. `score_draw` and `score_batch` take plain arrays (or tensors) and
nothing else, so ticket 04's choosing loop can call them on each validation
object.

Usage:
  python scripts/own_place.py --run artifacts/jugdraw/jugdraw_baseline_30130049 \
      --reconcile --pot-mm 65
  python scripts/own_place.py --decide untouched=RUN generic=RUN ceiling=RUN \
      --pot Juglet-000
"""

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))

from readout import (TAU, cloud_for, clouds_by_object, part_slices,  # noqa: E402
                     rescore_from_clouds, unit_box_scale)

# The tolerance as a distance: a sherd within this of its home, % of pot size, is seated.
SEAT_PCT = 100.0 * float(np.sqrt(TAU / 2.0))

# A pinned anchor reads exactly 0; this only absorbs float noise in the solid cloud.
PINNED_PCT = 0.05

CLOUDS = {"raw": "generations_pred", "solid": "generations_proposed"}
CLOUD_LABEL = {
    "raw": "raw output (what the evaluator scores)",
    "solid": "solid sherds (each true sherd rigidly placed; what could be glued)",
}


def pct(c: float) -> float:
    """Chamfer in the unit box -> % of pot size."""
    return 100.0 * float(np.sqrt(max(c, 0.0) / 2.0))


def median(xs) -> float:
    return float(np.median(xs)) if len(xs) else float("nan")


def cost_matrix(g: np.ndarray, p: np.ndarray, slices) -> np.ndarray:
    """cd[i, j]: chamfer of TRUE sherd i against PREDICTED sherd j, unit box.

    The computation of readout.seating_from_clouds (KD-trees, both directions
    summed as pytorch3d 0.7.8 does), kept whole so its diagonal can be read.
    """
    trees_g = [cKDTree(g[a:b]) for a, b in slices]
    trees_p = [cKDTree(p[a:b]) for a, b in slices]
    cd = np.zeros((len(slices), len(slices)))
    for i, (a, b) in enumerate(slices):
        for j, (c, d) in enumerate(slices):
            d1, _ = trees_p[j].query(g[a:b])
            d2, _ = trees_g[i].query(p[c:d])
            cd[i, j] = (d1 ** 2).mean() + (d2 ** 2).mean()
    return cd


@dataclass
class Draw:
    """One attempt at one object. Sherds are numbered by their slice in the cloud."""
    n: int            # sherds, anchor included
    own: int          # seated in their own place
    swap: int         # seated if look-alikes may swap: the evaluator's count
    status: list      # per sherd: "own" | "swapped" (seated in another's place) | "off"
    placed_in: list   # per sherd: the true sherd whose place it is seated in, or -1
    home_pct: list    # per sherd: how far from its OWN home, % of pot size
    anchor: int       # the largest sherd

    @property
    def off_pct(self) -> list:
        """How far from home the sherds NOT in their own place sit, % of pot size."""
        return [h for h, s in zip(self.home_pct, self.status) if s != "own"]

    @property
    def anchor_pct(self) -> float:
        return self.home_pct[self.anchor]


def score_draw(gt, pred, points_per_part) -> Draw:
    """Own-place and swap-allowed counts for one draw.

    gt, pred (N, 3) in the same frame, any units: both are divided by the TRUE
    object's longest box side, so the answer does not depend on the object's size.
    points_per_part (P,): zero entries (padding) are skipped, as the evaluator does.
    """
    gt, pred = np.asarray(gt, dtype=float), np.asarray(pred, dtype=float)
    slices = part_slices(points_per_part)
    unit = unit_box_scale(gt)
    cd = cost_matrix(gt / unit, pred / unit, slices)

    own = np.diag(cd) < TAU
    # The evaluator's assignment: on the BINARISED cost, so it maximises how many
    # pairs land within tolerance (tora/eval/metrics.py, compute_part_acc).
    r, c = linear_sum_assignment((cd >= TAU).astype(float))
    hit = cd[r, c] < TAU
    seated = {int(j): int(i) for i, j, h in zip(r, c, hit) if h}
    k = len(slices)
    status = ["own" if own[j] else "swapped" if j in seated else "off" for j in range(k)]
    return Draw(n=k, own=int(own.sum()), swap=int(hit.sum()), status=status,
                placed_in=[j if own[j] else seated.get(j, -1) for j in range(k)],
                home_pct=[pct(cd[j, j]) for j in range(k)],
                anchor=int(np.argmax([b - a for a, b in slices])))


def score_batch(pointclouds_gt, pointclouds_pred, points_per_part) -> list[Draw]:
    """score_draw over a batch: (B, N, 3), (B, N, 3), (B, P). Takes torch tensors.

    For ticket 04's choosing loop: call it on a validation batch's `pointclouds_gt`
    and the sampled clouds, and take the median `own` over the choosing vessels.
    """
    def arr(x):
        return x.detach().cpu().numpy() if hasattr(x, "detach") else np.asarray(x)
    g, p, n = arr(pointclouds_gt), arr(pointclouds_pred), arr(points_per_part)
    return [score_draw(g[b], p[b], n[b]) for b in range(len(g))]


def anchor_note(draws: list[Draw]) -> str:
    """How the anchor sat, in words. Flags any draw where the evaluator would differ."""
    worst = max(d.anchor_pct for d in draws)
    a = draws[0].anchor
    if worst <= PINNED_PCT:
        return (f"anchor = sherd {a} (the largest), pinned at its true place in every "
                f"draw; counted among the {draws[0].n}, as the evaluator counts it")
    off = sum(d.anchor_pct >= SEAT_PCT for d in draws)
    if not off:
        return (f"anchor = sherd {a}, not pinned but seated in every draw (worst "
                f"{worst:.2f}% from home); counted among the {draws[0].n}")
    return (f"anchor = sherd {a} OFF its home in {off} of {len(draws)} draws. The "
            f"evaluator would fit it back by ICP first and this scorer does not, so "
            f"these counts may differ from the evaluator's")


def summary(draws: list[Draw]) -> dict:
    off = [h for d in draws for h in d.off_pct]
    return {
        "n": draws[0].n,
        "draws": len(draws),
        "own": [d.own for d in draws],
        "swap": [d.swap for d in draws],
        "own_median": median([d.own for d in draws]),
        "swap_median": median([d.swap for d in draws]),
        "off_pct_median": median(off),
        "off_pct_quartiles": ([float(q) for q in np.percentile(off, [25, 75])]
                              if off else [float("nan")] * 2),
        "off_sherd_draws": len(off),
        "anchor": anchor_note(draws),
    }


def decide(untouched, generic, ceiling) -> dict:
    """U10's stage-1 rule on per-draw OWN-PLACE counts (intent/U10, gate section).

    The ceiling must beat generic by at least one sherd in its own place, median
    over draws, or U10 closes. Returns the reading, whether the C4 line applies,
    and the words to quote.
    """
    mu, mg, mc = median(untouched), median(generic), median(ceiling)
    margin = mc - mg
    text = [f"own-place medians: untouched {mu:g}, generic {mg:g}, ceiling {mc:g}. "
            f"Ceiling minus generic = {margin:+g} sherd(s); the rule needs +1."]
    if margin >= 1:
        reading = "ceiling_wins"
        text.append("CEILING WINS: shape information is enough when it is handed over. "
                    "Nothing usable is shown yet; stage 2 (look-alikes from typological "
                    "parallels) must earn the claim.")
    else:
        reading = "ceiling_loses"
        text.append("CEILING LOSES: shape is not what the Juglet is missing, even when "
                    "handed over. Close U10 (the method genuinely failed, for this "
                    "lever), skip stage 2, and write back to tora/intent/O8 and "
                    "GARF/intent/G1 that the break edges are what is left.")
    c4 = reading == "ceiling_loses" and mg - mu >= 1
    if c4:
        text.append(f"GENERIC HELPS AS MUCH: generic minus untouched = {mg - mu:+g}. "
                    "The gain came from the fine-tune, not the shape: a line for "
                    "CSC/intent/C4.")
    return {"reading": reading, "c4": c4, "margin": margin, "text": text}


def check_slices(ids: np.ndarray, points_per_part) -> None:
    """Each slice of the cloud must be exactly one sherd, or 'own place' means nothing."""
    for s, (a, b) in enumerate(part_slices(points_per_part)):
        got = set(ids[a:b].tolist())
        if len(got) != 1:
            raise SystemExit(f"slice {s} holds part ids {sorted(got)}; not one sherd")


def score_object(npz: Path) -> tuple[str, dict[str, list[Draw]]]:
    """{cloud: draws} for one saved object, both clouds."""
    with np.load(npz, allow_pickle=True) as d:
        for key in ("pts_gt", "points_per_part", *CLOUDS.values()):
            if key not in d.files:
                raise SystemExit(f"{npz} has no {key}; saved keys: {d.files}")
        if "part_ids" in d.files:
            check_slices(d["part_ids"], d["points_per_part"])
        gt, ppp, name = d["pts_gt"], d["points_per_part"], str(d["name"])
        out = {c: [score_draw(gt, g, ppp) for g in d[key]] for c, key in CLOUDS.items()}
    return name, out


def reconcile(run_dir: Path, name: str, npz: Path, scored: dict) -> list[str]:
    """Every place this scorer's swap-allowed count differs from an existing one.

    Against the evaluator's own results/*.json (raw cloud), and against
    readout.rescore_from_clouds on both clouds. Empty = exact agreement.
    """
    bad = []
    ev = {}
    for f in (Path(run_dir) / "results").glob("*.json"):
        r = json.loads(f.read_text())
        if r.get("name") == name:
            ev[int(r["generation_idx"])] = int(round(r["part_accuracy"] * r["num_parts"]))
    raw = scored["raw"]
    if len(ev) != len(raw):
        bad.append(f"{name}: results/ holds {len(ev)} draws, clouds hold {len(raw)}")
    for k, d in enumerate(raw):
        if k in ev and ev[k] != d.swap:
            bad.append(f"{name} draw {k}: evaluator {ev[k]}, scorer {d.swap}")
    for cloud, which in (("raw", "pred"), ("solid", "proposed")):
        ref = rescore_from_clouds(npz, which=which)["seated_per_draw"]
        for k, (a, d) in enumerate(zip(ref, scored[cloud])):
            if a != d.swap:
                bad.append(f"{name} {cloud} draw {k}: readout {a}, scorer {d.swap}")
    return bad


def mm(p: float, pot_mm: float | None) -> str:
    return f" ({p * pot_mm / 100:.1f} mm)" if pot_mm else ""


def print_object(name: str, scored: dict, pot_mm: float | None) -> None:
    raw = scored["raw"]
    print(f"\n{name}: {raw[0].n} sherds, {len(raw)} draws. {anchor_note(raw)}.")
    print(f"  seated = within {SEAT_PCT:.1f}% of pot size of home{mm(SEAT_PCT, pot_mm)}")
    for cloud, draws in scored.items():
        s = summary(draws)
        print(f"  {CLOUD_LABEL[cloud]}")
        print("    draw   own  swap   not-own sherds, median % of pot size from home")
        for k, d in enumerate(draws):
            off = median(d.off_pct)
            print(f"    {k:>4}   {d.own:>3}   {d.swap:>3}   "
                  + (f"{off:5.1f}{mm(off, pot_mm)}" if d.off_pct else "  -"))
        q1, q3 = s["off_pct_quartiles"]
        print(f"    own place     median {s['own_median']:g} of {s['n']}   "
              f"{sorted(s['own'])}")
        print(f"    swap-allowed  median {s['swap_median']:g} of {s['n']}   "
              f"{sorted(s['swap'])}")
        print(f"    not in own place: median {s['off_pct_median']:.1f}% of pot size from "
              f"home{mm(s['off_pct_median'], pot_mm)}, middle half {q1:.1f}-{q3:.1f}%, "
              f"over {s['off_sherd_draws']} sherd-draws")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run", type=Path, help="an evaluation run dir (clouds/, results/)")
    ap.add_argument("--pot", default=None,
                    help="one object by name; default = every object, each on its own")
    ap.add_argument("--decide", nargs=3, metavar="ARM=RUN",
                    help="untouched=RUN generic=RUN ceiling=RUN: apply U10's rule")
    ap.add_argument("--reconcile", action="store_true",
                    help="fail unless the swap-allowed count equals the evaluator's")
    ap.add_argument("--pot-mm", type=float, default=None,
                    help="pot size in mm, to print distances in mm too (Juglet: 65)")
    ap.add_argument("--json", type=Path, default=None, help="write per-draw scores here")
    a = ap.parse_args()

    if bool(a.run) == bool(a.decide):
        ap.error("give exactly one of --run or --decide")

    dump = {}
    if a.run:
        table = clouds_by_object(a.run)
        names = ([str(np.load(cloud_for(a.run, a.pot), allow_pickle=True)["name"])]
                 if a.pot else sorted(table))
        bad = []
        for name in names:
            name, scored = score_object(table[name])
            print_object(name, scored, a.pot_mm)
            dump[name] = {c: [asdict(d) for d in ds] for c, ds in scored.items()}
            if a.reconcile:
                bad += reconcile(a.run, name, table[name], scored)
        if a.reconcile:
            print("\nreconcile: swap-allowed count vs the evaluator's results/*.json and "
                  "readout.rescore_from_clouds, both clouds: "
                  + ("EXACT on every draw" if not bad else f"{len(bad)} MISMATCH(ES)"))
            for b in bad:
                print("   ", b)
        if a.json:
            a.json.parent.mkdir(parents=True, exist_ok=True)
            a.json.write_text(json.dumps(dump, indent=1))
            print("wrote", a.json)
        return 1 if bad else 0

    arms = dict(x.split("=", 1) for x in a.decide)
    if set(arms) != {"untouched", "generic", "ceiling"}:
        ap.error("--decide needs untouched=RUN generic=RUN ceiling=RUN")
    scored = {}
    for arm, run in arms.items():
        name, scored[arm] = score_object(cloud_for(Path(run), a.pot))
        print_object(f"{arm}: {name}", scored[arm], a.pot_mm)
    readings = {}
    for cloud, role in (("solid", "DECIDES"), ("raw", "reported beside it")):
        v = decide(*([d.own for d in scored[arm][cloud]]
                     for arm in ("untouched", "generic", "ceiling")))
        readings[cloud] = v["reading"]
        print(f"\nU10 stage-1 reading on the {CLOUD_LABEL[cloud]} ({role}):")
        for t in v["text"]:
            print("   ", t)
    if len(set(readings.values())) > 1:
        print("\nThe two clouds give DIFFERENT readings. The solid reading stands; the raw "
              "one differs by seats nobody could glue (mirror images or warped sherds). "
              "Say so in ticket 05.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
