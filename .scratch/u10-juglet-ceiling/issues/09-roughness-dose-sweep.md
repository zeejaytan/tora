# 09: How rough? One strength per training set, rough and worn, five levels each

**What to find out:** Ticket 08 found rough (noise) training beat fresh on the Juglet (median
4 vs 2 solid sherds home, two runs each) and on the erosion ladder, while worn did no better
than fresh. Each of 08's sets mixed two strengths (light and moderate), so it cannot say
which strength helped, and 08 wrote down beforehand that "worn failed because the wear was
too heavy" was a live reading (the corpus's joins were already more open than the Juglet's
at light: contact gap p50 about 0.5% of pot size vs 0.26%). This ticket trains one strength
per set, five strengths per operator, and reads the result as a curve.

**Answers:** O7 (the behavioural box: which augmentation, at what strength, earns its place
on an erosion operator it was not trained on). Reports back to U10's "what that leaves" line.

**Blocked by:** 08 (the operators, the recipe and the fresh baselines it reuses).

**Status:** resolved (2026-10-06). Written back to O7 and U10. Rough replicated; worn retired; read by best attempt; the
conservator has looked at the rough 1× best attempt (see "Witnessed look"). Refute-finding
was not run: the conservator chose to close on the replication in hand (2026-10-06). Conservator chose all ten arms.

## Result in plain words (2026-09-28)

