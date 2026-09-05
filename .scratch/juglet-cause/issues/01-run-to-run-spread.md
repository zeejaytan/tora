# 01: How much do repeat runs of the same thing disagree on the Juglet?

**Type:** `wayfinder:task` (AFK)
**What to build:** A number for the run-to-run spread of TORA's Juglet result under a
single fixed condition, so that every later ticket knows how big a difference has to be
before it means anything. Report it the way a conservator would read it: "repeat
attempts at the same job land this many degrees apart."

**Answers:** O8

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

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

- [ ] Non-anchor rotation error (`× n/(n-1)`, n=9) reported per generation for every
      existing `juglet_gt` run, with the median and full range, from saved results only —
      no new GPU job for this part
- [ ] The three cross-job "baseline" figures are either shown to be the same condition
      (and so usable as repeats) or shown not to be, by diffing the recorded sampler and
      checkpoint settings of the three jobs
- [ ] Stated as a decision rule the later tickets can apply: *a difference below X° on
      this object is not readable*
- [ ] The GT itself rendered once and confirmed to be an assembled vessel — cheap, and it
      is the one check that closes the reference question by looking rather than by
      inference
- [ ] If within-run draws turn out to be too few, say what job would fix it and **ask
      before submitting** (`scripts/hpc/juglet_draws.slurm` already exists)
- [ ] Names which of the three this is: method, ruler, or reference
