# 02: Is nine fragments on its own enough to explain the Juglet?

**Type:** `wayfinder:research` (AFK)
**What to build:** A direct comparison of the Juglet against fresh, unworn pots of
similar fragment count, using data already on disk, to decide whether the Juglet is
performing worse than its difficulty predicts — or exactly as well.

**Answers:** O8

**Blocked by:** 01 (needs the readable-difference threshold)

**Status:** ready-for-agent

## The claim under test

`JUGLET_TORA_ROOTCAUSE.md` ruled piece count out on the grounds that rotation error was
flat at 59–70° from 3 to 12 pieces. **That flatness was the units bug.** Normalised, the
same eight pots spread from 1.6° to 61.3°, so the ruling-out is void and piece count is
live again.

First-pass numbers, which this ticket must verify rather than inherit: the Juglet reads
35–66° non-anchor on `juglet_gt`; fresh normalised `galli_pot` (10 fragments) reads
31.4°, `plate` (6) 40.6°, `narrow_bottle1` (12) 57.1°. On that reading the Juglet is
**inside** the fresh range and there is nothing left for wear to explain.

The confound to name: `narrow_bottle3` has only 4 fragments and still reads 61.3°, so
fragment count is not a clean predictor even among fresh pots.

## Acceptance criteria

- [ ] Non-anchor rotation and fragments-seated plotted against fragment count for all
      eight fresh normalised pots (job 29891327) with the Juglet overlaid, using 01's
      spread as the error bar — no new GPU job
- [ ] Stated plainly whether the Juglet falls inside or outside the fresh band **for its
      fragment count**, and by how much relative to the readable threshold
- [ ] A render of the Juglet's proposed assembly beside a fresh pot of similar fragment
      count that scores similarly, so "the same score" can be checked to mean "the same
      kind of arrangement" — two assemblies can share a number and look nothing alike
- [ ] If it falls inside the band: say so, and record that the wear hypothesis has no
      residual to explain
- [ ] Names which of the three this is
