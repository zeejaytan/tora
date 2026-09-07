# 07: Why does `narrow_bottle3` collapse? Fresh, unworn, four fragments

**Type:** `wayfinder:research` (AFK)
**What to build:** An explanation for the largest unexplained reassembly failure in the
corpus — a **freshly broken, unworn, four-fragment** bottle that TORA tears into two
flaps, four times further off the fragment-count trend than the worn Juglet is.

**Answers:** O8

**Blocked by:** None. 05 closed the wear question and explicitly ruled this out of it.

**Status:** resolved 2026-09-07 — lead 2, by a different mechanism than the one stated.
No GPU bought; everything below is from job 30167044's saved clouds.

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

- [x] Which of the three leads it is — or a fourth — established, not assumed
- [x] Whether the same failure appears on the other three `narrow_bottle*` objects, which
      share the form but not the deviation
- [x] A render at individual-sherd placement for whatever is claimed
- [x] States which of the three: method failed, ruler broken, reference wrong
- [x] If it turns out to be a general failure mode rather than one object's bad luck, it
      is written back to `O8` and a new question opened; if it is one object, it is
      recorded and closed

## What would make this not worth pursuing

n = 1. One pot out of nine, two standard deviations out, is exactly what a nine-sample
draw from a wide distribution produces sometimes. If leads 1–3 all come back negative and
the other three `narrow_bottle*` objects behave normally, the honest answer is "one
object, unexplained, not a pattern" — and saying that is the result.

---

## Answer (2026-09-07)

**The model does not scatter this bottle. It builds the bottle and then puts the two
halves on the wrong sides of it.** Sherd 0 is placed where sherd 3 belongs and sherd 3
where sherd 0 belongs — the same exchange, in **all ten** of its ten attempts. That is
lead 2, the identity reading. But the ticket's own reason for suspecting lead 2 was
wrong, and the exchange accounts for about two thirds of the failure, not all of it.

**Which of the three: the method genuinely failed.** Not the ruler — the displacement
figure reports 26% and the picture shows 26%, and the same ruler measures the exchange.
Not the reference either, and that mattered enough to test: if the two flaps were truly
interchangeable, the exchanged assembly would be a perfectly good bottle and the answer
key would be arbitrary. It is not. Put the names the right way round and the worst loose
sherd still sits **8.1% of the pot's size from home** — about 8 mm on a 100 mm bottle,
against **2.4–3.3%** for the pots this model assembles correctly. The seam down the
middle stays open. The render shows it in row 3.

### How it was established

`scripts/check_identity_swap.py` scores every predicted sherd against **every**
ground-truth sherd rather than only against its own, then asks whether any renaming of
the pieces beats the naming the evaluator uses (Hungarian assignment on the cost matrix).
The per-sherd figure is `worst_sherd`'s exactly — symmetric chamfer in the unit-box frame,
`100*sqrt(c/2)`, anchor excluded from the reported worst but kept in the assignment.

The corpus splits three ways, and the split is the substance of this answer:

| | worst loose sherd, as scored | best renaming | same renaming | what it is |
|---|---|---|---|---|
| `narrow_bottle4` | 2.4% | 2.4% | identity wins | assembled correctly |
| `narrow_bottle2` | 2.8% | 2.8% | identity wins | assembled correctly |
| `pink_bowl` | 3.3% | 3.3% | identity wins | assembled correctly |
| `blue_pot` | 4.1% | 4.1% | identity wins | assembled correctly |
| **`narrow_bottle3`** | **26.2%** | **8.1%** | **10/10 draws** | **one exchange, 0 ↔ 3** |
| `plate` | 38.0% | 21.9% | 5/10, then 4/10 | scattered, repeated flavour |
| `galli_pot` | 44.3% | 20.7% | 8 different perms | scattered |
| `narrow_bottle1` | 73.6% | 21.0% | 9 different perms | scattered |

**The control is the four pots at the top.** On every one of them the Hungarian match
picks the identity assignment outright — no renaming beats it. So a non-identity match is
not something this test hands out for free, and `narrow_bottle3` picking the *same*
non-identity match ten times out of ten is not the algorithm shuffling noise.

**`narrow_bottle3` is the only clean exchange in the corpus.** On `plate`, `galli_pot`
and `narrow_bottle1` renaming does lower the worst sherd, but to 21% — still seven times
a correct assembly — and the winning permutation changes from attempt to attempt. Those
are genuine scatterings. Only `narrow_bottle3` has one repeated two-piece exchange with a
near-seated result behind it.

### Lead by lead

