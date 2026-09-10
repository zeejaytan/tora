# O7 — Does the wear augmentation earn its place, and are its parameters bounded?

**Status:** open · **Blocked by:** none · **Effort:** ~3 days, can run in parallel
**Restated 2026-09-09, accepted by the conservator.** This question used to read *"is the
wear model grounded in real material?"* and was blocked on a capture that does not exist and
cannot be built. The argument for the change is in **Restatement** below; the short version
is that the wear model is a **training augmentation**, not a measuring instrument, and
augmentations are validated by whether they help rather than by physical fidelity. The two
criteria are now **behavioural** and **bounded-range**.

## Why it matters

The wear model is currently calibrated against **a physical argument and one pot**. That is
enough to have shown wear-augmented training stops heavily worn pottery collapsing — a
visible effect, small n — but not enough to rely on without knowing *why* it helps.

Kura-Araxes black-burnished surfaces, Bedeni and Trialeti fabrics differ in hardness,
temper and firing, and therefore in how they abrade. Parameters chosen freely, with nothing
saying what a plausible value even is, are a soft spot in any claim built on top of them.
**What is no longer claimed** is that those parameters reproduce burial: that was the old
framing, it required a measurement of this material, and no reachable capture supplies it
(see the struck routes below). Bounding them against published archaeometry is a weaker and
achievable thing, and it must be labelled as the weaker thing.

## Handed here by O8, 2026-09-07

`O8` closed with wear **ruled in as a cause** — demonstrated by intervention, not
correlation: abrade only the break surfaces of pots TORA already reassembles, hold the
faces and correct poses fixed, and sherds seated falls **0.843 → 0.645** (retired ruler; **0.597 → 0.560** corrected, jobs 30187601 / 30190268 — the intervention still shows on the erosion ladder and per pot, not in a pooled mean), with the
baseline `blue_pot` splitting open and the baseline `plate` collapsing in the renders.

**What O8 could not close, and hands here, is the bridge**: whether *our simulated wear*
resembles *the Juglet's real wear*. It cannot be shown with these scans — the Juglet's
break faces are sampled at **0.243% of object size** while the blunting acts at
**0.3–0.5%**, so every scale a comparison can reach lies above where the wear lives. The
dimensionless fine-over-coarse ratio was tried and withdrawn (worn Juglet 0.169, fresh
`blue_pot` 0.167, fresh range 0.167–0.386).

**~~This makes O7 a capture question before it is a parameter question.~~ Struck
2026-09-10, on the conservator's objection: there is no capture.** Two captures were
offered here and **both are now struck** — the second on 2026-09-09, the first on
2026-09-10 for the second's reason, one level down. They are kept below because knowing
which route does not exist is worth as much as one that does.

1. **~~A scan of real worn material finer than 0.1% of object size.~~ Struck 2026-09-10
   on the conservator's objection.** Two clauses, and both hold:

   - ***"It might still show nothing, because the wear smoothed them."*** A finer scan of a
     worn face yields **one number with no reference to read it against**. A smooth reading
     at 0.1 mm is equally consistent with *the ground removed the relief* and with *this
     instrument never recorded it* — and that is not hypothetical: **Gate A already
     observed exactly this** (job 29404479, 20 RePAIR fresco fragments — real eroded
     archaeological fracture carries no fracture-like roughness at any resolvable scale,
     and the two explanations could not be separated). Finer capture moves that ambiguity
     down a decade; it does not resolve it. To read the number you must know what the face
     looked like **before burial**, and the object does not carry that at any resolution.
     The only sources of a "before" are the paired captures of (2), which are struck for
     reasons that have nothing to do with resolution. **So capture 1 fails for capture 2's
     reason: the missing reference state, not scanner precision.**
   - ***"And TORA might see that level of detail anyway."*** Correct, and already measured
     — see the condition below, which is true of the join gap and **false** of the
     orientation channel. The premise that a finer scan is needed before the network could
     use the detail was wrong.

   The original text follows, retained as the record of what was asked for.

   **~~A scan of real worn material finer than 0.1% of object size.~~** In plain terms: how far
   apart the points sit on the scan. The Juglet's current meshes carry neighbouring points
   **0.29–0.48 mm** apart; the blunting the wear model simulates acts at roughly
   **0.2–0.3 mm** on this vessel. The effect is smaller than the spacing of the dots we
   would see it with, which is why three instruments came back "cannot tell". What is needed
   is **about 0.1 mm point spacing, three to five times finer than now.**

   Not exotic equipment. Close-range structured-light scanners already used for
   archaeological recording declare ~0.1 mm 3D resolution and 0.05 mm point spacing; for a
   single break face rather than a whole vessel, focus-variation or confocal profilometry
   reaches micrometres.

   **Condition, added 2026-09-09; HALF-RETRACTED 2026-09-10 — it is true of the join gap
   and false of the orientation channel, so it does not support the claim that TORA cannot
   see the wear. See the strike above and the section "TORA is not blind to the wear"
   below.** *A finer scan grounds `O7` without reaching `O8` on its own.* Every config here sets `num_points_to_sample: 5000` (`config/data/*.yaml`), which
   on a 65 mm juglet puts about **1.2 mm** — some 1.8% of object size — between the points
   the network is actually shown. The pipeline already discards the 0.3–0.5 mm the current
   scan holds. So a finer capture validates the wear model's *parameters*, which is this
   question; making it bear on whether wear breaks the reassembly needs the point budget
   raised as well. That second part is cheap, testable, and does not need lab time.

   *(Size convention: ticket 10 measures the assembled Juglet at 65 mm. The "100 mm juglet"
   this line used to quote came in from an earlier note on a different convention. The
   requirement is the **ratio** — 0.1% of object size — and 0.1 mm is the honest figure on
   this vessel.)*

