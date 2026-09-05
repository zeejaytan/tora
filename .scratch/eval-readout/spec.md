# Spec — one honest read-out for every evaluation run

**Answers:** O8

**Status:** ready-for-agent

**Serves:** `.scratch/juglet-cause/map.md` (tickets 01–04 all read saved runs), and every
note written from an eval run after it.

## Problem Statement

Every number this project has published about a reassembly was read off disk by a
one-off script, and there are now five of them. They read the *same* files and
disagree.

`tora/eval/metrics.py:compute_transform_errors` skips the anchor fragment when it
averages rotation error, but divides by *all* fragments — so the number it writes to
`results/*.json` is diluted by a free zero. **Corrected 2026-09-05: this was first
described here as a rotation-only fault. It is not.** The same `/ n_parts` divides the
translation sum and the euler-angle rotation sum in the same function, so
`translation_error`, `translation_error_unit` and `euler/rotation_error` are diluted by
the identical factor. The module corrects all of them. Only one of the five readers
corrects for any of it:

| script | field read | correction |
|---|---|---|
| `scripts/summarise_scale_ladder.py` | `rotation_error` | `× n/(n-1)` |
| `scripts/audit_placement_metrics.py` | `rotation_error` | none |
| `scripts/summarise_juglet_draws.py` | `rotation_error` | none |
| `scripts/summarise_ceramics_arms.py` | `rotation_error` | none |
| `scripts/analyze_piececount_sweep.py` | derived | partial |

The correction is not a constant offset — it is `n/(n-1)`, which depends on how many
fragments the pot has. On the nine-sherd Juglet it is ×1.125. On a two-fragment bowl
it is ×2.00. So a table comparing objects of different fragment counts, built with an
uncorrected reader, is **wrong by a different amount in every row, in the direction
that makes few-fragment objects look better than they are.** That is precisely the
comparison ticket 02 of the Juglet map is about to make.

Three further things are re-derived by hand, differently, each time:

- **Part accuracy is quantised.** A nine-fragment pot can only score multiples of 1/9,
  and 1/9 of that is the free anchor. Printing `0.444` invites reading a precision
  that is not there; `4 of 9 fragments, floor 1 of 9` cannot be misread.
- **The scoring threshold changed.** Runs evaluated before the unit-box fix
  (`tora/eval/metrics.py:unit_box_scale`, gated by
  `scripts/check_metric_scale_invariance.py`) hold part-accuracy figures that are not
  comparable with runs after it. Nothing in the file says which side it is on.
- **The model's size input is not checked at read time.** The trained band is
  [0.375, 0.625]. `juglet_norm` runs sit at 0.041 and the millimetre Fractura subsets
  at 24–120. A run outside that band was handicapped before it started, and the number
  is being read as though it were not.

The cost is already on the record. Three runs on the same pot, all called "baseline",
read 31.4°, 33.5° and 58.2°, and the settings that separate them cannot now be
recovered from what was saved. A 27° spread on a scale where 10–35° means "correct
with symmetry residual" and 40–70° means "collapsed" is the difference between a
result and no result, and we cannot say which it is.

## Solution

**One read-out module. Every table, every note, every render draws from it.**

A conservator asks "how did TORA do on this pot?" and gets the same answer whoever
asks and whichever script they run — in fragments seated out of fragments present, in
degrees of turn on the fragments the model actually had to place, with the settings
that produced it printed beside it, and with a loud line when any of that cannot be
trusted.

Concretely, the module turns an evaluation run directory into records. Each record
carries the corrected, physically-meaningful quantity as its plain name, the raw
stored value under a name too ugly to use by accident, and the provenance needed to
know whether the record can be compared with another one. The five existing
summarisers keep their names and their command lines — notes cite them — and become
thin views over those records.

Nothing is re-run. The seam is the run directory that already exists on disk.

## User Stories

1. As a conservator, I want a result reported as "4 of the 9 sherds seated" rather than
   "part_accuracy 0.444", so that I can tell how much of the pot was actually rebuilt.
2. As a conservator, I want the free anchor named as free wherever a seated count is
   given, so that I know the floor the model got for nothing.
3. As a conservator, I want rotation error reported for the fragments the model had to
   place, so that a two-piece bowl and a nine-piece juglet can be put in the same table.
4. As a conservator, I want every number accompanied by how many objects, how many
   draws and how many trained models are behind it, so that I know whether it is a
   lead or a finding.
5. As a conservator, I want to be told in words when a run cannot be compared with the
   one beside it, so that I do not build an argument on two different rulers.
6. As a conservator, I want the command that draws the assembly printed next to the
   table that scores it, so that looking is the easy path and not the extra step.