**Lead 1, piece-size imbalance: dead.** `narrow_bottle3`'s largest-to-smallest ratio is
20. `blue_pot` is 28, `plate` is 32, `galli_pot` is 21 — and `blue_pot` assembles
correctly. Size imbalance does not separate the failing pot from the working ones.

**Lead 2, two near-equal pieces swapping identity: confirmed as the mechanism, refuted
as stated.** The ticket's evidence was point count — parts 0 and 3 within 2%. Point count
predicts nothing: `galli_pot` has a 303/304-point pair and assembles those two correctly.
What is true is the thing the point count was standing in for, and it had to be measured
directly rather than inferred.

**Lead 3, the elongated symmetric form: the enabling condition, not the cause.** Compared
as bare shapes — each sherd centred, principal axes aligned, best of the proper sign
flips — the two flaps are **3.1% of pot size apart**, the closest pair in that bottle.
But shape similarity alone does not predict failure either: `blue_pot` has a 1.8% pair,
`galli_pot` 1.6%, `narrow_bottle1` 1.5%, and those pots do better. What is distinctive is
that `narrow_bottle3`'s look-alike pair is **53% of the whole vessel**. Everywhere else
the near-duplicates are slivers — `blue_pot`'s 1.8% pair is 4.8% of the pot — and
exchanging two slivers barely moves anything, while the rest of the vessel still pins them
down. Here the two near-duplicates *are* the vessel, with only a 111-point sliver and the
anchor left to tell them apart.

`narrow_bottle3` is the extreme of that combination in this corpus but not a category of
its own: `plate` has a 2.6% pair at 42.5% of the vessel and does show a repeated
non-identity match, just not a clean one. It is a graded risk, not a threshold.

### The sibling bottles: no, they do not do this

Asked because the form is shared and the scores are not
(`artifacts/nb3/narrow_bottle_family.png`):

- `narrow_bottle2` (3 sherds) and `narrow_bottle4` (4 sherds) — **assembled correctly**,
  2.8% and 2.4%, identity wins, indistinguishable from their references by eye.
- `narrow_bottle1` (12 sherds) — **fails, but differently**: 73.6%, a different renaming
  every attempt, pieces flung below and outside the vessel. Scattering, not exchange.
- `narrow_bottle3` — the exchange.

So the narrow-bottle form is not sufficient to cause it. Two of the four are among the
best-assembled objects in the corpus.

### Renders

- `artifacts/nb3/narrow_bottle3_identity_swap.png` — three rows: the bottle as it really
  is; the model's answer coloured by the name the model gave each piece (red and blue on
  the wrong sides); the same points recoloured by where each piece actually landed (red
  and blue back on the reference's sides, seam still open). The third row moves no
  geometry — it is a recolouring, which is what makes it evidence about naming rather
  than about placement.
- `artifacts/nb3/narrow_bottle_family.png` — the four `narrow_bottle*` objects, true
  assembly above the model's answer.

### How much weight this can bear

**The exchange itself is solid; the generalisation is not.** Ten of ten attempts on one
object, with four control pots on which the same test declines to find any exchange at
all — so within this run it is not chance. But it is **one object out of eight**, and the
"look-alike pieces that are most of the vessel" rule that explains it is fitted to eight
points with one extreme. It predicts, it has not been tested. Confirming it needs objects
built to have that property, not found to have it.

**What it does not touch:** the Juglet. This is a fresh, unworn bottle, and nothing here
transfers to O8's five other candidates.

### What it means for the work

**A reassembly can fail in two ways that every metric we currently report conflates.**
Sherds seated, turn and distance-from-home all say "wrong" identically whether the model
scattered the pieces or exchanged two of them, and those call for opposite responses:
scattering is a placement problem where more or better training is the lever, exchange is
a naming problem where it is not. `scripts/check_identity_swap.py` separates them for
free from clouds already on disk.

That distinction is worth more than this bottle. On the material this project is actually
about — plain body sherds with no rim, no profile and no decoration — near-duplicate
pieces are the normal case rather than the exception, so the exchange failure is the one
that should be expected to grow with real assemblages, and it now has an instrument.

It also gives ticket 04's unexplained refusal a probable name: `plate` is thrown out by
the shape gate at every fragment-drop rank for "two near-equal-area sherds swapping
rank", and `plate` is the one other pot here with a repeated non-identity match. Two
instruments, built for different purposes, pointing at the same pair of sherds. Not
proven — `plate`'s renaming does not rescue it — but worth recording.

**Recorded and closed as one object.** No new question is opened: the corpus does not
support a general claim yet, and O8 is answered. What is written back to O8 is the
narrower fact that the object's failure now has a name and a mechanism.