**What was tested.** TORA's placement stage was fine-tuned on training pots whose break
faces had been altered, at one of five strengths each (¼× to 4×; 1× moves the break
surface by about 0.1 mm on a pot the Juglet's size). Two kinds of alteration were tried:
*rough* (break faces jittered, so matching faces no longer fit perfectly) and *worn*
(break faces receded, as wear opens a join). Each was scored against the conservator's
reassembly of the Juglet, the 8 unworn Fractura pots, and the same 8 pots under five
levels of simulated erosion. Every figure is the best of 20 attempts, because the
conservator picks the right attempt by eye.

**What came out.**
- **Rough at 1× is the setting to use.** Its best Juglet attempts put **7 or 8 of the 9
  sherds in their own place** in all four training runs (fresh training: 5). The best
  one, 8 of 9 with only sherd 8 out, is the one the conservator has looked at.
- Rough 2× reaches 8 of 9 as well, but it lowers the model's accuracy on ordinary unworn
  pots more. Rough 4× damages it: it builds a pot-shaped outline out of the wrong sherds.
- **Worn helps no more than fresh training at any strength.** Its best Juglet attempts
  level off at 6 of 9 from 1× upward, and 8× did not change that. Worn is retired as a
  training recipe.
- On the eroded test pots, rough 1× improves on fresh most at the heaviest erosion. On
  unworn pots it changes nothing, so the benefit is about damaged break surfaces.

**Which of the three.** This is a result about the method: changing how it is trained
changes how many sherds it seats. The ruler is the own-place count, checked in ticket
01. The reference is the conservator's reassembly, which is taken as correct.

**Weight.** One real pot. Rough 1× rests on four training runs, the other arms on one or
two. The erosion test is 8 pots under simulated wear from a different wear model. The
improvement is consistent in direction on both instruments. It is not yet shown on a
second real pot.

**What it leaves.** Even the best attempt misses one sherd. In the typical attempt, the
lower body (sherds 4, 5 and the base, 6) is still where placement fails, as in every run
since ticket 08. Rough training narrows the Juglet gap; it does not close it.

**What would change it.** Refute-finding overturning the replication. GARF, given the
same training, showing no change (tested now in `GARF/.scratch/rough-worn-dose/issues/01`),
which would point at a TORA-specific effect. A second real pot on which rough 1× loses
sherds.

**Needs-eye:** before training, one built join per level (both operators) in the same 5 mm
section window as 08 (`artifacts/u10/r08/`), paired with each build's measured break gap.
After, the Juglet median attempt of the best level per operator in visual-qa.

## Levels

The whole light operator scaled by the level: recession 0.15% of the pot's diagonal ×
level, chip radius 0.22% × level, 2 chips. Rough stays RMS-matched to worn at each level.
On a pot the Juglet's size, 1× is about 0.1 mm of recession.

| arm | level | recession (% diagonal) |
|---|---|---|
| worn_d025 / noise_d025 | ¼× | 0.0375 |
| worn_d050 / noise_d050 | ½× | 0.075 |
| worn_d100 / noise_d100 | 1× (= 08's light) | 0.15 |
| worn_d200 / noise_d200 | 2× (= 08's moderate recession; chips 0.44% vs 08's 0.25%, 3 chips there) | 0.30 |
| worn_d400 / noise_d400 | 4× | 0.60 |

Every set: every u10_pooled breakage once, no fresh copy, same vessels and split. 20 passes
(the same steps as 08's arms, about 1750). Seed 42. Ticket 07/08 recipe unchanged: alignment
off, r128, alpha 256, dropout 0.1, last 6 blocks, head frozen, lr 2e-5, `last.ckpt`.
Scored as 08: freshval guard, Juglet and 8 Fractura pots (20 draws), erosion ladder (8 pots
× 5 levels, 20 draws, sign tests per pot-level).

Baselines, not retrained: pooled fresh s42 (31296425) and s7 (31331447).

## Readings, written before any draw

- **The ladder is the main instrument.** Each level vs fresh (both seeds) by sign test over
  40 pot-levels. The Juglet is one pot and two runs of one arm differed by 0.5 sherd, so
  a Juglet difference under 1 sherd between neighbouring levels is no difference.
- **Rises then falls** → the peak is the strength to use. The peak and both neighbours get a
  seed-7 run before anything goes to `intent/`.
- **Flat across levels (every level beats fresh about equally)** → the benefit is breaking
  the perfect fit, not the amount; points to on-the-fly random roughening for the larger
  corpus.
- **Worn at ¼× or ½× beats fresh on the ladder (p < .05) and on the Juglet by ≥ 1 sherd**
  → "08's worn was too heavy" is the reading, and 08's "worn no better than fresh" is
  restricted to 08's strengths.
- **Worn no better than fresh at every level** → worn does not help at any strength tried.
- **Cross-check:** per ladder erosion level (e000–e100), which training strength scores
  best. If heavier test erosion prefers heavier training strength, that is the strongest
  sign the effect is about the break surface.
- **Guard:** an arm whose freshval falls below untouched (.911) or that loses a Fractura
  pot by ≥ 1 sherd is reported as damaging, whatever its Juglet score.

Weight: ten single-seed arms and one real pot. The curve is a lead until the peak is
replicated.

## Acceptance

- [x] Ten builds COMPLETED 0:0, manifest per build: break gap p50, skin max, dropped count
      (2026-09-26: worn 31343118-22, noise 31343123-27, 20-27 min each; table below)
- [x] One join per level rendered in the 5 mm window and looked at before any training
      (`artifacts/u10/r09/sections_{6_7,0_1}.png`)
- [x] Built files linked into `dataset/` only after the render
- [x] Ten training + eval jobs COMPLETED 0:0, strict diff PASS, sacct recorded here
- [x] Ladder scored; table per level, both operators; readings above applied as written
- [x] Peak level (if any) replicated from seed 7 (2026-09-27: 1×, with ½× and 2×)

## Builds (2026-09-26)

885 breakages per set (698 train / 187 val), none dropped, none still touching. RMS is the
break-face points' average move; gap is the median break gap; skin is how far any wall
point moved (median over breakages / worst), all % of the diagonal.

| level | worn rms | worn gap | worn skin | rough rms | rough gap | rough skin |
|---|---|---|---|---|---|---|
| ¼× | 0.0375 | 0.074 | 0 / 0.032 | 0.0375 | 0.018 | 0 / 0 |
| ½× | 0.075 | 0.147 | 0 / 0.068 | 0.075 | 0.033 | 0 / 0 |
| 1× | 0.150 | 0.288 | 0 / 0.144 | 0.150 | 0.058 | 0 / 0 |
| 2× | 0.300 | 0.509 | 0.185 / 0.292 | 0.300 | 0.099 | 0 / 0 |
| 4× | 0.602 | 0.798 | 0.462 / 0.698 | 0.602 | 0.164 | 0 / 0 |

1× reproduces 08's light (worn gap 0.288, rough 0.058). Looked at, join 6/7 and 0/1:
worn opens the join steadily, from barely visible at ¼× to about 1 mm at 4×; from 2× the
larger chips also nick the rim where break meets wall, which is the non-zero skin
column (the corner bevels themselves are recession — see the worn follow-up). Rough roughens the break face; at 2× and 4× it is no longer a plausible surface:
the two faces spike through each other by about 0.5 mm and rim points poke past the wall
line (they are break points, so the skin column does not see them). Read rough 2×-4× as
"shredded", not "rougher".

Training + eval submitted 2026-09-26: worn 31343491-95, noise 31343496-500 (polled).

## Results (2026-09-27)

All ten COMPLETED 0:0 (1:17-1:28), global_step 1760, "Fresh run with random seed 42",
strict diff PASS, no failed step.

**Juglet**, solid own-place over 20 draws (fresh = pooled s42 + s7, 40 draws, median 2, mean
2.67; Mann-Whitney two-sided vs fresh), with freshval (untouched .911):

| level | worn median (mean) | p | worn freshval | rough median (mean) | p | rough freshval |
|---|---|---|---|---|---|---|
| ¼× | 2 (1.70) | .001, **worse** | .946 | 3.5 (3.45) | .06 | .948 |
| ½× | 2 (2.25) | .17 | .947 | 3.5 (3.35) | .05 | .942 |
| 1× | 2 (2.10) | .09 | .948 | **4 (4.10)** | .0003 | .943 |
| 2× | 3 (3.00) | .46 | .948 | 3.5 (3.90) | .01 | .927 |
| 4× | 3.5 (3.30) | .05 | .942 | 2 (2.50) | .46 | **.907** |

Rough: a plateau from ¼× to 2× (3.5-4, no neighbour differs by ≥ 1 sherd), then a collapse
at 4× back to fresh. 1× (= 08's light) is the top and reproduces 08's noise (4). Worn: rises
with strength, ¼× below fresh, 2×-4× at 3-3.5; never significantly above fresh.

Renders `artifacts/u10/t09/j09_{arm}_median.png` (own-place, median attempt), looked at:
rough 1× closed pot, 0/1/3/6 home, 2 and 7 seated in neighbours' places, 4 and 5 off; rough
4× has a pot-shaped silhouette filled with the wrong sherds (6>4, 5>3, 4>5, 2>8; only 0 and 7
home) — the evaluator's count says 6, own place says 2; worn 4× top half home, lower half
unseated and riding high over the true base, the same failure as fresh in 08.

**Guard.** Rough 4× freshval .907 < untouched .911: **damaging**, as pre-registered. Rough 2×
freshval .927 is lowered but above the line. Fractura (solid median of 20, vs fresh s42 / s7):
plate falls 5→4 under worn ½×, worn 1× and rough 4×; fresh's two runs themselves differ by 2
on blue_pot and narrow_bottle3, so a 1-sherd Fractura loss is inside run-to-run spread, but
by the rule as written those three arms trip the guard. Nothing else lost.

| pot | fresh s42/s7 | worn ¼ ½ 1 2 4 | rough ¼ ½ 1 2 4 |
|---|---|---|---|
| blue_pot (5) | 3/5 | 5 5 5 5 5 | 5 5 5 5 5 |
| galli_pot (10) | 7/8 | 7 7 7.5 7 7 | 8 7.5 8 8 8 |
| narrow_bottle1 (12) | 2/3 | 4.5 3 3 3.5 3 | 4 4 3 2 2 |
| narrow_bottle3 (4) | 1/3 | 2 1 1 1 1.5 | 1 1 2.5 2 2 |
| plate (6) | 5/5 | 5 4 4 5 5 | 5 5 5 5 4 |

(narrow_bottle2, narrow_bottle4, pink_bowl: every arm scores the maximum.)

**Erosion ladder** (scored by CPU job 31360212 COMPLETED 0:0, 11:06; its glob missed
31343500, so rough 4× scored by 31360373). Sign tests over 40 pot-levels (ties dropped), vs
fresh s42 | fresh s7; the 32 eroded levels (e025-e100) in brackets:

| arm | vs fresh s42 | vs fresh s7 |
|---|---|---|
| worn ¼× | 8-4 p=.39 [7-3 .34] | 9-4 .27 [8-4 .39] |
| worn ½× | 9-7 .80 [9-6 .61] | 9-6 .61 [8-5 .58] |
| worn 1× | 7-7 1 [7-5 .77] | 7-8 1 [7-7 1] |
| worn 2× | 9-4 .27 [8-3 .23] | 11-7 .48 [10-6 .45] |
| worn 4× | 8-3 .23 [8-3 .23] | 10-6 .45 [9-5 .42] |
| rough ¼× | 14-6 .12 [11-5 .21] | 12-5 .14 [10-5 .30] |
| rough ½× | 8-5 .58 [7-4 .55] | 7-7 1 [6-6 1] |
| rough 1× | **16-5 .027 [14-3 .013]** | **17-6 .035 [16-4 .012]** |
| rough 2× | 15-6 .078 [**14-3 .013**] | 15-7 .13 [**15-4 .019**] |
| rough 4× | **13-3 .021 [12-2 .013]** | 14-5 .064 [**13-3 .021**] |

Cross-check, mean own-place over the 8 pots at each ladder level:

| | e000 | e025 | e050 | e075 | e100 |
|---|---|---|---|---|---|
| fresh s42 / s7 | 4.12 / 4.12 | 4.12 / 4.19 | 3.62 / 3.56 | 3.44 / 3.44 | 2.19 / 2.19 |
| worn ¼× … 4× | 3.88-4.19 | 4.00-4.38 | 3.69-4.00 | 3.25-3.69 | 2.00-2.62 |
| rough ¼× / ½× | 4.56 / 4.12 | 4.19 / 3.88 | 4.19 / 4.00 | 3.62 / 3.56 | 2.25 / 2.50 |
| rough 1× / 2× | 4.12 / 3.81 | 4.00 / 4.12 | 4.44 / 3.94 | 3.75 / 3.81 | **3.44 / 3.38** |
| rough 4× | 4.12 | 4.00 | 4.00 | 3.88 | 3.00 |

Rough 1×-4× gain about 0.8-1.2 sherds per pot at the heaviest ladder erosion and nothing on
unworn pots; lighter rough and every worn level gain little anywhere. Heavier test erosion
prefers the stronger (1×-4×) rough training. Rough ½× (8-5) scoring below ¼× (14-6) is not
a plausible dose effect; read it as the ladder's run-to-run spread (08: two runs of one arm
disagreed 6-9), i.e. neighbouring levels on the ladder are not distinguishable either.

## Readings applied (2026-09-27)

- **Worn no better than fresh at every level** (ladder: no level p < .2 against either
  fresh run; Juglet: ¼× significantly worse, 2×-4× at 3-3.5 not significant). → Worn does
  not help at any strength tried. **"08's worn was too heavy" is refuted**: lighter wear did
  worse on the Juglet, not better, and no worse or better on the ladder.
- **Rough: rises, then falls** — but the fall is on different instruments. Ladder: ¼×-½×
  not significant, 1×-4× significant against at least one fresh run (1× against both).
  Juglet: plateau ¼×-2×, collapse at 4× (2, = fresh; the render shows a pot-shaped
  silhouette built from the wrong sherds). Guard: 4× damaging (freshval .907). **Peak: 1×**
  — the only level significant on the ladder against both fresh runs, top on the Juglet
  (4.1 mean), and clear of the guard.
- **Not flat**: ¼× and ½× do not win the ladder, so "any roughening at all" is not the
  reading; strength matters, with a usable window around 1×-2× and damage at 4×.
- **Cross-check**: the gain sits at the heaviest ladder erosion (e100: 3.0-3.4 vs 2.2) and
  is nil on unworn pots — the effect is about the break surface.
- **Guard**: rough 4× damaging (freshval). Plate 5→4 under worn ½×, worn 1×, rough 4× trips
  the Fractura line as written; inside run-to-run spread, recorded, not acted on.

Weight: one run per level, one real pot, 8 simulated-wear pots. **Replication, as
pre-registered** (peak and both neighbours from seed 7): rough ½× 31360432, 1× 31360433,
2× 31360434 (repo d544f1f; outputs tagged `t08s7`, polled). Nothing goes to `intent/`
before these are in.

## Replication, seed 7 (2026-09-27)

Rough ½× 31360432, 1× 31360433, 2× 31360434: all COMPLETED 0:0 (1:21-1:24), "Fresh run with
random seed 7", STRICT PASS, any step failed 0. Ladder scored by 31366948 COMPLETED 0:0.

| rough | freshval s42 / s7 | Juglet mean s42 / s7 (s7 vs s42) | both runs vs fresh (40 v 40) | ladder s7 vs fresh s42 \| s7 | ladder s7 vs s42 |
|---|---|---|---|---|---|
| ½× | .942 / .941 | 3.35 / 4.10 (p=.15) | 3.73, p=.001 | 11-5 .21 \| 12-8 .50 | 9-7 |
| 1× | .943 / .937 | 4.10 / 3.90 (p=.57) | 4.00, p=.00009 | **16-3 .004 \| 16-3 .004** | 6-9 |
| 2× | .927 / .923 | 3.90 / 4.70 (p=.15) | 4.30, p=.00003 | **14-4 .031** \| 11-3 .057 | 8-9 |

Fractura: nothing lost by any s7 run beyond fresh's own spread (plate ½× s7 4/6, the rest
5/6). Renders `artifacts/u10/t09/j09_noise_d{050,100,200}s7_median.png`, looked at: 2× s7
median has 0/1/2/3/7 home and the lower half (4, 5, base 6) unseated and riding high, the
base tilted out — the same failure place as every rough run since 08.

**Reading.** Replicates. Rough 1× beats fresh on the ladder in all four run pairings (two
rough × two fresh), p ≤ .035 each, and on the Juglet in both runs. 2× beats fresh on the
Juglet in both runs and on the ladder in one pairing of two at p < .05 (the other .057),
with the lowest freshval of the three. ½× helps the Juglet but not the ladder, in either
run. On the Juglet the three are a plateau (no pair of levels differs by ≥ 1 sherd); the
ladder separates them. **The strength to use is rough 1×**: recession-matched RMS 0.15% of
pot diagonal, about 0.1 mm on a Juglet-sized pot. Worn helped at no strength tried; whether
its rise with strength on the Juglet is real is the worn follow-up below.

Next, per the rule: refute-finding before anything is written to O7 / U10; Juglet median
attempt of rough 1× staged in visual-qa for the conservator.

## Worn follow-up (2026-09-27, conservator: "do all 3")

The worn Juglet mean rises with strength (¼× 1.70 → 4× 3.30 sherds; Spearman ρ .45 over
100 draws, but only five training runs), while its ladder stays flat (heavy-erosion means
3.16 / 2.81 / 2.69 / 2.88 / 2.97 vs fresh 2.81). Three tests, readings fixed before any result:

| test | what | jobs |
|---|---|---|
| 1 | seed-7 repeats of worn 2× and 4× | train 31374722, 31374723 (repo f71294a) |
| 2 | worn 8× (`u10_worn_d800`): training gap ≈ 1 mm on the Juglet, notches ≈ 1 mm | build 31374754 |
| 3 | worn 4× recession only, no chips (`u10_worn_d400nc`): is it the gap or the notches? | build 31374755 |

Builds are rendered at a join, in the 5 mm window, **before** they are linked into
`dataset/` or trained on. For scale: the real Juglet gap is about 0.17 mm, and 4× already
trains on about 0.5 mm.

Readings:
- Seed-7 4× falls back to about 2 sherds on the Juglet → the rise was one lucky run; worn
  stays retired.
- 4× holds (≥ 3 sherds) and 8× reaches rough 1×'s level (≈ 4 Juglet sherds **and** a ladder
  win at p < .05 vs both fresh runs) → strong worn is a real alternative to rough, and
  goes to refute-finding beside it.
- Juglet rises but the ladder stays flat → it helps this pot, not worn pottery in general;
  recorded, not adopted.
- No-chips 4× within 0.5 sherd of 4× with chips → it is the gap, not the notches (and the
  reverse if it falls to the ¼×–1× level).

**Builds (2026-09-27).** Both COMPLETED 0:0 (8× 34 min, no-chips 24 min). 885 breakages,
698/187, none dropped, none still touching.

| set | rms | gap | skin (median / worst) |
|---|---|---|---|
| worn 4× (for reference) | 0.602 | 0.798 | 0.462 / 0.698 |
| worn 4× no chips | 0.600 | 0.796 | 0 / 0 |
| worn 8× | 1.205 | 1.350 | 0.855 / 1.597 |

Looked at (`artifacts/u10/r09/sectionsF_{6_7,0_1}.png`, same joins and 5 mm window as the
sweep): 8× opens the join to about 1.5 mm with deeper corners; no-chips 4× is
indistinguishable from 4× at both joins. The chips at 4× are small: on the reference
breakage 8–82 of several thousand vertices per sherd move, at most 0.5 mm
(`chip_s6.png`: a scoop where break meets wall). So the corner bevels seen at 2×–4× in the
sweep sections come from recession, not chips — the "Builds" paragraph above overstated
the chips' part; the skin column is where they show. The no-chips arm therefore asks
whether sub-millimetre notches on a small share of the rim matter, not whether notching
matters in general.

Training submitted 2026-09-27: worn_d800 31375211, worn_d400nc 31375212 (repo 23747c7, polled).

**Test 1, seed-7 repeats (2026-09-27).** Worn 2× 31374722 and 4× 31374723: COMPLETED 0:0
(1:21, 1:20), STRICT PASS, freshval .949 / .940. Ladder scored by 31377064 COMPLETED 0:0.

| worn | Juglet mean s42 / s7 | both vs fresh (40 v 40) | ladder s7 vs fresh s42 \| s7 | ladder s42 vs fresh s42 \| s7 |
|---|---|---|---|---|
| 2× | 3.00 / 3.65 | 3.33, p=.052 | **13-1 .002 \| 15-4 .019** | 9-4 .27 \| 11-7 .48 |
| 4× | 3.30 / 3.40 | 3.35, p=.021 | 8-6 .79 \| 10-9 1 | 8-3 .23 \| 10-6 .45 |

Heavy-erosion (e100) means: fresh 2.19 both runs; 2× 2.44 / 2.31; 4× 2.62 / 2.56. Renders
`j09_worn_d{200,400}s7_median.png`, looked at: top (0, 7, 1) home, lower half (4, 5, base 6)
unseated and riding high or tilted — the failure place of every run since 08.

Applying the readings: 4× did **not** fall back (3.40 on seed 7), so the rise is not one
lucky run. On the Juglet, worn 4× is about two-thirds of a sherd above fresh (p=.021) and
two-thirds below rough 1× (4.00, p=.09). The ladder is flat for 4× in both runs; 2× wins the
ladder in its seed-7 run only (2 of 4 run pairings, against 4 of 4 for rough 1×). Provisional
reading, pending 8× and no-chips: **worn helps this pot a little, not worn pottery in
general**; recorded, not adopted.

**Tests 2 and 3 (2026-09-27).** Worn 8× 31375211 and 4× no-chips 31375212: COMPLETED 0:0
(1:23, 1:19), STRICT PASS, any step failed 0; freshval .928 (8×, lowest worn, still above
untouched .911) and .944. Ladder scored by 31379160 COMPLETED 0:0.

| worn | Juglet mean | vs fresh | vs worn 4× (40) | vs rough 1× (40) | ladder vs fresh s42 \| s7 | e100 mean |
|---|---|---|---|---|---|---|
| 4× (both runs) | 3.35 | .021 | – | .09 | 8-3 .23, 8-6 .79 \| 10-6 .45, 10-9 1 | 2.62 / 2.56 |
| 4× no chips | 2.80 | .49 | .15 | .006 | 9-5 .42 \| 8-4 .39 | 2.31 |
| 8× | 3.15 | .15 | .55 | .041 | 6-9 .61 \| 10-11 1 | 2.44 |

Fractura: nothing lost beyond fresh's spread (plate 4/6 under 8×, 4.5/6 no-chips; 8× gains
one on narrow_bottle1). Renders `j09_worn_{d800,d400nc}_median.png`, looked at: 8× has the top
home and the lower half filled with the wrong sherds (6>4, 4>5; 3 and 8 off) — the
pot-shaped-but-wrong look of rough 4×. No-chips is the one run whose median attempt seats
the base (6) but loses 1, 7, 8 from the upper half; one attempt, not a finding.

