# 04: Does a missing sherd destabilise a pot that TORA otherwise reassembles?

**Type:** `wayfinder:task` (AFK)
**What to build:** A causal test of absence. Take pots TORA now reassembles cleanly,
remove one fragment, and re-run — the answer key for the remaining fragments is
unchanged, so any degradation is caused by the absence and nothing else.

**Answers:** O8

**Blocked by:** 01 (needs the readable-difference threshold)

**Status:** resolved 2026-09-06 — **graceful degradation**, job 30167044
(GPU) read by 30167787. See Answer.

## Why this is the strongest untested candidate

**The Juglet is incomplete.** One visible piece was never recovered, and no reassembly
can put it back (`scripts/build_juglet_ground_truth.py`). **None of the eight Fractura
pots TORA reassembles are missing anything.** That is a clean difference between the
Juglet and every object TORA succeeds on, it is not wear, and nobody has measured it.

Every benchmark this model was trained and tested on hands back all the parts. The
umbrella question [U4](../../../../intent/U4-missing-fragments.md) names the two failure
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

[U4](../../../../intent/U4-missing-fragments.md) asks for thinning at 90 / 75 / 50 / 25 %
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
- [x] Each pot run whole and with one fragment dropped, every fragment tried in turn where
      cheap, scored on the kept fragments only. Job **30167044** (GPU, COMPLETED 0:0,
      14m 10s on spartan-gpgpu127): seven arms -- `whole`, `reseed`, and `rank2..rank6` --
      over all eight fresh normalised pots, ten draws each.
- [x] Renders of whole vs one-dropped for at least two pots, at a view that shows whether
      the vessel still closes. `artifacts/fragdrop/fragment_drop_rank2.png` and
      `fragment_drop_rank3.png`, four columns each (reference whole / model whole /
      **reference dropped** / model dropped) so a correct answer's own hole is visible.
      Both looked at before anything below was written.
- [x] Stated as *degradation* or *destabilisation*, in those words, with the render as the
      arbiter -- **graceful degradation**, see Answer.
- [x] If destabilisation: the Juglet's incompleteness becomes a leading explanation and
      this is written back into O8 ahead of wear -- **it is not destabilisation**, so
      candidate 3 is written back into O8 as *not supported*, and it does **not** move
      ahead of wear.
- [x] Names which of the three this is -- **the measurement was broken** (twice more,
      during this ticket), and on the corrected measurement **the method mostly does not
      fail** on absence.


## Answer (2026-09-06)

**Graceful degradation, not destabilisation.** Take a pot TORA reassembles cleanly, remove
one fragment, and the fragments that remain go to essentially the same place they went
before. Across five different fragments removed and eight pots, there is no consistent
direction: some pots come out a little better, some a little worse, most unchanged.

That reading is the conservative one, because the confound runs the other way. Removing a
sherd also removes a sherd to place, so the task gets *easier*; destabilisation would have
had to show the kept sherds landing **further from home despite the smaller job**. It does
not, except once.

### The one exception

**`pink_bowl` at rank 2** goes from **1.48% to 13.06% of the pot's longest dimension** --
on a 100 mm bowl, from about **1.5 mm out (a hairline)** to **13 mm out (a bowl that will
not close)**. The render agrees: `fragment_drop_rank2.png` column 3 shows one continuous
shell where column 4 shows the two remaining pieces visibly coming apart. Its own noise
bar is 0.13%, so run-to-run variation cannot explain it.

**This is n = 1, on the most fragile possible case:** `pink_bowl` has three fragments, one
is the anchor, one is dropped, so exactly **one free sherd** is being scored. A single
sherd going wrong is the whole score. It is a lead, not a finding.

`blue_pot` reads readably further at ranks 2, 3 and 5 (+2.60, +4.18, +1.10% of pot size --
2 to 4 mm on a 100 mm pot). Real, visible as an open seam, but small.

### Per-rank result (job 30167787, the authoritative analysis run)

