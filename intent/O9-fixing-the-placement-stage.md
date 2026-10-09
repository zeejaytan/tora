# O9 — If placement is the bottleneck, what fixes it — and can it be fixed without retraining?

**Status:** open · **Blocked by:** none · **Effort:** ~2 weeks, no training runs required for the first half

## Why it matters

`U2` established, on TORA, that **the bottleneck is the placement stage, not perception** —
retraining on worn breaks moved fragments-correctly-seated by +0.235 (p = 0.008) while
break-surface discrimination did not move at all, and the `narrow_bottle3` seam check
showed the break edges carry enough information to say which half goes where even when the
model gets it backwards ten times out of ten.

**That finding names the culprit and stops.** Nothing in this workspace asks what to do
about it. `U2` asks whether the diagnosis holds on a second architecture; `O8` asks what
stops one specific object. Neither asks for an intervention, and a diagnosis with no
intervention is a paragraph in a thesis, not a chapter.

**The specific thing that makes this urgent.** The only placement fix demonstrated here is
*retraining on worn breaks* — and that needs a worn training set. For Rabati material we do
not have one, may never have one, and building one requires the wear model in
[O7](O7-wear-grounding.md) to be right. So the practical question is not "does retraining
help" (it does) but **"is there a fix that works on material we cannot train on."** That is
the field-ready half of *From Prototype to Practice*.

## The lead worth following first

`U2`'s seam check is already a working discriminator, and it was not built to be one:

| | typical gap at the join | worst tenth of the join |
|---|---|---|
| the bottle as it really is | 0.11 – 0.23% of its own size | 0.17 – 0.39% |
| the same bottle, halves exchanged, at its best | 0.58 – 0.61% | **3.2 – 5.7%** |

On a 100 mm bottle: true joins close to about a tenth of a millimetre; the wrong
arrangement stands three to six millimetres open. **A three-to-five-fold separation, from
the fragments' own scanned surfaces, with no reference answer.** The model could not tell
those two apart. A seam measurement could.

If that separation holds across objects, it converts into a placement fix that needs no
retraining at all: **sample the model several times and keep the arrangement whose seams
close.** The pieces for this already exist — TORA is stochastic and best-of-N is already
reported, `check_identity_swap.py` already scores arrangements, and the seam procedure is
already written.

Two published interventions do the same kind of thing and are worth reading before building
anything (rule 1 in `AGENTS.md`):

- **SARe-Refine** — an inference-time correction pass: voxelise under predicted poses,
  reject pairs that interpenetrate beyond a threshold, keep pairs whose fracture regions
  mutually overlap. Same shape of idea, different criterion.
- **PF++** — a verifier over candidate assemblies rather than a single forward pass.

## Done when

- [ ] **The seam measurement run on every object in the corpus, on the arrangement TORA
      actually produced**, not only on `narrow_bottle3`. Reported as gap at the join in
      **millimetres of the real pot**, with the worst-tenth figure, beside the seating score.
      This is the cheap half and it answers the question on its own if the separation
      collapses
- [ ] **Does the seam gap rank runs correctly?** Take N samples per object, rank them by
      seam closure, and check whether that ranking agrees with the ranking by fragments
      correctly seated. If it does not, the criterion is not usable as a selector and the
      idea stops here — say so plainly
- [ ] **Selection tested end to end:** best-of-N chosen *by seam closure with no reference*
      against best-of-N chosen by the ground-truth score (the ceiling) and against the mean
      of N (the honest baseline). Reported as all three numbers. Best-of-N reports only the
      best run of N — see `docs/glossary.md` — so the mean is what a conservator would get
- [ ] At least one recovered case **rendered before and after**, at a view that resolves the
      seam being measured. A selector that improves a number without a visible improvement
      in the join is measuring something other than the join
- [ ] **A statement of which failures it cannot fix.** Selection can only choose among
      arrangements the model already produced. If every sample scatters — which is what the
      Juglet, `plate`, `galli_pot` and `narrow_bottle1` did — there is nothing good to
      select, and this is not the fix for them. Name the fraction of the corpus in each case
- [ ] Only then, if selection is not enough: one **policy-level** change tried and reported,
      e.g. SARe-Refine's interpenetration + fracture-overlap filter reimplemented over TORA's
      output, or seam closure fed back as a refinement objective rather than only a selector

## Gate / stop condition

- **Seam closure separates good from bad arrangements across the corpus, and selecting on it
  recovers seating** → there is a field-ready placement fix that needs no worn training data,
  and it is the same instrument [U1](../../intent/U1-judging-without-answer-key.md) is trying
  to build. Those two then merge and the thesis gets one contribution instead of two halves.
- **Seam closure separates, but selection does not recover seating** → the model is not
  producing a correct arrangement to select. The fix has to be in the placement policy
  itself, and this question hands over to that with a measured reason.
- **Seam closure does not separate outside `narrow_bottle3`** → `U2`'s strongest single piece
  of evidence was one object, and that must be said out loud in `U2`, not only here.

## What would refute it

- The seam gap correlating with **object size or scan resolution** rather than with
  correctness. Check this first: it is the same failure mode as chamfer distance depending
  on object size, which produced a false finding here (`docs/lessons.md`).
- A selector that improves the reported number while the render looks no better — i.e. it is
  picking arrangements that satisfy the measurement, not arrangements that are right. This
  is **call 2, the measurement is broken**, and it is the likeliest way this goes wrong.

## Scope — what this is *not*

- **Not [O8](O8-what-stops-the-juglet.md).** O8 diagnoses one object: what stops the Juglet.
  O9 tests an intervention across the corpus. If O8 concludes the Juglet's problem is
  something selection cannot touch, that is an input here, not a duplicate.
- **Not [U2](../../intent/U2-perception-or-placement.md).** U2 asks whether the diagnosis
  generalises to a second architecture. O9 assumes it and asks what to do. They can run in
  either order; neither blocks the other.
- **Not [O7](O7-wear-grounding.md).** O7 is about whether simulated wear resembles real wear.
  O9 deliberately avoids needing that, which is most of its value.

## Related

- [U2](../../intent/U2-perception-or-placement.md) — the finding this follows through on.
- [U1](../../intent/U1-judging-without-answer-key.md) — a reference-free criterion good
  enough to *select* an arrangement is most of a reference-free criterion good enough to
  *judge* one. Watch for these converging.
- [G3](../../GARF/intent/G3-second-architecture-for-u2.md) — the same probe on
  GARF. If a selector works on TORA it should be tried there too; it is architecture-agnostic
  by construction.

## Source

Conservator's direction, 2026-09-18 ("let's get U2's finding a follow-through").
`intent/U2-perception-or-placement.md`; `.scratch/perception-or-placement/issues/01-does-the-break-edge-disambiguate.md`;
`scripts/check_identity_swap.py`; render `artifacts/nb3seam/narrow_bottle3_seam_swap.png`.
`.scratch/intent-gaps/findings.md` §7c. SARe-Refine and PF++ readings not yet done — first task.
