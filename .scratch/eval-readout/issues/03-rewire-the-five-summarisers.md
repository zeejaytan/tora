# 03: The five summarisers become views, and say what moved

**What to build:** Every script that prints a table about a reassembly draws its numbers
from the one module, so two of our own readers can no longer disagree about the same
run. The command lines stay exactly as they are — `docs/notes/` cites them — and each
script records, in its own docstring, which of its figures moved and by how much.

**Answers:** O8

**Blocked by:** 02

**Status:** done

## Why this is last, and why it is the bulk of the work

This is the ticket where published numbers change. It comes after the module has been
checked against a real run, so that when a figure moves we already know the instrument
is sound and the movement is the correction doing its job.

The mechanical part — deleting each script's own arithmetic and calling the module — is
small. The judgement is in the rest: five scripts, each cited by at least one note, each
of whose tables now reads differently, and each needing a sentence that a reader six
months from now can use to tell which version of a number they are looking at.

## Acceptance criteria

- [x] These five delegate to `scripts/readout.py` and keep their existing command-line
      interfaces unchanged:
  - [x] `scripts/audit_placement_metrics.py`
  - [x] `scripts/summarise_juglet_draws.py`
  - [x] `scripts/summarise_ceramics_arms.py`
  - [x] `scripts/summarise_scale_ladder.py`
  - [x] `scripts/analyze_piececount_sweep.py`
- [x] No arithmetic on `rotation_error`, on part accuracy thresholds, or on anchor
      handling survives outside the module. Grep proves it: the corrected field name is
      the only one any of these five reads.
- [x] Each script's docstring gains a dated paragraph naming **which of its figures
      moved and by how much** — the actual ratio observed, not the theoretical one.
- [x] `audit_placement_metrics.py`'s docstring describes `within10` as "the fraction of
      fragments within ten degrees of correct orientation". **It is not.**
      `_recall_at_thresholds` thresholds the per-object *mean*, so the field is a per-object
      0 or 1 — a whole pot passes or fails. Correct the description, and list every note
      that reads it as a fraction. `docs/notes/WEAR_TEST_RESULTS.md` quotes it as
      "recall@10° flat at 0.000"; on nine sherds averaging 35–60° a flat zero is what a
      per-object threshold must produce, so that sentence may be reporting the metric's
      shape rather than a result. (Found 2026-09-05 in ticket 01.)
- [x] `summarise_scale_ladder.py` produces byte-identical output to before. It was
      already correct; if it changes, stop.
- [x] Every view prints, beneath its table, the exact `scripts/render_juglet_attempts.py`
      or `scripts/render_assembly_grid.py` invocation that draws the rows above it —
      so looking is the default path rather than the extra step.
- [x] Every view prints the weight the table can bear: how many objects, how many draws,
      how many trained models. A single-object table says so on its face.
- [x] `scripts/check_readout.py` still passes, and `python scripts/check_intent_links.py`
      reports zero errors.
- [x] The notes that cite a figure which moved are **listed** with the affected section —
      not rewritten here. Correcting them is separate work and needs the conservator's
      call on what the corrected number now supports.
- [x] Confirm juglet-map ticket 02 can now be run honestly: rotation against fragment
      count across the eight fresh pots plus the Juglet, every row on the same ruler.
- [x] State which of the three this was.

## Result (2026-09-05)

**Which of the three: the measurement was broken.** No method result changed, no
reference answer was in question. Every figure that moved moved because the ruler was
being read wrong, and every movement is upward - the model was being scored more kindly
than it deserved, on the rotation column especially.

### Done, and the eleven scripts it took

The five named above, plus six more the grep exposed. All eleven keep their command
lines, print health flags, print the weight the table can bear, and print the exact
render command that draws the rows above.

| Script | What moved |
|---|---|
| `summarise_scale_ladder.py` | **nothing** - byte-identical, the control |
| `summarise_juglet_draws.py` | turn x1.125 on the nine-sherd Juglet |
| `summarise_ceramics_arms.py` | turn (blue_pot 24.4 to 30.5, pink_bowl 1.6 to 2.4, narrow_bottle1 57.1 to 62.3); offset changed denominator |
| `analyze_piececount_sweep.py` | the rotation column only; the placement rate was already corrected |
| `audit_placement_metrics.py` | turn corrected; `within10` renamed `pot<10d`; **DISAGREEMENT withdrawn** |
| `analyze_erosion_sweep.py` | nothing in the table; **a turn column is new** - it read `rotation_error` and never printed it |
| `analyze_pairwise_oracle.py` | absolute degrees **doubled** (k=2 throughout); the separation ratio did **not** move |
| `hpc/analyze_fractura_followup.py` | every rotation figure, by a **different factor per subset** - the exact distortion the report existed to avoid |
| `score_assembly.py` | validation seating rescored: tolerance was the withdrawn absolute metric |
| `refine_seating.py` | before/after seating rescored, same cause |
| `rescore_part_acc.py` | every seating count - the module chamfer was halved (below) |