**Readings applied (final).**
- Fluke: no — 4× held on seed 7.
- Strong worn a real alternative: **no** — 8× does not rise past 4× (3.15), is below rough
  1× on the Juglet (p=.04), and loses as often as it wins on the ladder.
- Helps this pot, not wear in general: **yes** — worn 4× lifts the Juglet about two-thirds
  of a sherd over fresh in two runs, while its ladder, and 8×'s, stays flat. Recorded, not
  adopted.
- Gap or notches: **inconclusive** — no-chips sits 0.55 sherd below 4× (p=.15), just past
  the 0.5 line and well above the ¼×–1× level. The chips at 4× are too small (≤ 0.5 mm on a
  few dozen vertices per sherd) for this to be a test of notching in general.

**Worn is retired as a training recipe**: its best strength is two-thirds of a sherd behind
rough 1× on the Juglet and never beats fresh on the ladder in 3 of 4 runs at 4×–8×. Rough 1×
stands as the strength to use.

## Read by best attempt (2026-09-28, conservator: "not median, best attempt")

The conservator picks the right attempt by eye, so the best of the 20 is what they get;
median readings above are superseded as the headline (glossary *best-of-N*). Same saved
attempts, no new jobs. Juglet, solid sherds home of 9, one number per training run:

| Arm | Best of 20 (runs) | Attempts reaching it |
|---|---|---|
| fresh | 5, 5 | 1, 4 |
| rough ¼× / ½× | 7 / 6, 7 | 1 / 2, 2 |
| **rough 1×** | **7, 7, 7, 8** | 3, 1, 1, 1 |
| rough 2× | 8, 8 | 1, 1 |
| rough 4× | 6 | 1 |
| worn ¼× / ½× | 3 / 5 | 2 / 1 |
| worn 1× | 6, 6, 4 | 2, 1, 2 |
| worn 2× | 6, 6 | 2, 3 |
| worn 4× | 6, 7 | 1, 1 |
| worn 4× no chips / 8× | 5 / 6 | 1 / 1 |

