# 04: Does a missing sherd destabilise a pot that TORA otherwise reassembles?

**Type:** `wayfinder:task` (AFK)
**What to build:** A causal test of absence. Take pots TORA now reassembles cleanly,
remove one fragment, and re-run — the answer key for the remaining fragments is
unchanged, so any degradation is caused by the absence and nothing else.

**Answers:** O8

**Blocked by:** 01 (needs the readable-difference threshold)

**Status:** ready-for-agent

## Why this is the strongest untested candidate

**The Juglet is incomplete.** One visible piece was never recovered, and no reassembly
can put it back (`scripts/build_juglet_ground_truth.py`). **None of the eight Fractura
pots TORA reassembles are missing anything.** That is a clean difference between the
Juglet and every object TORA succeeds on, it is not wear, and nobody has measured it.

Every benchmark this model was trained and tested on hands back all the parts. The
umbrella question [U4](../../../intent/U4-missing-fragments.md) names the two failure
modes that must be told apart, and they demand opposite responses:

1. **Graceful degradation** — it seats the fragments it has and leaves a gap.
2. **Destabilisation** — absence makes it place *present* fragments wrongly, because the
   assembly is scored whole and a hole wants filling.

Eight sherds clustered against one side with no vessel closing is what mode 2 looks like.

## Design

Use the four pots that reassemble cleanly normalised — `blue_pot` (4 of 4 seated),
`pink_bowl` (2 of 2), `narrow_bottle4` (3 of 3), `narrow_bottle2` (2 of 2) — plus
`galli_pot` (7 of 9) for a higher fragment count. Drop one fragment at a time; score only
the fragments that remain, against their unchanged correct poses.

Do **not** report a whole-assembly score: a missing piece deflates it automatically and
that would confuse absence with failure. The question is *did the fragments we kept still
go to the right place*.

## Acceptance criteria

- [ ] A dataset knob that omits a named fragment, with a gate asserting the remaining
      fragments' point clouds and reference poses are bit-identical to the full run —
      same discipline as `scripts/check_scale_conditioning.py`
- [ ] Each pot run whole and with one fragment dropped, every fragment tried in turn where
      cheap, scored on the kept fragments only. **Ask before submitting**
- [ ] Renders of whole vs one-dropped for at least two pots, at a view that shows whether
      the vessel still closes
- [ ] Stated as *degradation* or *destabilisation*, in those words, with the render as the
      arbiter
- [ ] If destabilisation: the Juglet's incompleteness becomes a leading explanation and
      this is written back into O8 ahead of wear
- [ ] Names which of the three this is
