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
from scipy.spatial import cKDTree

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
    multi_anchor: str = UNRECOVERABLE

    @property
    def complete(self) -> bool:
        return UNRECOVERABLE not in (
            self.checkpoint, self.seed, self.n_generations,
            self.anchor_free, self.dataset_config, self.points_sampled,
        )

    def describe(self) -> str:
        ckpt = self.checkpoint if self.checkpoint == UNRECOVERABLE else Path(self.checkpoint).name
        return (f"checkpoint={ckpt} seed={self.seed} draws={self.n_generations} "
                f"anchor_free={self.anchor_free} multi_anchor={self.multi_anchor} "
                f"data={self.dataset_config} points={self.points_sampled}")


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

    def pot_under(self, degrees: int) -> float:
        """Did the WHOLE object average under `degrees` on this draw? 1.0 or 0.0.

        `recall_at_5deg` and `recall_at_10deg` are not a fraction of fragments,
        however often they have been read as one.
        `Evaluator._recall_at_thresholds` (tora/eval/evaluator.py:205) thresholds
        a per-OBJECT mean of shape (B,), so each is 0 or 1 for a whole object on
        one draw. Averaged over draws it is the SHARE OF ATTEMPTS in which the
        pot came in under the threshold.

        A nine-sherd pot with eight sherds perfect and one turned a right angle
        scores zero here. Compare models on `seated` and `turn_deg` instead;
        this is reported only because past notes quote it.

        CORRECTED 2026-09-05. The evaluator thresholds the ANCHOR-DILUTED mean --
        it is `rot_errors` straight out of `compute_transform_errors`, the same
        field this module divides the free zero back out of. So the stored recall
        passes objects it should fail, by exactly the dilution factor: a
        two-fragment pair whose one placed piece is turned 19 degrees stores a
        mean of 9.5 and scores 1.0 at the ten-degree bar. The bias is worst where
        the fragment count is lowest, which is the same direction the rotation
        column was already wrong in, so the two errors compounded rather than
        cancelled.

        It is recoverable without a rerun -- the stored mean and the fragment
        count are both in the file -- so this thresholds the corrected turn
        instead. The stored value is still reachable as
        `pot_under_diluted_by_free_anchor`. Any `recall@5deg` / `recall@10deg`
        figure quoted from a note written before this date is the diluted one.
        """
        if math.isnan(self.turn_deg):
            return float("nan")
        return 1.0 if self.turn_deg <= degrees else 0.0

    def pot_under_diluted_by_free_anchor(self, degrees: int) -> float:
        """The stored `recall_at_{degrees}deg`, free anchor and all.

        Here so a note written before 2026-09-05 can be checked against what it
        actually quoted. Do not put it in a table.
        """
        return float(self.raw.get(f"recall_at_{degrees}deg", float("nan")))

    @property
    def placed(self) -> int:
        """Fragments the model actually had to place."""
        return self.n_fragments - self.n_anchors

    @property
    def anchor_correction(self) -> float:
        return self.n_fragments / max(self.n_fragments - self.n_anchors, 1)

    @property
    def gap_denominator(self) -> str:
        """What `gap_object_fraction` is a fraction OF.

        Two different normalisers are in play across the runs on disk and they must
        not be quoted as one column. A run scored after the unit-box fix stores
        `translation_error_unit`, already divided by the longest side of the ground
        truth bounding box. An older run stores only `translation_error` in the
        object's own units, and the only size beside it is the stored `scales`.
        """
        if "translation_error_unit" in self.raw:
            return "unit box (GT longest side)"
        if self.model_scale and not math.isnan(self.model_scale):
            return "stored scale"
        return UNRECOVERABLE

    @property
    def gap_object_fraction(self) -> float:
        """Offset as a fraction of the object's own size.

        A raw translation error in an object's stored units means nothing on its own:
        the ceramics are millimetres, so an offset of 167 is unreadable until it is
        divided by the pot. Read `gap_denominator` beside it.
        """
        if "translation_error_unit" in self.raw:
            return self.gap
        if self.model_scale and not math.isnan(self.model_scale) and self.model_scale:
            return self.gap / self.model_scale
        return float("nan")

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
        multi_anchor=get("data", "multi_anchor"),
    )


