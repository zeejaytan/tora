# O8 — What actually stops TORA reassembling the Juglet?

**Status:** open — **reopened 2026-09-07; route (b) is BACK IN PLAY as of 2026-09-09 (ticket 11), alongside (a) and (c).** Six candidates are ruled in or out, but none of them attributes *this object's* failure. Wear is ruled in as a cause of reassembly failure **on other pots, with simulated wear**; the bridge to the Juglet's own real wear is unmeasured, so "it is probably the wear" is a reasonable belief and not a result. · **Blocked by:** none · **Supersedes the diagnosis half of** [O6](O6-juglet-under-valid-reference.md)

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
**There is no wear-shaped gap left over *in turn* — and 2026-09-07 that sentence was
found to be the wrong test.** Wear's measured effect on turn is about **3°** (the causal
sweep, below); the between-pot spread on turn is **±27.7°**. A null against a noise floor
nine times the effect size says nothing. **Wear shows up in seating**, where the same
intervention costs twenty points. The residual figures here stand as arithmetic and are
withdrawn as evidence about wear — see candidate 5. The anchor-mode confound between the
two sides was measured, not assumed — job 28228263, six real pots run both ways, median change
**−2.2°**, inconsistent in sign, inside the threshold. Render:
`artifacts/fragment_count.png`.

**And the wear cannot be measured in this scan.** Break faces are sampled at 0.243% of
object size; the blunting acts at 0.3–0.5%. The dimensionless roughness ratio was tried
and withdrawn: the worn Juglet reads 0.169, fresh `blue_pot` reads 0.167. Between-pot
variation swamps the effect (`WEAR_TEST_RESULTS.md` §2, `GATE_A_RESULT.md`).

