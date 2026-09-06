# O8 — What actually stops TORA reassembling the Juglet?

**Status:** open · **Blocked by:** none · **Supersedes the diagnosis half of** [O6](O6-juglet-under-valid-reference.md)

## Why it matters

Two things changed the ground under the Juglet, and the old diagnosis has not been
re-derived since either of them.

1. **A correct reference now exists.** `juglet_gt.hdf5`, hand-reassembled by the
   conservator 2026-08-10, fitted rigidly to the source fragments with a residual of
   0.0000% of the object. The rotations needed to correct the old scan-table layout ran
   **26° to 177°** — that is how wrong the previous answer key was.
2. **Both units bugs are fixed.** The scoring threshold, and then the object's stored
   size being fed to the network as a conditioning input it had never seen out of band.

`docs/notes/JUGLET_TORA_ROOTCAUSE.md` diagnosed the Juglet as a synthetic-to-real
domain gap compounded by piece count. **Two of its three load-bearing findings were
computed on the corrupted run** and are dead: the four fresh control ceramics it said
TORA scored at chance on now seat every fragment, and the flat 3-to-12-piece curve it
used to rule out piece count *was* the units bug.

So the failure is real — the render shows no vessel — but its cause is unattributed,
and the obvious next move (train on worn fracture) rests on a premise the data does not
currently support.

## What the premise runs into

**The Juglet performs about as badly as a fresh pot of nine fragments does.** Confirmed
2026-09-06 by ticket 02 against eight fresh ceramics all normalised to the same stored
size (0.500, in band), on the common ruler, with a render. On sherds seated the Juglet
reads **5 of 9 (55%)**, sitting between `plate` (4 of 6) and `narrow_bottle1`
(5.5 of 12) — on the fresh trend, not below it. On rotation, 20 pooled baseline draws
give **median 60.9°, range 35.4–88.9°** at scale 0.511, which under ticket 01's 17° rule
is inside the range fresh pots occupy. **Re-read 2026-09-06 at the sharper 9° rule** (ticket 06): the Juglet ties only `narrow_bottle1` (62.3°, twelve fragments), reads readably worse than `plate` (48.7°, six) and readably *better* than `narrow_bottle3` (81.8°, four); fresh pots at four to six fragments themselves span 48.7–81.8°.
**There is no wear-shaped gap left over.** The anchor-mode confound between the two sides
was measured, not assumed — job 28228263, six real pots run both ways, median change
**−2.2°**, inconsistent in sign, inside the threshold. Render:
`artifacts/fragment_count.png`.

**And the wear cannot be measured in this scan.** Break faces are sampled at 0.243% of
object size; the blunting acts at 0.3–0.5%. The dimensionless roughness ratio was tried
and withdrawn: the worn Juglet reads 0.169, fresh `blue_pot` reads 0.167. Between-pot
variation swamps the effect (`WEAR_TEST_RESULTS.md` §2, `GATE_A_RESULT.md`).

**Wear training has already been run twice.** Jobs 29027773 and 29308186: rotation
51.5° → 49.2° → 52.9°. The "recall@10° flat at 0.000" once quoted alongside those is not
evidence: that field is a per-object 0/1 on the whole-pot mean, not a fraction of
fragments, so on a nine-sherd pot averaging 35–60° a flat zero is what the metric must
produce whatever the model does.

**The read-out is now one instrument, and every reader goes through it.**
`scripts/readout.py` (gated by `scripts/check_readout.py`) is the single place a run is
read: it undoes the free-anchor dilution once, reports seating as a count with its floor,
refuses to pool runs made differently, and flags a run whose stored size fell outside the
trained band. Eleven scripts previously kept their own copies of the arithmetic and
disagreed about the same run; as of 2026-09-05 none do
(`.scratch/eval-readout/issues/03`). Every candidate below is read through it, or the
number is not admissible. Every view now also prints the render command for its own rows
and the weight it can bear.

Rewiring the last of them exposed a **second** broken ruler, in the cloud-side scoring
rather than the run-json reading: two scripts thresholded seating at `0.01 / scale` (the
withdrawn absolute metric, converted wrongly on top), and the module's own chamfer
carried a stray 0.5 that made every cloud rescoring twice as forgiving as the evaluator.
Both are fixed and both are now gate assertions. It was caught only because two
independent implementations disagreed by a factor of two — which is the argument for the
module, and the reason candidate 5's "wear training changed nothing" evidence needed
re-reading before it could be trusted.

It was checked against runs already published (`docs/notes/READOUT_RECONCILIATION.md`,
2026-09-05): the ladder that was already corrected by hand does not move — 72 cells, all
within 0.05° — and the Juglet run read by an uncorrected reader rises by exactly 9/8,
**55.7° → 62.7° median**, with the render agreeing that draw 0 is not a vessel. So the
Juglet's non-anchor figure on a valid reference is worse than the number this question
was opened with, not better, and it sits inside the collapsed band rather than at its
edge.

**The reference has now also been confirmed by looking, not only by residual.** The
stored `juglet_gt` cloud renders as a closed vessel with rim and handle and the missing
sherd left open (`artifacts/juglet_spread.png`, 2026-09-05). The same render shows that
the whole-pot *outline* survives even in the worst draw — so on this object a silhouette
is not evidence, and any candidate below must be rendered at individual-sherd placement.

## The candidates

