# 08: Train the U10 corpus worn: does it give the Juglet back sherd 1?

**What to find out:** Ticket 07's adapters no longer damage placement, but on the Juglet
each costs about one sherd against untouched, and it is always sherd 1 (home 20/20
untouched, 2/20 generic, 0/20 ceiling). Shape family made no difference. The hypothesis
(ticket 07) is that every U10 training break fits perfectly by construction
(`coincident_share` ≈ 1), while the Juglet is real and worn, so the adapter learns to rely
more on a perfect fit. This ticket trains the U10 corpus (generic and Juglet-shaped vessels
pooled) with its break faces worn and asks whether that keeps sherd 1 and seats more of the
Juglet.

**Answers:** O7 (the BEHAVIOURAL box: wear augmentation shown to earn its place, on an
erosion operator it was not trained on, against a cruder augmentation). It also reports
back to U10's "what that leaves" line.

**Blocked by:** 07 (the alignment-off recipe).

**Status:** building (2026-09-25). Conservator chose the arms: pooled corpus, noise kept.

**Needs-eye:** before training, one worn join from the corpus, before/after, in a section
window that resolves 0.1 mm. After, the Juglet median attempt per new arm in visual-qa,
beside `u10_juglet_generic_noalign` and the correct reassembly.

## Why this is a fair test now and was not before

Worn training has been tried twice here (wear v2, wear v3), and both results read as "does
not help". Both trained with TORA's alignment term on. Wear v3 also had the pose head free.
Ticket 06 showed alignment alone makes an adapter lose placement, with wear v3's exact
signature (best at pass 0, then falling). So no fair worn-training run exists yet. The
one piece of evidence the other way: on the erosion ladder, wear made a pot fail by
*swapping* two sherds, while the Juglet *scatters* (`juglet-cause` tickets 09–10, one pot,
weak).

## Arms, fixed before any draw

The conservator's call (2026-09-25): keep the noise comparison, and train on the generic
**and** the Juglet-shaped (ceiling) vessels together: "it's just more pot to teach the
model". Ticket 07 found shape family made no difference, so pooling costs nothing in
interpretation, and it means the fresh arm must be retrained on the pooled corpus.

