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

## Why bit-identity is not available (found 2026-09-06, before any GPU time)

The first criterion as originally written cannot be met, and it is worth saying why
rather than quietly weakening it. Three things in `tora/data/dataset.py` couple every
fragment to every other:

```python
remaining_points = self.num_points_to_sample - base * len(meshes)
counts = (base + (remaining_points * (areas / total_area)).astype(int)).tolist()
```

Each fragment's share of the fixed 5000-point budget is its area over the **total**
area. Drop one mesh and both `total_area` and `len(meshes)` change, so every surviving
fragment is allotted a different number of points and re-sampled. Then `center_pcd` on
the concatenation moves the origin to the new centre of mass, and `scale =
np.max(np.abs(pts_gt))` renormalises the object to its new largest extent. The kept
sherds are not preserved; they cannot be.

**That is not a defect to engineer around — it is what a genuinely incomplete pot does.**
The Juglet's missing piece is missing at scan time, so the sampler has never seen it
either. An alternative design (sample the whole pot, then delete the dropped fragment's
points) would give bit-identical arithmetic while centring and normalising the pot as if
the lost sherd were still there, which is the wrong physics, and it would need code
changes anyway: `anchor_mask` is hard-coded to `num_points_to_sample`.

So the confound is bounded rather than assumed away:

- `scripts/check_fragment_omission.py` reports, in percent of pot size, how far
  re-sampling alone moves a kept sherd (a **reseed control**: same pot, new sampler
  seed) and how far removing a sherd moves it. It states the bar the experiment must
  clear, and fails only if a kept sherd comes back a different **shape** — measured with
  its own centroid removed, so the moving frame cannot inflate it — or if the anchor
  changes identity.
- The job runs a **reseed arm** as well, so the same floor exists at score level.

**The anchor trap.** `anchor_idx = np.argmax(counts)` and counts rise with area, so the
largest fragment *is* the anchor — the sherd handed to the model already seated.
Dropping it silently changes the starting position, which is a different task. The
dataset refuses `omit_rank < 2` and the gate checks that it does.

**The direction is what carries the argument.** Removing a sherd also removes a sherd to
place, and fewer pieces is an easier task, so the confound pushes *towards* a better
score. Graceful degradation therefore predicts the kept sherds score the same or better;
destabilisation predicts they score **worse despite the task getting smaller**. Only the
second is a reason to make generative completion load-bearing.

## Relation to the umbrella question

[U4](../../../intent/U4-missing-fragments.md) asks for thinning at 90 / 75 / 50 / 25 %
present. This ticket is the **drop-one** rung of that ladder, which on pots of 3–12
fragments already lands between 67 % and 92 % present. The `omit_rank` knob takes one
fragment; reaching 25 % would need repeated drops and is deliberately not in scope here.
Do the shallow end first: if drop-one shows nothing, a deeper ladder is the next
question, and if it shows destabilisation, the ladder becomes worth its GPU time.

## Acceptance criteria

- [x] A dataset knob that omits a named fragment, with a gate — **amended 2026-09-06,
      see "Why bit-identity is not available" below**: the gate *asserts* what must hold
      (the right sherd is gone, the anchor did not change) and *measures* the
      disturbance it cannot remove, against a re-sampling control.
      `tora/data/dataset.py` (`omit_rank`), `scripts/check_fragment_omission.py`
- [ ] Each pot run whole and with one fragment dropped, every fragment tried in turn where
      cheap, scored on the kept fragments only. **Ask before submitting**
- [ ] Renders of whole vs one-dropped for at least two pots, at a view that shows whether
      the vessel still closes
- [ ] Stated as *degradation* or *destabilisation*, in those words, with the render as the
      arbiter
- [ ] If destabilisation: the Juglet's incompleteness becomes a leading explanation and
      this is written back into O8 ahead of wear
- [ ] Names which of the three this is
