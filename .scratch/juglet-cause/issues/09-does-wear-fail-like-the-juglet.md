# 09: Does abrasion make a pot fail the way the Juglet fails?

**Type:** `wayfinder:research` (AFK)
**What to build:** The behavioural bridge the map has been missing — a test of whether
wear, applied to pots we control, produces the *kind* of failure the Juglet is having,
using no scan finer than the ones we already have.

**Answers:** O8

**Blocked by:** None. Job 30190268's clouds are on Spartan (36 MB, ten attempts per
variant). No GPU, no queue.

**Status:** resolved 2026-09-09 -- **wear produced an EXCHANGE, not a scattering.** The opposite of the Juglet, on n = 1 usable object. No GPU: laptop analysis of clouds already computed.

## Why it exists

The map is reopened on one gap: wear demonstrably breaks reassembly **on pots we
abraded ourselves**, and nothing carries that to this vessel, because the Juglet's own
wear cannot be seen at the resolution it was scanned (Gate A, job 29404479). Route **(a)**
is a better capture and is not compute. Route **(c)** is to declare it unattributable.
This ticket is route **(b)**: ask whether the Juglet's failure has the *shape* that wear
produces where we control it.

Three results make the question sharp rather than vague:

- **The Juglet fails by scattering** — its sherds are genuinely in the wrong places, and
  the best renaming of them is a *different* one in 16–17 of every 20 attempts (ticket 08).
- **`narrow_bottle3` fails by exchange** — pieces roughly in the right places wearing the
  wrong names, the *same* renaming 10 times in 10 (ticket 07).
- **On a fresh break the edges carry the answer.** Put `narrow_bottle3`'s two halves in
  each other's places and settle them as tightly as they will go, and the joins still
  stand 3–6 mm open on a 100 mm bottle where the true assembly closes to about a tenth of
  a millimetre (`.scratch/perception-or-placement/issues/01`).

So the intuitive account of wear — abrasion eats the break edges, the model can no longer
tell one sherd from another — is a **discrimination** story, and a discrimination failure
is an **exchange**. The Juglet is not doing that.

## The prediction, written before the result

**If wear works the way the intuitive account says**, then as abrasion rises the failures
on the erosion ladder should drift towards **exchange**: the winning renaming should start
repeating across draws, and it should rescue the assembly when it wins.

**If instead wear produces scattering**, the Juglet's failure has the shape wear produces,
and route (b) has carried something across the bridge without a finer scan.

**Both outcomes are results and they point opposite ways.** The second is evidence *for*
wear on this object; the first is the strongest argument yet for taking wear off the list
for the Juglet, arrived at by the test that could have gone the other way.

I expect **neither cleanly** — most likely the ladder degrades into scattering, because
the erosion operator removes material from both mating faces rather than making two
sherds resemble each other. Recording that expectation so it can be wrong.

## The analysis rule, fixed in advance

**Read the low and middle rungs, not `e100`.** At the heaviest wear the pots collapse so
completely that "scattering" is what the instrument must report — once nothing is placed,
no renaming can rescue anything, and the reading would be trivially true. The signature
has to be taken where seating is still partly intact.

**The control is each pot's own `e000` rung**, same pot, same pieces, same correct answer,
zero abrasion. On the pots TORA assembles the instrument must pick the identity naming
outright there; if it does not, the instrument is wrong on this data and the ticket stops.

**Use the baseline arm.** `wear_v1` and `wear_v2` carry their own regression — `galli_pot`
loses 21–40 points at *zero* wear under `wear_v2`, which is capability lost in finetuning
and not a wear effect (`WEAR_TEST_RESULTS.md` §4). The baseline reproduces `galli_pot`
e000–e075 nearly perfectly and is the clean instrument here.

**`limb3` and `coxae` carry no signal** — `limb3` sits at 1.000 throughout and `coxae` at
about zero for every model at every rung. They are reported and excluded from the reading.

## What to do

1. Fetch `wearft2_sweep_baseline_30190268/clouds` (30 variants = 6 pots × 5 rungs, ten
   draws each) to `artifacts/wearsig/`.
2. Confirm the control: at `e000`, the identity naming wins on the pots this model
   assembles. If it does not, stop and report that.
3. Per pot per rung, report the same four numbers ticket 08 reported for the Juglet:
   worst loose sherd under the evaluator's naming, worst under the best renaming, how many
   *distinct* renamings win across the ten draws, and whether identity ever wins.
