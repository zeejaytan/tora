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
2. **It runs three arms.** `adapter_on`, `adapter_off` and `baseline` at twenty draws
   each. Running all three is a scope decision, not a default — but the arithmetic below
   changed on 2026-09-06 and now favours it.

## Correction, 2026-09-06: the baseline arm is already bought

The four historical `baseline` runs on `juglet_gt` — `lorav_juglet_baseline_29527496`,
`lorav_juglet_baseline_29623885`, `lorav3_juglet_baseline_29880370`,
`wearft2_jugletgt_baseline_29308186` — **pool cleanly**: `readout.pool()` accepts all
twenty draws with no `across=` override, because the provenance matches on every field it
checks. So the baseline already has its twenty draws, and a fifth baseline run adds
precision at the margin rather than halving anything.

The arms that are *not* bought are the adapter arms, and they **cannot** be pooled:

```
adapter_off (29527496 + 29623885)  -> REFUSED, different adapter checkpoints
adapter_on  (29623885 + 29880370)  -> REFUSED, last.ckpt vs epoch-0.ckpt
```

Each therefore stands at five draws, which under 01's rule cannot separate anything
smaller than 17° — and the whole adapter effect on this pot is one to two sherds. So the
value of this job now sits almost entirely in the two arms the ticket originally proposed
to drop.

(Small gap noticed while checking: the first refusal prints two *identical* provenance
lines, because the LoRA adapter path is not among the fields `readout` displays. The
refusal is correct; the explanation it prints is not usable. Worth a line in `readout.py`
when something depends on it.)

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
