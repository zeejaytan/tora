# 05: Can the Juglet's wear be demonstrated at all, at any resolution we have?

**Type:** `wayfinder:grilling` (HITL)
**What to build:** A decision on whether "the fracture surfaces are worn" is a claim this
project can currently support with data — and if not, whether the honest next step is a
capture (a finer scan) rather than an algorithm.

**Answers:** O8

**Blocked by:** 02, 04 (its framing depends on what they leave unexplained)

**Status:** needs-info

## Why it is last and why it is framed this way

The opening proposal for this whole effort was to teach TORA how worn fracture surfaces
align. That is set aside as a destination, not dismissed — but three things have to be
faced before spending a curriculum on it.

**The wear cannot be seen in this scan.** Break faces are sampled at 0.243% of object
size; the blunting acts at 0.3–0.5%. Every scale a comparison can reach lies *above*
where the wear lives. The dimensionless fine-over-coarse ratio was tried and withdrawn:
the worn Juglet reads **0.169**, fresh `blue_pot` reads **0.167**, and between-pot
variation spans 0.167–0.386 (`WEAR_TEST_RESULTS.md` §2).

**Real eroded fracture carries no fracture-like roughness at any scale these scans
resolve**, and whether the ground removed it or the scanner never recorded it cannot be
separated at 0.4 mm (`GATE_A_RESULT.md`, job 29404479).

**It has already been trained twice.** Jobs 29027773 and 29308186: Juglet rotation
51.5° → 49.2° → 52.9°, recall@10° flat at 0.000. Note that 29027773 ran at `scales`
0.041 — ticket 03 decides whether that comparison was fair.

## Acceptance criteria

- [ ] Whatever residual tickets 02 and 04 leave unexplained is stated as a number, with
      01's threshold, so it is clear how much there is for wear to account for
- [ ] A decision, taken with the conservator: is wear (a) demonstrably the residual,
      (b) demonstrably not, or (c) unmeasurable with current data
- [ ] If (c): what capture would settle it — resolution, and on what material — written
      down, and whether it is reachable. `WEAR_TEST_RESULTS.md` names the two options:
      a scan finer than 0.1% of object size, or fresh *and* worn scans of the same pot
      so between-pot variation cancels
- [ ] If (a): the wear curriculum is specified enough to hand to `/to-spec`, and this map
      closes
- [ ] Names which of the three this is
