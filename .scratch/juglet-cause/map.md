# Map — what actually stops TORA reassembling the Juglet

**Label:** `wayfinder:map` · **Charted:** 2026-09-05 · **Status:** open — **reopened
2026-09-07; the remaining work is one GPU pass, not a lab decision (revised 2026-09-09)**
**Why it is open:** six candidates are ruled in or out and the object's own failure is still
unattributed. Wear was demonstrated on *other* pots with *simulated* wear; nothing carries
that to this vessel. Wear is the leading suspect, not the answer. **The behavioural route
(b) has now been run and did not carry it across** — and on the one object where wear does
break a pot, it breaks it the *opposite* way to the Juglet. **Revised the same day, after
`O7` was restated:** a finer capture yields the Juglet's wear *dose*, and a dose is not an
attribution — so route (a) can rule wear **out** but not **in**, and it is no longer the
decision this map is waiting on. Route (b) is **underpowered, not spent**, and repowering it
is compute we already have. Route (c) stands as the statement about the data that exists.
**Answers:** [O8](../../intent/O8-what-stops-the-juglet.md)

## Destination

Establish what actually stops TORA reassembling the Juglet, now that both units bugs
are fixed and a correct reference exists. Ends with each of five candidate causes ruled
in or out — each with a render — and whichever survives specified precisely enough to
hand to `/to-spec`. It does **not** end with a trained model.

## Notes

**Domain.** The Juglet is a nine-sherd excavated vessel, worn, and **incomplete** — one
visible piece was never recovered. A reconstruction that leaves that gap open is
*correct*; a model that fills it is wrong. Any metric rewarding contact everywhere will
mislead here (`scripts/build_juglet_ground_truth.py`).

**This map runs its own experiments** (deliberate override of wayfinder's plan-only
default). A claim is not settled here without a render, and a ticket that only specifies
an experiment cannot produce one. **Ask before submitting any Slurm job.**

**Every ticket must state which of the three it found:** the method failed, the ruler
was broken, or the reference was wrong. These lead to opposite decisions and both of the
last two have already happened on this object.

**Rotation error thresholds on this material** (`WEAR_TEST_RESULTS.md` §5): 10–35° the
assembly looks correct and the residual is symmetry; 40–70° it has genuinely collapsed.
"Within 10°" reads 0.000 almost everywhere and is too strict to be useful. Report
non-anchor rotation (`× n/(n-1)`) — the raw mean is diluted by the free anchor.

**The read-out is now one instrument and every reader goes through it**
(`scripts/readout.py`, gated by `scripts/check_readout.py`, built under
`.scratch/eval-readout/`). It applies the non-anchor `× n/(n-1)` correction once, and it
**refuses to pool runs made differently** — which is how ticket 02 found the anchor-mode
split rather than quietly averaging across it. Do not hand-compute these numbers; if the
module refuses a comparison, that refusal is the finding.

**Skills each session should consult:** `grilling` and `domain-modeling` for any ticket
that turns into a judgement call; `diagnosing-bugs` if a measurement looks wrong.

**Conventions:** `docs/agents/issue-tracker.md` for the ticket template — the `Answers:`
line is mandatory. Verify with `python ../../scripts/check_intent_links.py`.

## Decisions so far

- **The reference is trusted.** `juglet_gt.hdf5` was hand-reassembled by the conservator
  (2026-08-10) and fitted rigidly to the source fragments at a residual of 0.0000% of
  the object, so it holds the same vertices in the same order — the scan-layout
  substitution that broke the previous reference cannot have happened silently. Settled
  on the conservator's authority plus `scripts/build_juglet_ground_truth.py`.
- **The destination is a diagnosis, not a wear curriculum.** Teaching worn-fracture
  alignment was the opening proposal; it was set aside as a *destination* because the
  Juglet's rotation error already sits inside the fresh-break range, the wear cannot be
  measured at this scan resolution, and wear training has been run twice with no
  movement in rotation. It survives as candidate 5, last, reframed as "can wear be
  demonstrated at all".