**Wear training has already been run twice, and what it did depends entirely on where you
look.** Jobs 29027773 and 29308186. **On the Juglet** it did nothing readable: rotation
51.5° → 49.2° → 52.9° as printed, **57.9° → 55.3° → 59.6°** corrected. The
"recall@10° flat at 0.000" once quoted alongside those is not evidence: that field is a
per-object 0/1 on the whole-pot mean, not a fraction of fragments, so on a nine-sherd pot
averaging 35–60° a flat zero is what the metric must produce whatever the model does.
**On the worn sweep it worked, visibly** — baseline seats 0.645 of the loose sherds (retired ruler; 0.560 corrected — see the candidate 5 row) where
wear_v2 seats 0.815, and the pictures show the baseline `blue_pot` splitting open and the
baseline `plate` collapsed, both of which wear_v2 assembles. Reading only the Juglet rows
of that table is what made "wear training changed nothing" look true.

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
| 5 | Wear | expensive | **Ruled in, 2026-09-07 — demonstrated by intervention, not by correlation; decision taken with the conservator.** Take pots TORA reassembles cleanly, abrade **only the break surfaces**, leave the faces and the correct poses untouched, re-run: same pots, same pieces, same correct answer. **Sherds seated falls 0.843 → 0.645**, twenty points, and the pictures agree — the baseline `blue_pot` splits open at heaviest wear, the baseline `plate` has collapsed by heavy — with wear-augmented training repairing exactly those two (16.3° and 19.9°). The repair transfers **across simulators**: the test sweep uses GARF's `erode_fracture_band`, wear_v2 was trained on `wear_ops.apply_wear` from different source objects. wear_v1 does **not** earn that credit — trained on the test operator, so object-held-out but operator-circular. **Which of the three: the method genuinely failed**, plus **the measurement was broken** in this ticket's own first pass — the +14.3° residual was tested in *turn*, which the intervention moves by ~3°, against a ±27.7° between-pot floor. Standing rule: **score wear on seating, not turn.** **Two things are not claimed:** the Juglet's own +14.3° gap is not attributed to wear (n = 8, 27.7° spread — it fails as a nine-fragment pot fails *and* is worn, and this data cannot apportion them); and the bridge from simulated wear to the Juglet's **real** wear stays **(c) unmeasurable** — Gate A, job 29404479, found real eroded fracture carries no fracture-like roughness at any resolvable scale. That half is a **capture** question and moves to [O7](O7-wear-grounding.md): a scan finer than 0.1% of object size (~0.1 mm points on this vessel), or a real paired control. **Corrected 2026-09-09:** "fresh *and* worn scans of the same pot" as originally written included abrading a modern replica, which is **struck** — burial cannot be simulated, so that calibrates one simulator against another. The surviving form is an excavated sherd bearing both an ancient and a fresh break face. A finer scan also does not reach *this* question alone: `num_points_to_sample: 5000` leaves ~1.2 mm between the points the network sees. The wear curriculum is specified for `/to-spec` in the ticket. Job 29308186. Renders: `WEAR_TEST_RESULTS.md` §6 `heldout_viz/`. Ticket `.scratch/juglet-cause/issues/05-can-wear-be-demonstrated.md`. **Superseded 2026-09-07 (jobs 30187601 / 30190268): those two figures are on the retired size-dependent ruler.** On the corrected unit-box scoring the baseline seats **0.597** fresh and **0.560** worn — a gap of **3.7 points, not 20**. The intervention finding survives on the erosion ladder (0.624 → 0.407) and per pot, but never as a pooled six-pot mean, which scored a model that cut the ladder drop by two thirds as indistinguishable from the untouched baseline. See `intent/O2`, `WEAR_TEST_RESULTS.md` §4. |
| 6 | Evaluated in a mode the model was never trained in | free | **Opened and closed 2026-09-06, same day: ruled out.** `juglet_gt.yaml:6` is `anchor_free: true` while all twelve training configs are `false`, and the encoder does read absolute coordinates (`tora/modeling/encoder/point_cloud_encoder.py:101-113`), so this looked live. It is not: job **28228263** already ran six real pots in both modes, median change **−2.2°**, inconsistent in sign, every object inside the 17° threshold, seating unchanged on five of six — and not a floor effect, since `blue_pot` reads 5.6° anchor-fixed with all five seated. Recorded because the search for it produced the ruled-in reading of candidate 2, not because it explains anything. Renders: `artifacts/anchor_mode.png`, `artifacts/fragment_count.png` |
| 7 | Whole-vessel shape (umbrella [U10](../../intent/U10-type-specific-shape-prior.md)) | weeks | **Tested 2026-09-25, not ruled out.** An adapter trained on juglets shaped like the answer ("ceiling: shown the answer's shape") seated **1 of 9** in own place, against 2 for an adapter trained on ordinary pots and 3 untouched (20 draws each; ticket `u10-juglet-ceiling/05`). But the fine-tune damaged placement on its own choosing vessels too (.897 → .815), and on unworn galli_pot (8 → 2 of 10). So the loss says this way of adding shape hurts, not that shape is not missing. It does **not** narrow O8 toward the break edges. One training run per arm |

## The ladder reproduced from an independent run (job 30337242, 2026-09-10)

Job 30293058 built the erosion ladder and read it on the baseline only. Job 30337242 is
a separately submitted three-arm run on the same eight pots and five rungs, and its
baseline arm **reproduces the ladder**: `blue_pot` exchanging at light abrasion and
scattering by e075, `pink_bowl` holding 3 of 3 at every rung with its worst free sherd
moving only 1.7% → 3.6% of bowl width. The instrument repeats, which is what route (b)
needed before anything is carried across the bridge on it.

**Ticket 11's floor is cleared.** Six of eight ceramics pass their own e000 control
(`blue_pot` 5/5, `narrow_bottle4` 4/4, `narrow_bottle2` 3/3, `pink_bowl` 3/3,
`galli_pot` 8/10, `plate` 4/6), against a floor of three. This is no longer n ≈ 1.
`narrow_bottle1` and `narrow_bottle3` are broken unworn and their ladders carry nothing.

**A prediction stated in advance, and refuted.** `eval_erosion_ceramics.slurm` predicted
exchange would be the common pattern at light and moderate wear. The own-place vs
Hungarian audit says otherwise: on every pot that assembles unworn, relabelling gains
nothing at all — nothing is being swapped, so the failure is **scattering**, the Juglet's
own shape. Exchange shows up only on the pots that were already broken at zero wear.
That is the outcome the ticket said would point route (b) *toward* the Juglet, and it
is the one that happened. It remains a shape match, not an attribution.

