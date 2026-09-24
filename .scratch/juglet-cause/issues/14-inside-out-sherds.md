# 14: Does TORA put sherds down inside out, and can "outside faces out" catch it without the answer key?

**Type:** `wayfinder:research` (AFK)

**What to build:** `scripts/check_inside_out.py`. For every sherd in every saved attempt it
reads two things:

- **Answer-key label:** is the sherd turned inside out relative to its true pose?
- **Answer-key-free rule:** does the sherd's hollow side face into the assembled pot? The
  sherd's own curvature centre must lie on the pot's side of the sherd.

It then asks three questions: does the rule agree with the label; do attempts with fewer
inside-out sherds really place more sherds home; and does turning a flagged sherd back the
right way out put it home?

**Answers:** O8, U1

**Blocked by:** None. No GPU, no fetch, no Slurm: every input is already under `artifacts/`.

**Status:** done (rule and scoring); conservator's look on `insideout_rulepick` pending

**Needs-eye:** the conservator saw it first (orange sherd 4, pair `twoheld_best`,
2026-09-24). Whether a corrected sherd now sits right closes on a look, not on numbers.

## Why

The conservator saw sherd 4 in the best two-held attempt sitting inside out, and noted
that this is physically impossible: the outer face is convex and the inner face concave,
so a sherd turned over cannot lie in the wall. A quick check (2026-09-24) found:

- On the Juglet two-held job 30919372, 78 sherds counted "home" were turned 120-180°.
  The turn angles have nothing between 60° and 120°.
- About two-thirds of those have the through-wall direction reversed, so they are truly
  inside out. The rest are spun end for end, but still have the right face outward.
- The own-place score counts them home, because it only asks whether the sherd's surface
  lies near the surface of its home.
- TORA's encoder does receive point normals (`tora/modeling/encoder/point_cloud_encoder.py:113`),
  and the Juglet meshes are closed and consistently wound. So the input tells the model
  which side is outside, and it does not use it.

The rule "outside faces out" needs only the sherd's own shape and the assembled attempt.
It is usable on an excavated vessel (U1). SfS++ builds the same constraint in: it tries
inner and outer normals both ways (`papers/text/sfspp-2502.13986v1.md`, appendix).
PuzzleFusion++ reports 180-degree errors on small pieces (§4.4, App. B.4).

## Definitions (fixed before the run)

- **Curvature centre:** a least-squares sphere fitted to the sherd's points. The sherd is
  *undecidable* (too flat to say) if the radius is over 3× the sherd's longest side.
- **Rule (no answer key):** a placed sherd is flagged inside out if the direction from
  its centroid to its curvature centre points away from the assembled attempt's
  centroid (dot product < 0).
- **Label (answer key):** the curvature direction in the true pose, turned by the
  sherd's rigid move (Kabsch fit, true → placed). The sherd is inside out if that
  reverses it (cosine < -0.5).
- **Strict home:** own-place home (chamfer, as now), **and** each point on average within
  SEAT_PCT (7.1% of pot size) of its *own* true point. A turned-over sherd fails this.
- **Correction:** turn a flagged sherd 180° about an axis through its centroid lying in
  its wall. Try 12 such axes and keep the one whose edge points (the nearest 10%) sit
  closest to the other sherds. No answer key is used.

## Predictions (written 2026-09-24, before the run)

1. **Instrument:** on the *correct* assemblies, the rule says right-way-out for at least
   95% of decidable sherds. If it does not, the rule is the broken ruler: stop.
2. The rule agrees with the label on at least 90% of decidable sherds counted home.
3. Inside-out placements are not Juglet-only. They appear on the comparison pots TORA
   fails, and are rare on the ones it rebuilds.
4. Within an object, attempts with more flagged sherds have fewer strict-home sherds
   (rank correlation below 0 on the Juglet runs).
5. At least half the flagged sherds that were on their home patch (chamfer home) become
   strict home once corrected.

## Acceptance criteria

- [x] Script written; run on the Juglet (job 30919372, three arms; job 30130049 baseline)
      and the eight Fractura ceramics (job 30167044 `whole`). Also run on the three
      anchor-choice arms (job 30917498) to correct anchor-choice ticket 01.
- [x] Prediction 1 checked first
- [x] Predictions 2-5 each marked held / failed
- [x] Strict-home counts for the two-held arms, written back to anchor-choice tickets 01,
      02 and O8. **Corrected** counts do not exist: the correction failed (P5).
- [x] Staged in visual-qa for the conservator's look: pair `insideout_rulepick`. This is
      the attempt the rule picks, not a corrected one, because the correction failed.
- [x] Which of the three, and the weight
- [ ] Conservator's witnessed look and note on `insideout_rulepick`, with agent reply

## Result (2026-09-24)

Run: `python scripts/check_inside_out.py LABEL=NPZ ... --held ... --json artifacts/insideout/<arm>.json`
(from `tora/`). Solid sherds throughout. Sherds held by the job are skipped.

**P1 (instrument), checked first: held on the Juglet, failed on three of eight
comparison pots.** On the correct Juglet the rule says right-way-out for all 9 sherds, and
it does so in every file. On the correct Fractura pots it wrongly flags:

- `narrow_bottle4`: 2 of 4. Sherd 1 is 46% of the pot and has its centroid near the
  pot's centre; sherd 3 is 28%.