def _n_anchors_from(prov: Provenance) -> tuple[int, str]:
    """How many fragments were excluded from the error sum.

    `compute_transform_errors` skips every part flagged as an anchor.
    `tora/data/dataset.py:324` flags exactly one -- the part with the most points --
    and does so whether or not `anchor_free` is set; anchor-free changes what the model
    is *given*, not which part the metric skips. The one way to get more than one is
    `multi_anchor`, which adds extras at random and only in anchor-fixed mode.

    So: `multi_anchor: false` in the config settles the count at one. A run with
    `multi_anchor: true` varies per sample and cannot be corrected from the summary
    json alone -- say so rather than quietly dividing by the wrong number.
    """
    if str(prov.multi_anchor).lower() in ("false", "0"):
        return 1, "config"
    if prov.multi_anchor == UNRECOVERABLE:
        return 1, "assumed"
    return 1, "multi_anchor"


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
    """Every distinct health warning across these records, for printing above a table.

    Warnings are collapsed, not repeated. A sweep that deliberately walks the size
    input across two orders of magnitude would otherwise print the same sentence once
    per rung, which is how a warning stops being read.
    """
    seen: list[str] = []
    out_of_band = [r.model_scale for r in records
                   if any(f.startswith(FLAG_SCALE_OUT_OF_BAND) for f in r.flags)]
    if out_of_band:
        lo, hi = TRAINED_SCALE_BAND
        seen.append(
            f"{FLAG_SCALE_OUT_OF_BAND}: {len(out_of_band)} of {len(records)} draws, "
            f"{min(out_of_band):.4g} to {max(out_of_band):.4g}, outside [{lo}, {hi}]")
    for r in records:
        for f in r.flags:
            if f.startswith(FLAG_SCALE_OUT_OF_BAND) or f in seen:
                continue
            seen.append(f)
        if r.n_anchors_source == "assumed":
            note = "anchor count assumed to be 1 (the run did not record it)"
            if note not in seen:
                seen.append(note)
        if r.n_anchors_source == "multi_anchor":
            note = ("multi_anchor was on: the number of free fragments varies per "
                    "sample and the correction here assumes one -- do not trust the "
                    "turn column on this run")
            if note not in seen:
                seen.append(note)
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
    """Symmetric SUM of the two mean squared nearest-neighbour distances.

    This must match what the evaluator thresholds, exactly, or every rescoring
    done here is measured with a different ruler from the one that produced the
    numbers it is being compared against.

    `compute_part_acc` (tora/eval/metrics.py:151) calls pytorch3d
    `chamfer_distance(single_directional=False, point_reduction="mean",
    batch_reduction=None)`. At the pinned version -- pytorch3d 0.7.8, the wheel
    named in pyproject.toml -- that returns `loss = cham_x + cham_y`, each side
    summed over its points and divided by that side's point count. There is no
    0.5 anywhere in it.

    CORRECTED 2026-09-05. This function carried a 0.5 factor and a docstring
    claiming it was what pytorch3d does. It was not: it made every rescoring
    here exactly TWICE AS FORGIVING as the evaluator against the same 0.01
    threshold. Caught by `scripts/score_assembly.py`, which had computed the
    same quantity independently and without the halving, so the two disagreed
    by a factor of two on the same clouds. Anything rescored from clouds before
    this date -- `rescore_from_clouds`, `scripts/rescore_part_acc.py` -- was
    scored too generously and must be rerun before it is quoted.
    """
    d = ((a[:, None, :] - b[None, :, :]) ** 2).sum(-1)
    return float(d.min(axis=1).mean() + d.min(axis=0).mean())


def unit_box_threshold(pts_gt: np.ndarray) -> float:
    """TAU, expressed in the frame the saved clouds are actually stored in.

    A script that scores from `clouds/*.npz` works in the dataloader's normalised
    frame, so it needs the unit-box tolerance translated into that frame rather
    than applied there directly. Two conversions are easy to get wrong and both
    have been got wrong here:

      - dividing by the stored scale rather than its SQUARE. The threshold is
        compared against a SQUARED chamfer distance, so it scales as scale^2. At
        a Breaking Bad scale of 0.5 the shipped 0.01 is 0.04 in this frame, not
        0.02 -- a script using 0.02 is twice as strict as the metric it claims
        to be reproducing.

      - using the stored scale at all. That is the WITHDRAWN absolute metric: a
        fixed 0.01 in each dataset's own units, which is 2% of a Breaking Bad
        vessel and 0.014% of a millimetre-stored ceramic pot. It faked a finding
        once already (docs/notes/TORA_GOOD_VS_BAD_ANALYSIS.md, jobs 27858648 /
        27859890).

    The tolerance is a fraction of the OBJECT, so it is derived from the ground
    truth bounding box and never from the prediction.
    """
    return TAU * unit_box_scale(pts_gt) ** 2


def part_slices(points_per_part) -> list[tuple[int, int]]:
    """Start and end index of each non-empty part in a flattened cloud."""
    out, start = [], 0
    for n in points_per_part:
        n = int(n)
        if n > 0:
            out.append((start, start + n))
            start += n
    return out


def seating_from_clouds(pred, gt, slices, threshold=None, n_anchors: int = 1):
    """Anchor-corrected seating rate for one assembly, from its saved clouds.

    Returns the fraction of the fragments the model actually had to place that
    landed within tolerance -- 1.0 = every loose fragment seated, 0.0 = none
    beyond the ones handed over for free. It is the cloud-side twin of
    `Record.seated` minus `Record.floor`, over `Record.placed`, and it exists so
    that a script scoring `clouds/*.npz` does not have to keep its own copy of
    the metric. Two did, and both had the tolerance wrong.

    `threshold` defaults to `unit_box_threshold(gt)`. Pass one only to compare
    conventions deliberately.

    Uses KD-trees rather than the dense matrix in `part_acc`, because the
    callers run this over every draw of every object in a run.
    """
    if threshold is None:
        threshold = unit_box_threshold(gt)
    k = len(slices)
    if k < 2:
        return float("nan")
    cd = np.zeros((k, k))
    trees_gt = [cKDTree(gt[a:b]) for a, b in slices]
    trees_pr = [cKDTree(pred[a:b]) for a, b in slices]
    for i, (a, b) in enumerate(slices):
        for j, (c, d) in enumerate(slices):
            d1, _ = trees_pr[j].query(gt[a:b])
            d2, _ = trees_gt[i].query(pred[c:d])
            # both directions SUMMED, as pytorch3d 0.7.8 does; see chamfer()
            cd[i, j] = (d1 ** 2).mean() + (d2 ** 2).mean()
    r, c = linear_sum_assignment((cd >= threshold).astype(float))
    seated = float((cd[r, c] < threshold).sum())
    placed = max(k - n_anchors, 1)
    return (seated - n_anchors) / placed


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