Detail and the full table: `docs/notes/CERAMARM_30337242_RESULT.md`.

## Done when

- [x] Each candidate is ruled in or ruled out (**6 of 6 done**: 1 and 5 ruled in, 2 ruled
      in weakly, 3, 4 and 6 ruled out), each with a **render** at a view that resolves what
      it claims to test
- [x] Whichever survives is specified precisely enough to hand to `/to-spec` — the wear
      curriculum, in `.scratch/juglet-cause/issues/05-can-wear-be-demonstrated.md`
- [x] Every reading states which of the three it is — method failed, ruler broken,
      reference wrong
- [x] **The failure to attribute it is stated as the result (2026-09-09).** Ruling six
      candidates in or out is not the same as naming the cause, and the cause has not been
      named: candidate 5 was demonstrated on *other* pots with *simulated* wear, and the
      two things that would carry it to this object — a scan that resolves the real wear
      (~0.1 mm points, and a point budget that does not throw them away), or a real paired
      control such as an excavated sherd bearing both an ancient and a fresh break face —
      still do not exist. *(The "abrade a replica" version of that second capture was struck
      2026-09-09: burial cannot be simulated — see `O7`.)* Everything reachable
      from the scans we hold has now been tried, by three instruments that agree the data
      runs out before the question does (tickets 05, 09, 10). This box records that
      the negative result is stated; it does not close the question. **Revised 2026-09-09
      after `O7` was restated:** the outstanding item is no longer a lab-time decision.
      Buying a finer capture would give the Juglet's wear *dose*, and a dose is not an
      attribution — getting from "worn by this much" to "and that is why it fails" still
      runs through an intervention on pots we control, which is route (b). So **(a) can
      rule wear out but cannot rule it in**, and **(b) is not spent, it is underpowered**:
      ticket 09 had exactly one object with a usable control because five of six were
      already broken at zero abrasion. The live work is a ladder built on objects TORA
      assembles correctly unworn — one GPU evaluation pass, no lab. **Ticketed as
      `.scratch/juglet-cause/issues/11` (2026-09-09):** the sweep never ran a selection
      step at all, and the Fractura `ceramics` group holds eight real pots against the
      three ever worn

Stopping at the first candidate that looks sufficient is what produced "piece count is
ruled out" in the first place. Rule all six.

## What would refute the whole framing

The five together leaving the gap unexplained — then the cause is something not on this
list, and saying so is the result.

## What is still open (reopened 2026-09-07)

The six candidates are settled. **The object is not.** What the map established is that
five of the six do not explain the Juglet and one — wear — demonstrably breaks
reassembly *on pots we abraded ourselves*. Nothing measured carries that from simulated
wear to this vessel's own, because the wear on it cannot be seen at the resolution we
scanned it (Gate A, job 29404479). So the honest statement is **the cause is unattributed
and wear is the leading suspect**, and the question stays open until that gap is closed or
declared unclosable.

- **The Juglet is still not reassembled by anything**, and closing that last step is a
  **capture** problem, not a training one. It is shared with [O7](O7-wear-grounding.md);
  it does not leave here.

- **[SUPERSEDED by ticket 11, below — the reading reversed when the ladder got more than one pot. The `blue_pot` observation itself reproduced exactly and stands.]** **Wear breaks pots the *other* way round (2026-09-09, ticket 09, no GPU).** The
  behavioural route — route (b), does the Juglet's failure have the shape wear produces
  where we control it — has now been run, and it does not carry wear across. On the
  erosion ladder (job 30190268, six objects, five abrasion levels, ten attempts each) the
  **one object that goes from correctly assembled to broken as its break surfaces are worn
  is `blue_pot`, and it fails by *exchange***: at light abrasion the pot is still built and
  two small shoulder chips have been given each other's names, the same swap in **9 of 10**
  attempts, seed-stable across five seeds. Correcting that one swap takes the worst loose
  piece from **14.2% of pot size back to 4.0%**, where the unworn pot sits. The Juglet
  **scatters**. So the shape of the failure does not point at wear on this vessel — if
  anything it points away, on **n = 1**. The prediction recorded in the ticket before the
  run said the ladder would degrade into scattering; it was wrong and is left standing.
  **Why n = 1 and not 6:** five of the six objects are already broken at *zero* abrasion,
  so they cannot show a wear-induced transition at all, and `limb3` is immune at every
  rung. A confound was measured rather than argued — agreement between attempts correlates
  with piece count at **r = −0.81** (a three-piece object has six possible renamings, a
  ten-piece one has 3.6 million), so cross-object "this repeats, therefore exchange"
  readings are partly just counting pieces; the script now prints this itself and states
  its reading per object, up its own ladder. **Which of the three: the method genuinely
  failed** on `blue_pot`; on the ticket's own question, nothing failed — the sweep is
  underpowered. Renders: `artifacts/wearsig/blue_pot_e{000,025,075}.png`,
  `artifacts/wearsig/vert9_e075.png`. `scripts/check_wear_failure_shape.py`. Ticket
  `.scratch/juglet-cause/issues/09-does-wear-fail-like-the-juglet.md`.