7. As an agent working ticket 01, I want the spread across draws within a single run,
   so that I can say what difference on this pot is readable and what is noise.
8. As an agent working ticket 02, I want rotation and seating against fragment count
   across all eight fresh pots, correctly normalised per object, so that the Juglet can
   be placed inside or outside the band it belongs to.
9. As an agent working ticket 03, I want the recorded model size input for every run,
   so that I can find which conclusions were drawn from out-of-band inputs.
10. As an agent working ticket 04, I want to score a named subset of fragments and
    exclude the rest, so that dropping a sherd does not silently change the denominator
    and manufacture the effect I am testing for.
11. As an agent, I want the raw stored field available but awkwardly named, so that
    using it is always a deliberate act.
12. As an agent, I want the module to refuse to average across runs whose settings
    differ or are unrecoverable, so that a table cannot silently mix two experiments.
13. As an agent, I want a run whose settings were never saved to be stamped
    `unrecoverable` in every output it appears in, so that its numbers are never quietly
    promoted to comparable.
14. As an agent, I want runs scored before the unit-box threshold fix flagged, and
    rescored from saved clouds where the clouds exist, so that old runs re-enter the
    record on the current ruler or not at all.
15. As an agent, I want any run whose model size input falls outside the trained band
    flagged in the output rather than in a comment, so that the second units bug cannot
    happen a third time.
16. As an agent, I want the module to work with no GPU, no model weights and no
    project config, so that reading a result costs seconds and never a queue wait.
17. As an agent, I want the existing summariser command lines to keep working, so that
    the paths cited in `docs/notes/` still resolve to the same tables.
18. As an agent, I want the corrections checked against arithmetic I can do on paper,
    so that the instrument itself is not the next thing that needs auditing.
19. As a reader of a note six months from now, I want the settings printed in the table
    I am reading, so that I can tell whether two rows in it are the same experiment.
20. As a reader, I want a per-fragment breakdown available, so that "average 31°" can be
    checked against whether that is nine fragments at 31° or seven at 5° and two at 120°.
21. As the person who has to decide what to run next, I want to see whether a
    difference exceeds the run-to-run spread before it is called a difference, so that
    GPU time is not spent chasing noise.

## Implementation Decisions

**One seam, and it already exists.** The evaluation run directory on disk:
`<run>/results/*_generation*.json` for per-draw records and `<run>/clouds/*.npz` for
saved point clouds. All five current readers already use it. The module is a pure
function of that directory's contents — no `torch`, no Hydra config, no dataset, no
network. This is the highest available seam: it is downstream of everything that
requires a GPU and upstream of everything that produces a table or a picture.

**The record is per draw, per object, with per-fragment detail attached.** Averaging is
a view, never the stored thing. A caller that wants the median across draws, the
distribution of seated counts, or the worst fragment can all get it from the same
records without a second reader.

**Corrected quantities take the plain names; raw takes the ugly one.** `turn_deg` is
the non-anchor mean. The stored field is exposed as
`turn_deg_diluted_by_free_anchor`, and no view prints it. The correction `n/(n-1)` is
applied in exactly one place.

**Seating is a count, not a fraction.** `seated` is fragments, `n_fragments` is the
total, `floor` is the free anchor. A fraction is available but never printed without
its floor beside it.

**Provenance rides on every record.** Trained model, seed, number of draws, anchor
mode, dataset file, and the object's model size input. Read from whatever the run
saved; where a field is absent the record carries `unrecoverable` for it and every view
that includes such a record prints that word. Records whose provenance differs, or is
unrecoverable, cannot be pooled into one mean — the module raises rather than averages,
and the caller must pool them explicitly if that is genuinely what it wants.

**Two health flags, evaluated at read time, on by default.** (a) Model size input
outside [0.375, 0.625]. (b) Scored before the unit-box threshold fix. Neither is an
error — historical runs must remain readable — but neither can be silent. Where flag
(b) is set and saved clouds exist, the module rescores using the per-object unit-box
derivation already written and corrected in `scripts/rescore_part_acc.py`, which moves
into the module as its single implementation.

**Fragment subsets are first-class.** A record can be built over a named subset of
fragments, with the denominator following the subset. Ticket 04 drops a sherd; the
score must be over the kept fragments only, and the module should make the wrong thing
hard rather than leaving it to the caller's care.

**Every view emits the render command for the rows it just printed.** The existing
`scripts/render_juglet_attempts.py` and `scripts/render_assembly_grid.py` take run
directories; the view prints the invocation that draws the rows in the table. Looking
becomes the default path, which is the rule this project keeps having to relearn.