4. Read the trend up the ladder against the pot's own `e000`, on the low and middle rungs.
5. Render individual sherd placement for the clearest case at both ends of the ladder —
   whole-pot outline is not admissible on this material (`artifacts/juglet_spread.png`).
6. Compare the resulting signature with the Juglet's, and say which it is.

## Acceptance criteria

- [x] The `e000` control is reported first, and the test proceeds only if it holds
- [x] Every pot × rung reported, including the ones with no signal, not only the ones
      that move
- [x] Distinct-renaming counts reported, not just the median draw — that is the number
      that separates an exchange from a scattering
- [x] A render at individual-sherd placement, at both ends of the ladder
- [x] States which of the three: method failed, ruler broken, reference wrong
- [x] States how much weight it can bear — pot count, draw count, and whether the
      six-pot sweep can carry a claim about one excavated juglet
- [x] Written back to `O8` and to the map either way, including "the signature does not
      separate", which would be a real answer

## What would make this not worth pursuing

If at `e000` the instrument already reports scattering on pots the baseline assembles
correctly, there is no signature to track up the ladder and the test is dead on arrival.
That is what step 2 checks before anything is built.

---

## Answer (2026-09-09)

**Abrasion made a pot fail — but it failed the *opposite* way to the Juglet.** On the one
object in this sweep that goes from correctly assembled to broken as its break surfaces
are worn down, the model keeps building the pot and swaps two pieces' names. That is an
**exchange**. The Juglet **scatters**. So this test did not carry wear across the bridge;
if anything it points the other way — and it rests on one object, which is a lead, not a
finding.

**My recorded prediction was wrong**, and it is worth saying so plainly: I wrote before
looking that the ladder would most likely degrade into scattering, on the reasoning that
the erosion operator eats both mating faces rather than making two sherds resemble each
other. It did not. `blue_pot` produced a clean exchange at light wear.

### The control, reported first

At zero abrasion the instrument must pick the true naming outright on the pots this model
assembles, or there is no signature to track up the ladder. It does:

| object | assembled at `e000`? | true naming wins? |
|---|---|---|
| `blue_pot` | yes — worst loose sherd **4.0%** of pot size | **yes** |
| `limb3` | yes — **2.8%** | **yes** |
| `vert9` | no — 11.9% | true naming still wins, 9 of 10 |
| `coxae` | no — 25.7% | no |
| `galli_pot` | no — 45.6% | no |
| `plate` | no — 54.8% | no |

**The control holds.** But look at what it costs: **five of the six objects are already
broken before any wear is applied**, so they cannot show a wear-induced transition at all.
`limb3` is immune — 2.5–3.0% at every rung, true naming 10 of 10 throughout. That leaves
exactly **one informative object**. This limitation is larger than the result.

### The one informative ladder: `blue_pot`

Same pot, same five pieces, same correct answer at every rung; only the break surfaces are
abraded. Worst loose sherd as a percent of the pot's own size, median of ten attempts —
2–3% is a correct assembly:

| wear | as the evaluator names the pieces | if the pieces may swap names | the swap that wins | how often |
|---|---|---|---|---|
| none (`e000`) | **4.0%** | 3.9% | *(the true naming)* | 8/10 |
| light (`e025`) | **14.2%** | **4.0%** | pieces 0 and 3 exchanged | **9/10** |
| moderate (`e050`) | 9.9% | 5.3% | pieces 0 and 3 exchanged | 6/10 |
| heavy (`e075`) | 70.1% | 37.7% | a four-piece cycle | 0/10 |

At light wear the pot is still **built** — nearly everything is where it belongs — and two
small shoulder chips have been given each other's names. Correcting that one swap takes
the worst loose piece from 14.2% back to 4.0%, which is where the unworn pot sits. At heavy
wear the exchange is gone and the pot has genuinely collapsed; no renaming rescues it
(37.7%).

**It is not an artefact of the matcher.** The 0↔3 exchange count is 2 / 9 / 6 / 0 out of
ten at `e000` / `e025` / `e050` / `e075`, and is **identical for random seeds 0–4** — the
sub-sampling inside the matcher does not move it at all.

**The same mechanism as `narrow_bottle3`, a very different consequence.** In both cases the
pair that exchanges is the object's own closest-matching pair of pieces (PCA-aligned
chamfer, percent of object size):