- **The ladder had never run its own selection step, and with it run the reading
  reverses (2026-09-09, ticket 11, job 30293058, `COMPLETED|0:0`).** Ticket 09's
  n = 1 was not a limit of the method or the instrument. `build_erosion_sweep.py`
  specifies in its own docstring that it wears "pots TORA CAN currently rebuild",
  but the job passed **no `--objects` filter** and sourced `real_heldout_norm.hdf5`
  — six objects, **three of them bones**. The Fractura `ceramics` group holds
  **eight** real pots. There is no leakage bar to using them: the baseline is
  trained on synthetic data only, so no real pot was ever in it — "held out" was
  never the constraint, the six-object file was.

  Rerun on all eight, **four** pots now carry a valid unworn control (2.4–4.0% of
  pot size) against ticket 09's one: `narrow_bottle4`, `narrow_bottle2`,
  `pink_bowl`, `blue_pot`. The other four are already broken at zero abrasion and
  were excluded before the ladder was read.

  **`blue_pot` reproduced exactly, from a different source file** — 13.8% → 4.0%
  on relabelling, the same swap in 9 of 10 attempts, against ticket 09's 14.2% →
  4.0%, 9 of 10. The instrument is sound and that observation stands.

  **What ticket 09 could not see with one pot is that exchange is the light-wear
  mode.** `pink_bowl` fails the other way and fails at the wear level that
  matters: at e050 and e075 its worst sherd sits **11.9–12.1%** of pot size,
  **relabelling gains nothing** (11.9% → 11.9%), and the **true naming still wins
  10 of 10**. No piece has the wrong name; a piece is in the wrong place. That is
  **scattering — the Juglet's shape** — and e075 is past the Juglet's own measured
  roughness. `blue_pot`'s own ladder has gone to scattering by e075 too.

  **The binding limit is now calibration, not object count.** Only **two** of the
  four controlled pots were actually worn to the Juglet's `relief_p90` of 0.171:
  `blue_pot` (0.170 at e050) and `pink_bowl` (0.152 at e075). `narrow_bottle4`
  survives every rung but **plateaus at 0.244 and never reaches the Juglet's
  condition**, so its survival is not evidence of anything — GARF's Exp 7 failure
  mode, recurring. **Which of the three: the measurement was broken**, in one
  bounded place — `relief_p90` *inverts* on a piece whose break face is already
  smooth, because the mollifier's feathered band boundary leaves a raised rim that
  a 90th percentile picks up (`narrow_bottle2` reads 0.180 → 0.369 under
  *increasing* abrasion). Rendered and confirmed as a statistic artefact, not mesh
  damage: displacement is monotone on every pot and inverted triangles stay below
  0.1%.

  **Weight: n = 2, a lead and not a conclusion.** The direction has reversed,
  which is worth more than the count, but two Fractura ceramics cannot carry a
  claim about one excavated juglet. What route (b) now needs is not more pots — it
  is an erosion operator that reaches the Juglet's condition on more than two of
  them. Renders:
  `artifacts/wearsig_ceramics/renders/ladder_sherd_placement.png` (per sherd,
  unbinned, median draw), `.../narrow_bottle{2,3,4}_band.png`. Note:
  `docs/notes/EROSION_LADDER_CERAMICS.md`. Ticket
  `.scratch/juglet-cause/issues/11-erosion-ladder-on-pots-tora-rebuilds.md`.

