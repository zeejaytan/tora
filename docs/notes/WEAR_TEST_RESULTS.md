# What the wear tests found

Record of the wear-simulation work through 2026-08-18: the model rebuild, what
could and could not be validated, the retrain, and what the pictures showed that
the numbers did not.

> **⚠️ CORRECTION (2026-09-05) — the rotation numbers in §4 and the threshold
> argument in §5 were computed on a broken ruler; §1, §2 and §6 are untouched.**
>
> **Which of the three: the measurement was broken.** Two faults, both in the
> evaluator, both found on 2026-09-05 and both fixed:
>
> 1. Stored `rotation_error` skips the anchor fragment when summing but divides by
>    the **total** fragment count, so every figure carries a free zero — ×1.500 at
>    three fragments, ×1.125 at nine.
> 2. `within10` was thresholded on that same diluted mean, so it passed objects it
>    should have failed, in the same direction.
>
> **And `within10` is not what §4 said it was.** It is a **per-object 0 or 1 on
> the whole pot's average turn**, not "the fraction of fragments within ten
> degrees" — that sentence is corrected in place below, because a wrong definition
> is not a superseded result and would mislead anyone reading the table under it.
>
> **What survives:** everything in §1 (the wear model itself — pure mesh geometry,
> no evaluator), §2, §3, and **all of §6, the pictures**. The wear training's win
> on heavily worn pottery is a visual finding and is unaffected. What moves is the
> size of every angle in §4 and the "about 40°" threshold in §5, which was
> calibrated against diluted numbers and should read **roughly 50°**.
>
> Recomputed from the stored result files through `scripts/readout.py` (gated by
> `scripts/check_readout.py`); nothing re-run. Ticket
> `.scratch/eval-readout/issues/03`.

**The short version.** The rebuilt wear model does what the conservator
described — blunts the teeth, leaves the curve, opens the joins — verified on
four objects. Training on it **stops heavily worn pottery from collapsing**, and
that gain is visible, not just numerical. Whether the simulated wear *resembles*
real archaeological wear is still unknown and cannot be settled with the scans
we have. The Juglet is still not reassembled by anything.

---

## 1. The model, and why it was rebuilt

The previous micro-wear term was Laplacian mollification. Measured on `blue_pot`
before and after — same mesh, so no density confound — it did the opposite of
wear at both ends: it **added** fine structure (0.073 → 0.090) and **removed 14%
of the curve** (1.723 → 1.483). Its kernel was 5% of the object, above the curve
scale, so it was filtering away the feature that has to survive.

`blunt_asperities` replaced it. One-sided peak truncation: the part of a
break-face point standing proud of the surface's own local envelope is removed,
nothing else. Material can only leave, and structure coarser than the cutoff is
invisible to the operation, so the curve is safe by construction rather than by
choosing a gentle dose.

**Validated on four objects spanning the thickness spectrum** — `blue_pot` and
`plate` (thin-walled ceramic), `coxae` and `vert9` (solid bone):

| | teeth 0.4% | teeth 0.8% | curve 3.2% | curve 6.4% | joins |
|---|---|---|---|---|---|
| blue_pot | −9.4% | −2.9% | +2.0% | +1.0% | open |
| coxae | −6.1% | −2.9% | +0.2% | −0.5% | open |
| vert9 | −8.2% | −5.7% | +0.1% | +0.5% | open |
| plate | −6.0% | −0.3% | +0.7% | +0.8% | open |
| **old model** | *rose 33–57%* | | **−8 to −28%** | | |

**Zero vertices gained material** on any object. Under the old model that was
where the inverted-normal bug lived.

### Recession retired

Measured dose response, not judgement. Recession alone, curve at the 6.4% scale
against the join opening it buys:

| dose | blue_pot curve | plate curve | join opening |
|---|---|---|---|
| 0.02% | −1.0% | −2.0% | +1.1% |
| 0.05% | −2.5% | −5.3% | +2.9% |
| 0.10% | −5.3% | −11.6% | +5.8% |
| 0.20% | −11.7% | −26.3% | +12.4% |

