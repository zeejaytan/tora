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
settle it, and neither is an algorithm:

1. **A scan of real worn material finer than 0.1% of object size** — under 0.1 mm point
   spacing on a 100 mm juglet, roughly 2.5× finer than the current capture.
2. **Fresh *and* worn scans of the same pot**, so between-pot variation cancels and wear is
   the only difference. Reachable on excavated material where a fresh break was made during
   conservation, or on a modern replica: break it, scan it, abrade it, scan it again.

Until one exists, "the Juglet fails *because* its fractures are worn" is an inference from
a simulator, not a measurement of the object — and the wear model's parameters cannot be
validated against the material they claim to imitate.

## Done when

- [ ] One of the two captures above exists, or is recorded as unreachable with a reason
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

## Source

`../../CSC/docs/notes/PLAN.md` §R5, `WEAR_V3_PLAN.md`, `WEAR_TEST_RESULTS.md`.