- **The Juglet's own joins close — to about the width of the scan's resolution, which
  settles nothing (2026-09-09, ticket 10, no GPU, no fetch).** The last cheap check on this
  vessel: in the conservator's hand-built reassembly, do the break edges still meet, or has
  abrasion taken material off them? Measured per vertex on the source meshes, the joins sit
  **0.21–0.28 mm** apart typically and **0.44–0.52 mm** at the worst tenth — against
  neighbouring scan points **0.29–0.48 mm** apart. The gap and the measurement's own noise
  floor are the same size. **The test is one-sided by construction and it failed on the
  informative side:** a join standing open would have been direct evidence of material loss
  (a hand fitter cannot close a join where material is gone), but a join that closes is
  equally consistent with no loss, with loss too fine to see, and with loss taken evenly off
  both faces — which simply lets the fitter seat the pieces deeper. **Which of the three:
  none.** Nothing failed and nothing was mis-measured; the question is smaller than the
  scan. This is the **third** independent instrument to hit the same wall — Gate A (job
  29404479) found no fracture-like roughness at any resolvable scale, ticket 05 found the
  wear unmeasurable at 0.1% of object size, and this finds the joins unmeasurable at
  0.3–0.5 mm. Renders: `artifacts/jugseam/juglet_gt_seam_gap.png` (the measured quantity
  itself, per vertex — the break network draws itself), `artifacts/jugseam/juglet_gt_vs_scan.png`.
  Ticket `.scratch/juglet-cause/issues/10-does-the-juglet-seam-close.md`.
- **What the failure is *not*: a mix-up.** Ticket 07's instrument, pointed at the Juglet
  for the first time (ticket 08, 2026-09-07, no GPU), says the pieces are genuinely
  mis-placed rather than in the right places wearing the wrong names. Across twelve runs
  and four model arms the best renaming of the sherds still leaves the worst loose sherd
  **19–25% of the pot's size from home** — roughly 12–16 mm on a 65 mm juglet, against
  2–3% for a pot this model assembles correctly — and the renaming that wins is a
  different one in 16 or 17 of every 20 attempts. Contrast `narrow_bottle3`, where the
  *same* renaming wins 10 times in 10 and takes 26.2% down to 8.1%. This matters because
  “plain body sherds look alike, so it swaps them” is the first failure a conservator
  would predict on excavated pottery, and it is the one failure more training could not
  fix. It is not what is happening here. Render:
  `artifacts/juglet_scatter_vs_swap.png`. Ticket
  `.scratch/juglet-cause/issues/08-scattered-or-exchanged.md`. It also gives the
  umbrella's [U2](../../intent/U2-perception-or-placement.md) a second, independent probe
  pointing the same way as its first.
- **The largest unexplained failure in the corpus is not the Juglet.** It is
  `narrow_bottle3` — fresh, unworn, four fragments, +55.3° (2.0 sd) off the trend, rendered
  as a bottle torn into two flaps. None of the six candidates explains it.
  **Explained 2026-09-07, ticket 07, no GPU: the model does not scatter this bottle, it
  exchanges its two halves** — sherd 0 placed where sherd 3 belongs and the reverse, the
  same exchange in **all ten** attempts, while on the four pots this model assembles
  correctly the same test picks the identity naming outright. The two flaps are the
  closest-matching pair of shapes in the bottle (3.1% of pot size apart) **and 53% of the
  whole vessel**; everywhere else in the corpus the near-duplicate pairs are slivers the
  rest of the pot can pin down. **Which of the three: the method genuinely failed** — not
  the reference, because putting the names the right way round still leaves the worst
  sherd **8.1% of pot size** from home against 2.4–3.3% for a correct assembly, with the
  seam down the middle still open. **The form is not the cause**: `narrow_bottle2` and
  `narrow_bottle4` share it and are among the best-assembled objects here (2.8%, 2.4%);
  `narrow_bottle1` fails by scattering instead, a different renaming every attempt.
  Recorded and closed as **one object** — n = 1, the explanation is fitted to eight pots
  and predicts rather than generalises. The transferable part is the instrument:
  **sherds seated, turn and distance-from-home all score a scattering and an exchange
  identically, and those call for opposite responses** (more training helps the first and
  cannot help the second). `scripts/check_identity_swap.py` separates them for free from
  clouds already on disk. Renders:
  `artifacts/nb3/narrow_bottle3_identity_swap.png`, `artifacts/nb3/narrow_bottle_family.png`.
  Ticket `.scratch/juglet-cause/issues/07-narrow-bottle3-collapse.md`.