Cost is linear in dose, so a safe setting exists — and is not worth having.
**Blunting alone opens joins by more than any safe recession dose** (+4.4% on
blue_pot, +6.4% on plate) while leaving the curve intact and blunting the teeth,
neither of which recession does. Recession also *adds* fine relief, the opposite
of abrasion. Severity now rides on the blunting cutoff alone.

### Chips use the dish, not boolean subtraction

Two independent reasons. GARF trains on `shared_faces` labels naming faces of
the original mesh, and a boolean rebuilds the mesh, so those labels stop
referring to anything. And a boolean changes the vertex set, so before and after
cannot be compared vertex for vertex — which forced the validator into
distance-based selection and made chipped runs falsely report joins *closing*.

### Known and unfixed

- **Under-wear at break-face edges.** Within about one cutoff of the edge of a
  break face only **7–9%** of available relief is removed, against **93–99%**
  well inside. Roughly a quarter of break-face points sit in that zone, so every
  fracture in the training set carries a slightly under-worn rim.
- **Band tolerance on thin walls.** The 2%-of-object contact band may be
  counting intact vessel surface as break face: the plate's band is **57% of the
  whole fragment** against blue_pot's 40%, and a section through it shows long
  stretches with no fracture relief at all.

---

## 2. What could NOT be validated, and why

**Whether our simulated wear resembles real archaeological wear.** Not "it
does", not "it doesn't" — the question is unanswerable with these scans.

The Juglet's break faces are sampled at **0.243% of object size**, so nothing
finer than about 0.5% is recorded. Our blunting acts at **0.3–0.5%**. Every
scale a comparison can reach lies *above* where the wear acts. It is a property
of the scan and no wear setting changes it.

A dimensionless fine-over-coarse ratio was tried to get around it and had to be
withdrawn: measured on three fresh pots it spans **0.167 (blue_pot), 0.229
(galli_pot), 0.386 (plate)**, and the real worn Juglet sits at **0.169** —
inside the fresh range. Between-pot variation swamps the effect of wear.

**What would settle it:** a scan of real worn material finer than 0.1% of object
size, or fresh *and* worn scans of the same pot so the between-pot variation
cancels. Neither exists here.

---

## 3. The training set

288 variants across 24 objects, twelve each: seven at full resolution and
**five blurred to 0.25% of object size** — the Juglet's own measured scan
resolution — because simulated fresh breaks carry fracture detail at 0.068% that
no real scan delivers, and that domain gap exists before any wear is applied.

Smoothness spans 0.1245–0.8960; the Juglet sits at 0.171 and **22 of 288
variants reach it or better**. Proportionally fewer than the old set (27 of 168),
because blunting is bounded: at full strength a face lands on its own envelope
and stops.

---

## 4. The retrain (job 29308186)

Three models on three test sets. `seated` is part accuracy, `turned` is mean
rotation error, and `within10` is **a per-object 0 or 1: did the whole object's
average turn come in under ten degrees?** *(That last definition is corrected
2026-09-05. It previously read "the fraction of fragments within ten degrees",
which is wrong — `_recall_at_thresholds` thresholds the per-object mean. On a
nine-sherd pot averaging 50°, a flat 0.000 is what the metric must produce
whatever the model does, so the zeros in the Juglet rows below are not a result.)*

| set | model | seated | turned | within10 |
|---|---|---|---|---|
| **fresh held-out** | baseline | 0.881 | 34.4° | 0.056 |
| | wear_v1 | 0.794 | 33.7° | 0.000 |
| | **wear_v2** | **0.904** | **32.4°** | 0.000 |
| **worn sweep** | baseline | 0.741 | 36.7° | 0.100 |
| | wear_v1 | 0.860 | 34.0° | 0.056 |
| | **wear_v2** | **0.867** | 35.1° | 0.067 |
| **the Juglet** | baseline | 0.667 | 51.5° | 0.000 |
| | wear_v1 | 0.800 | 49.2° | 0.000 |
| | wear_v2 | 0.800 | **52.9°** | 0.000 |