- Worn plateaus at 6 from 1× up; best does not rise with strength. Retirement stands.
- Rough 1× and 2× tie (7–8 vs 8, 8); 1× stays chosen.
- Fractura best-of-20 is saturated on 6 of 8 pots and does not separate arms.
- Ladder best-of-20 (40 cells, sign test vs fresh s42 | s7): rough 1× 10-1 p=.012 | 11-2
  p=.022 (s42 run; the other three runs lean the same way, n.s.); rough ¼× 12-2 | 12-3;
  no worn arm beats both fresh runs.
- Renders: `artifacts/u10/t09b/jbest_*.png`. Pair `u10_juglet_rough1x_t09` repointed to
  the best attempt (31360433 attempt 8, 8/9, sherd 8 off). Script: `t09_best.py` (scratchpad).

## Witnessed look (2026-09-28)

The conservator looked at `u10_juglet_rough1x_t09` in visual-qa (their reassembly beside
the rough 1× best attempt) and said so in chat: "i have seen the rough best attempt". They
left no note in the viewer (no `annotations_manifest_u10_juglet_rough1x_t09.jsonl`) and gave
no verdict on the "8 of 9 home, only sherd 8 out" reading, so the count stands as measured,
not as confirmed by eye. Their next instruction was to repeat the sweep on GARF.