- **`plate` is refused by the shape gate at every fragment-drop rank** (shape gap 0.119
  against its own 0.031: two near-equal-area sherds swapping rank). Reported, not fixed.
  Ticket 07's independent test agrees there is something to it — `plate` is the one other
  pot whose best renaming repeats across attempts (5/10, then 4/10) — but renaming does
  **not** rescue `plate` (38.0% → 21.9%, against 2–3% for a correct assembly), so it is a
  scattering with a repeated flavour, not an exchange. Two instruments built for
  different purposes pointing at the same pair of sherds; suggestive, not established.
- **TORA does not already have the Juglet's shape, and the "warped" sherds are mirror
  images (2026-09-12, ticket 12, no GPU).** The conservator had seen TORA's intermediate
  output form a convincing juglet out of warped sherds. TORA moves every point on its own
  and makes each sherd solid only at the end, so the test was whether the shape is there
  before that step. It is not, beyond what the solid assembly already shows.
  - **Outline.** Over 20 attempts by the untouched model, the free output sits **4.4%**
    of pot size from the true surface (about 2.9 mm on the 65 mm juglet). After the
    solid step it is **4.9%**. The 0.3 mm difference is finer than the spacing between
    points.
  - **Against the control pots.** Pots TORA rebuilds sit at **1.1–1.3%**, and pots it
    fails on at 2.0–5.1%. Every one of the 20 attempts is above 3.0%.
  - **Placement.** Before the solid step each free sherd is already about **18%** of pot
    size (about 12 mm) from its own place.
  - **The 2026-08-10 picture reproduces** (wear_v2, attempt 05), and it is the flattering
    end: the free outline is 2.5% against 3.7% solid, with the sherds still 15% from home.

  **What the eye read as warping is mirroring.** A sherd's free points form the mirror
  image of the real sherd. No solid turn reproduces a mirror image, so once the sherd is
  made solid its points sit on average up to about 4 mm from the free version, and 6 mm
  in the worst attempt. That is 64 of 160 free sherd-attempts. No sherd on any Juglet arm
  is bent out of shape.

  TORA is trained on turns only, never reflections, so the mirroring is unexplained. It
  is not why the Juglet fails: mirrored sherds sit no further from home than solid ones
  (13.5% against 19.2%). It does appear on the control pots too:
  - on `blue_pot`, its two smallest rim chips mirror and still seat;
  - on `galli_pot` and `plate`, the mirrored sherds are the misplaced ones (20–32% from
    home, against 1.4–2.4% for the solid ones).

  **A lead, not established.** Ticket
  `.scratch/juglet-cause/issues/13-why-mirror-image-sherds.md` tests it, starting with
  whether the mirror test itself can be trusted.

  **The missing piece.** The Juglet's lower body has one hole, about 16 mm across,
  bordered by sherds 2, 3, 4 and 6. Those four are not clearly the worse-placed ones:
  - the two sherds TORA usually seats (1 and 7) are away from the hole, but so are two
    of the worst;
  - a split this lopsided comes up about one time in five by chance.

  So the `galli_pot` follow-up is not triggered.

  **Which of the three: the method genuinely failed**, by misplacement, before the solid
  step as after it. The instrument was checked on the four rebuilt pots, and three faults
  in it were fixed first. This is one object: 20 attempts, against eight control pots.
  Renders: `artifacts/shape12/shape_before_rigid.png`,
  `artifacts/shape12/juglet_gap_map.png`. Ticket
  `.scratch/juglet-cause/issues/12-does-tora-already-have-the-shape.md`; the per-sherd
  and per-arm figures are in its **Result** section.
