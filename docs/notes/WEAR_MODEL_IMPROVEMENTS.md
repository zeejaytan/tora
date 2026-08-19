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

## 2. Fix the under-worn rim

**Evidence: strong, measured on two objects.** Within about one cutoff of the
edge of a break face, blunting removes only **7–9%** of the available relief,
against **93–99%** well inside it. Roughly a quarter of break-face points sit in
that zone, so every fracture in the training set carries a rim that is barely
worn.

**Cause:** the local envelope is one-sided near a region boundary — a point's
neighbours all lie inward — so the height it appears to stand proud of that
envelope is underestimated and almost nothing is removed.

**Fix:** replace the local mean with a locally fitted **plane or quadric**,
which does not care that the neighbours are all on one side. Gate A already
showed a quadric fit doing exactly this job on real fragments, so the machinery
exists and is tested.

This is the same fix as §1 of the instrument work, applied to the model.

---

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