2. **~~Fresh *and* worn scans of the same pot~~ — half of this was wrong. Struck
   2026-09-09 on the conservator's objection.** The original line offered two ways to get
   the paired comparison and treated them as equivalent. They are not.

   - **Struck: a modern replica — break it, scan it, abrade it, scan it again.** The
     objection, in the conservator's words: *we cannot simulate two thousand years
     underground, so this is as much a guess as the synthetic wear it would be validating.*
     That is correct, and it is worse than it first looks. Any lab abrasion is a **chosen**
     process with chosen parameters, so it calibrates one simulator against another and
     moves the guess rather than removing it. And burial does not only abrade — it changes
     the material: after two millennia of salts, leaching and freeze-thaw the fabric being
     worn is not the fabric a replica offers. The taphonomy literature makes this point
     directly for bone, where abrasion outcome depends heavily on the material's initial
     state — fresh, weathered or fossil — so a fresh substrate cannot stand in for a buried
     one even if the process were right.
   - **Also struck, 2026-09-09, same day it was written: one excavated sherd carrying both
     an ancient break face and a modern one.** This was offered as the surviving strong
     version — same fabric, temper, firing and vessel, burial on one face and none on the
     other — and it does not survive. **Two break faces are two fracture events.** How rough
     a break surface is depends on how it broke: impact against bending, energy, direction
     through the wall, whether it ran along a coil join or through temper. Holding the
     material fixed does not hold the fracture fixed, and the fracture is the thing being
     measured. The comparison confounds two thousand years of burial with "these two breaks
     were made differently".

   **So the paired control is struck in every form** — two pots, one pot two faces, replica
   abrasion. No fourth variant is proposed; the problem is not that the right pairing has
   not been found. See the restatement below.

**Rewritten 2026-09-10, now that both captures are struck.** This used to read "until one
exists" — as though the measurement were merely unfunded. It is not. **The *paired*
fidelity question is unanswerable from the object**: reading a measurement of one worn break
face as correct-or-not requires knowing what *that face* was like before burial, no capture
recovers that, and every route to a "before" is a second fracture event, a second chosen
abrasion process, or a different pot. So "the Juglet fails *because* its fractures are worn"
stays an inference from a simulator permanently, not pending equipment.

**Corrected the same day, on the conservator's objection.** The paragraph above first said
the fidelity question was unanswerable full stop, and that was over-broad. The objection:
*we know the definition of wear, we have real archaeological objects showing the wear, and
the simulator was built to reproduce what those objects show.* That is right, and it names a
**second, different question** that the struck captures do not touch:

| | needs a before-state | needs a pairing | status |
|---|---|---|---|
| **paired** — is the wear on *this* face right? | yes | yes | **struck, permanently** |
| **distributional** — do our worn surfaces land where real worn archaeological surfaces land, and away from fresh fracture? | **no** | **no** | **open, and testable now** |

The distributional question is answerable because the real-worn end of the axis has already
been measured here. Gate A put a roughness-scaling exponent of **1.71** on real eroded
archaeological fracture — 20 RePAIR Pompeii frescoes, one straight log-log line from 0.4 to
6.4 mm, no kink, low scatter across all 20 — against **0.4–0.8** for fresh fracture in
metals, ceramics and rocks. That statistic is dimensionless and size-independent, which is
exactly the property the fine/coarse ratio lacked when it put the worn Juglet at 0.169
*inside* the fresh range 0.167–0.386. A bad statistic is not an unanswerable question.