- **Which sherds TORA gets right depends on which sherd it is given (2026-09-21,
  `.scratch/anchor-choice/issues/01`, job 30917498, `COMPLETED|0:0`).** TORA holds one
  sherd at its true place and places the rest. Normally that is the largest, sherd 0,
  the neck. Moving the held sherd moved the good placements with it. Counts are attempts,
  out of 20, in which each sherd was **truly seated**: a solid sherd (placed rigidly,
  unbent) on its own home patch *and* the right way round, not turned over or spun end
  for end (strict home, `.scratch/juglet-cause/issues/14`):

  | held sherd | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | total /160 |
  |---|---|---|---|---|---|---|---|---|---|---|
  | 0 (neck, as trained) | held | 13 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 14 |
  | 6 (base) | 0 | 0 | 0 | 11 | 11 | 12 | held | 0 | 0 | 34 |
  | 4 (lower body) | 0 | 0 | 0 | 0 | held | 4 | 3 | 0 | 0 | 7 |

  With the neck held, only sherd 1 beside it is reliably right. With the base held, the
  lower body (3, 4, 5) comes right about half the time. **The base is the best single
  reference**, and sherd 4 is the weakest. Sherds 2, 7 and 8 are never seated by any
  single reference.
  - **What follows the held sherd is its region of the pot**, not contact alone: the
    base's neighbours 3, 4, 5 come right, and sherd 4's upper neighbours (2, 7) do not.
  - **The far region is not a correct block put in the wrong place.** Even allowed to
    move as one rigid piece, it sits 15-28% of pot size off, against 3-4% for the near
    region on the same ruler (measured on the raw output; not re-run on solid sherds).
    TORA builds outward from what it is given and loses the thread across the pot's middle.
  - **Which of the three: the method genuinely failed**, in the part of the pot far from
    the held sherd. The held sherd sat exactly at home in all 60 attempts.
  - **Weight: one pot, 20 attempts per arm.** Neck held seats 14 of 160 in this job and
    14 in job 30919372 (9 in job 30130049), so run-to-run noise is a few placements; the
    base-vs-neck gap (34 vs 14) is beyond it.
  - **Two rulers were broken before this table.** TORA's raw output lets the model bend a
    sherd to fit (found by posing real meshes for visual-qa). The own-place home count
    accepts a sherd lying in its place turned over (found by the conservator's eye on
    `twoheld_best`). Both inflated the counts; the region-follows-the-held-sherd pattern
    survives both.
  - **For the pipeline ([U16](../../intent/U16-shortest-route-to-one-reassembled-pot.md)):**
    the Juglet's two halves are each placeable, just not in the same run. Whether that can
    be used without an answer key is open. It would need a reference-free way to tell
    which region of a run to trust, and the one tried so far is at chance
    (`.scratch/juglet-draw-selection/issues/01`).

  Render: `artifacts/anchor/anchor_choice_30917498.png` (median attempt per arm; raw
  output -- superseded by the visual-qa pair below for anything a person judges).

- **Holding neck and base more than triples what TORA truly seats (2026-09-24,
  `.scratch/anchor-choice/issues/02`, job 30919372, `COMPLETED|0:0`).** Same pot, same
  model, 20 attempts per arm, neck alone as the in-job control, solid sherds, strict home:

  | held | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | free sherds seated |
  |---|---|---|---|---|---|---|---|---|---|
  | neck (0) | 13 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 9% |
  | neck + base (0, 6) | 18 | 1 | 7 | 3 | 13 | held | 2 | 1 | **32%** |
  | neck + sherd 4 | 13 | 0 | 0 | held | 0 | 2 | 6 | 0 | 15% |

  - With neck and base held, 5 comes right 13 of 20 and 3 about a third of the time.
    **No attempt is whole:** the best seat 4 of the 7 free sherds.
  - 2, 7 and 8 stay wrong in every arm. That is still a separate problem.
  - The base is a better second reference than sherd 4.
  - **Which of the three:** the method, given one correct sherd per half, seats about a
    third of the rest. Held sherds sat at exactly 0.000% in all 60 attempts.
  - **Weight:** one pot, one job. 9% -> 32% is far beyond run-to-run noise.
  - **For U16:** a person seating two sherds and TORA placing the rest is still the most
    promising route on this pot, but it is further from a whole pot than first reported.
    Open: sherds 2, 7, 8; a second pot.

  Seen in visual-qa (conservator's look pending): pair `twoheld_best` (attempt 3, which
  seats 3 of 7; its sherd 4 is the inside-out one).