| | candidate | cost | why it is live |
|---|---|---|---|
| 1 | Run-to-run spread | free | **Ruled in, 2026-09-05 — and it is the ruler, a third kind: imprecise rather than wrong.** Four baselines are byte-identical repeats. Draws within one run spread by a median 31.6°; run medians spread 12.5°; the 31.4/33.5/58.2 quoted here was draw 0 of three identical runs on the diluted ruler. **Decision rule: on the Juglet a difference below 17° between two five-draw runs is not readable — sharpened 2026-09-06 to 9.1° for twenty-draw runs (job 30130049, ticket 06); a mixed pair uses its own standard error.** Renders: `artifacts/juglet_spread{,_draws}.png`. Ticket `.scratch/juglet-cause/issues/01-run-to-run-spread.md` |
| 2 | Fragment count (9) | free | **Ruled in weakly, 2026-09-06 — and it does not single the Juglet out.** More pieces does mean more error, but loosely: r = 0.47 over eight fresh ceramics, and `narrow_bottle3` breaks it outright at 4 fragments and 81.8°. The Juglet lands where a nine-piece fresh pot lands, on seating exactly and on rotation at the high end of the spread. So piece count is part of the difficulty and none of the mystery. Ticket `.scratch/juglet-cause/issues/02-is-nine-fragments-enough.md` |
| 3 | A missing sherd | cheap GPU | **Ruled out, 2026-09-06 — graceful degradation, not destabilisation.** Job **30167044** removed one fragment at a time (ranks 2–6) from all eight fresh normalised pots, ten draws each, and scored only the sherds that remain against their unchanged correct poses, with a **reseed control arm** giving each pot its own noise floor. Across five ranks there is no consistent direction — rank 2: two pots further, two closer, three unchanged, median +0.15% of pot size; ranks 3–6 read graceful degradation. The direction carries the argument: fewer pieces is an *easier* task, so the confound pushes towards better scores and destabilisation would have had to beat it. It does not. **One exception survives**: `pink_bowl` at rank 2 goes 1.48% → **13.06%** of pot size (about 1.5 mm → 13 mm on a 100 mm bowl) against a 0.13% bar, and the render shows its two remaining pieces coming apart — but that pot has exactly **one free sherd**, so n = 1 and it is a lead, not a finding. `plate` is refused at every rank (shape gap 0.119 against its own 0.031: two near-equal-area sherds swapping rank) and the refusal is reported, not papered over. **Which of the three: the measurement was broken** — four separate faults, two found inside this ticket (the two arms averaging over *different* sherd sets; a shape-gate tolerance picked by eye that was refusing correct mappings), and fixing them turned the rank-2 headline from “destabilisation on most pots” into “no consistent direction”. On the corrected measurement the method mostly does **not** fail on absence. Repeated drops (50% / 25% present) remain untested — [U4](../../intent/U4-missing-fragments.md). Renders: `artifacts/fragdrop/fragment_drop_rank{2,3}.png`. Ticket `.scratch/juglet-cause/issues/04-missing-sherd-destabilises.md` |
| 4 | Low-side out-of-band scale | cheap | **Ruled out, 2026-09-06 — the prediction failed and that is the answer.** A downward ladder (job 30130045, 8 pots × 10 draws × 5 rungs, gate passed) was submitted with the prediction *written into the job header before the result arrived*: if a too-small stored size damages the reconstruction, rotation should climb as the rung falls. It does not. Across a twelvefold drop (0.04 to 0.50) seven of eight pots move a few degrees; `blue_pot` moves the wrong way (11.4° at the smallest size, 46.1° in the middle) and is the noisiest pot on the in-band ladder. The render of both ends shows no visible difference (`artifacts/ladder_down_ends.png`). What *is* broken at 0.0408 is the sherds-seated measure, which saturates at 9 of 9 on every draw of every arm while the same runs report sherds turned 85° out of true — established by the audit of all 141 eval runs (`scripts/audit_run_provenance.py`). So the `juglet_norm` runs were handicapped in their ruler, not their reconstruction, and the nine-fragment wear comparison needs no re-run: it exists in band as job 29308186 (56.8 / 59.6 / 62.2°). **Which of the three: the measurement was broken**, seating half only. `.scratch/juglet-cause/issues/03-low-side-out-of-band-scale.md` |
| 5 | Wear | expensive | Cannot currently be shown to differ from fresh pots at the resolution available |
| 6 | Evaluated in a mode the model was never trained in | free | **Opened and closed 2026-09-06, same day: ruled out.** `juglet_gt.yaml:6` is `anchor_free: true` while all twelve training configs are `false`, and the encoder does read absolute coordinates (`tora/modeling/encoder/point_cloud_encoder.py:101-113`), so this looked live. It is not: job **28228263** already ran six real pots in both modes, median change **−2.2°**, inconsistent in sign, every object inside the 17° threshold, seating unchanged on five of six — and not a floor effect, since `blue_pot` reads 5.6° anchor-fixed with all five seated. Recorded because the search for it produced the ruled-in reading of candidate 2, not because it explains anything. Renders: `artifacts/anchor_mode.png`, `artifacts/fragment_count.png` |

## Done when

- [ ] Each candidate is ruled in or ruled out (**5 of 6 done**: 1 ruled in, 2 ruled in
      weakly, 3, 4 and 6 ruled out; only 5 remains, and it now has no residual left to
      explain), each with a **render** at a view that resolves what it claims to test
- [ ] Whichever survives is specified precisely enough to hand to `/to-spec`
- [ ] Every reading states which of the three it is — method failed, ruler broken,
      reference wrong

Stopping at the first candidate that looks sufficient is what produced "piece count is
ruled out" in the first place. Rule all six.

## What would refute the whole framing

The five together leaving the gap unexplained — then the cause is something not on this
list, and saying so is the result.

## Source

`docs/notes/JUGLET_TORA_ROOTCAUSE.md`, `WEAR_TEST_RESULTS.md`, `GATE_A_RESULT.md`,
`scripts/build_juglet_ground_truth.py`, job 29891327. Map: `.scratch/juglet-cause/map.md`.
Instrument: `scripts/readout.py`, `.scratch/eval-readout/`.
