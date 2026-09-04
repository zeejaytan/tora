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

Three runs labelled "baseline" on the same pot and the same reference read **31.4°,
33.5° and 58.2°** (`lorav_juglet_baseline_29623885`, `wearft2_jugletgt_baseline_29308186`,
`lorav3_juglet_baseline_29880370`). If that is the noise floor, then most of what this
map is trying to separate is smaller than the instrument, and tickets 02–05 need many
draws rather than one.

Those three are different jobs whose sampler settings cannot be fully recovered — the
same trap that made the earlier cross-job scale comparison a lead rather than a finding.
**The honest measure is the spread across generations *within* one run**, which is free:
every existing run already stores `model.n_generations` draws.

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