- **TORA puts sherds down inside out, and a simple rule catches it on this pot
  (2026-09-24, `.scratch/juglet-cause/issues/14`, no new job).** A sherd's outer face is
  convex and its inner face concave, so a sherd lying in the wall turned over is
  physically impossible. Yet 10-23 of the placements the home count accepted per Juglet
  arm were exactly that. The rest of the inflation is sherds spun end for end with the
  right face out. The encoder is given point normals, so the information is in TORA's
  input and it does not use it.
  - **Rule, no answer key:** a sherd's own curvature centre must lie on the pot's side of
    it. On the Juglet it never flags a correct sherd and agrees with the answer key on
    212 of 212 placements. On the comparison pots it wrongly flags very large sherds
    (`narrow_bottle4`) and tiny chips (`narrow_bottle1`, `galli_pot`), so it is
    **validated on the Juglet only**.
  - **Picking the attempt with fewest flags works here:** it is the best or tied best in 3
    of 4 arms. For neck + base it picks attempt 0, which seats 4 of 7, the maximum,
    reached by 2 of 20 attempts. That is one pick on one pot, not yet a selection method.
  - **Flipping flagged sherds back failed:** 0 of 23 became seated. A flip exists (the
    answer key finds one for about half), but the reference-free choice of axis misses it,
    and the sherds are also off-centre.
  - **Which of the three:** the method genuinely failed (inside-out placements). Separately,
    the measurement was broken (home count blind to it); all earlier Juglet home counts
    overstate.
  - **Next, and what would change this:** a strict home inside `own_place.py`, so other
    analyses stop inheriting the blind spot. Solid-only sampling was tried (ticket 15,
    below) and did not help; rejecting inside-out sherds during sampling is untested.

  Seen in visual-qa (conservator's look pending): pair `insideout_rulepick`, correct Juglet
  beside the rule-picked attempt 0.

- **Stopping TORA from ever mirroring or bending a sherd does not help (2026-09-25,
  `.scratch/juglet-cause/issues/15`, job 31207476, `COMPLETED|0:0`).** A test-only option
  (`model.rigid_from_t`) makes every sampling step head for the sherds moved as solid
  pieces, so TORA keeps its trained shape knowledge but can only turn and slide. Checked:
  no sherd mirrored, every sherd an exact solid copy. Strict home, 20 attempts per arm:
  neck 20 -> 22 of 160; neck + base 33 -> 35 of 140 (solid from halfway: 37). All inside
  the +-10 band the ticket called refuted. Inside-out placements barely fall (60 -> 47):
  TORA turns sherds over with ordinary turns just as readily, so mirroring was one route to
  an inside-out sherd, not why sherds are misplaced.
  - **Which of the three:** the method genuinely failed. TORA's knowledge of where the
    Juglet's sherds go is the limit, not the moves it is allowed.
  - **Weight:** one pot, one seed. The neck + base control itself came out 33 against 45
    in job 30919372 on the same seed, so the 9% -> 32% rise above is really 9-13% ->
    24-32%: still real, but smaller than first stated. A gain under ~10 sherds cannot be
    ruled out; a large one can. Nothing was staged for the conservator's eye; that look was
    reserved for a positive result.
  - **What it rules out for U16:** making TORA move sherds as solid pieces is not the
    route. Rejecting inside-out sherds during sampling is still untested. What is left is the reference sherds a
    person seats, a better-trained model, or a different method.

## Source

`docs/notes/JUGLET_TORA_ROOTCAUSE.md`, `WEAR_TEST_RESULTS.md`, `GATE_A_RESULT.md`,
`scripts/build_juglet_ground_truth.py`, job 29891327. Map: `.scratch/juglet-cause/map.md`.
Instrument: `scripts/readout.py`, `.scratch/eval-readout/`.
