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

**Status:** replicating the peak (2026-09-27). Conservator chose all ten arms.

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
- [ ] Peak level (if any) replicated from seed 7

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
larger chips also cut the corners where break meets wall, which is the non-zero skin
column. Rough roughens the break face; at 2× and 4× it is no longer a plausible surface:
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

## Cost

Builds: ten CPU jobs, about 15–30 min each on 32 CPUs. Training + eval: ten A100 jobs,
about 1.3 h each (13 GPU-hours). Ladder scoring on CPU as 08.