**What it can and cannot settle.** It can say whether our operator moves a real ceramic
break face off the fresh-fracture value and toward the value real worn fracture shows. It
cannot say any particular sherd's wear is right, and it inherits Gate A's own limit —
"the ground removed the texture" and "the scanner never recorded it" are not separable. So
the claim it supports is *our simulated wear matches real **scanned** worn fracture*, which
is the honest target for training data anyway, because the file is what a model sees.

**This still strengthens the 2026-09-09 restatement, for a narrower reason.** That
restatement moved the question to behavioural and bounded-range criteria on the grounds that
no *reachable* capture supplies the paired measurement. That ground holds: no capture
supplies it. What has changed is that the behavioural criteria are no longer the *only*
category of claim available — there is one physical claim this material can carry, and it is
the population one.

**Being tested:** `scripts/wear_fracture_spectrum.py`. Predictions are recorded in its
docstring before each run, including the one that refutes the test: **if our fresh e000 faces
already read ≥ 1.5, the fingerprint cannot separate fresh from worn on this material** and
this route closes too.

**Job 30352180 (2026-09-10) is void — do not quote it.** Its numbers were a measurement of
the pot wall, not the break face. It selected the break face as anything within 2% of object
size of another sherd and read Gate A's radii unchanged; Gate A's largest patch is 12.8 mm
across, which is 0.55× the thickness of a 23.5 mm RePAIR fresco plaque but **2.9×** a 4.5 mm
pot wall, so patches ran over the arris onto the vessel surface and a quadric absorbs
curvature but not a crease. At 6.4 mm, 64% of each patch faced away from its own probe point
and 100% of patches straddled an edge; the residual there was 1.1 mm on a 4.5 mm wall.
Fresh ceramic read 1.06–1.81. **Which of the three: the measurement was broken** — nothing
follows from it about the wear model. Diagnosed by `scripts/diagnose_wear_spectrum_band.py`
and rendered per point in `artifacts/wearspec_diag_smoke/residual_pink_bowl_e000.png`, where
the residual runs in a line along the broken edge rather than spreading over a face.

**What the correction cost the question, stated before the next run reads out.** Version 2
selects the break face by mating direction (near another sherd *and* facing it), stops the
radii at 1.60 mm because that is the largest patch a 4.5 mm wall holds, and gates every
radius on off-face fraction and patch shape. It is calibrated against surfaces of known
roughness first — a flat break reads 0.00000, white noise of σ = 0.02 mm reads 0.01594
against the analytic 0.01596, and known Hurst exponents 0.2/0.5/0.8 recover as
0.36/0.58/0.86. Two properties of that calibration bear on this question directly:

1. **The instrument cannot read above about 0.9 on any real fracture surface.** So version
   1's 1.06–1.81 was never fracture texture — an independent confirmation of the
   contamination that does not use the wall-thickness argument at all.
2. **A high reading does not distinguish erosion from lost detail.** A known-fresh H = 0.5
   surface blurred by only 0.20 mm reads 1.445 while its actual roughness falls 3%. This
   statistic measures the finest wavelength *present*, so "worn away by burial" and "never
   recorded by the capture" give the same number. That is a limit on the reference as much
   as on us, and it is the sharpest form yet of the scanner-vs-ground caveat above.

**~~What rescues the comparison is the shape of the log-log line, not its slope.~~ STRUCK
2026-09-10 — it does not.** The claim was that a resolution artefact's local slope collapses
as patches grow while genuine erosion's does not, so the *decline* separates them: a
known-fresh surface smoothed until it read slope 1.60 fell 2.43 → 1.50 → 0.91 over
0.8–6.4 mm, a decline of +1.52, whereas RePAIR's slope *rises* over 0.4–1.6 mm
(decline −0.56). That contrast is real. It is not diagnostic of erosion, because two other
things reproduce −0.56 on a surface built to be **fresh**.

Both were measured on a pot whose every point is labelled by construction — thin curved
wall, 4.5 mm, 0.2 mm spacing, 0.10 mm mating gap, roughness at a known Hurst H — because the
dataset carries no break-face label and all three routes to one are closed (`shared_faces` is
−1 for every triangle; `full_mesh` contains the break faces rather than predating them; the
cut duplicated no vertices). `scripts/selftest_wear_spectrum_pot.py`.

**1. A fresh break that merely MEANDERS lands on RePAIR's decline.** Add a 3 mm waviness at
~15 mm wavelength — less than any real pot break — and hold the roughness fixed:

| true H | flat cut | | wavy cut | |
|---|---|---|---|---|
| | slope | decline | slope | decline |
| 0.2 | 0.573 | **+0.61** | 0.546 | **−0.25** |
| 0.5 | 0.763 | **+0.52** | 0.906 | **−1.00** |
| 0.8 | 0.994 | **+0.45** | 1.618 | **−1.76** |

