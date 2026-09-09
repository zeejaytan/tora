# O7 — Is the wear model grounded in real material?

**Status:** open · **Blocked by:** none · **Effort:** ~3 days, can run in parallel

## Why it matters

The wear model is currently calibrated against **a physical argument and one pot**.
That is enough to have shown wear-augmented training stops heavily worn pottery
collapsing — a visible effect, small n — but not enough to call the result
*archaeologically accurate*.

Kura-Araxes black-burnished surfaces, Bedeni and Trialeti fabrics differ in hardness,
temper and firing, and therefore in how they abrade. Parameters chosen rather than
measured are a soft spot in any claim built on top of them.

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

**This makes O7 a capture question before it is a parameter question.** Two captures would
settle it, and neither is an algorithm. **Both were rewritten 2026-09-09** — the first
because its millimetre figure was on a different size convention and because it omits a
condition, the second because half of it was wrong.

1. **A scan of real worn material finer than 0.1% of object size.** In plain terms: how far
   apart the points sit on the scan. The Juglet's current meshes carry neighbouring points
   **0.29–0.48 mm** apart; the blunting the wear model simulates acts at roughly
   **0.2–0.3 mm** on this vessel. The effect is smaller than the spacing of the dots we
   would see it with, which is why three instruments came back "cannot tell". What is needed
   is **about 0.1 mm point spacing, three to five times finer than now.**

   Not exotic equipment. Close-range structured-light scanners already used for
   archaeological recording declare ~0.1 mm 3D resolution and 0.05 mm point spacing; for a
   single break face rather than a whole vessel, focus-variation or confocal profilometry
   reaches micrometres.

   **Condition, added 2026-09-09: a finer scan grounds `O7` without reaching `O8` on its
   own.** Every config here sets `num_points_to_sample: 5000` (`config/data/*.yaml`), which
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
   - **Survives, and is the strong version: one excavated sherd carrying both an ancient
     break and a modern one.** Sherds break again during excavation, lifting, washing and
     storage. A fragment with a buried, weathered break face **and** a fresh break face
     gives the same fabric, the same temper, the same firing, the same vessel and the same
     scan session, with two thousand years of burial on one face and none on the other.
     Nothing is simulated; the control is internal to the object. This is the design bone
     taphonomy uses when it compares ancient with modern material to establish a baseline,
     and it is tighter here because both faces sit on one piece.

     **What it costs:** no equipment and no experiment — a shelf search, and conservator's
     work rather than compute. **What to watch:** the two faces differ in more than age
     (orientation in the ground, exposure, whether the fresh break followed an existing
     weakness), so it wants several sherds rather than one, and the fresh face should be a
     clean break rather than a crumbled one. **What it would settle:** whether real burial
     blunts a break edge at all at the scale the wear model claims, and by how much —
     measured, on real material, against a real fresh control.

Until one exists, "the Juglet fails *because* its fractures are worn" is an inference from
a simulator, not a measurement of the object — and the wear model's parameters cannot be
validated against the material they claim to imitate.

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

## Done when

- [ ] One of the two captures above exists, or is recorded as unreachable with a
      reason. **Now the binding constraint on `O8` as well (2026-09-09)** — three
      instruments agree the existing scans cannot reach the question
- [ ] Fabric, temper and wall-thickness distributions have been pulled from the
      archaeometric literature (Khashuri Natsargora, Tsaghkasar, the Kars corpus)
- [ ] Wear parameters are driven from **measured ranges** rather than chosen values
- [ ] The mapping from measured property to wear parameter is written down, so a
      reader can disagree with it specifically

## What this buys

It is what makes "archaeologically accurate" a defensible phrase rather than an
aspiration — and it is the part a conservation examiner is most likely to press on.

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
