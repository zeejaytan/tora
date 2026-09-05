# 01: One module that reads an evaluation run correctly

**What to build:** A single place that turns an evaluation run directory into records
anyone can trust, so that "how did TORA do on this pot?" has one answer regardless of
who asks. It reports fragments seated out of fragments present with the free anchor
named, degrees of turn on the fragments the model actually had to place, and the
settings that produced both — and it says so out loud when any of that cannot be
trusted. Nothing that currently prints a table is touched by this ticket.

**Answers:** O8

**Blocked by:** None (can start immediately)

**Status:** done

## Why this is first, and why it stops short of the callers

The correction has to exist and be proven before anything is rewired. The moment the
five summarisers change, every table in `docs/notes/` is being read by a different
instrument; that should happen after the module has been checked against reality
(ticket 02), not at the same time.

The defect it fixes: `tora/eval/metrics.py:compute_transform_errors` skips the anchor
fragment when averaging but divides by all fragments, so the stored `rotation_error`
carries a free zero — and so, by the same `/ n_parts`, do `translation_error`,
`translation_error_unit` and `euler/rotation_error`. (This ticket was written saying
rotation only; corrected 2026-09-05 on reading the function in full.) Only
`scripts/summarise_scale_ladder.py` corrects for any of it, and only for rotation. The factor is `n/(n-1)` — ×1.125 on the nine-sherd Juglet, ×2.00 on a
two-fragment bowl — so it is not an offset that cancels in a comparison.

## Acceptance criteria

- [x] `scripts/readout.py` exists and is importable, reading only
      `<run>/results/*_generation*.json` and `<run>/clouds/*.npz`. It imports no `torch`,
      no Hydra config, no dataset and no model, and runs on the laptop in seconds.
- [x] Records are **per draw, per object**, with per-fragment detail attached. Averaging
      is a view over records, never the stored thing.
- [x] `turn_deg` is the non-anchor mean, corrected once, in one place. The raw stored
      value is reachable only as `turn_deg_diluted_by_free_anchor` and no view prints it.
- [x] Seating is a count: `seated`, `n_fragments`, `floor`. A fraction is available but
      never emitted without its floor beside it.
- [x] Every record carries provenance — trained model, seed, number of draws, anchor
      mode, dataset file, model size input — read from whatever the run saved. Any field
      the run never saved is stamped `unrecoverable`.
- [x] Pooling records whose provenance differs, or is `unrecoverable`, **raises** rather
      than averaging. A caller that genuinely wants it must say so explicitly.
- [x] Health flag (a): model size input outside `[0.375, 0.625]`, on by default.
- [x] Health flag (b): scored before the unit-box threshold fix. Where the flag is set
      and clouds exist, rescore using the per-object unit-box derivation currently in
      `scripts/rescore_part_acc.py`, which **moves into this module** as its single
      implementation. `scripts/rescore_part_acc.py` keeps its command line and delegates.
- [x] A record can be built over a **named subset of fragments**, with the denominator
      and the floor following the subset — so juglet-map ticket 04 cannot drop a sherd
      and silently change what it is dividing by.
- [x] `scripts/check_readout.py` exists, follows the repo's gate idiom (docstring stating
      WHY and WHAT THIS ASSERTS, non-zero exit on failure, no pytest), and asserts:
  - [x] 9-fragment fixture, every non-anchor fragment turned exactly 40°, anchor 0°:
        stored mean **35.56°**, `turn_deg` **40.00°**. The arithmetic is visible in the
        assertion, not hidden behind a helper.
  - [x] The same fixture at 2, 3 and 9 fragments — the correction scales with fragment
        count and is not a constant.
  - [x] Seated 4 on a 9-fragment object reports `4 of 9, floor 1 of 9`; no view emits a
        bare fraction.
  - [x] Pooling two records with different seeds raises; identical provenance succeeds.
  - [x] An absent settings field is stamped `unrecoverable`, and a view containing that
        record prints the word.
  - [x] Model size 0.041 and 61.0 both raise flag (a); 0.511 does not.
  - [x] Rescoring a pre-fix fixture reproduces what `scripts/rescore_part_acc.py`
        produces today on the same input — the move changes location, not numbers.
  - [x] A subset record over 8 of 9 fragments uses 8 as denominator and floor.
- [x] **No snapshot or golden-output tests.** Every assertion is against arithmetic a
      person can check on paper. A snapshot would have frozen the diluted-anchor bug.
- [x] No summariser is modified in this ticket, and no number in `docs/notes/` changes.
- [x] State which of the three this was: the method failed, the ruler was broken, or the
      reference was wrong. (Expected: the ruler.)

## Result, 2026-09-05

**Which of the three: the ruler was broken.** Not the method and not the reference — the
model's assemblies were never re-run. What changed is what we read off them.

Built:

- `scripts/readout.py` — the one place an evaluation run is read. numpy and scipy only;
  no torch, no Hydra runtime, no dataset, no model. Reads `<run>/results/*_generation*.json`
  and `<run>/clouds/*.npz`, and runs on the laptop in about a second.
- `scripts/check_readout.py` — the gate. 26 assertions, all arithmetic a person can check
  on paper; no snapshots. Passes.
- `scripts/rescore_part_acc.py` — CLI and table unchanged, computes nothing of its own;
  the unit-box, chamfer and Hungarian derivations moved into the module.

Three things found while building it, each of which changes something already written
down:

1. **The dilution is not rotation-only.** The same `/ n_parts` divides the translation
   sum and the euler-angle rotation sum. `translation_error`, `translation_error_unit`
   and `euler/rotation_error` are diluted by the identical `n/(n-1)`. The spec and the
   premise above were corrected in place; the module corrects all of them.
2. **Run settings are recoverable after all.** `.hydra/config.yaml` sits in every run
   directory. The claim in `.scratch/juglet-cause/issues/01-run-to-run-spread.md` that
   they could not be recovered was wrong and has been corrected there.
3. **`recall_at_5deg` / `recall_at_10deg` are a per-object 0/1, not a fraction of
   fragments.** `_recall_at_thresholds` thresholds the per-object mean. This is the field
   `audit_placement_metrics.py`'s docstring calls "the fraction of fragments within ten
   degrees", and it is the figure quoted as "recall@10° flat at 0.000" in
   `docs/notes/WEAR_TEST_RESULTS.md`. Left for ticket 03, which owns that docstring.

No summariser was modified and no number in `docs/notes/` changed — that is ticket 03,
and it waits on the reconciliation in ticket 02.