The decline is **+0.45 to +0.61 on a flat cut whatever the roughness, and −0.25 to −1.76 on a
wavy one**. It is a measure of the break's shape, not its wear, and RePAIR's −0.56 sits
between the H = 0.2 and H = 0.5 fresh-wavy rows. The slope is no better: the meander moves it
by −0.03 at H = 0.2 and **+0.62** at H = 0.8, so its effect is neither a fixed size nor a
fixed sign and cannot be subtracted off.

**2. A contaminated selection lands there too, on a FLAT fresh cut.** The near-only selection
of job 30352180 is 62% pure on this pot, and reads **slope 1.217–1.414, decline −1.35 to
−1.68** on a cut built flat and fresh at H = 0.2–0.8. Its slope barely tracks H at all
(1.217 / 1.354 / 1.414 for H = 0.2 / 0.5 / 0.8) — the signature of a statistic reading the
vessel wall rather than the break. That reproduces job 30352180's 1.06–1.81 from ground truth
and closes it independently of the wall-thickness argument: **void, and now demonstrably so.**

**What survives.** The v2 selection is exact — **100% purity and 100% recall** on every row,
its slope matching the labelled truth to within 0.006 — and the candidate tightening (mating
gap within 3 point spacings *and* an antiparallel partner normal) is equally exact at 99.5–
99.8% recall. The instrument reads high but monotonically on a flat cut, roughly
0.7·H + 0.43, so it can **rank** roughness. What it cannot do is separate roughness from break
shape, and the two confound each other at the same magnitude.

**Consequence for this question: Gate A cannot ground the wear model, on either axis.** Our
fresh e000 faces read 0.67–1.78 (job 30356470, v2 selection), RePAIR's real eroded fresco
reads 1.71, and a fresh synthetic break at H = 0.8 with a modest meander reads 1.62. Those are
the same number. The distributional comparison — *do our worn surfaces land where real worn
archaeological surfaces land* — is not refuted as a question; it is that **this statistic
cannot answer it**, which is category 2, a broken ruler, and not a verdict on the wear model.
This does not touch O8's finding that wear *causes* reassembly failure, which came from
intervention.

**A confound recorded earlier and now subsumed:** a reconstruction with a smoothness prior
removes roughness at all scales and would give a high slope with a small decline. It no longer
needs separating, because the decline axis is spent either way.

**A second confound, measured after job 30356470 completed, which withdraws the direction
reading.** The exponent *falls* up the wear ladder on 7 of 8 pots, opposite to what burial
erosion should do. That is not a wear-model result. The erosion meshes are **byte-identical at
every rung** (`blue_pot` 1,043,149 v / 2,086,278 f at e000 and at e100 — the operator displaces
vertices and changes no topology), but the selection keeps steadily more of the break face as
wear rises (`blue_pot` 18.2% → 25.7% of near), so the point spacing *within the measured set*
falls **20–46% on every pot** (0.106 → 0.084, 0.168 → 0.090, 0.198 → 0.121 mm …). This
statistic tracks the finest wavelength present in the sampled set, and that sampling changes in
the same direction as the wear on every pot. **The wear column cannot be read until every rung
is subsampled to a common spacing** — cheap, and the next job. The hypothesis that our erosion
operator reduces the break's meander is withdrawn with it: decline *falls* up the ladder, and
on labelled geometry a falling decline is what **added** waviness produces.

**The one comparison that still reads as physical**, from the log-log plot rather than the
exponent: RePAIR's curve starts **lowest of everything** at 0.40 mm (~0.0018 mm of texture) and
converges with ours by 6.40 mm (~0.22 mm). Its steep exponent is *missing fine relief*, which
is what erosion physically does — not extra coarse roughness. Ours start higher at the fine end
(0.002–0.009 mm). Whether that survives the sampling correction is untested.

**What would still discriminate**, for whoever picks this up: a statistic computed *after* the
break's low-frequency shape is removed — not by a quadric over a 1.6 mm patch, which cannot
see a 15 mm meander, but by subtracting a fit over the whole face; and absolute fine-scale
texture at a fixed point spacing, which is the axis the plot above suggests is meaningful.
Untested. Full read-out: `docs/notes/WEAR_SPECTRUM_GATE_A_30356470.md`.

## TORA is not blind to the wear — the orientation channel, measured

Recorded here 2026-09-10 because it was buried in `.scratch/juglet-cause/issues/05` and its
absence let the "TORA cannot see it" claim stand unqualified above.