**Corrected 2026-09-05**, same result files through `scripts/readout.py`. `seated`
is now the fraction of the **loose** fragments seated (free anchor removed, so it
starts at zero rather than at 1/n), `turned` the mean turn on those fragments, and
`pot<10°` the fraction of objects whose corrected average came in under ten
degrees:

| set | model | seated (loose) | turned | pot<10° | stored size |
|---|---|---|---|---|---|
| **fresh held-out** | baseline | 0.843 | 46.4° | 0.056 | 0.319–0.383 ⚠️ |
| | wear_v1 | 0.705 | 46.0° | 0.000 | 0.319–0.383 ⚠️ |
| | **wear_v2** | **0.864** | **44.3°** | 0.000 | 0.320–0.383 ⚠️ |
| **worn sweep** | baseline | 0.645 | 49.3° | 0.067 | 0.319–0.321 ⚠️ |
| | wear_v1 | 0.807 | **46.2°** | 0.022 | 0.319–0.321 ⚠️ |
| | **wear_v2** | **0.815** | 47.7° | 0.022 | 0.320–0.321 ⚠️ |
| **the Juglet** | baseline | 0.625 | 57.9° | 0.000 | 0.5114 |
| | wear_v1 | **0.775** | **55.3°** | 0.000 | 0.5114 |
| | wear_v2 | **0.775** | 59.6° | 0.000 | 0.5114 |

**Every ranking in the table is unchanged** — wear_v2 still best on the fresh
held-out set, wear_v1 and wear_v2 still well ahead of baseline on the worn sweep,
wear training still not fixing the Juglet. That is not luck: each test set holds
the same objects for all three models, so the correction applies the same factor
to every row of a block. **What changes is the physical size of the error.** The
worn sweep is not "about 35° out" but **about 47° — half a right angle**, and the
Juglet's loose sherds are **55–60°** from correct, not 49–53°. Read against the
threshold argument in §5, that matters: several of these sit at or above the line
where the assembly has genuinely collapsed rather than below it.

⚠️ **The fresh and sweep sets were scored at a stored object size of 0.319–0.383,
at or below the trained floor of 0.375** — a handicap at source, separate from the
reading error, and untested. The Juglet rows at 0.5114 are inside the band.

---

## 5. THE METRICS MISLEAD, IN BOTH DIRECTIONS

This is the most transferable finding here and it cost three wrong reports to
reach.

**Part accuracy over-credits.** It passes a fragment on chamfer distance, which
stays small for a sherd sitting roughly in the right region however it is
turned. On the Juglet it read **0.80** — eight fragments in ten "correctly
placed" — for an assembly that the render shows is scattered and never closes
into a vessel. ~~The gap between "counted as placed" and "actually within ten
degrees" is **0.64 to 0.90 across all 32 object-conditions**.~~

> **⚠️ Struck 2026-09-05.** That gap was computed by subtracting `within10` from
> part accuracy as though both were fractions of fragments. They are not the same
> kind of number: part accuracy is a fraction of fragments, `within10` is a
> per-object 0 or 1. Subtracting them is not a meaningful quantity, and the
> "0.64 to 0.90" range is mostly just part accuracy itself with a zero taken off
> it. **The conclusion of the paragraph is unaffected** — part accuracy really
> does pass sherds the render shows to be scattered, and the Juglet reading 0.80
> (corrected: **0.775** — 5 to 7 of the 8 loose sherds across five draws, averaging 6.2) beside a 55–60° mean turn is
> the demonstration. Only the arithmetic in the last sentence is withdrawn.
> Corrected per-object figures are in the §4 table.

**Rotation error over-penalises.** A bone shaft rotated about its own axis, or a
smooth shell sherd rotated within its own surface, gives a different rotation
matrix and the *same assembly*. `limb3` at 30° and `blue_pot` at 19° both look
correctly assembled. "Within 10°" read 0.000 almost everywhere for this reason
and is too strict to be useful on this material.

**The practical threshold is about 40°, not 10°.** Where rotation error reads
40–70° the assembly has genuinely collapsed (baseline `plate` at heavy wear
69.8°, `blue_pot` at heaviest 40.4°). Where it reads 10–35° the assembly looks
correct and the residual is symmetry.

