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

**Status:** building (2026-09-26). Conservator chose all ten arms.

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
- [ ] Ten training + eval jobs COMPLETED 0:0, strict diff PASS, sacct recorded here
- [ ] Ladder scored; table per level, both operators; readings above applied as written
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

## Cost

Builds: ten CPU jobs, about 15–30 min each on 32 CPUs. Training + eval: ten A100 jobs,
about 1.3 h each (13 GPU-hours). Ladder scoring on CPU as 08.
