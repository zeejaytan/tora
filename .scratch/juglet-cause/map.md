# Map — what actually stops TORA reassembling the Juglet

**Label:** `wayfinder:map` · **Charted:** 2026-09-05
**Answers:** [O8](../../intent/O8-what-stops-the-juglet.md)

## Destination

Establish what actually stops TORA reassembling the Juglet, now that both units bugs
are fixed and a correct reference exists. Ends with each of five candidate causes ruled
in or out — each with a render — and whichever survives specified precisely enough to
hand to `/to-spec`. It does **not** end with a trained model.

## Notes

**Domain.** The Juglet is a nine-sherd excavated vessel, worn, and **incomplete** — one
visible piece was never recovered. A reconstruction that leaves that gap open is
*correct*; a model that fills it is wrong. Any metric rewarding contact everywhere will
mislead here (`scripts/build_juglet_ground_truth.py`).

**This map runs its own experiments** (deliberate override of wayfinder's plan-only
default). A claim is not settled here without a render, and a ticket that only specifies
an experiment cannot produce one. **Ask before submitting any Slurm job.**

**Every ticket must state which of the three it found:** the method failed, the ruler
was broken, or the reference was wrong. These lead to opposite decisions and both of the
last two have already happened on this object.

**Rotation error thresholds on this material** (`WEAR_TEST_RESULTS.md` §5): 10–35° the
assembly looks correct and the residual is symmetry; 40–70° it has genuinely collapsed.
"Within 10°" reads 0.000 almost everywhere and is too strict to be useful. Report
non-anchor rotation (`× n/(n-1)`) — the raw mean is diluted by the free anchor.

**Skills each session should consult:** `grilling` and `domain-modeling` for any ticket
that turns into a judgement call; `diagnosing-bugs` if a measurement looks wrong.

**Conventions:** `docs/agents/issue-tracker.md` for the ticket template — the `Answers:`
line is mandatory. Verify with `python ../../scripts/check_intent_links.py`.

## Decisions so far

- **The reference is trusted.** `juglet_gt.hdf5` was hand-reassembled by the conservator
  (2026-08-10) and fitted rigidly to the source fragments at a residual of 0.0000% of
  the object, so it holds the same vertices in the same order — the scan-layout
  substitution that broke the previous reference cannot have happened silently. Settled
  on the conservator's authority plus `scripts/build_juglet_ground_truth.py`.
- **The destination is a diagnosis, not a wear curriculum.** Teaching worn-fracture
  alignment was the opening proposal; it was set aside as a *destination* because the
  Juglet's rotation error already sits inside the fresh-break range, the wear cannot be
  measured at this scan resolution, and wear training has been run twice with no
  movement in rotation. It survives as candidate 5, last, reframed as "can wear be
  demonstrated at all".
- **Scope is the Juglet alone.** The general claim — does any of this hold beyond one
  architecture and a handful of objects — stays with the umbrella's `U3`.

## Not yet specified

- **What replaces "domain gap" as the standing explanation.** `JUGLET_TORA_ROOTCAUSE.md`
  concluded synthetic-to-real domain gap plus piece count; both halves were computed on
  the corrupted run. Once the five tickets land, that note needs rewriting — but what it
  should *say* cannot be drafted until they do.
- **Whether the Juglet can carry any claim at all.** If run-to-run spread turns out to
  be ~27°, most differences on a single object are unreadable and the honest move may be
  to stop treating one pot as evidence. That decision waits on ticket 01.
- **What a fair test of wear would even look like** given that the scan cannot resolve
  it. Possibly a capture question (a finer scan) rather than an algorithm question, but
  which, and at what resolution, is not sharp enough to ticket yet.
- **Whether GARF should be run alongside.** Only becomes a question if something here
  turns out to be TORA-specific.

## Out of scope

- **Building a worn-fracture curriculum.** Beyond the destination: this map decides
  whether wear is the cause, and hands off if it is. `O7` grounds the wear model.
- **Fixing the other unexplained failures** — the already-normalised simulated bones
  (61°, 64°) and `coxae` (86°). Real, open, and not about the Juglet.
- **Re-running the millimetre-stored Fractura subsets** (real bones, egg) normalised.
  Owed from the units fix, but it is bookkeeping on a different question.