All arms use ticket 07's recipe unchanged: alignment off, r128, alpha 256, dropout 0.1,
last 6 blocks, head frozen, lr 2e-5, `last.ckpt`. They also use the same vessels and the
same train/val split as `u10_generic.hdf5` + `u10_ceiling.hdf5`. Only the break faces
differ. Every arm trains for the **same step count** (`trainer.max_steps`, set from the
fresh arm's 20 passes), so each arm sees the same number of examples.

- **pooled fresh:** new adapter on both source files as they are.
- **pooled worn:** each breakage stored twice, light and moderate, **no fresh copy**
  (wear v3's change 2: exactly-fitting joins teach lookup). Operator below. Doses are wear
  v3's `WEAR_LEVELS` (`build_bbad_vessel_trainset.py`): light 0.15% of the object's
  bounding-box diagonal + 2 chips, moderate 0.30% + 3 chips. TORA's loader
  (`tora/data/dataset.py`) has no per-pass variant choice, so the variants are separate
  training objects.
- **pooled noise (the cruder baseline O7 asks for):** Gaussian jitter on the same
  break-face vertices, RMS displacement matched per breakage and level to the worn arm's.
  Same two copies, same step count.
- **untouched:** ticket 05's Juglet and ticket-11 ladder baselines stand. Check that it is
  the same model file before reusing.
- **ticket 07's fresh generic** is kept beside as a reference, not as an arm.

## The operator: break faces only, not wear v3's `recede_surface`

Wear v3's operator does not open these joins, so it is not used. It finds the contact band
by distance (2% of the diagonal) and pushes vertices along the sherd's outward direction.
The U10 walls are 1.6–2.5 mm, so that band covers 45–100% of each sherd, and both sides of
a join move together. The wall thins by about 0.25 mm per side while the join stays shut:
the gap left is 0.003–0.02% of the diagonal. Rendered: `artifacts/u10/r08/section_g00_6_7.png`,
`section_g00_0_1.png` (about 5 mm windows; this is **a measurement of the operator on this
corpus**, not a claim about wear v3's own bbad results, which had thicker walls).

In its place, `scripts/write_u10_worn.py` uses **break-face recession**. CSC's corpus stores
an exact per-face break flag (`f{k}_p{i}_break` in `<vessel>_sherds.npz`; per FACE, about 3.5%
of faces). Every vertex of a flagged face moves back along the break face's own smoothed
normal by the dose, then wear v3's dish chips are cut on the same vertices. Prototype on
`generic_train_00` breakage 3, moderate: no vertex still touches a neighbour, the median
gap is 0.39–0.57% of the diagonal (2 × 0.30% at most), and the inner and outer surfaces move
at most 0.06%. Rendered at the same 5 mm window: `section_breakface_6_7.png`,
`section_breakface_0_1.png`. The join opens as a clean gap with both skins in place. Known
flaw: where a break face meets a skin, one triangle (facets are about 1.5–2 mm) makes a
sliver or hook about 0.2–0.3 mm across. It is left in and named.

## The ruler

A gap is measured as **vertex to the nearest surface** of another sherd (exact
point-to-triangle, tested against brute force), not vertex to the nearest vertex, which
carries mesh density. Two numbers, as % of the diagonal, p10/p50/p90:

- **break gap:** flagged break vertices only (U10 files; needs CSC's flags).
- **contact gap:** every vertex within 2% of another sherd. It needs no flags, so it is
  the only one that also runs on the Juglet (`--measure`).

Dry run (2 breakages per source), contact gap:

| | p10 | p50 | p90 |
|---|---|---|---|
| Juglet, `juglet_gt` (real) | 0.03 | 0.26 | 1.33 |
| U10 light | 0.20–0.23 | 0.47–0.59 | 1.67–1.73 |
| U10 moderate | 0.32–0.36 | 0.59–0.60 | 1.69–1.75 |

On this ruler the corpus's joins are **more open than the Juglet's**, even at light. Two
reasons not to re-dose on it: `juglet_gt` is a hand-registered assembly, so its gaps are
partly registration, and which vertices fall inside the 2% cut depends on wall thickness and
scan density. Wear v3's doses are kept as pre-registered. If worn fails, "the dose was too
high" is a live reading, and the light-only copies can be tested against it.

## Readings, written before any draw

Juglet, solid sherds, median of 20 draws (raw beside), sherd-home counts reported:
- **worn beats pooled fresh by 1 sherd or more, and sherd 1 is home in 10+ of 20** →
  the adapter's Juglet cost was the perfect-fit training. Goes to U10 and O8.
- **noise does as well as worn** → the benefit is augmentation in general, not
  wear-shaped. O7's box stays unmet on its second half.
- **worn within 1 sherd of fresh, and sherd 1 still lost** → this wear does not undo the
  cost. The perfect-fit hypothesis is not supported, at this dose. The sherd-1 loss stays
  unexplained; record it as that, not as "wear does not matter".
- **worn beats untouched by 1 or more** → the first fine-tune here that helps the Juglet.
  Name it, weight one pot.

Erosion ladder (`zeroshot/erosion_ceramics`, 8 real Fractura pots × 5 abrasion levels,
20 draws; the operator is GARF's mollifier, which is **not** the training operator, so it
is not circular): per pot and level, worn vs pooled fresh and worn vs noise, as a sign
test. Never pooled. This is O7's box.

Guard: each new arm's practice-vessel curve is reported beside pooled fresh's, ticket 07's generic .974 and
untouched .958. An arm that falls below untouched is named before its Juglet number is
read.

## Results so far

**Pooled fresh (job 31296425, COMPLETED 0:0, 1:20:51).** last.ckpt global_step 1760,
epoch 19 (20 passes × 88 steps, as planned).

Freshval, u10_pooled val set, own place (solid):

| Model | overall | u10_generic | u10_ceiling |
|---|---|---|---|
| untouched (same job) | .911 | .939 | .888 |
| pooled fresh | **.952** | .976 | .932 |

Guard passes: pooled fresh is above untouched on its own kind of pot.

Juglet, 20 draws, solid (raw beside): own place median **2** of 9 (range 1–5; raw 3),
swap-allowed 4 (raw 5), not in own place 22.3% of pot size from home (≈14.5 mm at 65 mm).
Home count per sherd out of 20: `20, 6, 0, 8, 1, 2, 2, 12, 0`. Same as ticket 07's
generic (2) and ceiling (2.5), one below untouched (3). Sherd 1 is again the cost:
untouched seats it 20/20, this arm 6/20.

Fractura, solid median of 20 (untouched / t07 generic / pooled fresh): blue_pot 5 / 5 /
**3**; galli_pot 8 / 7.5 / **7**; narrow_bottle1 2 / 3 / 2; narrow_bottle2 3 / 3 / 3;
narrow_bottle3 1 / 1 / 1; narrow_bottle4 4 / 4 / 4; pink_bowl 3 / 3 / 3; plate 4 / 4 /
**5**. Named: blue_pot −2, galli_pot −1, plate +1. Blue_pot is two-valued: every draw
is 5 or 3 (11 of 20 are 3), and swap-allowed stays 5, so the loss is two sherds trading
places, not sherds thrown away.

Ladder clouds saved (`eval_runs/u10_ladder_pooled_t08_31296425`); scored with worn and
noise together.

**Pooled worn (job 31298231, COMPLETED 0:0, 1:18:28).** global_step 1750, epoch 9 (10
passes × 175; 0.6% fewer steps than fresh). Strict diff PASS (only the 48 adapter
tensors new). Freshval own place (solid): overall **.943**, u10_generic .974,
u10_ceiling .918 — below pooled fresh (.952), above untouched (.911). Guard passes.

Juglet, 20 draws, solid (raw beside): own place median **2** of 9 (range 1–6; raw 3),
swap-allowed 4, not in own place 21.4% of pot size (≈13.9 mm). Home per sherd out of 20:
`20, 4, 4, 4, 2, 3, 3, 16, 0`. Sherd 1 home 4/20.

**Reading that fires:** "worn within 1 sherd of fresh, and sherd 1 still lost" (2 vs 2;
sherd 1 4/20, rule needs 10+). This wear, at this dose, does not undo the adapter's
Juglet cost; the perfect-fit hypothesis is not supported. The sherd-1 loss stays
unexplained. Worn does not beat untouched (2 vs 3). Provisional until noise and the
ladder are in, and the median attempts are looked at.

Fractura, solid median of 20 (untouched / pooled fresh / worn): blue_pot 5 / 3 / **5**;
galli_pot 8 / 7 / 7; narrow_bottle1 2 / 2 / 3; plate 4 / 5 / 5; the other four unchanged
(3, 1, 4, 3). Worn recovers blue_pot's swap; no pot is lost against fresh.

**Pooled noise (job 31298232, COMPLETED 0:0, 1:21:34).** global_step 1750, epoch 9.
Strict diff PASS. Freshval own place (solid): overall **.935**, u10_generic .959,
u10_ceiling .916. Lowest of the three arms, above untouched (.911). Guard passes.

Juglet, 20 draws, solid (raw beside): own place median **4** of 9 (range 2–7; raw 4),
swap-allowed 6, not in own place 17.7% of pot size (≈11.5 mm). Home per sherd out of 20:
`20, 17, 5, 14, 1, 8, 7, 13, 1`. Sherd 1 home 17/20 (untouched 20, fresh 6, worn 4).

Per-draw own place, sorted:

| Arm | 20 draws (solid) | mean |
|---|---|---|
| untouched (31215861) | 2 2 3 3 3 3 3 3 3 3 3 3 3 4 4 4 4 4 4 5 | 3.3 |
| pooled fresh | 1 1 2 2 2 2 2 2 2 2 2 3 3 3 3 3 3 4 4 5 | 2.55 |
| pooled worn | 1 1 2 2 2 2 2 2 2 2 2 2 3 3 3 4 4 5 6 6 | 2.8 |
| pooled noise | 2 2 2 2 3 3 3 4 4 4 4 4 5 5 6 6 6 7 7 7 | 4.3 |

Mann-Whitney over draws (two-sided): noise vs fresh p = .001, vs worn p = .005, vs
untouched p = .07. These are draws from ONE trained adapter per arm; they say nothing
about how much a second training run of the same arm would differ.

Looked at (`artifacts/u10/t08/j08_{pooled,worn,noise}_median.png`, own-place render,
middle attempt): noise's middle attempt is one closed pot inside the true outline, its
errors lower-body look-alikes seated in each other's places (7>2, 6>4, 2>3); fresh's
middle attempt has sherds 3 and 8 standing outside the pot.

**Readings.** Worn: "within 1 of fresh, sherd 1 still lost" (above). Noise: not
pre-registered as written — the rule anticipated noise *matching* worn, and noise beats
both. Nearest honest reading: whatever helps here is not wear-shaped; rough,
non-matching break faces help, directional recession does not. O7's box (wear-shaped
benefit) stays unmet. Noise is the first fine-tune here that does not lose sherd 1,
and its Juglet median is one above untouched — which would fire "beats untouched by 1
or more" if it were the worn arm; named here, weight one pot and one training run.

Fractura (untouched / fresh / worn / noise): blue_pot 5/3/5/5; galli_pot 8/7/7/7.5;
narrow_bottle1 2/2/3/3.5; plate 4/5/5/**6**; other four unchanged. Noise loses nothing
against fresh or worn.

**Erosion ladder** (scored by CPU job 31301455, COMPLETED; `own_place.py` on each arm's
20 draws; `artifacts/u10/t08/ladder_{pooled,worn,noise}.json`). Solid own-place median
per pot and level, fresh / worn / noise (e000 = unworn, e100 = heaviest):

| Pot (sherds) | e000 | e025 | e050 | e075 | e100 |
|---|---|---|---|---|---|
| blue_pot (5) | 5/5/5 | 5/5/5 | 4/5/4 | 5/5/5 | 2.5/3/3 |
| galli_pot (10) | 8/8/7 | 8/8.5/9 | 7/8/8 | 8/8/8 | 4/**2**/**5** |
| narrow_bottle1 (12) | 3/5/3 | 4/3/3 | 3/3/3 | 1.5/2/2 | 1/2/2 |
| narrow_bottle2 (3) | 3/3/3 | 3/3/3 | 3/3/3 | 3/3/3 | 2/2/3 |
| narrow_bottle3 (4) | 2/1/1 | 1/2/2.5 | 1/1/1 | 1/1/2.5 | 1/1/2 |
| narrow_bottle4 (4) | 4/4/4 | 4/4/4 | 4/4/4 | 4/4/4 | 4/4/4 |
| pink_bowl (3) | 3/3/3 | 3/3/3 | 2/2/2 | 2/2/2 | 1/2/2 |
| plate (6) | 5/5/6 | 5/5/5.5 | 5/5/5 | 3/2/**5** | 2/1/3 |

Sign tests over the 40 pot-levels (ties dropped), and over the 32 worn levels only:
- worn vs fresh: 9 wins, 5 losses (p = .42); worn levels 8–4. **Not a wear-shaped
  benefit.** O7's box stays unmet.
- worn vs noise: 3–10 (p = .09); worn levels 1–9. Noise beats worn.
- noise vs fresh: 15–3 (p = .008); worn levels **14–1**. Noise's gains sit on the
  heavier levels (plate e075 3→5, galli e100 4→5).

The ladder's wear is GARF's mollifier, not either training operator, so this is a second
instrument that agrees with the Juglet: roughened faces help, receded faces do not. Same
caveat: every cell of an arm is the same one trained adapter. The untouched model's
ladder (ticket 11) was scored with a different ruler and is not put beside this.

**Replication, before anything goes to `intent/`** (conservator, 2026-09-25): worn and
noise retrained from seed 7 (the first runs used train.yaml's 42), same recipe and steps,
evaluated the same way; outputs tagged `t08s7`. Jobs worn 31307630, noise 31307631
(repo 36d3780). The noise finding goes to O7/U10 only if noise again beats worn on the
Juglet and the ladder. Fresh has one run too; retrain it if noise's lead holds, since
fresh's single run could be a low draw.

*Result (2026-09-26; both COMPLETED 0:0, 1:19 each, global_step 1750, strict diff PASS,
train log "Fresh run with random seed 7"; ladder scored by CPU job 31331261 COMPLETED 0:0).*

| | freshval | Juglet solid median (range) | sherd 1 home | Juglet vs worn s7 |
|---|---|---|---|---|
| worn s42 | .943 | 2 (1–6) | 4/20 | p = .29 |
| worn s7 | .945 | 2 (1–6) | 2/20 | — |
| noise s42 | .935 | 4 (2–7) | 17/20 | p = .0006 |
| noise s7 | .929 | **4.5** (2–7) | 17/20 | **p = .0001** |

Noise s7 vs fresh p = .0001; noise s7 vs noise s42 p = .82; worn s7 vs worn s42 p = .29.
**The Juglet result replicates**: the two noise runs are indistinguishable from each other and
both beat both worn runs. Renders `artifacts/u10/t08/j08_{noise,worn}s7_median.png`
(ranked on raw): noise s7 is a closed pot, 6 of 9 home, errors confined to the lower-left
wall (3, 4 off; 8 in 2's place); worn s7 has the lower half unseated and sherd 8 outside
the pot beside the handle. Same picture as seed 42.

Fractura: nothing lost by either; plate noise s7 5/6 (s42 6/6), worn s7 4/6 (s42 5/6).

Ladder, seed 7 (sign tests over 40 pot-levels; worn levels only in brackets):
- noise s7 vs fresh: 13–3, p = .02 (11–3, p = .06). **Replicates** in direction and size.
- noise s7 vs worn s7: 10–6, p = .45 (8–4, p = .39). **Does not replicate** at
  significance (s42 was 3–10 the other way round, i.e. noise ahead, p = .09).
- worn s7 vs fresh: 10–6, p = .45. As before, no wear-shaped benefit.
- run-to-run: noise s7 vs s42 6–9; worn s7 vs s42 6–7. On the ladder, two runs of the
  same arm disagree about as often as noise and worn do.

**Against the rule written before the rerun**: noise again beats worn on the Juglet (yes,
strongly) and on the ladder (direction yes, significance no). So the rule is half met.
What stands: on the Juglet, roughened break faces beat both receded faces and fresh faces,
across two training runs each; on the ladder, noise beats fresh across two runs. What does
not stand: noise beating worn on the ladder. Fresh still has one run.

## Acceptance

- [x] Worn and noise files built. The share of break-face vertices identical to a
      neighbour's falls from ≈1 to 0. Break and contact gaps (surface ruler) reported, the
      Juglet beside. Loader keeps every object. Not trusted until a built join is rendered.
      (2026-09-25: worn job 31296315 COMPLETED 0:0, 30:12; noise job 31296316 COMPLETED 0:0,
      43:12. 885 breakages per level, none dropped, none still touching. Loader admits
      train 1396, val 374, 3-36 sherds. Size label 0.4993 worn, 0.5037 noise, Juglet 0.5115.
      Break gap, median of per-breakage p50, % diagonal: worn light 0.288, moderate 0.509;
      noise light 0.058, moderate 0.099. Contact p50: worn 0.535 / 0.599, noise 0.454 /
      0.446. Juglet contact p10/p50/p90 0.033 / 0.259 / 1.334. Worn skin moves p99 0.15%,
      i.e. chips only; noise skin 0. Noise's break gap is a fifth of worn's at equal RMS
      because random jitter crosses the faces into each other, where recession opens
      them: noise is "rough faces, same displacement", not "a gap". Files:
      `TORA/work/u10_worn_{worn_31296315,noise_31296316}/`, linked into `dataset/`.)
- [x] Rendered before training: one join, fresh / worn, 5 mm window (prototype, 2026-09-25).
      Built files, same join (generic_train_00 fractured_3, sherds 6/7, moderate):
      `artifacts/u10/r08/built_{worn,noise}_6_7.png`. Worn is identical to the prototype;
      noise is a jagged, interpenetrating face with the walls untouched.
- [ ] Three adapters (pooled fresh, worn, noise) trained. Alignment logs 0. Strict diff passes. Curves reported.
- [ ] Juglet: 20 draws per arm, own place, sherd-home counts, readings applied.
- [ ] Ladder per pot and level, sign tests, readings applied.
- [ ] Viewer pairs staged; conservator's look.
- [ ] Weight stated. Which of the three kinds named. Written back to O7 (and U10/O8 if
      the first reading fires).
- [ ] Every `sbatch` has a laptop poll; sacct State/ExitCode recorded here.
      Builds 31296315, 31296316: COMPLETED 0:0. Training + eval: pooled 31296425, worn
      31298231, noise 31298232 (running / queued 2026-09-25). Pooled 31296425: COMPLETED 0:0. Worn 31298231: COMPLETED 0:0. Noise 31298232: COMPLETED 0:0. Ladder scoring
      (CPU) 31301455. Seed-7 replication: worn 31307630, noise 31307631 (submitted
      2026-09-25, polled).

## Cost (estimate)

Build: two CPU jobs (worn, noise), about 1 h each on 32 CPUs (dry run: about 2 min per breakage per worker). Training: three arms at the pooled step count, about 1 h each (twice ticket 07's corpus, if max_steps is set by 20 passes over it).
Juglet: about 5 min per arm. Ladder: about 50 min for 3 arms (job 30337242). Total about
4 A100-hours.