- **One Juglet run cannot tell two methods apart** — repeat attempts at the identical
  job land ~30° apart, and two five-draw runs differ by up to **17°** by chance alone.
  Decision rule for every later ticket: *below 17°, report no difference detected* —
  **sharpened 2026-09-06 by ticket 06 to 9.1° for twenty-draw runs**; 17° still governs
  five-draw runs, and a mixed pair uses its own standard error. The
  27° gap this map was opened on was draw 0 of three identical runs, not three methods.
  Renders confirm the reference is an assembled juglet, and also that the whole-pot
  outline cannot separate a 35° draw from an 89° one — later renders must show
  individual sherd placement.
  [01: How much do repeat runs of the same thing disagree on the Juglet?](issues/01-run-to-run-spread.md)
- **The Juglet performs about as badly as a fresh, unworn pot of nine fragments does —
  it is not an outlier, and there is no Juglet-shaped residual for wear to explain.**
  Against eight fresh ceramics all normalised to the same stored size, it seats 5 of 9
  (55%), landing between `plate` (4 of 6) and `narrow_bottle1` (5.5 of 12) — on the
  trend, not below it. On rotation the reading was sharpened by ticket 06 and is now
  **inside the fresh range rather than indistinguishable from it**: at the 9° rule the
  Juglet ties only `narrow_bottle1` (12 fragments), reads readably worse than `plate`
  (6 fragments, 48.7°) and readably *better* than `narrow_bottle3` (4 fragments,
  81.8°) — and fresh pots at 4–6 fragments themselves span 48.7–81.8°, so it is not an
  outlier among them.
  **Candidate 2 is ruled in weakly**: fragment count predicts error loosely (r = 0.47
  over eight pots) and `narrow_bottle3` breaks it — 4 fragments, 81.8°. A confound was
  found and then *measured rather than argued*: `juglet_gt` runs anchor-free while every
  ceramic runs anchor-fixed, but job 28228263 ran six real pots both ways for a median
  change of **−2.2°**, inconsistent in sign and well inside the 17° threshold, so it
  cannot manufacture the result. **Which of the three: none — the method is doing what it
  does on any pot of this many pieces.** Renders: `artifacts/fragment_count.png`,
  `artifacts/anchor_mode.png`.
  [02: Is nine fragments on its own enough to explain the Juglet?](issues/02-is-nine-fragments-enough.md)
- **A stored size far below the trained band does not damage the reassembly — it breaks
  the sherds-seated measure and nothing else. Candidate 4 is ruled out.** The prediction
  written into the job header before submitting (rotation should climb as the size falls)
  **failed**: across a twelvefold drop in stored size, seven of eight pots move by a few
  degrees, and the one that moves — `blue_pot`, 11.4° at the smallest size against 46.1°
  in the middle — moves the *wrong way*. The render of both ends agrees: no visible
  difference. So the `juglet_norm` runs at 0.0408 were handicapped in their *ruler*, not
  in their reconstruction. **Which of the three: the measurement was broken**, on the
  seating half only. Job 30130045, 8 pots × 10 draws × 5 rungs, gate passed. Render:
  `artifacts/ladder_down_ends.png`.
  [03: Does a scale below the trained band damage the result too?](issues/03-low-side-out-of-band-scale.md)
- **The ruler is now sharp to 9°, and at that sharpness the adapter still does nothing —
  and one sherd at a time, all three arms are plainly wrong.** Twenty draws per arm takes
  the readable threshold from 17° to **9.1°**; every pair of arms is still a tie
  (adapter_on 61.2°, baseline 66.2°, adapter_off 69.8°, largest gap 8.6° against a 9.4°
  bar), and the *adapter-off* arm reads worst, which is what three samples of one
  distribution look like. The per-sherd render is what changes the reading: behind a
  whole-pot median of 60–70° sit individual sherds turned **75–176°** and displaced
  **3–51% of the pot's size**, several onto the opposite side of the vessel, in every
  arm. A sherd can count as "seated" while being turned most of the way round.
  **Which of the three: the method genuinely failed** — this ticket existed to rule out a
  blunt instrument, and the instrument was not the problem. Job 30130049. Render:
  `artifacts/juglet_arms_sherds.png`.
  [06: Buy a finer decision rule — twenty draws per condition](issues/06-twenty-draws-per-condition.md)