### The control held, and that is what licenses the rest

`summarise_scale_ladder.py` was already correct and its 72-cell table regenerates
**byte-identical** through the module. Two views that previously disagreed now agree:
`summarise_ceramics_arms.py` and `summarise_scale_ladder.py` print the same turn for the
same pots (blue_pot 30.5, galli_pot 34.8, narrow_bottle1 62.3, plate 48.7; pooled median
30.8 matches the ladder ALL POTS row).

### One case worth keeping straight: the ruler was wrong and the comparison was immune

`analyze_pairwise_oracle.py` reported rotation errors that were exactly **half** the turn
on the piece the model had to place (every sample is a pair, so k=2). But its headline
output is a **ratio** of two rotation errors at the same k, so the x2.000 cancels
exactly. Every DISCRIMINATES / NO CLEAR DISCRIMINATION verdict it has ever printed still
stands. "The ruler was broken" does not automatically mean "the conclusion was wrong",
and saying so precisely is worth more than a blanket retraction.

### A second broken ruler, found on the way

Rewiring the last two scripts exposed a different error, in cloud-side scoring rather
than run-json reading. Full write-up: `docs/notes/READOUT_RECONCILIATION.md`. In short:

- `score_assembly.py` and `refine_seating.py` each kept their own copy of the seating
  metric, thresholded at `0.01 / scale` - the **withdrawn absolute metric**, and not even
  a faithful copy of it, since the tolerance is compared against a squared distance and
  so converts by scale SQUARED.
- `readout.chamfer` carried a `0.5` factor with a docstring claiming it matched
  pytorch3d. It does not: at the pinned 0.7.8, `chamfer_distance(point_reduction="mean")`
  returns `cham_x + cham_y`. Every cloud rescoring was **twice as forgiving** as the
  evaluator.

It was caught only because `score_assembly.py` had computed the same quantity
independently and disagreed by a factor of two. Both conventions are now gate assertions
(3 apart gives 18.0; box 2.0 gives 0.04).

### Grep proof

    grep -rn 'rotation_error|part_accuracy|num_parts|recall_at_|0.01 *[/*]' scripts/ --include=*.py

Every surviving hit outside `readout.py` / `check_readout.py` is either prose in a
docstring, or a rendering tolerance unrelated to part accuracy
(`measure_bbad_hollowness.py`, `visualise_wear_join.py`, `visual_check.py` use
`0.01 * size` as a slab thickness). No script reads `rotation_error`, thresholds part
accuracy, or handles an anchor on its own any more. `part_slices`, the KD-tree seating,
the chamfer, the unit box and the tolerance all live in the module; the duplicate copies
in `score_assembly.py` and `refine_seating.py` are deleted, not merely corrected.

### Notes that quote a figure which moved - listed, not rewritten

Correcting these needs a decision about what the corrected number now supports, which is
the conservator call, not a mechanical edit.

| Note | What it quotes |
|---|---|
| `docs/notes/TORA_GOOD_VS_BAD_ANALYSIS.md` | the most affected - rotation figures throughout, and the pairwise-oracle separation (**ratio unchanged**) |
| `docs/notes/JUGLET_TORA_TEST_PLAN.md` | rotation figures and the pairwise-oracle verdicts (**verdicts unchanged**) |
| `docs/notes/JUGLET_TORA_ROOTCAUSE.md` | Juglet rotation, x1.125 |
| `docs/notes/WEAR_TEST_RESULTS.md` | "recall@10 degrees flat at 0.000" - true as printed, but it means **no pot averaged** under ten degrees, not "no fragment was within ten degrees" |
| `docs/notes/LORA_VESSELS_29623885_RESULT.md` | per-pot rotation |
| `docs/notes/test_results.md`, `analysis_failure_patterns.md`, `TORA_WEAR_SOLUTIONS.md`, `FRACTURA_WHY_IT_FAILS.md`, `fractura_followup_24343146.md`, `WEAR_V3_PLAN.md` | rotation and seating figures in passing |

### juglet-map ticket 02 can now be run honestly

Rotation against fragment count across the eight fresh pots plus the Juglet is now a
valid comparison: every row is corrected by its own n/(n-1), so the eight-pot ladder and
the nine-sherd Juglet sit on the same ruler. Before this they did not - the correction is
x2.000 at two fragments and x1.125 at nine, so the old table slope was partly an artefact
of piece count, which is the very axis that ticket plots.

### Gates

    python scripts/check_readout.py          # passes, 10 sections
    python scripts/check_intent_links.py     # zero errors
