"""One place that reads an evaluation run, so two of our scripts cannot disagree.

WHY THIS EXISTS. `tora/eval/metrics.py:compute_transform_errors` skips the anchor
fragment when it sums rotation and translation error, but divides by ALL fragments:

    n_parts = (points_per_part != 0).sum(dim=1)
    rot_errors_mean = rot_errors.sum(dim=1) / n_parts

so the `rotation_error` and `translation_error` written into `results/*.json` each
carry a free zero. Of the five scripts in this repo that read those fields, exactly
one (`summarise_scale_ladder.py`) multiplies the dilution back out. The factor is
n/(n-1): x1.125 on the nine-sherd Juglet, x2.00 on a two-fragment bowl. It is NOT an
offset that cancels in a comparison -- a table across objects of different fragment
counts, built with an uncorrected reader, is wrong by a different amount in every row,
in the direction that flatters few-fragment objects.

Three further things were re-derived by hand, differently, in each of those scripts:

  - Part accuracy is quantised. A nine-fragment pot can only score multiples of 1/9,
    and one of those ninths is the free anchor. "0.444" invites a precision that is
    not there; "4 of 9 fragments, 1 free" cannot be misread.
  - The scoring threshold changed on 2026-09-02 (commit 0d6a85f, unit_box_scale).
    Runs evaluated before it hold part-accuracy figures that are not comparable with
    runs after it, and nothing in the file says which side it is on. This module
    detects it: the post-fix evaluator writes `part_accuracy_absolute` alongside
    `part_accuracy`; the pre-fix one wrote only `part_accuracy`, and that figure IS
    the absolute one.
  - The model's size input is not checked at read time. `scales` is fed into the flow
    model at every denoising step, and the model has only ever seen it in
    [0.375, 0.625]. `juglet_norm` runs sit at 0.041 and the millimetre Fractura
    subsets at 24-120. Such a run was handicapped before it started.

WHAT THIS DOES NOT DO. It does not change `tora/eval/metrics.py`. Correcting the
stored field at source would silently change the meaning of every historical
`results/*.json` and make old runs unreadable. The correction belongs at read time.

CONVENTIONS. Corrected quantities get the plain names; the raw stored value is
reachable only as `turn_deg_diluted_by_free_anchor` / `gap_diluted_by_free_anchor`,
which are deliberately too ugly to use by accident. Seating is a count, never a bare
fraction. Every record carries the settings that produced it, and a field the run
never saved reads UNRECOVERABLE rather than defaulting to something plausible.

Usage:
    from readout import read_run, pool, format_seated, format_turn
    records = read_run(Path("eval_runs/lorav3_juglet_baseline_29880370"))
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field, replace
from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment

# The band the flow model was trained on. Breaking Bad objects arrive at max|v| = 0.5
# and training adds random_scale_range (0.75, 1.25).
TRAINED_SCALE_BAND = (0.375, 0.625)

# Breaking Bad's tau, in the frame Breaking Bad states it in: a unit-length box.
# compute_part_acc thresholds pytorch3d's chamfer_distance with point_reduction="mean",
# which is a mean of SQUARED distances, so this is a squared tolerance.
TAU = 0.01

UNRECOVERABLE = "unrecoverable"

# Written by the post-fix evaluator only (commit 0d6a85f, 2026-09-02). Its presence in
# a result json is what separates a run scored in the unit box from one scored in
# stored units.
POST_FIX_MARKER = "part_accuracy_absolute"

FLAG_SCALE_OUT_OF_BAND = "model size input outside the trained band"
FLAG_PRE_UNIT_BOX = "scored before the unit-box threshold fix"


class ProvenanceMismatch(RuntimeError):
    """Raised when records that were not produced the same way are pooled."""


@dataclass(frozen=True)
class Provenance:
    """The settings that produced a record, as far as the run saved them.

    Read from the run's `.hydra/` directory, which Hydra writes beside `results/`.
    Any field the run did not save reads UNRECOVERABLE; nothing is inferred.
    """

    checkpoint: str = UNRECOVERABLE
    seed: str = UNRECOVERABLE
    n_generations: str = UNRECOVERABLE
    anchor_free: str = UNRECOVERABLE
    dataset_config: str = UNRECOVERABLE
    points_sampled: str = UNRECOVERABLE

    @property
    def complete(self) -> bool:
        return UNRECOVERABLE not in (
            self.checkpoint, self.seed, self.n_generations,
            self.anchor_free, self.dataset_config, self.points_sampled,
        )

    def describe(self) -> str:
        ckpt = self.checkpoint if self.checkpoint == UNRECOVERABLE else Path(self.checkpoint).name
        return (f"checkpoint={ckpt} seed={self.seed} draws={self.n_generations} "
                f"anchor_free={self.anchor_free} data={self.dataset_config} "
                f"points={self.points_sampled}")


@dataclass(frozen=True)
class Record:
    """One draw, one object.

    `turn_deg` and `gap` are the quantities on the fragments the model actually had to
    place. The stored, anchor-diluted values are kept under their long names so that
    using them is always a deliberate act.
    """

    run: str
    object_name: str
    dataset: str
    draw: int

    n_fragments: int
    n_anchors: int
    n_anchors_source: str          # "config" or "assumed"

    seated: int                    # fragments, not a fraction
    turn_deg: float                # non-anchor mean rotation error
    gap: float                     # non-anchor mean translation error
    turn_deg_diluted_by_free_anchor: float
    gap_diluted_by_free_anchor: float

    model_scale: float
    provenance: Provenance
    flags: tuple[str, ...] = ()
    raw: dict = field(default_factory=dict, repr=False)

    @property
    def floor(self) -> int:
        """Fragments the model was given for free. It cannot score below this."""
        return self.n_anchors

    @property
    def placed(self) -> int:
        """Fragments the model actually had to place."""
        return self.n_fragments - self.n_anchors

    @property
    def anchor_correction(self) -> float:
        return self.n_fragments / max(self.n_fragments - self.n_anchors, 1)

    @property
    def seated_fraction(self) -> float:
        """Available, but never print it without the floor beside it.

        Use `format_seated`, which cannot omit the floor.
        """
        return self.seated / self.n_fragments if self.n_fragments else float("nan")


def _load_hydra(run_dir: Path) -> Provenance:
    """Read the settings Hydra saved beside the results. Absent field -> UNRECOVERABLE."""
    cfg_path = run_dir / ".hydra" / "config.yaml"
    if not cfg_path.is_file():
        return Provenance()
    try:
        import yaml
    except ImportError:
        return Provenance()
    try:
        cfg = yaml.safe_load(cfg_path.read_text()) or {}
    except Exception:
        return Provenance()

    def get(*path, default=UNRECOVERABLE):
        node = cfg
        for key in path:
            if not isinstance(node, dict) or key not in node:
                return default
            node = node[key]
        return UNRECOVERABLE if node is None else str(node)

    return Provenance(
        checkpoint=get("ckpt_path"),
        seed=get("seed"),
        n_generations=get("model", "n_generations"),
        # The data-level flag is the one that decides whether an anchor fragment is
        # handed to the model; model.anchor_free is a separate switch.
        anchor_free=get("data", "anchor_free"),
        dataset_config=get("data", "_target_"),
        points_sampled=get("data", "num_points_to_sample"),
    )


def _n_anchors_from(prov: Provenance) -> tuple[int, str]:
    """How many fragments were excluded from the error sum.

    `compute_transform_errors` skips every part flagged as an anchor. In every run in
    this project that is exactly one, and every hand-correction written so far has
    assumed one. Where the config settles it, say so; where it does not, say that too
    rather than presenting an assumption as a reading.
    """
    if prov.anchor_free == UNRECOVERABLE:
        return 1, "assumed"
    if str(prov.anchor_free).lower() in ("true", "1"):
        # An anchor is still designated for the error computation even when the model
        # is not handed it as a condition. Ticket 02 confirms this against a real run.
        return 1, "assumed"
    return 1, "config"


def read_run(
    run_dir: Path,
    subset: dict[str, int] | None = None,
    n_anchors: int | None = None,
) -> list[Record]:
    """Every draw of every object in one evaluation run.

    Args:
        run_dir: an eval_runs/<name> directory, holding results/ and optionally
            clouds/ and .hydra/.
        subset: optional {object_name: fragments_kept}. When an experiment drops a
            fragment, the denominator and the floor must follow the subset rather than
            silently staying at the full count -- that is how a dropped-sherd test
            manufactures its own effect.
        n_anchors: override the anchor count when the caller knows it.
    """
    run_dir = Path(run_dir)
    results = run_dir / "results"
    if not results.is_dir():
        raise SystemExit(f"no results/ under {run_dir}")

    prov = _load_hydra(run_dir)
    records: list[Record] = []

    for path in sorted(results.glob("*_generation*.json")):
        entry = json.loads(path.read_text())
        name = entry.get("name", path.stem)

        n_fragments = int(entry.get("num_parts", 0))
        if subset is not None and name in subset:
            n_fragments = int(subset[name])
        if n_fragments <= 0:
            continue

        if n_anchors is not None:
            n_anch, anch_src = int(n_anchors), "caller"
        else:
            n_anch, anch_src = _n_anchors_from(prov)
        correction = n_fragments / max(n_fragments - n_anch, 1)

        flags = []
        scale = float(entry.get("scales", float("nan")))
        lo, hi = TRAINED_SCALE_BAND
        if not (lo <= scale <= hi):
            flags.append(f"{FLAG_SCALE_OUT_OF_BAND}: {scale:.4g} not in [{lo}, {hi}]")
        if POST_FIX_MARKER not in entry:
            flags.append(FLAG_PRE_UNIT_BOX)

        raw_turn = float(entry.get("rotation_error", float("nan")))
        raw_gap = float(entry.get("translation_error_unit",
                                  entry.get("translation_error", float("nan"))))
        part_acc = float(entry.get("part_accuracy", float("nan")))

        records.append(Record(
            run=run_dir.name,
            object_name=name,
            dataset=str(entry.get("dataset", UNRECOVERABLE)),
            draw=int(entry.get("generation_idx", 0)),
            n_fragments=n_fragments,
            n_anchors=n_anch,
            n_anchors_source=anch_src,
            seated=int(round(part_acc * n_fragments)) if not math.isnan(part_acc) else -1,
            turn_deg=raw_turn * correction,
            gap=raw_gap * correction,
            turn_deg_diluted_by_free_anchor=raw_turn,
            gap_diluted_by_free_anchor=raw_gap,
            model_scale=scale,
            provenance=prov,
            flags=tuple(flags),
            raw=entry,
        ))

    return records


def pool(records: list[Record], across: str | None = None) -> list[Record]:
    """Check that these records may be averaged together, and hand them back.

    Raises unless every record shares one complete provenance. A caller that genuinely
    wants to pool across different settings passes `across` with the reason, which then
    travels with the result instead of being lost.
    """
    if not records:
        raise ProvenanceMismatch("nothing to pool")
    if across is not None:
        return [replace(r, flags=r.flags + (f"pooled across settings: {across}",))
                for r in records]

    first = records[0].provenance
    if not first.complete:
        raise ProvenanceMismatch(
            f"{records[0].run}: provenance is {UNRECOVERABLE} in part "
            f"({first.describe()}). Pass across='<reason>' to pool anyway.")
    for r in records[1:]:
        if r.provenance != first:
            raise ProvenanceMismatch(
                f"{records[0].run} and {r.run} were not produced the same way:\n"
                f"  {first.describe()}\n  {r.provenance.describe()}\n"
                f"Pass across='<reason>' to pool anyway.")
    return records


def format_seated(record: Record) -> str:
    """Fragments seated, with the free anchor named. Never a bare fraction."""
    if record.seated < 0:
        return f"seated {UNRECOVERABLE} of {record.n_fragments} sherds"
    return (f"{record.seated} of {record.n_fragments} sherds seated "
            f"({record.floor} free)")


def format_turn(record: Record) -> str:
    """Degrees of turn on the fragments the model had to place."""
    return (f"{record.turn_deg:.1f} deg turn on the {record.placed} sherds it "
            f"had to place")


def format_flags(records: list[Record]) -> list[str]:
    """Every distinct health warning across these records, for printing above a table."""
    seen: list[str] = []
    for r in records:
        for f in r.flags:
            if f not in seen:
                seen.append(f)
        if r.n_anchors_source == "assumed" and "anchor count assumed to be 1" not in seen:
            seen.append("anchor count assumed to be 1 (the run did not record it)")
        if not r.provenance.complete:
            note = f"{r.run}: settings partly {UNRECOVERABLE} -- {r.provenance.describe()}"
            if note not in seen:
                seen.append(note)
    return seen


def weight(records: list[Record]) -> str:
    """How much a table over these records can bear, in the terms that decide it."""
    objects = {r.object_name for r in records}
    draws = {(r.run, r.object_name, r.draw) for r in records}
    ckpts = {r.provenance.checkpoint for r in records}
    return (f"{len(objects)} object(s), {len(draws)} draw(s), "
            f"{len(ckpts)} trained model(s)")


# --------------------------------------------------------------------------------
# Rescoring from saved clouds. Moved here from scripts/rescore_part_acc.py so that the
# unit-box derivation exists once. numpy only -- no torch, no GPU.
# --------------------------------------------------------------------------------


def unit_box_scale(pts: np.ndarray) -> float:
    """Longest side of a cloud's axis-aligned bounding box.

    Measured on the ground truth, never the prediction: a scattered prediction has a
    larger box than the object it is rebuilding, and using it would hand a failing
    assembly a more forgiving tolerance.
    """
    return float(max((pts.max(axis=0) - pts.min(axis=0)).max(), 1e-8))


def chamfer(a: np.ndarray, b: np.ndarray) -> float:
    """Symmetric mean of squared nearest-neighbour distances, as pytorch3d does."""
    d = ((a[:, None, :] - b[None, :, :]) ** 2).sum(-1)
    return 0.5 * (d.min(axis=1).mean() + d.min(axis=0).mean())


def part_acc(pts_gt, pts_pred, points_per_part, threshold) -> tuple[float, int]:
    """Fraction of parts whose chamfer to their matched GT part is under threshold.

    Hungarian matching on the chamfer cost, as compute_part_acc does: parts are
    interchangeable, so a prediction may claim any GT part once.
    """
    ppp = [int(n) for n in points_per_part if int(n) > 0]
    bounds = np.cumsum([0] + ppp)
    gt = [pts_gt[bounds[i]:bounds[i + 1]] for i in range(len(ppp))]
    pr = [pts_pred[bounds[i]:bounds[i + 1]] for i in range(len(ppp))]
    p = len(ppp)
    cost = np.zeros((p, p))
    for i in range(p):
        for j in range(p):
            cost[i, j] = chamfer(gt[i], pr[j])
    r, c = linear_sum_assignment(cost)
    return float((cost[r, c] < threshold).mean()), p


def rescore_from_clouds(npz_path: Path, which: str = "pred",
                        absolute: bool = False) -> dict:
    """Rescore one saved object in the unit box, without a GPU.

    Args:
        which: "pred" is the raw flow output, which is what the evaluator scores;
            "proposed" is the input parts rigidly posed by the predicted SE(3).
        absolute: reproduce the OLD shipped metric -- rescale to stored units, then
            threshold at a fixed 0.01. Kept so the two can be compared on the same
            predictions.
    """
    d = np.load(npz_path, allow_pickle=True)
    key = "generations_" + ("pred" if which == "pred" else "proposed")
    if key not in d:
        raise SystemExit(f"{npz_path.name} has no {key}; saved keys: {list(d.keys())}")

    gt = d["pts_gt"]
    ppp = d["points_per_part"]
    scale = float(d["scale"]) if "scale" in d else 1.0
    unit = unit_box_scale(gt)

    accs, n_parts = [], 0
    for g in d[key]:
        if absolute:
            acc, n_parts = part_acc(gt * scale, g * scale, ppp, TAU)
        else:
            acc, n_parts = part_acc(gt / unit, g / unit, ppp, TAU)
        accs.append(acc)

    return {
        "name": str(d["name"]),
        "n_fragments": n_parts,
        "seated_per_draw": [int(round(a * n_parts)) for a in accs],
        "part_accuracy_per_draw": accs,
        "model_scale": scale,
        "unit_box": unit,
        "frame": "stored units, absolute tau" if absolute else "unit box",
    }