The encoder is fed **six** numbers per point, not three — position *and* the normal of the
triangle the point landed on (`tora/modeling/encoder/point_cloud_encoder.py:113`). The
normal is a **sub-spacing cue**: it reports surface orientation at triangle scale, some
**0.07–0.20%** of object size, roughly thirty times finer than the spacing between the
sampled points. Break-face roughness *as the network actually receives it* falls
monotonically under the simulated wear, on the six real objects:

| erosion | e000 | e025 | e050 | e075 | e100 |
|---|---|---|---|---|---|
| roughness | 29.7° | 27.2° | 26.6° | 24.3° | **22.2°** |

So "TORA's sampling is too coarse to resolve the wear" is **true of the join gap and false
of the orientation channel**. There is a signal, the network is fed it, and the intervention
moves it. `scripts/measure_faces_as_network_sees.py`,
`docs/notes/LORA_VESSELS_29623885_RESULT.md`.

## Reinforced by O8, 2026-09-09 — a third instrument, the same wall

`O8` has now run everything reachable from the scans that exist, and closes on the
statement that the Juglet's failure **cannot be attributed to its wear with this data**.
That makes capture 1 or capture 2 above not a refinement but the only remaining route, so
it is worth recording what the third instrument added.

`.scratch/juglet-cause/issues/10` measured the Juglet's **joins** rather than its
roughness: in the conservator's hand-built reassembly, per vertex of every fragment, how
far is the break surface from the piece it should be touching? The joins close to
**0.21–0.28 mm** typically and **0.44–0.52 mm** at the worst tenth, while neighbouring
vertices on those same meshes sit **0.29–0.48 mm** apart (0.445–0.733% of a 65 mm vessel).
The gap and the measurement's own noise floor are the same size.

*(That spacing is nearest-neighbour distance on the source fragment meshes, a different
sampling from the 0.243% quoted above for the point clouds the network is fed. The two
figures describe different objects and should not be quoted interchangeably; both say the
same thing about the scale available.)*

**The test is one-sided, and it failed on the informative side.** A join standing open
would have been direct evidence of material loss — a hand fitter cannot close a join where
the material is gone — and would have made capture 1 strongly indicated on evidence rather
than on argument. A join that closes establishes nothing: it is equally consistent with no
loss, with loss too fine for this scan, and with loss taken evenly off both faces, which
simply lets the fitter seat the pieces deeper. The vessel is also **incomplete**, so one
stretch of break edge has no mate and contributes nothing either way.

Three independent quantities, three instruments, one wall: Gate A found no fracture-like
roughness at any resolvable scale; ticket 05 found the wear unmeasurable at 0.1% of object
size; this finds the joins unmeasurable at 0.3–0.5 mm. **A capture finer than roughly
0.1 mm on this vessel is now the binding constraint on the whole wear-grounding claim**,
and no amount of compute substitutes for it.

## The erosion operator's own limits, measured 2026-09-09 (ticket 11, job 30293058)

This question's restated, accepted criterion is **behavioural**: the wear model earns its
place if abrading pots we control changes reassembly behaviour in a way that transfers.
Ticket 11 ran that on all eight Fractura ceramics and the behavioural answer is yes — but
it also put two hard numbers on what the operator can and cannot do, and both belong here
rather than in `O8`, because they bound any claim made about the wear model itself.

**1. The operator does not reach the Juglet's condition on most pots.** Achieved
`relief_p90` at maximum strength, against the Juglet's measured **0.171** (lower = more
worn): `blue_pot` 0.118 and `pink_bowl` 0.134 pass it; `narrow_bottle4` stops at **0.244**
and `narrow_bottle1` at 0.245, nowhere near. So on half the pots that can carry a control,
the ladder **plateaus above the target and cannot be interpreted** — the exact failure that
made GARF's Exp 7 uninterpretable. A pot surviving "full wear" therefore does not mean it
survives Juglet-level wear, and must not be reported as if it did.

**2. `relief_p90` inverts on a smooth-faced piece, so the calibration cannot be trusted
unchecked.** On `narrow_bottle2` achieved wear reads 0.228 → 0.217 → 0.180 → **0.272** →
**0.369**: rising under increasing abrasion. Rendered per sample, the cause is visible and
is not mesh damage — displacement is clean and monotone on every pot and inverted triangles
stay under 0.1%. The break face interior is *already* smooth, so the mollifier has no relief
to remove; what it does instead is round the rim, and the boundary where its feathered band
meets untouched surface is a new sharp crease. A 90th percentile is dominated by exactly
that minority. Restricting the measure to the fracture band makes it worse (0.396 → 0.629),
which confirms the band boundary as the source.