| fragment removed | pots scored | further | closer | no change | median | reading |
|---|---|---|---|---|---|---|
| rank 2 (2nd largest) | 7 | 2 | 2 | 3 | +0.15% | **no consistent direction** |
| rank 3 | 7 | 1 | 0 | 6 | +0.01% | graceful degradation |
| rank 4 | 3 | 0 | 0 | 3 | +0.12% | graceful degradation |
| rank 5 | 2 | 1 | 0 | 1 | +2.39% | graceful degradation |
| rank 6 | 1 | 0 | 0 | 1 | +2.85% | graceful degradation |

Displacement is per-sherd distance from its correct pose as a percentage of the pot's
longest bounding-box side, so **1% is about 1 mm of open seam on a 100 mm pot**. Two bars
must be cleared before a change is called: the pot's **own** run-to-run bar (from the
reseed arm, `2 * hypot(SE, SE)`) and a **1% seam floor** -- a change smaller than a
millimetre of seam is not something a conservator could see, however statistically clean.

Ranks cannot be compared with each other: no pot survives the shape gate at every rank, so
the rank rows are different sets of pots.

### Which of the three: the measurement was broken

Four separate measurement faults were found and fixed before this answer could be written.
Two of them were found *in this ticket* and both pointed the wrong way:

1. **The two arms were averaging over different sherds.** The whole arm averaged over every
   placed sherd *including the one later dropped*; the dropped arm averaged over survivors
   only. Dropping a well-seated sherd raises the survivors' average all by itself. Fixed by
   pairing the arms sherd-for-sherd on **area rank** -- `_omit_fragment` renumbers the
   survivors, so part ids do not correspond across arms and nothing records which fragment
   went. Under the old arithmetic `narrow_bottle3` read -14.38 and `narrow_bottle1` -13.15;
   corrected they are -12.04 and -13.70.
2. **The shape gate tolerance was picked by eye.** A flat 0.05 was refusing `blue_pot`,
   `galli_pot` and `plate`. The control arm -- nothing dropped, mapping certainly correct --
   showed re-sampling alone manufactures gaps of 0.008 to **0.112**, so the flat tolerance
   was refusing *correct* mappings. Each pot is now gated against **its own control gap**.

Two more, from earlier in the same investigation: **the seam floor** (`narrow_bottle2`
moved +0.16% -- a sixth of a millimetre -- and was being counted alongside `pink_bowl`'s
+11.58%) and **the majority test** (`DESTABILISATION on most pots` was firing at four of
eight). With all four fixed, the rank-2 headline changed from *destabilisation on most
pots* to *no consistent direction*.

**`plate` is refused at every rank** (shape gap 0.119 against its own 0.031 at rank 2, on
its smallest sherd) -- that is what two near-equal-area sherds swapping rank looks like. The
refusal is reported rather than papered over; `plate` contributes to no rank.

### Weight this can bear

Eight pots, ten draws each, one GPU job, one fragment removed at a time. The reseed control
arm gives a per-pot noise floor, which is what makes the "no change" rows meaningful rather
than merely quiet. It does **not** cover repeated drops (25-50% of the pot missing) -- that
is the deeper rung of [U4](../../../../intent/U4-missing-fragments.md) and remains untested.

### What it means for the work

**The Juglet's incompleteness is not the leading explanation for why TORA cannot reassemble
it.** Losing one piece does not make a model that works stop working. Generative completion
of the missing sherd does not become load-bearing on this evidence. `pink_bowl` says the
picture may differ for a pot with very few fragments, and the U4 ladder (50% / 25% present)
is the test that would change this answer.

**Jobs:** GPU run **30167044** -- `COMPLETED | 0:0`. Analysis chain 30167530 -> 30167619 ->
30167678 -> 30167745 -> **30167787** (authoritative) -- all `COMPLETED | 0:0`, all polled
laptop-side; 30167591 was `scancel`led deliberately to avoid two jobs writing the same PNGs.
Renders at `artifacts/fragdrop/`.