> **⚠️ Recalibrated 2026-09-05 — the threshold is about 50°, not 40°.** The four
> anchor points above were all diluted, each by its own fragment count:
>
> | anchor point | as printed | corrected | fragments |
> |---|---|---|---|
> | `limb3`, looks assembled | 30° | **45°** | 3 (×1.500) |
> | `blue_pot`, looks assembled | 19° | **23.8°** | 5 (×1.250) |
> | `blue_pot` at heaviest, collapsed | 40.4° | **50.5°** | 5 (×1.250) |
> | `plate` at heavy wear, collapsed | 69.8° | **83.8°** | 6 (×1.200) |
>
> The looks-assembled band now tops out at **45°** and the collapsed band starts
> at **50.5°**, so the practical line sits at roughly **48–50°**. The *finding* is
> unchanged and its basis is still the pictures in §6, not this arithmetic: a
> rotation figure well past ten degrees can still be a correct assembly on this
> material, because a bone shaft turned about its own axis and a shell sherd
> turned within its own surface both score as wrong and look right. But a reader
> applying "40°" to a corrected number would now call several correctly assembled
> objects collapsed. **Use ~50° with corrected figures; the two must not be
> mixed.**

**Neither number is trustworthy alone. The picture is the arbiter.**

---

## 6. What the pictures showed

Rendered from the saved posed clouds, correct assembly beside each model's first
attempt — never the best of five. Figures in `heldout_viz/`.

**Fresh objects:** five of six look correctly assembled by both models
(`blue_pot`, `galli_pot`, `limb3`, `plate`, `vert9`). `coxae` is the exception
and looks genuinely wrong. The two models are not visually distinguishable here
— nothing needed fixing on fresh breaks.

**The worn sweep is where the wear training earns its place, and it is
unambiguous:**

- **`blue_pot` at the heaviest wear:** the baseline **falls apart** — the pot
  splits open, pieces splayed (40.4°). **wear_v2 assembles it correctly**
  (16.3°, and the only case in the whole sweep where a third of fragments land
  within ten degrees). Every lighter level, both models manage.
- **`plate`:** the baseline sheds pieces from moderate wear and has **collapsed
  by heavy** (54.1°); **wear_v2 holds a clean plate through to the
  second-heaviest** (19.9°) and only partly degrades at the very heaviest
  (35.5° against the baseline's 69.8°).

**The Juglet is not reassembled by any model.** The neck piece lands roughly
right; the body sherds fan outwards and never close. Its contact is also *below*
the hand assembly's — 8.6–17.1% of one sherd within touching distance of
another, against **24.3%** for the conservator's own reassembly — so the pieces
are floating near each other rather than seated against each other.

---

## 7. Conclusion

**Wear-augmented training prevents collapse on heavily worn pottery.** That is
real, visible, and appears exactly where it should: not on lightly worn material
where nothing needed fixing, but at the severe end where the baseline fails.

It is **not** a general accuracy gain. On lightly worn and fresh material the two
models are indistinguishable by eye.

The Juglet remains unsolved and is harder than anything in the sweep — real
archaeological material rather than simulated wear, nine pieces, one visibly
missing.

---

## 8. Corrections made along the way

Recorded because the pattern matters more than any single number, and every one
was caught by two measurements disagreeing rather than by one looking wrong.

- **"The trade is gone."** Wrong. Reported from part accuracy alone.
- **"A fragment turned 30° is not a reassembly."** Wrong. Refuted by rendering
  the assemblies; symmetry accounts for the residual.
- **"Our wear is too gentle to reach the real pot."** Withdrawn. It compared the
  Juglet against a *different pot's* fresh state.
- **"The rebuild matches real worn material at resolvable scales."** Withdrawn.
  It rested on the single pairing where the two happened to coincide.

Four instrument faults were also found and fixed: sampling too coarse to resolve
the scale being judged; a ruler that moved with the surface; measuring total
displacement where only the normal component is relief; and a measurement window
that shrank with the wear dose.