- `narrow_bottle1`: 1 of 12 (sherd 2, a 3% chip).
- `galli_pot`: 1 of 10 (sherd 7, a 3% chip).

It holds on `blue_pot`, `narrow_bottle3`, `pink_bowl`, `plate` and `narrow_bottle2`. So
the rule breaks at both extremes: a sherd that is most of the pot, and a small chip whose
fitted sphere is noise. The Juglet's mid-size sherds sit inside the range where it
works. **The rule is usable on the Juglet only.** Before it is used anywhere else it
needs a size guard (skip sherds under ~5% or over ~25% of the pot) and a re-check.

**P2 (rule vs label): held.** Juglet 212 of 212 decidable chamfer-home sherds: neck 47/47,
baseline 36/36, neck + base 79/79, neck + 4 50/50. On the controls the rule agrees on
230/249, and 10 of the 19 misses are on `narrow_bottle4`, where P1 already failed.

**Chamfer home vs strict home.** "Chamfer home" is what own-place has reported until now.
"Strict home" also requires each point to be near its own true point.

| Juglet arm | chamfer home | strict home | inside out, among chamfer home |
|---|---|---|---|
| neck held (30919372) | 47/160 | 14/160 (9%) | 19 |
| neck held, baseline job 30130049 | 36/160 | 9/160 (6%) | 16 |
| neck + base | 79/140 | 45/140 (32%) | 23 |
| neck + sherd 4 | 50/140 | 21/140 (15%) | 10 |

The rest of the gap between chamfer and strict is sherds spun end for end with the right
face out (turn 120-180°, through-wall direction kept). The rule cannot see those, and
nothing reference-free here can yet.

**P3 (not Juglet-only): roughly held.** Inside-out sherds counted home appear on pots TORA
struggles with: `blue_pot` 7, `narrow_bottle3` 4, `narrow_bottle1` 2, `galli_pot` 2. They
are absent on the four it rebuilds (`narrow_bottle4`, `narrow_bottle2`, `pink_bowl`,
`plate`). Strict vs chamfer on the controls: nb4 30/30, blue_pot 27/36, nb3 7/10,
nb1 29/35, pink_bowl 20/20, plate 30/33, nb2 20/20, galli 57/65.

**P4 (fewer flags, more home): held on the Juglet, small numbers.** Rank correlation between
flags and strict home per attempt: -0.44 (neck), -0.31 (baseline), -0.32 (neck + base),
-0.76 (neck + 4). The attempt with the fewest flags is the best, or tied best, in 3 of 4
arms:

- neck + base: attempt 0, with 0 flags, has 4 strict home, which is the maximum. Only 2
  of 20 attempts reach 4.
- neck + 4: five tied picks, strict home [1, 2, 2, 2, 2], maximum 2.
- neck: the pick has 2, which is the maximum.
- baseline: the pick has 1, which is the maximum.

On the controls P4 says little: mostly undefined (no variation), and `galli_pot` +0.40.

**P5 (correction): failed.** Flagged chamfer-home sherds that became strict home after the
12-axis flip: 0/19 (neck), 0/16 (baseline), 0/23 (neck + base), 3/10 (neck + 4). A check
using the answer key tried the best of 36 flips per sherd. That brings 16/19 (neck) and
11/23 (neck + base) home, so a flip exists, but the reference-free way of choosing the axis
does not find it. The flipped sherds also sit off-centre (median 4.2% and 6.1% of pot
size), so a real fix needs a flip plus a slide. Not tuned further: the prediction was
fixed before the run and it failed.

**The attempt the rule picks** (neck + base, attempt 0), per free sherd:

| sherd | 1 | 2 | 3 | 4 | 5 | 7 | 8 |
|---|---|---|---|---|---|---|---|
| strict home | yes | no | yes | yes | yes | no | no |
| turn from true | 14° | 170° | 4° | 6° | 11° | 133° | 158° |
| mean point offset (% pot) | 2.6 | 28 | 2.5 | 5.9 | 4.5 | 36 | 15.3 |

Sherd 8 counts as chamfer home but is spun end for end with its outside still out. Staged
as visual-qa pair `insideout_rulepick`: correct left, attempt 0 right, real meshes, mm.

**Which of the three.** Two separate findings:

1. **The method genuinely failed.** TORA places sherds inside out. That is physically
   impossible, since the outer face is convex and the inner concave. It happens on 19-23
   of the placements counted home per Juglet arm, and on four comparison pots. The
   encoder is given point normals, so the information is in its input.
2. **The measurement was broken.** Own-place chamfer home is blind to a sherd turned over
   in its own place. Every Juglet home count so far overstates. Strict home is the honest
   figure: neck held 9%, neck + base 32%, where 29% -> 56% had been reported. The
   direction of the two-held finding survives. Its size does not.

**Weight:** one pot (Juglet), 20 attempts per arm across five arms and two jobs; 8
comparison pots with 10 attempts each. The rule is validated on the Juglet only (P1).

**What would change the answer:** a strict-home score in `own_place.py` itself, so other
analyses stop inheriting the blind spot. After that, the next step is to put the
constraint where the error is made, not to fix it afterwards: reject or resample an
attempt with an inside-out sherd during TORA's sampling. The rule also needs a size guard
before it goes near another pot.
