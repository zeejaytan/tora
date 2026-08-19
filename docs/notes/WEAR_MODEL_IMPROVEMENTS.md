# What to improve in the wear model

Backlog, ordered by evidence behind it rather than by ease. Everything here is
measured, not speculated; where a fix is a guess it says so.

Current state: `wear_ops.apply_wear` does one-sided peak truncation
(`blunt_asperities`) plus dish chipping, recession retired. Validated on four
objects — teeth blunted, curve preserved within ~2%, joins opened, no vertex on
any object gaining material. Training on it prevents heavily worn pottery from
collapsing, visibly (`WEAR_TEST_RESULTS.md`).

---

## 1. Make scan-realistic the default, not half the set

**Evidence: strong.** Gate A (`GATE_A_RESULT.md`) measured 20 real eroded
archaeological fragments and found **no fracture-like roughness at any scale
their scans resolve** — texture rising as R^1.7 where a fracture surface should
rise as R^0.4–0.8, over 0.4–6.4 mm.

Our training set is seven crisp variants per object and five blurred to
0.25% of object size. The crisp ones carry self-affine fracture roughness at
exactly the scales real scans do not record, so they teach the model to read a
signal that will not be there at inference.

**Change:** invert the ratio, or drop the crisp variants entirely and keep one
as a control. Cheap — a constant in `build_wear_trainset_v2.py`.

**What would change the answer:** a scan of real worn material below 0.1 mm
showing roughness after all. Then the crisp variants are right and the blur is
throwing away signal.

---

## 2. ~~Fix the under-worn rim~~ — WITHDRAWN, there was no defect

**Measured 2026-08-19, and the item was a misdiagnosis.** The observation was
real: blunting removes 7% of the available relief within one cutoff of the
break-region boundary against 93% well inside it. The interpretation was wrong.

Reporting the FEATHER beside the efficiency settles it:

| distance from edge | efficiency (plate) | feather | efficiency (blue_pot) | feather |
|---|---|---|---|---|
| under ½ cutoff | 6.4% | 0.057 | 7.0% | 0.063 |
| ½ to 1 | 14.0% | 0.124 | 15.1% | 0.135 |
| 1 to 2 | 24.0% | 0.216 | 25.2% | 0.225 |
| 2 to 4 | 45.6% | 0.400 | 45.0% | 0.402 |
| beyond 4 | 93.9% | 0.903 | 92.8% | 0.918 |

Efficiency **is** the feather value, to within a few percent, in every bin on
both objects. `blunt_asperities` scales its budget by `strength * feather *
exposure`, so this is the taper doing exactly what it was written to do.

And the taper is right. The region boundary those distances are measured from
sits about 6% of object size from the mating surface — that is the pot's own
outer surface, not fracture face. Wearing it would be the bug. On the actual
fracture face, where feather is ~0.9, wear runs at **93% efficiency**.

**What was actually changed, and why it is kept anyway.** The fix attempted here
replaced the mean-of-neighbours envelope with a locally fitted plane
(`_proud_height`), on the theory that a one-sided neighbourhood biased the
height estimate. That theory is refuted — the gradient did not move at all. But
the change is a clear improvement for an unrelated reason: on the synthetic pair
it removes as much texture as the mean envelope (teeth −39.1% against −39.8%)
while cutting curve damage tenfold (−0.3% against −3.1%), and on real objects
the spectrum now passes on blue_pot, coxae and vert9 with the plate failing only
on monotonicity. Kept on that evidence, not on the reasoning that produced it.

**The lesson, which is the transferable part:** a real measurement (7% vs 93%)
was attached to a wrong cause for three days. Nothing about the number was
false; the story told about it was. Reporting the suspected mechanism's own
value alongside the symptom is what settled it, and would have settled it
immediately.

## 3. Settle whether the contact band is counting intact pot

**Evidence: suggestive, not settled.** The break face is defined as everything
within 2% of object size from the neighbouring fragment. On thin-walled objects
that reaches through the wall and onto the vessel's own surfaces: the plate's
band is **57% of the whole fragment** against blue_pot's 40%, and a section
through it shows long stretches with no fracture relief at all.

If true, wear is being applied to sound pot on exactly the thin-walled material
that is archaeologically most common — including the Juglet.

**Test, and it is decisive and cheap:** tighten the band to well below the wall
thickness (0.2% instead of 2%) so only genuinely mating surface qualifies, then
re-measure. If the plate's blunting jumps, that was it.

---

## 4. Give severity a physical anchor

**Evidence: circumstantial but now supported.** Severity currently rides on the
blunting cutoff, 0.30–0.50% of object size. Gate A puts the scale at which real
digitised fracture stops carrying texture at **0.3–0.5 mm**, which for a ~100 mm
juglet is the same number.

That is a coincidence worth converting into a rule: express the cutoff in
**millimetres** with the object's physical size, not as a fraction of it. Wear is
a physical process and a 300 mm amphora does not wear at three times the scale of
a 100 mm juglet.

**Blocked on:** physical sizes for our objects, which the normalised datasets
have discarded. Recoverable from the source scans if they carry units.

---

## 5. Model wear as uneven along the fracture, not uniform

**Evidence: none yet — this is a hypothesis.** Real burial does not abrade a
sherd evenly: the exposed edge of a fragment sitting in soil wears more than a
sheltered one, and the conservator has said chips form at the pointy ends.

`blunt_asperities` has an exposure term that varies the rate by how far a
neighbourhood stands proud at a coarser scale, but it has never been validated
against anything. Gate A's per-fragment spread (grey lines in
`repair_fracture_spectrum.png`) is the obvious place to look: if real fragments
differ from each other far more than our simulated ones do, our wear is too
uniform.

**Test:** measure the spread of the texture exponent across RePAIR fragments and
across our simulated ones, with the same instrument. Cheap, and it either
motivates the work or closes it.

---

## 6. Measure our own wear with Gate A's instrument

**Evidence: this is the obvious missing comparison.** Gate A measured real
material in millimetres with curvature removed. Our simulated surfaces have never
been measured the same way — the wear validation used relief against the local
mean as a fraction of object size, which Gate A showed is dominated by shape.

**Do this before anything else in this file.** It is the only way to know whether
our simulated fracture sits in the fracture band (R^0.4–0.8) or the smooth band
(R^1.7), and therefore whether the wear model needs to remove more, less, or
differently.

Blocked on the same physical-size question as §4, but a stated assumption
("blue_pot is ~200 mm") is enough to place it on the same axis.

---

## Not worth doing

**Reviving recession.** Measured against what it buys: at every dose keeping the
curve within tolerance it opened joins *less* than blunting alone, while adding
the fine relief abrasion is supposed to remove. Retired on evidence, and the
evidence would have to be overturned rather than argued with.

**Chasing the Juglet's shape.** The hypothesis that its handle and asymmetry make
it hard was tested: it is *more* axially symmetric than the average training
object (1.31% surface movement against 3.16%). What distinguishes it is its
coarse scan and that its wear is real.
