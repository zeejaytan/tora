# 01: One module that reads an evaluation run correctly

**What to build:** A single place that turns an evaluation run directory into records
anyone can trust, so that "how did TORA do on this pot?" has one answer regardless of
who asks. It reports fragments seated out of fragments present with the free anchor
named, degrees of turn on the fragments the model actually had to place, and the
settings that produced both — and it says so out loud when any of that cannot be
trusted. Nothing that currently prints a table is touched by this ticket.

**Answers:** O8

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

## Why this is first, and why it stops short of the callers

The correction has to exist and be proven before anything is rewired. The moment the
five summarisers change, every table in `docs/notes/` is being read by a different
instrument; that should happen after the module has been checked against reality
(ticket 02), not at the same time.

The defect it fixes: `tora/eval/metrics.py:compute_transform_errors` skips the anchor
fragment when averaging rotation but divides by all fragments, so the stored
`rotation_error` carries a free zero. Only `scripts/summarise_scale_ladder.py` corrects
for it. The factor is `n/(n-1)` — ×1.125 on the nine-sherd Juglet, ×2.00 on a
two-fragment bowl — so it is not an offset that cancels in a comparison.

## Acceptance criteria

- [ ] `scripts/readout.py` exists and is importable, reading only
      `<run>/results/*_generation*.json` and `<run>/clouds/*.npz`. It imports no `torch`,
      no Hydra config, no dataset and no model, and runs on the laptop in seconds.
- [ ] Records are **per draw, per object**, with per-fragment detail attached. Averaging
      is a view over records, never the stored thing.
- [ ] `turn_deg` is the non-anchor mean, corrected once, in one place. The raw stored
      value is reachable only as `turn_deg_diluted_by_free_anchor` and no view prints it.
- [ ] Seating is a count: `seated`, `n_fragments`, `floor`. A fraction is available but
      never emitted without its floor beside it.
- [ ] Every record carries provenance — trained model, seed, number of draws, anchor
      mode, dataset file, model size input — read from whatever the run saved. Any field
      the run never saved is stamped `unrecoverable`.
- [ ] Pooling records whose provenance differs, or is `unrecoverable`, **raises** rather
      than averaging. A caller that genuinely wants it must say so explicitly.
- [ ] Health flag (a): model size input outside `[0.375, 0.625]`, on by default.
- [ ] Health flag (b): scored before the unit-box threshold fix. Where the flag is set
      and clouds exist, rescore using the per-object unit-box derivation currently in
      `scripts/rescore_part_acc.py`, which **moves into this module** as its single
      implementation. `scripts/rescore_part_acc.py` keeps its command line and delegates.
- [ ] A record can be built over a **named subset of fragments**, with the denominator
      and the floor following the subset — so juglet-map ticket 04 cannot drop a sherd
      and silently change what it is dividing by.
- [ ] `scripts/check_readout.py` exists, follows the repo's gate idiom (docstring stating
      WHY and WHAT THIS ASSERTS, non-zero exit on failure, no pytest), and asserts:
  - [ ] 9-fragment fixture, every non-anchor fragment turned exactly 40°, anchor 0°:
        stored mean **35.56°**, `turn_deg` **40.00°**. The arithmetic is visible in the
        assertion, not hidden behind a helper.
  - [ ] The same fixture at 2, 3 and 9 fragments — the correction scales with fragment
        count and is not a constant.
  - [ ] Seated 4 on a 9-fragment object reports `4 of 9, floor 1 of 9`; no view emits a
        bare fraction.
  - [ ] Pooling two records with different seeds raises; identical provenance succeeds.
  - [ ] An absent settings field is stamped `unrecoverable`, and a view containing that
        record prints the word.
  - [ ] Model size 0.041 and 61.0 both raise flag (a); 0.511 does not.
  - [ ] Rescoring a pre-fix fixture reproduces what `scripts/rescore_part_acc.py`
        produces today on the same input — the move changes location, not numbers.
  - [ ] A subset record over 8 of 9 fragments uses 8 as denominator and floor.
- [ ] **No snapshot or golden-output tests.** Every assertion is against arithmetic a
      person can check on paper. A snapshot would have frozen the diluted-anchor bug.
- [ ] No summariser is modified in this ticket, and no number in `docs/notes/` changes.
- [ ] State which of the three this was: the method failed, the ruler was broken, or the
      reference was wrong. (Expected: the ruler.)
