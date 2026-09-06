# 06: Buy a finer decision rule — twenty draws per condition on the Juglet

**Type:** `wayfinder:task` (AFK, GPU)
**What to build:** A tighter version of the readable-difference threshold that
[01](01-run-to-run-spread.md) produced, by drawing each condition twenty times instead of
five, so that tickets 02–05 can resolve smaller effects.

**Answers:** O8

**Blocked by:** None. It sharpens 01's rule rather than replacing it — 02, 03 and 04 can
proceed under the coarse 17° rule while this runs.

**Status:** answered 2026-09-06 — **job 30130049**, all three arms at twenty draws
each. The rule sharpens from 17° to **9°**, and the adapter still does nothing.

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

- [x] The two faults above resolved before submission, and the arms actually run stated —
      the checkpoint filter now excludes `_smoke_` and resolves to exactly one
      (`output/lora_vessels_v3_29880370/epoch-0.ckpt`, verified on Spartan before
      submitting); **all three arms run**, because the adapter arms are the ones stuck
      at five draws and they cannot be pooled
- [x] Twenty baseline draws on `zeroshot/juglet_gt` — confirmed from the run's own
      recorded config; scale 0.5110–0.5118, in band on all three arms
- [x] The revised threshold stated in the same plain form as 01, arithmetic shown below
- [x] 01's answer, the map's Decisions-so-far and `intent/O8` updated to the new rule,
      and every figure quoted under the 17° rule re-read against it (see *Re-read* below)
- [x] Renders at individual-sherd placement, not whole-pot silhouette —
      `artifacts/juglet_arms_sherds.png` (`scripts/render_juglet_arms.py`), 8 non-anchor
      sherds × 3 arms × 2 views, every panel in the reference frame, nothing re-centred
- [x] Names which of the three this is — **the method genuinely failed.** The ruler is now
      as sharp as it is going to get, and the failure is still there.

## Answer

**Twenty draws per arm takes the readable threshold from 17° to 9°, and at that
sharpness the LoRA adapter still makes no readable difference to the Juglet.** Buying
four times the evidence did not turn the adapter effect into a result; it turned "we
cannot tell" into "there is nothing there to tell".

**Which of the three this is: the method genuinely failed.** This ticket existed to rule
out the second possibility — that the instrument was too blunt to see a real effect. It
was not.

Job **30130049**, 4m 47s, exit 0:0. Read through `scripts/readout.py`, so the
`× 9/8` non-anchor correction is applied once.

```
arm            scale    draws   turn median   [range]      seated med  range   sd
adapter_off   0.5110     20        69.8     [44.8-106.0]      5.0/9     3-7   16.7
adapter_on    0.5118     20        61.2     [46.0- 90.4]      4.0/9     2-7   13.0
baseline      0.5114     20        66.2     [37.0- 86.0]      5.5/9     3-7   12.4
```

### The revised decision rule

> **On the Juglet, a difference below 9° between two twenty-draw runs is not readable.**
> One draw carries a standard error of about 14°; a twenty-draw median about 3.2°; the
> difference of two twenty-draw medians about 4.5°, so 2 sd is **9.1°**. Below that,
> report *no difference detected*, never a result.

Arithmetic on the pooled sd of all sixty new draws (14.35°), the same form ticket 01
used. Per-arm the figure is 7.9° (baseline), 8.2° (adapter_on), 10.5° (adapter_off) — the
adapter_off arm is the noisiest of the three and needs the largest gap before anything
can be claimed from it. **The rule applies to twenty-draw runs only.** A five-draw run is
still governed by 01's 17°, and comparing a twenty-draw run against a five-draw one uses
the pair's own standard error, not either headline number.

### What the three arms say

```
adapter_on vs adapter_off   gap  8.6°   readable only if >= 9.4°   -> not readable
baseline   vs adapter_on    gap  4.9°   readable only if >= 8.0°   -> not readable
baseline   vs adapter_off   gap  3.7°   readable only if >= 9.3°   -> not readable
```

Every pair is a tie. Note the ordering is also wrong for the adapter story: the arm with
the adapter *switched off* reads worst (69.8°) and the plain baseline sits between the
two, which is what three samples of one distribution look like.

### The render is the part that changes the reading

`artifacts/juglet_arms_sherds.png` draws the median draw of each arm one sherd at a time,
in the conservator's own frame, nothing re-centred, with the whole reference pot behind
in pale grey. At that resolution the whole-pot median of ~60–70° resolves into something
the silhouette hid: **individual sherds are turned 75–176° and land 3–51% of the pot's
size away from where they belong.** Sherd 3 is put on the opposite side of the vessel in
all three arms; sherd 5 likewise; sherd 8 is thrown clear of the body in all three. No
arm is visibly better than another, and the per-sherd differences between arms are
inconsistent in sign (sherd 1: 151° / 96° / 174°; sherd 7: 160° / 87° / 34°) — the
signature of sampler scatter, not of a method difference.

This is also the answer to *what "5 of 9 seated" means on this pot*: a sherd can count as
seated while being turned most of the way round, because seating passes a fragment on
distance and not on pose.

### Re-read: what changes under 9° that did not hold at 17°

Only one reading on the map moves, and it sharpens rather than reverses.

Ticket 02 reported the Juglet as tying `plate`, `narrow_bottle1` and `narrow_bottle3`
under the 17° rule — "one point against, three ties". Re-run against each fresh pot's own
standard error (their runs are ten draws each, so the pair's threshold, not the headline
one):

```
object            n   median     gap to Juglet   readable if >=   verdict
pink_bowl        10      2.4          63.8            5.6         READABLE
narrow_bottle2   10      4.3          61.9            5.6         READABLE
narrow_bottle4   10      7.8          58.3            5.6         READABLE
blue_pot         10     30.5          35.7           12.9         READABLE
galli_pot        10     34.8          31.3            8.2         READABLE
plate            10     48.7          17.5            8.4         READABLE
narrow_bottle1   10     62.3           3.8            7.2         tie
narrow_bottle3   10     81.8          15.6            6.4         READABLE (Juglet better)
```

So the honest count is now **one tie, not three**: the Juglet is readably worse than the
six-fragment `plate` and readably *better* than the four-fragment `narrow_bottle3`, and
matches only the twelve-fragment `narrow_bottle1`. **This does not overturn ticket 02's
conclusion** — the fresh pots' own spread at 4–6 fragments runs from 48.7° to 81.8°, so
the Juglet at 66° still sits inside the range fresh pots occupy, and seating still puts
it exactly on the trend at 5 of 9. What it removes is the stronger phrasing: the Juglet
is *within the fresh range*, not *indistinguishable from comparable fresh pots*.

Nothing else quoted under 17° changes. The in-band wear comparison (job 29308186,
56.8 / 59.6 / 62.2°) is five-draw runs and stays under 01's rule, where a 5.4° spread is
not readable; it would not be readable at 9° either. The anchor-mode ablation's −2.2°
median (job 28228263) is smaller than either threshold.

### How much weight this can bear

One pot, one trained model, 20 draws per arm — 60 draws total. Strong enough to say the
adapter does not move this object, and to fix the threshold for future comparisons on it.
Not enough to say the adapter is useless in general: it was trained on vessels and has
never been tested on more than this one worn pot at this fragment count.