**3. A mechanism behind both, found by reading the operator.** `erode_fracture_band`
mollifies each band vertex onto at most `knn=48` of `n_self_samples=20000` surface samples.
Past the radius that holds 48 samples the kernel **saturates**: further strength no longer
widens the smoothing, it only raises the blend weight. Measured, the requested radius
exceeds that radius from e075 on **for every pot in the corpus**. Raising `knn` and
`n_self_samples` with strength is the obvious fix and has not been tried.

**What this does to the criterion.** The behavioural evidence strengthened — the operator
demonstrably drives correctly-assembled real pots into failure, and at the Juglet's own
roughness the failure it produces is **scattering**, which is the Juglet's shape. But the
bounded claim this question exists to protect must now also say: *the operator is validated
over the range it actually reaches, which on this corpus is roughly `relief_p90` 0.12–0.24,
and its achieved-wear calibration is unreliable on pieces whose break faces are already
smooth.* That is a concession worth making in advance, for the same reason as the rest of
this question.

Detail: `docs/notes/EROSION_LADDER_CERAMICS.md`. Renders:
`artifacts/wearsig_ceramics/renders/narrow_bottle{2,3,4}_band.png` (the measured quantity
itself, per sample) and `.../ladder_sherd_placement.png`. Ticket
`.scratch/juglet-cause/issues/11-erosion-ladder-on-pots-tora-rebuilds.md`.

## Wear v3 tested the behavioural criterion directly, and failed it (job 29880370, read out 2026-09-10)

This is the first intervention aimed squarely at the **BEHAVIOURAL** box below, and it is
worth recording as a negative because the box says "shown to earn its place" and this one
did not. Wear v3 attacked the shape-variety half of the gap — 203 synthetic vessel shapes
instead of our 8 real ceramic pots — and delivered it as a **switchable LoRA adapter**
(2.69% of the weights) rather than a full fine-tune, precisely so that the do-no-harm arm
would be guaranteed by construction rather than bought with replay data.

**Read per object, never pooled.** On the adapter's own held-out vessel shapes (107 objects,
3 draws each), switching the adapter **on** seats fewer sherds than the untouched model on
**49** objects against **30** better (sign test **p = 0.042**); against the same trained file
with the switch flipped off it is **20 better / 53 worse (p < 0.001)**. The off-arm against
the untouched model is 39/30/38, p = 0.34 — the control behaves. So the adapter weights
themselves carry the loss. The validation curve agrees from the other end: seating peaks at
**epoch 0 (0.843)** — the selected checkpoint — and falls to 0.727-0.76 for the remaining
nineteen epochs.

On the erosion sweep, the gain it was bought for, there is **nothing**: 3 better / 7 worse /
5 unchanged over 15 ceramic ladder points, p = 0.34, on far too few pots to have detected a
small effect. **Half that sweep is not pottery** — it is the six-object `real_heldout_norm`
file, three of whose objects are bones. Same defect ticket 11 found, recurring because the
same source file was used.

**Which of the three: the method genuinely did not help.** The ruler was the corrected
unit-box one (every arm carries `part_accuracy_absolute`), the comparison is paired against
the untouched model, and the ground truth on the synthetic and Fractura material is sound.

**Three things this leaves behind that do bear on the criterion.**

1. **"Reversible" is only three-quarters true.** `train_head=true` left the pose head
   trainable and 5 of its tensors moved (largest 1.943e-03). The switch does not cover them,
   so "adapter off" is not the untouched baseline — and on `blue_pot` the off-arm holds
   5.0/5 seated while its average turn goes from **6 deg to 53 deg**. A seating count alone
   would have called that "no change". Set `train_head=false` next time.
2. **The seating count is a *relabelled* count.** `compute_part_acc` runs a Hungarian
   assignment, so a sherd standing in another sherd's place is credited. On the Juglet, the
   only arm whose clouds were saved, own-place seating is **3.4 / 2.6 / 1.2 of 9** against
   the reported 5.0 / 3.8 / 4.0 — **70% of the adapter arm's credit is relabelling**, and
   one of the 1.2 is the free anchor. Every seating figure in this question's evidence base
   should be read as an upper bound until an arm is audited against identity.
3. **Clouds must be saved on every arm.** They were not here, so the vessel, sweep and fresh
   numbers cannot be rendered or identity-checked at all.

Rendered before reporting: `artifacts/lorav3_29880370/juglet_arms_per_sherd.png` — the
measured quantity itself, per sherd, all five draws, with the median draw drawn above.
**Nothing is a juglet on any arm**, and all three sit above the ~50 deg collapse threshold.

Detail: `docs/notes/LORAV3_29880370_RESULT.md`; the change record against wear v2 is
`docs/notes/WEAR_V2_TO_V3.md`.