- **A missing sherd degrades gracefully; it does not destabilise the sherds that
  remain. Candidate 3 is ruled out.** Take a pot TORA reassembles cleanly, remove one
  fragment, re-run, and score only the survivors against their unchanged correct poses:
  across ranks 2–6 on eight fresh pots (job 30167044, ten draws per arm, with a reseed
  control arm giving each pot its own noise floor) there is **no consistent direction** —
  rank 2 is two pots further, two closer, three unchanged, median +0.15% of pot size, and
  ranks 3–6 read graceful degradation. The direction is what carries it: fewer pieces is
  an easier task, so the confound pushes *towards* better scores and destabilisation would
  have had to beat it. **One exception survives every correction** — `pink_bowl` at rank 2,
  1.48% → 13.06% of pot size (1.5 mm → 13 mm on a 100 mm bowl) with the render showing its
  two remaining pieces coming apart — but it has exactly one free sherd, so n = 1.
  **Which of the three: the measurement was broken**, four times; two of the faults were
  found inside this ticket (the two arms averaged over *different* sherd sets; the shape
  gate's tolerance was eyeballed and refusing correct mappings) and both pointed the wrong
  way — fixing them turned the rank-2 headline from “destabilisation on most pots” into
  “no consistent direction”. On the corrected measurement the method mostly does not fail
  on absence, so **generative completion of the missing piece is not load-bearing for the
  Juglet**. Repeated drops (50% / 25% present) remain untested — that is `U4`'s deeper
  rung. Renders: `artifacts/fragdrop/fragment_drop_rank{2,3}.png`.
  [04: Does a missing sherd destabilise a pot that TORA otherwise reassembles?](issues/04-missing-sherd-destabilises.md)
- **The Juglet's failure looks like a fresh pot's failure, not a different kind of
  failure** — the render ticket 02 owed and could not produce from disk.
  `artifacts/fragdrop/juglet_vs_fresh.png` draws the Juglet's proposed assembly beside
  three fresh pots, one colour per sherd, nothing re-centred. Its worst-placed sherd ends
  **32.2% of pot size** from home, against `galli_pot` 29.9%, `plate` 32.4% and
  `narrow_bottle1` 47.2% — inside the fresh spread, not an outlier. The proposed juglet
  still reads as a juglet in outline with its sherds shuffled. The caption metric had to
  be changed to get there: it used to quote the worst sherd's **turn**, and `plate`
  reported 177° for a sherd sitting 1% of pot size from correct — small sherds are
  near-planar and near-symmetric, so a half-turn puts them back on themselves, and the
  Kabsch angle also ignores displacement entirely. **Which of the three: the measurement
  was broken** — distance from home cannot be fooled that way, and it is the thing a
  conservator can see (1% of a 100 mm pot is a millimetre of open seam).
- **Wear demonstrably causes reassembly failure — and that was shown by intervention,
  not by correlation. Candidate 5 is ruled in — for pots we abraded ourselves, not yet
  for the Juglet.** Take pots TORA
  reassembles cleanly, abrade **only the break surfaces**, leave the faces and the correct
  poses untouched, and re-run: same pots, same pieces, same correct answer.
  **Sherds seated falls from 0.843 to 0.645** — twenty points — with the pictures agreeing
  (baseline `blue_pot` splits open at heaviest wear, baseline `plate` has collapsed by
  heavy), and wear-augmented training repairs exactly those two cases.
  **Both of those numbers are on the retired ruler and are superseded (2026-09-07, jobs
  30187601 / 30190268).** On the corrected unit-box scoring the baseline seats **0.597**
  fresh and **0.560** worn — a gap of **3.7 points, not 20**. The intervention finding
  survives, but only when read as the erosion ladder (baseline 0.624 → 0.407) or per pot,
  never as a pooled six-pot mean: a pooled mean scored wear_v2, which cuts the ladder drop
  from 0.217 to 0.077, as indistinguishable from the untouched baseline. Wear v3's success
  criterion cannot be written against 0.843 / 0.645. `WEAR_TEST_RESULTS.md` §4,
  `intent/O2`, `.scratch/eval-readout/issues/05`. That repair is a
  **cross-simulator** result: the worn test sweep is built with GARF's `erode_fracture_band`
  while wear_v2 was trained on `wear_ops.apply_wear` (one-sided peak truncation, recession
  removed) from different source objects. wear_v1 does **not** get this credit — it was
  trained on the test operator and is object-held-out but operator-circular.
  **Which of the three: the method genuinely failed** — plus **the measurement was broken**
  inside this ticket's own first analysis. The residual it was asked to state (+14.3° of
  turn against a ±27.7° between-pot spread) was measured in **turn**, which the intervention
  moves by about **3°**, against a noise floor nine times larger. A null in that metric says
  nothing about wear. Standing rule from here: **score wear on seating, not on turn.**
  The bridge from simulated wear to the Juglet's own **real** wear remains **(c),
  unmeasurable** — Gate A found real eroded fracture carries no fracture-like roughness at
  any resolvable scale — and is a **capture** question: a scan finer than 0.1% of object
  size, or fresh *and* worn scans of the same pot. The wear curriculum is specified in the
  ticket and hands to `/to-spec`. Job 29308186; `WEAR_TEST_RESULTS.md` §4 §6.
  [05: Can the Juglet's wear be demonstrated at all, at any resolution we have?](issues/05-can-wear-be-demonstrated.md)
- **TORA can see the wear; the earlier "it cannot" was proved for the join gap only.** The
  encoder is fed six numbers per point, not three — the sixth is the face normal of the
  triangle each point landed on, a cue at roughly thirty times finer scale than the spacing
  between the points themselves. Measured on the exact points the network receives,
  break-face roughness falls monotonically as wear rises on the six real objects:
  29.7° → 27.2 → 26.6 → 24.3 → **22.2°**. `LORA_VESSELS_29623885_RESULT.md`.
- **`narrow_bottle3` does not get scattered — its two halves get exchanged.** The worst
  unexplained failure in the corpus, resolved 2026-09-07 from clouds already on disk, no
  GPU. Sherd 0 is placed where sherd 3 belongs and sherd 3 where sherd 0 belongs, the same
  exchange in **all ten** attempts; on the four pots this model assembles correctly the
  same test picks the identity naming outright, so a non-identity match is not something
  it hands out for free. The two flaps are the bottle's closest-matching pair of shapes
  (3.1% of pot size apart) **and 53% of the whole vessel** — elsewhere the near-duplicate
  pairs are slivers the rest of the pot pins down. **The method genuinely failed**, not
  the reference: with the names put right the worst sherd still sits **8.1% of pot size**
  from home (about 8 mm on a 100 mm bottle) against 2.4–3.3% for a correct assembly, and
  the seam stays open. The narrow-bottle form is not the cause — `narrow_bottle2` and
  `narrow_bottle4` share it and are among the best-assembled objects here, and
  `narrow_bottle1` fails by scattering instead. **Closed as one object** (n = 1); the
  transferable part is that **sherds seated, turn and distance-from-home score a
  scattering and an exchange identically while the two call for opposite responses** —
  more training is the lever for the first and cannot be for the second.
  `scripts/check_identity_swap.py`, `scripts/render_identity_swap.py`.
  [07: Why does `narrow_bottle3` collapse? Fresh, unworn, four fragments](issues/07-narrow-bottle3-collapse.md)
- **The Juglet is scattered, not mixed up — and that rules out the failure a
  conservator would predict first.** Ticket 07 built an instrument that tells two failure
  kinds apart and had never been pointed at the Juglet. Pointed at it (2026-09-07, no GPU,
  twelve runs across four model arms), it says the pieces are genuinely mis-placed: the
  best renaming still leaves the worst loose sherd **19–25% of pot size from home**
  (12–16 mm on a 65 mm juglet, against 2–3% for a correct assembly) and the winning
  renaming is a **different** one in 16–17 of every 20 attempts. `narrow_bottle3`, the
  one real exchange in the corpus, repeats the *same* renaming 10 times in 10 and drops
  26.2% → 8.1%. **Which of the three: the method genuinely failed** — and now more
  narrowly, by mis-placing rather than by confusing look-alike sherds, which is the one
  failure mode more training could not have fixed. Render:
  `artifacts/juglet_scatter_vs_swap.png`. Also the second, independent probe the
  umbrella's `U2` (perception or placement?) was short of.
  [08: Is the Juglet scattered, or are its sherds merely mixed up?](issues/08-scattered-or-exchanged.md)
- **`narrow_bottle3`'s exchange is a real exchange, and the break edges prove it —
  recorded here 2026-09-09 because this map's instruments now lean on it.** The seam test
  (`.scratch/perception-or-placement/issues/01`, resolved 2026-09-07, no GPU) took the two
  swapped flaps down to the source **meshes** and measured, per vertex of the break surface,
  how far it sits from the fragment it should be touching. In the true bottle the joins
  close to **0.11–0.23%** of the bottle's own size; with the two flaps swapped and then let
  settle into their best possible fit, they sit **0.58–0.61%** apart typically and
  **3.2–5.7%** apart at the worst tenth — the fit can only press one stretch of seam shut by
  levering the rest of it open, which is what a mismatched edge does. The control matters:
  the same settling run on the *true* arrangement leaves it where it already was (0.23 →
  0.18%), so the optimiser is not simply dragging whatever it is handed into contact.
  **Resolution gate, reported first:** vertices sit 0.22–0.26% apart, against an effect of
  1% and up. On the 5000-point clouds those two numbers were both about 1.8% — the ruler and
  its own noise floor the same size, which is why this needed meshes. Two instruments were
  built and the first was wrong in a way every number it produced concealed; its control
  caught it. This is the result the Juglet's own seam check (ticket 10) is calibrated
  against. `scripts/check_seam_swap.py`, `artifacts/nb3seam/narrow_bottle3_seam_swap.png`.
- **Wear breaks a pot the *other* way round: route (b) is spent.** Ticket 09 (2026-09-09, no
  GPU, laptop analysis of clouds already fetched) asked the bridge question that needs no
  finer scan — does wear produce the *kind* of failure the Juglet is having? On the erosion
  ladder (job 30190268 baseline arm, six objects × five abrasion levels × ten attempts), the
  **one object that goes from correctly assembled to broken as its break surfaces are worn
  is `blue_pot`, and it fails by exchange, not scattering**: at light abrasion the pot is
  still built and two small shoulder chips wear each other's names, the same swap in **9 of
  10** attempts and identical across five random seeds. Putting that one swap right takes
  the worst loose piece from **14.2% of pot size back to 4.0%**, where the unworn pot sits.
  The Juglet scatters (ticket 08). So the behavioural bridge does not carry wear across —
  weak evidence *against* wear as the Juglet's cause. **The prediction recorded before the
  run was the opposite and it was wrong**; it is left standing in the ticket. **Weight:
  n = 1.** Five of the six objects are already broken at zero abrasion and can show no
  wear-induced transition; `limb3` is immune at every rung; `vert9`, briefly counted as a
  second control, reads 11.9% at e000 and is not one. A confound was measured rather than
  argued: agreement between attempts tracks piece count at **r = −0.81** (three pieces = six
  possible renamings, ten pieces = 3.6 million), so cross-pot "it repeated, therefore
  exchange" readings partly just count pieces — the script now prints this itself and states
  its reading per pot, up its own ladder. **Which of the three: on `blue_pot` the method
  genuinely failed; on the ticket's own question nothing failed — the sweep is
  underpowered.** What would change it: an erosion ladder built on objects TORA assembles
  correctly when unworn (one GPU evaluation pass). `scripts/check_wear_failure_shape.py`,
  `artifacts/wearsig/blue_pot_e{000,025,075}.png`.
  [09: Does wear fail like the Juglet?](issues/09-does-wear-fail-like-the-juglet.md)
- **The Juglet's own joins close — to about the width of the scan's resolution, which
  settles nothing.** Ticket 10 (2026-09-09, no GPU, no fetch) pointed the `narrow_bottle3`
  seam instrument at this vessel before any decision to spend lab time on route (a). In the
  conservator's hand-built reassembly the break surfaces sit **0.21–0.28 mm** from their
  neighbours typically and **0.44–0.52 mm** at the worst tenth, while neighbouring scan
  points are **0.29–0.48 mm** apart: the gap and the measurement's own noise floor are the
  same size. **The test is one-sided by construction and it failed on the informative side.**
  A join standing open would have been direct evidence of material loss — a hand fitter
  cannot close a join where material is gone — but a join that closes is equally consistent
  with no loss, with loss too fine for this scan, and with loss taken evenly off both faces,
  which simply lets the fitter seat the pieces deeper. **Which of the three: none of them.**
  Nothing failed and nothing was mis-measured; the question is smaller than the scan. Kept
  for the record: the same "closest 2% of vertices" statistic reads 0.14–0.19% of object size
  on the **scan-table jumble** too, which looks like a closed seam and is nothing of the kind
  — the pieces are overlapping. That is this workspace's recurring failure mode and the
  reason the measured quantity itself was rendered per vertex, where the break network draws
  itself. **This is the third independent instrument to hit the same wall**: Gate A (job
  29404479) found no fracture-like roughness at any resolvable scale, ticket 05 found the wear
  unmeasurable at 0.1% of object size, and this finds the joins unmeasurable at 0.3–0.5 mm.
  `artifacts/jugseam/juglet_gt_seam_gap.png`, `artifacts/jugseam/juglet_gt_vs_scan.png`.
  [10: Do the Juglet's own joins still close?](issues/10-does-the-juglet-seam-close.md)
- **Scope is the Juglet alone.** The general claim — does any of this hold beyond one
  architecture and a handful of objects — stays with the umbrella's `U3`.

## Not yet specified

- **What would attribute the Juglet's failure to wear — or take wear off the list.
  Narrowed 2026-09-09: route (b) is spent, and the choice is now (a) or (c).** This is the
  reopened destination. Wear breaks reassembly on pots we abrade ourselves; the Juglet's own
  wear is invisible at the resolution it was scanned. Of the three routes originally
  visible:
  - **(a) a capture that resolves the wear** — points about **0.1 mm** apart on this
    vessel, three to five times finer than the 0.29–0.48 mm we have, reachable with
    close-range structured-light kit rather than anything exotic. **Heavily downgraded
    2026-09-09, in three steps.** First, the paired-control half of this route — an
    excavated sherd bearing both an ancient and a fresh break face, or a replica broken and
    abraded — is **struck in every form**: burial cannot be simulated, no two pots are the
    same, and even two faces on one sherd are two different *fracture events*, so the
    comparison confounds burial with "these broke differently" (`O7`). Second, a finer scan
    does not reach this map's question anyway, because `num_points_to_sample: 5000` puts
    ~1.2 mm between the points the model is shown — the pipeline already discards the detail
    the current scan holds. Third and decisive: **a capture measures the wear *dose*, and a
    dose is not an attribution.** Going from "the Juglet is worn by this much" to "and that
    is why it fails" still requires an intervention on pots we control, which is route (b).
    So this route **can rule wear out** — a fine scan showing nothing there would falsify
    the candidate — **but it cannot rule it in**, and it is not what this map is waiting on.
  - **(b) a behavioural test that needs no scan** — does the Juglet's failure have the shape
    wear produces on pots where we control it? **Run once, and it did not carry wear across:**
    ticket 08 found the Juglet scattered; ticket 09 found that the one object wear breaks on
    the erosion ladder fails by *exchange* instead. Weak evidence against wear, on n = 1.
    **Called "spent" on 2026-09-09 and that was wrong — it is underpowered, not spent**, and
    the difference matters because route (a) turns out not to attribute anything either. The
    fix is a ladder built on objects TORA assembles correctly when unworn; ticket 09's own
    sweep had five of six objects already broken at zero abrasion, which is a selection
    problem in the sweep and not a limit on the method. **One GPU evaluation pass, no lab
    time — this is now the cheapest live route and the only one with power to grow.**
  - **(c) accept it cannot be attributed with what exists and say so as the result.**
    **This is what the evidence now supports.** Three independent instruments — Gate A,
    ticket 05, ticket 10 — agree the data runs out before the question does. The failure to
    attribute has been written into `O8` as the result.

  So this is no longer fog. **Revised 2026-09-09 after `O7` was restated: close on (c) as
  the statement about the data that exists — that part is settled and does not depend on
  what happens next — and treat the powered erosion ladder (route b) as the live follow-up.**
  It is one GPU pass rather than a lab booking, and it is worth running whether or not this
  map stays open, because it is the only thing that would let ticket 09's n = 1 bear weight.
  Route (a) reduces to a falsification test held in reserve. Nothing further can be squeezed
  from the scans that exist, and nothing needs to be.

- **What replaces "domain gap" as the standing explanation.** `JUGLET_TORA_ROOTCAUSE.md`
  concluded synthetic-to-real domain gap plus piece count; both halves were computed on
  the corrupted run. Once the five tickets land, that note needs rewriting — but what it
  should *say* cannot be drafted until they do.
- **Two anchor-mode inconsistencies that currently cost nothing but are still wrong.**
  All 141 eval runs on Spartan have `model.anchor_free: false`, so (a) in anchor-free
  *data* mode the sampler pins the anchor to ground truth while the encoder is shown it
  at the origin, and (b) `evaluator.py:74`'s anchor-aligning ICP has never run, on any
  run. Job 28228263 puts the net effect below the noise floor on six pots, so nothing
  here needs redoing — but whether the four anchor-free Juglet configs should be split
  into "benchmark" and "deployment" is a real question, and not sharp enough to ticket
  until something depends on the answer.
- **Whether GARF should be run alongside — this fired on 2026-09-07, and what fired it is
  out of this map's scope.** Something did turn out to be TORA-specific, but it is not
  about the Juglet: TORA normalises a fragment set by the half-span of the **whole
  assembled object** and feeds that one number to every point
  (`tora/data/dataset.py:427-430`, `flow_model/embedding.py:151-152`), so a partial
  assemblage is inflated to whole-pot size and the model cannot be told pieces are
  missing. GARF normalises and labels **per fragment** and ships a removal / foreign-piece
  test harness. That decides how `U4` (most fragments never recovered) must be run, and
  it is ruled **out of scope here** — see Out of scope. What remains fog on *this* map is
  narrower: whether GARF should be run on the **Juglet itself**, which only becomes a
  question if the Juglet diagnosis needs a second architecture to stand up.
  Full argument: `docs/notes/PARTIAL_ASSEMBLAGE_TORA_VS_GARF.md`.

## Out of scope

- **Building a worn-fracture curriculum.** Beyond the destination: this map decides
  whether wear is the cause, and hands off if it is. `O7` grounds the wear model.
- **Fixing the other unexplained failures** — the already-normalised simulated bones
  (61°, 64°) and `coxae` (86°). Real, open, and not about the Juglet.
- **Re-running the millimetre-stored Fractura subsets** (real bones, egg) normalised.
  Owed from the units fix, but it is bookkeeping on a different question.
- **Partial assemblages — how much of a pot do you need before reassembly works.** The
  proposed `piececount_sweep` on `galli_pot` was **not run**, and should not be: its
  subsets are drawn without any adjacency test (only 19 of 45 fragment pairs on that pot
  share a break surface, and connectedness climbs with k, so the confound runs along the
  tested axis), and TORA inflates every subset to whole-pot size regardless. This is
  `U4`'s question, on a different model, and it does not bear on what stops the Juglet —
  ticket 04 already showed a single missing sherd degrades gracefully.
  `docs/notes/PARTIAL_ASSEMBLAGE_TORA_VS_GARF.md`, `intent/U4`.