Not staged: worn's best attempt. The Needs-eye line asked for the best level per
operator, but worn was retired before the look. Stage it if the conservator wants the
worn side seen.

## Follow-ups

- **GARF, same sweep, up to 8×** (conservator, 2026-09-28): `GARF/.scratch/rough-worn-dose/issues/01`,
  same training files and read-out. Rough 8× (`u10_noise_d800`) built for it: job 31449062
  COMPLETED 0:0 (26 min), 698/187, none dropped or still touching, rms 1.205%, skin 0.
  Looked at before linking (`artifacts/u10/r09/sectionsN8_{6_7,0_1}.png`, same joins and
  5 mm window): the break face zig-zags about ±1 mm, as deep as the 2 mm wall is thick, and
  spikes stand up to ~0.7 mm proud of both wall faces at join 6/7. That is the dose doing what
  it says, but past any real sherd edge; it is the far endpoint, not a plausible surface.
  Linked 2026-09-28. **TORA has no rough 8× arm.** Rough 4× already damaged TORA, so an 8× TORA
  run is expected to be worse. Train it only if a side-by-side at 8× is wanted.

## Cost

Builds: ten CPU jobs, about 15–30 min each on 32 CPUs. Training + eval: ten A100 jobs,
about 1.3 h each (13 GPU-hours). Ladder scoring on CPU as 08.
