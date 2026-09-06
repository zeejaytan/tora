# 07: Why does `narrow_bottle3` collapse? Fresh, unworn, four fragments

**Type:** `wayfinder:research` (AFK)
**What to build:** An explanation for the largest unexplained reassembly failure in the
corpus — a **freshly broken, unworn, four-fragment** bottle that TORA tears into two
flaps, four times further off the fragment-count trend than the worn Juglet is.

**Answers:** O8

**Blocked by:** None. 05 closed the wear question and explicitly ruled this out of it.

**Status:** needs-triage

## Why it exists

Ticket 05 needed a test that could refute the wear hypothesis, and ranking every pot by
its deviation from the fresh fragment-count trend produced one:

| pot | deviation from trend | fragments | worn? |
|---|---|---|---|
| **`narrow_bottle3`** | **+55.3° (2.0 sd)** | 4 | no |
| `plate` | +14.1° | 6 | no |
| **the Juglet** | **+14.3° (0.51 sd)** | 9 | yes |
| `narrow_bottle1` | +3.6° | 12 | no |
| `blue_pot` | −0.1° | 5 | no |
| `galli_pot` | −15.9° | — | no |
| `narrow_bottle2` | −18.2° | — | no |
| `narrow_bottle4` | −18.7° | — | no |
| `pink_bowl` | −20.1° | — | no |

**The worst object in the corpus is fresh, unworn and has only four pieces.** It is not
explained by wear (there is none), by fragment count (four is the easy end), or by a
missing sherd (nothing is missing).

**It was rendered before being reported** (2026-09-06,
`artifacts/nb3/narrow_bottle3_vs_working.png`, drawn locally from job 30167044's saved
clouds — no GPU bought). The median draw, not the best one:

```
narrow_bottle3   worst free sherd 27.0% of pot size from home
     part 0   1348 pts   23.70% from home   turn 108.5 deg
     part 1   2217 pts    0.01% from home   turn   0.0 deg   <- anchor
     part 2    111 pts    1.58% from home   turn   9.0 deg
     part 3   1324 pts   26.96% from home   turn 176.6 deg
```

The picture shows a **closed bottle torn into two flaps with a wide gap down the
middle** — about 24 mm and 27 mm of displacement on a 100 mm bottle. Beside it in the
same figure, `blue_pot` and `pink_bowl` are visually indistinguishable from their
references. So 81.8° here is **genuine collapse, not a small-sherd symmetry artefact**,
and the near-symmetric-sherd trap that has caught this project before is not what is
happening.

## What to look at first

Three leads, cheapest first, none of them yet tested:

1. **Piece-size imbalance.** Two large flaps of 1348 and 1324 points against a
   111-point sliver, with a 2217-point anchor. `_sample_points` allots the 5000-point
   budget by area, so the sliver gets almost nothing to match on. Do the other
   `narrow_bottle*` objects — which sit at −18.2, −18.7 and +3.6 — have flatter size
   distributions? This is free to check from the saved clouds.
2. **Two near-equal-area pieces swapping identity.** `plate` is refused by ticket 04's
   shape gate at every rank for exactly this reason (shape gap 0.119 against its own
   0.031: two near-equal-area sherds swapping rank). Parts 0 and 3 here are 1348 and
   1324 points — within 2%. If the model is confusing two interchangeable-looking flaps,
   the failure is an identity problem, not a placement one, and the fix is not more
   training.
3. **Elongated, thin-walled, axially symmetric form.** A narrow bottle split lengthwise
   into two long flaps is close to symmetric under a half-turn about its long axis —
   and part 3 reads **176.6°**. The turn metric cannot separate "correctly placed on a
   symmetric object" from "flipped", but the **displacement** figure can, and it says
   27% of pot size. So this is not the metric being fooled. Whether the *model* is
   fooled by the symmetry is the open question.

## Acceptance criteria

- [ ] Which of the three leads it is — or a fourth — established, not assumed
- [ ] Whether the same failure appears on the other three `narrow_bottle*` objects, which
      share the form but not the deviation
- [ ] A render at individual-sherd placement for whatever is claimed
- [ ] States which of the three: method failed, ruler broken, reference wrong
- [ ] If it turns out to be a general failure mode rather than one object's bad luck, it
      is written back to `O8` and a new question opened; if it is one object, it is
      recorded and closed

## What would make this not worth pursuing

n = 1. One pot out of nine, two standard deviations out, is exactly what a nine-sample
draw from a wide distribution produces sometimes. If leads 1–3 all come back negative and
the other three `narrow_bottle*` objects behave normally, the honest answer is "one
object, unexplained, not a pattern" — and saying that is the result.