| | the exchanging pair | next most alike pair |
|---|---|---|
| `blue_pot` | 0↔3 at **1.78%** | 2.78% |
| `narrow_bottle3` | 0↔3 at **2.17%** | 4.05% |

*(Ticket 07 quotes 3.1% for `narrow_bottle3` from a different implementation of the same
idea. The ordering agrees; the absolute figures are not comparable and should not be quoted
across the two.)*

But `narrow_bottle3`'s exchanging pieces are the **two halves of the vessel** — 53.5% of
it. `blue_pot`'s are two chips off the shoulder, **2.1% and 2.6% of the pot's points**,
each about a quarter of the pot's own size across. Both are real failures; only one of them
would be visible to a conservator looking at the reassembled object.

### The confound, measured rather than argued

"The same renaming won again" is not comparable between pots, because a three-piece object
has six possible renamings and a ten-piece one has 3.6 million. Across all thirty variants:

| pieces | possible renamings | median agreement across ten attempts |
|---|---|---|
| 3 (`coxae`, `limb3`, `vert9`) | 6 | 8/10 |
| 5 (`blue_pot`) | 120 | 7/10 |
| 6 (`plate`) | 720 | 4/10 |
| 10 (`galli_pot`) | 3,628,800 | 3/10 |

**r = −0.81.** So a cross-pot "this one repeats, therefore it is an exchange" reading is
partly just counting pieces — `coxae`'s and `vert9`'s "EXCHANGE-like" rows in the printed
table are exactly that artefact and must not be read as exchanges.
`scripts/check_wear_failure_shape.py` now prints this block itself and states the reading
**per object, up its own ladder**, where the piece count is constant and only the wear
changes. Where a rule is checkable, it was made a check.

### Which of the three

**On `blue_pot`: the method genuinely failed.** The pot's own unworn rung is the control
and it holds; the correct answer is identical at every rung by construction; the matcher's
result is seed-stable. Light abrasion made the model mis-name two pieces it had named
correctly when they were fresh.

**On this ticket's own question: nothing failed — the test is underpowered.** The
instrument works and the control holds, but the sweep does not contain enough objects this
model can assemble unworn to say whether wear generally produces exchange or scattering.

### How much weight this can bear

**Very little on its own.** One object with a usable control, ten attempts, one
architecture, one erosion operator (GARF's `erode_fracture_band`, which is a simulation and
not the same process as burial and abrasion in the ground). "The signature does not
separate" was named in advance as a real possible answer, and this is close to it: the
sweep produced one exchange and no clean counter-example either way.

What it does establish, for the object it concerns: **abrasion of break surfaces can
produce an exchange**, so the intuitive account of wear as a discrimination failure is not
wrong in principle. It simply is not what the Juglet is doing.

**What would change the answer:** an erosion ladder built on objects TORA assembles
correctly when they are unworn. Five of the six here were already broken before the
experiment started, which is a selection problem in the sweep, not in the analysis. The
analysis side is free; the sweep would need one evaluation pass on a GPU. That is the
obvious follow-up if `O8` is to be pushed further along route (b).

### What it means for `O8`

Route (b) has been run and it does **not** attribute the Juglet's failure to wear. The
Juglet scatters; the one object here that wear breaks, exchanges. That is weak evidence
*against* wear as the cause, on n = 1, and it leaves `O8` where the map put it: either a
capture that resolves the wear (route **a**, `O7`, conservation-lab work) or stating that
the failure cannot be attributed with the data that exists (route **c**).

### Where the work is

- `scripts/check_wear_failure_shape.py` — the instrument; control and confound are printed
  by the script itself
- `artifacts/wearsig/` (gitignored) — 30 clouds fetched from
  `spartan:/data/gpfs/projects/punim2657/TORA/eval_runs/wearft2_sweep_baseline_30190268/clouds/`
- `artifacts/wearsig/blue_pot_e000.png` — the control: all three rows agree
- `artifacts/wearsig/blue_pot_e025.png` — the exchange: rows 1 and 3 agree, row 2 has the
  two chips traded, and the rest of the pot is correctly assembled
- `artifacts/wearsig/blue_pot_e075.png` — the collapse: row 3 no longer recovers row 1
- `artifacts/wearsig/vert9_e075.png` — the other pattern, on an object that was never
  assembled: rows 2 and 3 are the same picture, so no renaming helps