## Confirmed on real pottery, with a control arm (job 30337242, 2026-09-10)

The v3 read-out above was on synthetic vessels and one Juglet. This is the same
adapter on **eight real Fractura pots at five levels of controlled abrasion** — 40
objects, 20 draws, three arms — which is the material the BEHAVIOURAL box is actually
about.

**It failed again, and this time the instrument was known-good first.** Six of the eight
pots reassemble essentially completely unworn (`blue_pot` 5/5, `narrow_bottle4` 4/4,
`narrow_bottle2` 3/3, `pink_bowl` 3/3, `galli_pot` 8/10, `plate` 4/6), so a loss here is
a loss on pots the model demonstrably can do.

Paired per pot per rung, on fragments earned (no pooled mean):

| comparison | adapter better | baseline better | level | p |
|---|---|---|---|---|
| `adapter_on` vs `baseline` | 4 | **14** | 22 | **0.031** |
| `adapter_off` vs `baseline` | 5 | 11 | 24 | 0.210 |
| `adapter_on` vs `adapter_off` | 6 | 13 | 21 | 0.167 |

**The `train_head=true` contamination flagged above is now measured, not just noted.**
`adapter_off` is the same weights with the adapters switched off and should reproduce the
baseline exactly. It loses 11 to 5. The five moved pose-head tensors do not switch off,
so the do-no-harm arm that the LoRA design was *chosen* to guarantee by construction was
never guaranteed at all. Sharpest case: `pink_bowl` at full abrasion holds 3 of 3 on the
untouched baseline (worst fragment 3.6% of bowl width) and collapses to 1 of 3 on
`adapter_off` (21.1%) — with the adapter disabled.

That splits the headline honestly: `adapter_on` vs `adapter_off` (6–13, p = 0.167)
isolates the adapter and is a null, not a loss; the significant 4–14 against baseline is
the adapter **plus** the damaged head.

Rendered before reporting: `artifacts/ceramarm_30337242/ladder_blue_pot_baseline.png`
and `ladder_pink_bowl_{baseline,adapter_off}.png` — the median draw of twenty above the
per-sherd distances, so picture and figure are the same attempt.

**Any future adapter run sets `train_head=false`, or its control arm means nothing.**

Detail: `docs/notes/CERAMARM_30337242_RESULT.md`.

## Restatement — **ACCEPTED by the conservator, 2026-09-09.** Criteria are now
behavioural and bounded-range; the boxes below were rewritten to match.

Three capture routes have now been written into this question and all three are struck or
conditional. That is a pattern, and the honest reading of it is that **the problem is the
question, not the routes.**

**The diagnosis.** `O7` asks a *metrology* question — is the wear model grounded in real
material, is it "archaeologically accurate" — about something that is not a measuring
instrument. The wear model is a **training augmentation**. Its job is to produce training
data that makes the network robust on worn pottery, not to reproduce burial. Augmentations
are validated by whether they help, not by whether they are physically faithful; nobody
validates image-blur augmentation against real lens optics. The phrase "archaeologically
accurate" is what generates the impossible requirement, and every capture route here has
been an attempt to satisfy it.

**Conservator's objection, 2026-09-09, which is what forced this.** You cannot simulate two
thousand years underground; you cannot break a second pot the same way; and no two pots are
the same. Each strikes a different route, and together they close the paired-control idea
entirely rather than sending it back for a better design.

**What survives, ranked by cost:**

- **Dead — the paired control, in every form.** Struck above. Not to be re-proposed in a
  fourth variant.
- **Free, and already partly done — behavioural validation.** Does wear augmentation
  improve reassembly of *real* worn material, and does it beat cruder augmentation? The
  strongest evidence we hold is already of this kind and needed no capture: **the repair
  transfers across simulators** — wear_v2 trained on `wear_ops.apply_wear`, tested against
  GARF's `erode_fracture_band` on different source objects (wear_v1 does not earn this, being
  trained on the test operator). Lean on it carefully: on the corrected unit-box ruler that
  effect survives on the erosion ladder and per pot, **not** as a pooled six-pot mean. What
  is missing is a comparison against simpler augmentation, which is GPU we already use.
- **Cheap, no capture — parameter ranges from published archaeometry.** The second "Done
  when" box below already asks for this. It bounds the parameters without measuring this
  material. It is grounding-by-literature, not grounding-by-measurement, and is honest only
  if labelled as such.
- **Conditional on capture 1 — endpoint comparison.** Not "does our process match burial"
  but "does our *output* resemble real worn fracture, statistically". Needs no control and
  no pairing: compare simulated-worn against real-worn directly. One attempt has already
  failed on resolution (fine-over-coarse ratio: worn Juglet 0.169 against fresh `blue_pot`
  0.167, indistinguishable). **This is the only thing a finer capture would still buy.**

