# 04: Label GARF's Fractura attempts as right way round or not

**What to build:** for every pot in GARF's existing Fractura evaluation runs on Spartan,
how many attempts are genuine full reassemblies (every sherd in its own place and the
right way round), and which pots qualify for ranking. CPU only; no new GPU run.

**Answers:** U17

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] Confirm which pots the Fractura file holds (plate, narrow_bottle3, galli_pot expected)
- [ ] `own_place.py` (with `oriented`) run over every GARF `rwlora_eval_*_fractura_fresh_*`
      run as a Spartan CPU batch job; polled; sacct State/ExitCode recorded here
- [ ] Per pot and training variant: attempts, own place, full reassembly
- [ ] Pots qualify where the right answer is rare but present; pots where all or none are
      right are set aside with the count stated
