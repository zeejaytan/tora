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
is not readably different from `plate` (48.7°), `narrow_bottle1` (62.3°) or
`narrow_bottle3` (81.8°); only `galli_pot` (34.8°, ten fragments) is readably better.
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
| 1 | Run-to-run spread | free | **Ruled in, 2026-09-05 — and it is the ruler, a third kind: imprecise rather than wrong.** Four baselines are byte-identical repeats. Draws within one run spread by a median 31.6°; run medians spread 12.5°; the 31.4/33.5/58.2 quoted here was draw 0 of three identical runs on the diluted ruler. **Decision rule: on the Juglet a difference below 17° between two five-draw runs is not readable.** Renders: `artifacts/juglet_spread{,_draws}.png`. Ticket `.scratch/juglet-cause/issues/01-run-to-run-spread.md` |
| 2 | Fragment count (9) | free | **Ruled in weakly, 2026-09-06 — and it does not single the Juglet out.** More pieces does mean more error, but loosely: r = 0.47 over eight fresh ceramics, and `narrow_bottle3` breaks it outright at 4 fragments and 81.8°. The Juglet lands where a nine-piece fresh pot lands, on seating exactly and on rotation at the high end of the spread. So piece count is part of the difficulty and none of the mystery. Ticket `.scratch/juglet-cause/issues/02-is-nine-fragments-enough.md` |
| 3 | A missing sherd | cheap GPU | The Juglet is **incomplete** and none of the eight pots TORA reassembles are. Never tested. [U4](../../intent/U4-missing-fragments.md) names the failure mode |
| 4 | Low-side out-of-band scale | cheap | **Still open, but narrowed 2026-09-06.** `juglet_norm` runs report `scales = 0.041`, 9× below the trained floor of 0.375, and the scale ladder only ever tested *above* 0.5. An audit of all 141 eval runs (`scripts/audit_run_provenance.py`) shows the damage is confined: every conclusion the map rests on comes from `juglet_gt` at 0.511, in band. What sits at 0.041 is the nine-fragment wear comparison (job 29027773) — and **at that size the sherds-seated measure saturates: 9 of 9 on every draw of every arm, while the same runs report sherds turned 85° out of true.** That comparison does not need re-running: it already exists in band as job 29308186, which says wear training moves nothing (56.8 / 59.6 / 62.2°, spread 5.4° against a 17° floor). Whether a small scale *causes* damage still needs the downward ladder. `.scratch/juglet-cause/issues/03-low-side-out-of-band-scale.md` |
| 5 | Wear | expensive | Cannot currently be shown to differ from fresh pots at the resolution available |
| 6 | Evaluated in a mode the model was never trained in | free | **Opened and closed 2026-09-06, same day: ruled out.** `juglet_gt.yaml:6` is `anchor_free: true` while all twelve training configs are `false`, and the encoder does read absolute coordinates (`tora/modeling/encoder/point_cloud_encoder.py:101-113`), so this looked live. It is not: job **28228263** already ran six real pots in both modes, median change **−2.2°**, inconsistent in sign, every object inside the 17° threshold, seating unchanged on five of six — and not a floor effect, since `blue_pot` reads 5.6° anchor-fixed with all five seated. Recorded because the search for it produced the ruled-in reading of candidate 2, not because it explains anything. Renders: `artifacts/anchor_mode.png`, `artifacts/fragment_count.png` |

## Done when

- [ ] Each candidate is ruled in or ruled out (**3 of 6 done**: 1 ruled in, 2 ruled in
      weakly, 6 opened and ruled out; 3 and 4 remain, and 5 now has no residual left to
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