**What it does to the thesis claim.** It gets stronger, not weaker. "Our wear model is
archaeologically accurate" is indefensible and is exactly where an examiner would press.
What is defensible:

> The wear model is a training augmentation with parameters bounded by published
> archaeometric ranges. It is validated behaviourally — its benefit transfers to an erosion
> operator it was not trained on. We do not claim it reproduces burial processes, and we
> state why that cannot be measured with available capture: three independent instruments
> show the wear on real material lies below the resolution of the scans that exist.

A stated and argued limitation is a better position than a claim that can be knocked over.

**Accepted.** The two "Done when" boxes that demanded parameters *driven from measured
ranges* and a *mapping from measured property to wear parameter* were the impossible pair
and have been replaced by a behavioural criterion and a bounded-range one. Note what did
**not** get easier: the behavioural box carries a control the old framing never had — a
comparison against cruder augmentation — because "wear augmentation helps" is worth nothing
until it is shown that *wear-shaped* augmentation is what helps, rather than augmentation in
general. The bar moved sideways, not down.

## Done when

- [x] **One of the two captures is recorded as unreachable, with a reason (2026-09-09).**
      Both are. Capture 1 is reachable in principle but buys only the endpoint comparison,
      and the pipeline discards the scale it would deliver; capture 2 is struck in every
      form. Three instruments (Gate A, ticket 05, ticket 10) agree the existing scans cannot
      reach the question
- [ ] **BEHAVIOURAL — the augmentation is shown to earn its place.** Its benefit holds on
      an erosion operator it was **not** trained on (wear_v2 already has this; wear_v1 does
      not, being trained on the test operator), **and** beats at least one cruder
      augmentation baseline, so the gain is attributable to *wear-shaped* augmentation
      rather than to augmentation in general. Reported **per object and up the erosion
      ladder, never as a pooled mean** — a pooled six-pot mean already scored a model that
      cut the ladder drop by two thirds as indistinguishable from the untouched baseline
      (`intent/O2`). **Attempted twice and not met (2026-09-10).** Job 29880370: the wear
      v3 shape-variety adapter lost on its own held-out vessels (49 worse / 30 better,
      p = 0.042) and did nothing on the erosion sweep. Job 30337242, on **real** pottery
      with a control arm — eight Fractura pots at five abrasion levels, six of which the
      baseline assembles unworn — it lost again, 14 worse to 4 better, p = 0.031. The
      cruder-augmentation comparison this box also asks for has still never been run, so
      the box is unmet on both halves. Still open
- [ ] **BOUNDED-RANGE — the parameters are defensible without being measured.** Fabric,
      temper and wall-thickness distributions pulled from the archaeometric literature
      (Khashuri Natsargora, Tsaghkasar, the Kars corpus), wear parameters shown to lie
      inside the ranges those imply, and the mapping from published property to parameter
      written down so a reader can disagree with it specifically
- [ ] **The claim as written down is the bounded one.** Wherever this work is described,
      it says the wear model is a training augmentation validated behaviourally with
      parameters bounded by published ranges — **not** that it reproduces burial — and
      states why the stronger claim is not measurable here

## What this buys

A claim that survives being pressed on. "Archaeologically accurate" could not be defended
and was the obvious place for a conservation examiner to push; a bounded, behaviourally
validated claim with its limitation stated in advance is a stronger position precisely
because it concedes the right thing before being asked.

## Related

Real eroded fracture carries no fracture-like roughness at any scale current scans
resolve ([GATE_A_RESULT.md](../docs/notes/GATE_A_RESULT.md)) — and whether the ground
removed it or the scanner never recorded it **cannot be separated** with 0.4 mm data.
Any wear model grounded here inherits that limit and should say so.

The Juglet's joins say the same thing from a different direction
([`.scratch/juglet-cause/issues/10`](../.scratch/juglet-cause/issues/10-does-the-juglet-seam-close.md),
render: `artifacts/jugseam/juglet_gt_seam_gap.png`), and the calibration that makes that
number readable is the `narrow_bottle3` seam test
([`.scratch/perception-or-placement/issues/01`](../.scratch/perception-or-placement/issues/01-does-the-break-edge-disambiguate.md)),
where a fresh, crisp break reads 0.11–0.23% of object size against a mismatched one at
0.6–5.7%.

## Source

`../../CSC/docs/notes/PLAN.md` §R5, `WEAR_V3_PLAN.md`, `WEAR_TEST_RESULTS.md`.
