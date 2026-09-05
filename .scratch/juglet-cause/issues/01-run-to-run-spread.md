# 01: How much do repeat runs of the same thing disagree on the Juglet?

**Type:** `wayfinder:task` (AFK)
**What to build:** A number for the run-to-run spread of TORA's Juglet result under a
single fixed condition, so that every later ticket knows how big a difference has to be
before it means anything. Report it the way a conservator would read it: "repeat
attempts at the same job land this many degrees apart."

**Answers:** O8

**Blocked by:** None (can start immediately)

**Status:** resolved

## Why this is first

Three runs labelled "baseline" on the same pot and the same reference were quoted as
**31.4°, 33.5° and 58.2°** (`lorav_juglet_baseline_29623885`,
`wearft2_jugletgt_baseline_29308186`, `lorav3_juglet_baseline_29880370`). If that is the
noise floor, then most of what this map is trying to separate is smaller than the
instrument, and tickets 02–05 need many draws rather than one.

**Two corrections to this ticket's original premise, both found on 2026-09-05 while
researching the read-out module. Neither is written up yet; both are still this
ticket's to confirm.**

*The settings are recoverable.* This ticket was opened saying they "cannot be fully
recovered". They can: Hydra writes `.hydra/config.yaml` and `.hydra/overrides.yaml` into
every run directory. Diffing them (excluding `log_dir`) shows
`lorav_juglet_baseline_29623885` and `lorav3_juglet_baseline_29880370` are
**byte-identical**, and `wearft2_jugletgt_baseline_29308186` differs only by absent
`lora` (disabled anyway) and `visualizer` blocks. All three: `seed: 42`,
`n_generations: 5`, `anchor_free: true`, checkpoint `bbad_everyday_cka.ckpt`, dataset
`zeroshot/juglet_gt`, 5000 points. They are the same condition, and the acceptance
criterion below that asks whether they are is answerable by reading, not by rerunning.

*The three quoted figures look like generation 0, not run means.* Pulling all five draws
of each run gives run means far closer together than 31.4 / 33.5 / 58.2 suggests, while
the draws **within** a single run span roughly 31°–69° — straddling the whole
"looks correct" / "collapsed" boundary. If that holds, the between-run spread this
ticket was opened to measure is mostly the spread between *draws*, and the answer is
that a single draw of this pot means very little. Confirm it against the module rather
than trusting this paragraph.

**The honest measure is the spread across generations *within* one run**, which is free:
every existing run already stores `model.n_generations` draws. Read them through
`scripts/readout.py` so the ×n/(n-1) correction is applied once, in one place.

## Acceptance criteria

- [x] Non-anchor rotation error (`× n/(n-1)`, n=9) reported per generation for every
      existing `juglet_gt` run, with the median and full range, from saved results only —
      no new GPU job for this part
- [x] The three cross-job "baseline" figures are either shown to be the same condition
      (and so usable as repeats) or shown not to be, by diffing the recorded sampler and
      checkpoint settings of the three jobs
- [x] Stated as a decision rule the later tickets can apply: *a difference below X° on
      this object is not readable*
- [x] The GT itself rendered once and confirmed to be an assembled vessel — cheap, and it
      is the one check that closes the reference question by looking rather than by
      inference
- [x] If within-run draws turn out to be too few, say what job would fix it and **ask
      before submitting** (`scripts/hpc/juglet_draws.slurm` already exists)
- [x] Names which of the three this is: method, ruler, or reference

## Answer

**Repeat attempts at the same job land about 30° apart on this pot, and two five-draw
runs can differ by 17° through luck alone.** That is larger than most of the differences
this map was opened to explain. The Juglet, run once, cannot tell two methods apart.

**Which of the three this is: the ruler — but a third kind of broken ruler.** Not a wrong
formula this time (that was the free-anchor dilution, fixed) and not a wrong reference
(the ground truth renders as a juglet, below). The instrument is *imprecise*: a single
draw of a stochastic sampler was being read as if it were a measurement of the method.
The three figures this ticket was opened on — 31.4°, 33.5°, 58.2° — are not three
methods disagreeing. They are draw 0 of three identical runs, on the old diluted ruler
(× 8/9 of the corrected 35.4°, 37.7°, 65.5°), and the apparent 27° gap between them is
sampler noise.

### What the numbers are

Recomputed from saved results only — no GPU — through `scripts/readout.py`, so the
× n/(n-1) non-anchor correction is applied once, in one place
(`scripts/analyze_juglet_spread.py`).

*Within one run,* the five draws of a single attempt spread by a median of **31.6°**
(range 6.7–47.6°) across all twelve `juglet_gt` runs. On this material 10–35° looks
correct and 40–70° has collapsed, so **a single run routinely contains both a result
that looks right and a result that has fallen apart.**

*Between runs of the same condition,* the four baselines are true repeats — identical
checkpoint (`bbad_everyday_cka.ckpt`), seed 42, five draws, `anchor_free: true`, 5000
points, verified by diffing the recorded provenance, not assumed. Their medians are
59.3 / 50.2 / 62.7 / 56.8°, a spread of **12.5°**. Their draw-0 values are
59.3 / 35.4 / 65.5 / 37.7°, a spread of **30.2°** — which is the artefact this ticket
was opened on, and it is two and a half times the honest between-run figure.

Pooled, twenty baseline draws: median **60.9°**, min 35.4°, max 88.9°, middle 80% of
draws between 42.3° and 72.9°, sd **13.2°**.

### The decision rule for tickets 02–05

> **On the Juglet, a difference below 17° between two five-draw runs is not readable.**
> One draw carries a standard error of about 13°; a five-draw median about 6°; the
> difference of two five-draw medians about 8°, so 2 sd is 17°. Below that, report the
> comparison as *no difference detected*, never as a result.

A single draw is worth nothing on its own: quote the run median over all draws, and say
how many draws it rests on.

### What the renders show

`artifacts/juglet_spread.png` — the conservator's assembly beside the best (35.4°) and
worst (88.9°) baseline draws, two orthographic views, one colour per sherd.

- **The reference is an assembled vessel.** Closed body, rim, handle loop, the missing
  piece left open. Confirmed by looking, which closes the reference question for this
  object independently of the fitting residual quoted in the map.
- **The picture cannot separate 35° from 89°.** Both draws still read as a juglet in
  silhouette — the model puts sherds in roughly the right region and turns them wrongly
  there. This is a warning for every later ticket: on this object the outline is not
  evidence, and a render must be of individual sherd placement, not of the whole pot.

`artifacts/juglet_spread_draws.png` — all twenty baseline draws, unbinned, grouped by
run, with each run's median. The four runs' bands overlap almost completely. This is the
plot to point at when someone quotes a single Juglet number.

### Draws are too few — what would fix it, not yet submitted

Five draws give a median with a ±6° standard error, so the rule above is coarse. Twenty
draws per condition would roughly halve it, to about ±3°, making a ~9° difference
readable. `scripts/hpc/juglet_draws.slurm` exists for exactly this.
**Not submitted — needs the conservator's go-ahead** (map: *ask before submitting any
Slurm job*). Tickets 02–05 can proceed under the 17° rule in the meantime; they would
simply be able to resolve smaller effects with the extra draws.

### Caveat carried forward

Only `lorav3_*_29880370` was scored after the unit-box threshold fix (2026-09-02,
`0d6a85f`). **Seating counts are not comparable across that fix; rotation is
unaffected**, and every figure above is rotation.