**The five summarisers stay, as views.** `audit_placement_metrics.py`,
`summarise_juglet_draws.py`, `summarise_ceramics_arms.py`, `summarise_scale_ladder.py`
and `analyze_piececount_sweep.py` keep their names and command-line interfaces and
delegate. Their numbers will move where they were wrong — that is the point, and each
one's docstring records what changed and by how much.

**Placement.** The module and its gate go in `scripts/`, alongside the readers they
serve. No new top-level directories.

## Testing Decisions

**A good test here asserts a number a person can check on paper.** These are read-out
corrections, not behaviour with hidden state: the whole point is that a reader can
confirm the instrument by hand. Tests assert against fixtures whose right answer is
arithmetic, never against a recorded output of the code itself — a snapshot test would
have happily frozen the diluted-anchor bug.

**The repo's idiom is a standalone gate script, not pytest.** There is no test runner
and no `tests/` directory; correctness is enforced by `scripts/check_*.py` files with a
docstring stating WHY and WHAT THIS ASSERTS, exiting non-zero on failure. Prior art:
`check_metric_scale_invariance.py`, `check_scale_conditioning.py`,
`verify_parallel_kdtree.py`. Follow it. The new gate is `scripts/check_readout.py`.

**What it asserts:**

1. On a hand-written fixture run of a 9-fragment object where every non-anchor fragment
   is turned exactly 40° and the anchor 0°, the stored mean is 35.56° and `turn_deg` is
   40.00°. The arithmetic is visible in the assertion.
2. The same fixture at 2, 3 and 9 fragments, confirming the correction scales with
   fragment count and is not a constant.
3. A seated count of 4 on a 9-fragment object reports `4 of 9, floor 1 of 9`, and no
   view emits a bare fraction.
4. Pooling two records with different seeds raises; pooling two with identical
   provenance succeeds.
5. A record with an absent settings field is stamped `unrecoverable`, and a view
   containing it prints that word.
6. A model size input of 0.041 and of 61.0 both raise the out-of-band flag; 0.511 does
   not.
7. Rescoring a pre-fix fixture from clouds reproduces the figure
   `scripts/rescore_part_acc.py` currently produces on the same input, so the move
   changes nothing but the location.
8. A subset record over 8 of 9 fragments uses 8 as its denominator and its floor.

**Validated against a real run before use.** The gate proves the arithmetic; it cannot
prove the module reads our actual files correctly. Before any ticket uses it, run it on
one already-published run and reconcile every column against the note that reported it,
writing down each difference and its cause. A column that matches for the wrong reason
is the failure this whole spec exists to prevent.

**And the render.** Ticket 01's first act is to draw the Juglet ground truth and confirm
it is an assembled vessel. That render is the acceptance test for the reference the
whole module reports against, and it comes before any table is believed.

## Out of Scope

- **Any new GPU job.** Everything here reads runs that already exist.
- **Changing `tora/eval/metrics.py`.** The evaluator's stored field stays as it is;
  correcting it at source would silently change the meaning of every historical
  `results/*.json` and make old runs unreadable. The correction belongs at read time.
- **New metrics.** No new measure of assembly quality. `scripts/score_assembly.py`'s
  reference-free scores are a separate line of work and are not folded in.
- **The diagnosis itself.** Which of the five candidates stops the Juglet is `O8` and its
  map; this spec builds the instrument, and deliberately takes no position on the answer.
- **`O2`'s question.** What corpus we should be scoring against — RePAIR, Rabati sherds
  — is unaffected. This makes the existing instrument honest; it does not make it
  sufficient.
- **Retrospective correction of published notes.** The numbers in `docs/notes/` that
  move will be corrected as the tickets that touch them run, not in a sweep.

## Further Notes

**Which of the three this is.** The measurement was broken — failure mode (2). Not the
method, and not the reference. This is the third units-or-convention fault in this
project in a month, after the absolute chamfer threshold and the model size input, and
all three had the same shape: a value read in one place under an assumption that was
true there and false everywhere else.

**Why a module and not a fix to each script.** Fixing five scripts leaves five scripts,
and the sixth experiment writes a sixth. The three faults above were each found only
after a conclusion had been drawn from them.

**The cheap check that would have caught this.** Reading the same run with two of our
own scripts and comparing. It costs seconds and had never been done.

**Expected effect on the record.** Rotation figures reported by the three uncorrected
readers will rise: ×1.125 on the Juglet, up to ×2 on two-fragment pots. Relative
comparisons across objects of different fragment counts will change more than the
absolute figures do. The 72.6%-seated Fractura result is a seating count and is not
affected. `summarise_scale_ladder.py`'s figures were already corrected and should not
move at all — if they do, the module is wrong.
