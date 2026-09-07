# O2 — Is there any valid way to score this work?

**Status:** open · **Blocked by:** none · **Blocks:** O6, and every corpus stage

## Why it matters

**There is currently no valid instrument.** The Juglet is one object and its reference
answer was wrong — it is the scattered scan/table layout, not an assembled vessel.
Until this closes, nothing built here can be shown to help or hurt, and any number
produced is unattributable to method, ruler or reference.

This is the failure mode that has already cost the most in this project: four probes
and two GPU training runs spent on a broken absolute-distance threshold.

## The two candidate routes

**RePAIR** (Zenodo 15800029, the 3 GB open-discovery subset) — about 1,000 real
fragments with archaeologist ground truth. The caveats are real and must be stated
wherever it is used: frescoes are **flat**, have **no vessel curvature**, and are
reassembled largely from the **painting**. It measures *worn fracture surfaces*, not
pottery reassembly.

**Real Rabati sherds**, scanned and physically reassembled by a conservator — the
honest instrument for this material, and the reason the fragment archive comes first.

## What the instrument is now known to do, 2026-09-07 (job 30185814)

**The ruler has a third axis nobody was watching: the size the model is *told* the pot
is.** `scales` is fed into the flow model at every step of the reconstruction, and every
run was being judged against a band derived on paper rather than measured. It is now
measured: **0.375 – 0.811**, from 400 objects of the corpus the baseline was trained on.

Two consequences for this question:

- **Every real pot we own is scored in the extreme bottom of that band, and two are
  below it.** `plate` 0.321 and `coxae` 0.332 sit under everything training showed;
  `vert9`, `galli_pot`, `limb3`, `blue_pot` (0.380–0.410) sit in its lowest 0.2–4.3%.
  So an absolute score on real material is measured on a handicapped model, and any
  route agreed under this question must state its `scales` alongside its numbers.
- **Paired comparisons are safe; absolute levels are not.** The wear sweep holds `scales`
  fixed to within 2% across the intervention, so its 0.843 → 0.645 fall stands. A
  bare "TORA seats 0.843 of real sherds" does not, and should not be quoted without the
  conditioning value beside it.

The earlier "normalised" route made this worse rather than better: `juglet_norm` was
rescaled about an origin the pot sits 0.48 away from, handing the model **0.041** —
eleven times below the floor. `juglet_gt` fixed it. `docs/notes/SCALE_CONDITIONING_MEASURED.md`,
ticket `.scratch/eval-readout/issues/04-what-does-the-scales-input-actually-mean.md`.

**What is not yet known is what the handicap costs**, and that is now ticket
`.scratch/eval-readout/issues/05-does-the-out-of-band-size-cost-anything.md`: re-run the
fresh and worn sets with the size input moved to 0.550 and read the difference in seating.
Two earlier ladders (jobs 29891327, 30130045) found the model flat against this input from
0.04 to 5 — but in *turn*, on *fresh* pots only, so neither touched the metric or the
material the wear claim rests on.

**Measured 2026-09-07, job 30187601 — and the answer moved the question.** The size input
costs little: correcting it lifts fresh seating by 7.5 points (CI [+0.8, +17.1]) and moves
worn seating not at all (−1.6, CI [−18.1, +9.5]), against draw scatter of ±16–20 points.
The refuting outcome did not occur — the wear gap widened rather than closed.

**What the job found instead is a ruler problem, and it is larger.** Job 29308186, the
source of every number in `WEAR_TEST_RESULTS.md` §4, ran 2026-08-17; the unit-box scoring
fix `0d6a85f` landed 2026-09-02. §4 is entirely on the **retired size-dependent** score,
re-pooled for the anchor on 09-05 but never re-scored. On the corrected ruler the baseline
seats **0.597** fresh and **0.560** on the worn sweep, not 0.843 and 0.645, and the gap
between them is **3.7 points, not 20**. Wear still costs seating when read as the erosion
ladder (0.610 → 0.423 at stored size, 0.632 → 0.318 corrected).

**The model comparison, rescored 2026-09-07, job 30190268.** All three models, all three
sets, 10 draws, both gates passed. On the pot-level average **no model is distinguishable
from the untouched baseline**: wear_v2 − baseline is +4.7 fresh (CI [−8.0, +18.5]) and +2.8
worn (CI [−13.3, +14.6]). The prediction that the ranking would survive **failed**.

**The average is a cancellation, and this is the thing O2 exists to catch.** wear_v2 gains
+60 points on `blue_pot` at full wear (the render shows the baseline breaking into two
offset shells and wear_v2 closing the pot) and +2 to +36 on `plate` at every rung, while
losing 21 to 40 points on `galli_pot` at **every rung including zero wear**. The render
shows sherds flying off the *unworn* pot, so that is not a wear effect — it is capability
lost in finetuning, on the 10-fragment pot. On the erosion ladder wear_v2 flattens the drop
from 0.217 to 0.077. A single pooled mean reports all of that as nothing.

**So the evaluation route this question is about must be per-pot, or on the ladder slope.**
A pooled seating mean over six pots is not a valid evaluation of wear training: it scored a
model that cut the wear penalty by two thirds as indistinguishable from one that did not.
That is now a measured statement, not a worry.

Wear v3's success criterion cannot be written against 0.843 / 0.645, and cannot be written
as a pooled mean either.

## Done when

- [ ] At least one evaluation route that is **not the Juglet** is agreed and written down,
- [ ] with its limits stated in the same place (what it can and cannot measure),
- [ ] and validated on a **known-answer case** before any conclusion is drawn from it.
- [ ] and reported with the model's size input (`scales`) beside every score, against
      the measured band 0.375–0.811
- [ ] and read **per object**, not as a pooled mean: job 30190268 showed a pooled mean
      reporting a real two-thirds reduction in the wear penalty as no effect at all

That last line is not optional. A metric that cannot distinguish a good model from a
bad one will happily report a stable, publishable-looking constant.

## Source

`../../CSC/docs/notes/PLAN.md` §R4, `EXTERNAL_DATA_PLAN.md` §4.
