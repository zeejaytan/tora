# 06: Buy a finer decision rule — twenty draws per condition on the Juglet

**Type:** `wayfinder:task` (AFK, GPU)
**What to build:** A tighter version of the readable-difference threshold that
[01](01-run-to-run-spread.md) produced, by drawing each condition twenty times instead of
five, so that tickets 02–05 can resolve smaller effects.

**Answers:** O8

**Blocked by:** None. It sharpens 01's rule rather than replacing it — 02, 03 and 04 can
proceed under the coarse 17° rule while this runs.

**Status:** ready-for-agent · **needs the conservator's go-ahead before sbatch**

## Why it exists

01 established that on the Juglet a difference below **17°** between two five-draw runs
is not readable. That is coarser than several of the differences this map is trying to
explain. Twenty draws roughly halves the standard error of a run's median (≈6° → ≈3°),
taking the readable threshold to about **9°**.

It is written as a separate ticket rather than folded into 01 because it *changes the
rule 02, 03 and 04 depend on*. Anything quoted under the 17° rule may need re-reading
against 9° once this lands, and that has to be findable.

## Before submitting — two faults in the job script, both found 2026-09-05

1. **It will exit before using any GPU.** `scripts/hpc/juglet_draws.slurm` insists on
   exactly one v3 adapter checkpoint and stops otherwise. The filter `*lora_vessels_v3_*`
   now matches three files, because two are `_smoke_` test runs:
   `lora_vessels_v3_29880370/epoch-0.ckpt` (the real one),
   `lora_vessels_v3_smoke_29825847/epoch-0.ckpt`, `lora_vessels_v3_smoke_29880370/epoch-0.ckpt`.
   Pass `TRAINED_CKPT=` explicitly, or exclude `_smoke_` from the search.
2. **It runs three arms, and this ticket needs one.** `adapter_on`, `adapter_off` and
   `baseline` at twenty draws each. Only `baseline` sharpens the rule. The other two
   settle "does the adapter hurt on the Juglet" — never established, but **not one of
   O8's five candidates**. Running them is a scope decision, not a default.

## Acceptance criteria

- [ ] The two faults above resolved before submission, and the arms actually run stated
- [ ] Twenty baseline draws on `zeroshot/juglet_gt` — never `juglet_norm`, which sits
      out of band (see [03](03-low-side-out-of-band-scale.md))
- [ ] The revised threshold stated in the same plain form as 01: *a difference below X°
      between two runs is not readable*, with the arithmetic shown
- [ ] 01's answer, the map's Decisions-so-far and `intent/O8` updated to the new rule,
      and any figure already quoted under the 17° rule re-read against it
- [ ] Renders at individual-sherd placement, not whole-pot silhouette — 01 showed the
      outline survives even at 89° and so cannot separate a good draw from a bad one
- [ ] Names which of the three this is: method, ruler, or reference
