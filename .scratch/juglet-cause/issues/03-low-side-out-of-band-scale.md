# 03: Does a scale *below* the trained band damage the result too?

**Type:** `wayfinder:task` (AFK)
**What to build:** An answer to whether TORA degrades when the object's stored size is
too *small*, and an audit of which past Juglet conclusions were drawn from runs sitting
there.

**Answers:** O8

**Blocked by:** None (can start immediately)

**Status:** answered 2026-09-06 — job 30130045 (downward ladder) came back and the
prediction written into the job header **failed**

## Why it is live

The scale ladder (job 29891327) established a cliff between 15 and 50 and that the model
is fine from 0.5 to 5. **It never tested below 0.5.** The trained band is [0.375, 0.625].

`juglet_norm` runs report `scales = 0.041` — nine times below the floor. The wear
comparison that produced wear_v1 and wear_v2 (job 29027773) ran there. `juglet_gt` runs
sit at 0.511 and are clean.

If the low side is also damaging, then the wear experiments were scored on a handicapped
input and their "no movement in rotation" reading is not a fair test of wear.

## Acceptance criteria

- [x] Every Juglet-related eval run on Spartan audited for its recorded `scales`, and a
      table produced of which conclusions rest on out-of-band runs
      (`scripts/audit_run_provenance.py`, 141 runs — see **Audit** below)
- [x] The ladder extended downward — rungs giving scale roughly 0.04, 0.08, 0.15, 0.25
      alongside 0.5 as the in-band control — **job 30130045**, 12m 23s, exit 0:0,
      `ARMS= RUNGS="0.08 0.16 0.3 0.5 1" LADDER_DRAWS=10`, 8 pots × 10 draws × 5 rungs
- [x] The gate (`scripts/check_scale_conditioning.py`) passes, so only `scales` moves —
      *"every compared tensor matched to 0.00e+00 (tol 1e-04)"*
- [x] Renders at the worst rung and at 0.5, same pot, same seed —
      `artifacts/ladder_down_ends.png`, all eight pots, two views, correct assembly
      beside scale 0.04 and scale 0.50
- [x] A verdict on whether job 29027773's wear comparison must be re-run in band —
      **no: it already exists in band as job 29308186, and that is the one to quote**
- [x] Names which of the three this is — **the measurement was broken**, and only the
      seating half of it. The method is unharmed by a small stored size.

## Audit (first criterion, done 2026-09-06 — no GPU)

**Headline: the Juglet's *wear* experiment was run on a pot stored nine times smaller
than anything the model was trained on, and at that size the "how many sherds are seated"
measure stops working entirely — it reads 9 of 9 on every draw of every arm, including the
arm that turns sherds 85° out of true. The Juglet's *baseline* numbers, the ones the map's
conclusions actually rest on, are clean.**

**Which of the three this is: the measurement was broken** — for one family of runs
(`juglet_norm`, which includes the wear comparison), on one of the two measures. Not the
method, and not the reference answer.

Method: `scripts/audit_run_provenance.py` copied to Spartan and run over all **141**
eval-run directories under `/data/gpfs/projects/punim2657/TORA/eval_runs`, reading each
run's `.hydra/config.yaml` (for `data.anchor_free`, `model.anchor_free`, `n_generations`)
and its `results/*.json` (for the recorded `scales`). One-level glob, no recursive find.
The Juglet table below is re-read locally through `scripts/readout.py`, so the non-anchor
`x n/(n-1)` correction is applied.

Trained band: **[0.375, 0.625]**. The ladder (job 29891327) showed the model is fine from
0.5 to 5 and collapses between 15 and 50. **It never tested below 0.5**, which is why the
low side is still a live question and not an answered one.

### Every Juglet run, by stored size

```
run                                        scale   draws  turn  seated   dataset
-- IN BAND ------------------------------------------------------------------------
lorav_juglet_baseline_29623885            0.5114     5    50.2   6/9     juglet_gt
lorav_juglet_baseline_29527496            0.5110     5    59.3   5/9     juglet_gt
lorav_juglet_adapter_on_29623885          0.5109     5    63.1   4/9     juglet_gt
lorav_juglet_adapter_off_29527496         0.5109     5    67.1   7/9     juglet_gt
lorav_juglet_adapter_off_29623885         0.5109     5    69.8   6/9     juglet_gt
lorav3_juglet_baseline_29880370           0.5114     5    62.7   5/9     juglet_gt
lorav3_juglet_adapter_off_29880370        0.5109     5    69.6   4/9     juglet_gt
lorav3_juglet_adapter_on_29880370         0.5110     5    72.6   4/9     juglet_gt
wearft2_jugletgt_baseline_29308186        0.5114     5    56.8   7/9     juglet_gt
wearft2_jugletgt_wear_v1_29308186         0.5114     5    59.6   7/9     juglet_gt
wearft2_jugletgt_wear_v2_29308186         0.5114     5    62.2   7/9     juglet_gt
jugletgt_render_wear_v2_29330980          0.5114     5    56.7   7/9     juglet_gt
juglet_v2_pairs_baseline_29027773         0.5017   180    50.5   1/2     juglet_pairs
juglet_v2_pairs_wear_v1_29027773          0.5017   180    45.2   2/2     juglet_pairs
juglet_v2_pairs_wear_v2_29027773          0.5017   180    48.8   2/2     juglet_pairs
juglet_deploy_local02_25528198            0.6043     3    83.2   1/9     juglet_deploy_local02
-- ABOVE THE BAND, inside the ladder's proven-safe 0.5-5 region ---------------------
juglet_robust_last_27798522               0.8870     3    62.1   1/9     juglet_deploy_local02
juglet_robust_best_27798522               0.8867     3    71.3   1/9     juglet_deploy_local02
juglet_deploy_local02_25594802            0.8867     3    74.0   1/9     juglet_deploy_local02
juglet_deploy_25192222                    2.4904     3    97.3   1/9     juglet_deploy
juglet_deploy_proposed_25279003           2.4904     3   104.0   1/9     juglet_deploy
juglet_25118786                           2.4914     3   103.0   1/9     juglet
juglet_deploy_proposed_25275931           2.4914     3   109.7   1/9     juglet_deploy
-- FAR BELOW THE BAND, never tested -- 9x under the floor ---------------------------
juglet_v2_wear_v1_29027773                0.0408     5    62.9   9/9     juglet_norm
juglet_norm_baseline_27859890             0.0408     5    68.5   9/9     juglet_norm
juglet_v2_wear_v2_29027773                0.0408     5    74.5   9/9     juglet_norm
juglet_norm_robust_27859890               0.0408     5    85.6   9/9     juglet_norm
juglet_v2_baseline_29027773               0.0408     5    85.4   9/9     juglet_norm
anchor2x2_juglet_affalse_28228263         0.0408     3    95.1   9/9     juglet_norm
anchor2x2_juglet_aftrue_28228263          0.0408     3    87.9   9/9     juglet_norm
```

### The seating measure is dead at both ends, and the pattern says so plainly

Read the `seated` column down the table. It is not noisy — it is **stuck**:

| stored size | sherds seated | what it means |
|---|---|---|
| 0.0408 (9× too small) | **9 of 9, on every draw of every arm, 7 runs** | the whole pot is smaller than the "close enough" distance, so everything counts as seated no matter where it is put |
| ~0.5 (in band) | 3 to 9, varying draw to draw | the measure is doing work |
| 0.6–2.5 (large) | **1 of 9, every run** | only the given anchor fragment is ever inside the distance |

That is the size-dependence of chamfer distance that `docs/glossary.md` already warns
about, showing up in the record. At 0.0408 the `juglet_norm` runs report a *perfect*
reassembly while simultaneously reporting sherds turned 85° out of true — a physically
impossible pair, and the clearest possible sign that the ruler, not the method, produced
the number. Rotation is an angle and does not scale, so **the rotation column survives at
all three sizes; the seating column does not.**

Note this cuts the other way too: the old `juglet_deploy` runs at 2.49 that read "1 of 9
seated" were never as catastrophic as they looked on that measure.

### Which conclusions rest on out-of-band runs

| conclusion | run family | scale | verdict |
|---|---|---|---|
| The Juglet baseline reassembles badly (median ~59–61°, ~5 of 9 seated) — the map's premise, ticket 01's 20 draws, ticket 02's comparison | `juglet_gt` | 0.511 | **Safe.** In band on every run. |
| Fragment-count comparison against fresh ceramics (ticket 02) | `juglet_gt` vs `scaleladder_B` | 0.511 vs 0.500 | **Safe.** Both sides in band, both on the corrected ruler. |
| LoRA adapter on/off makes no readable difference | `lorav*`, `lorav3*` | 0.511 | **Safe.** |
| Anchor-fixed vs anchor-free costs nothing (ticket 02's confound check) | `anchor2x2_*` on six real pots | 0.500 | **Safe** — the six ceramics are in band. The *Juglet* arm of that ablation is at 0.0408 and only corroborates; ticket 02 already says so. |
| **Wear v1 / v2 do not move the result** — job 29027773 | `juglet_norm` | **0.0408** | **Compromised on seating, weak on rotation.** See below. |
| Wear v1 / v2 do not move the result — job 29308186 | `juglet_gt` | 0.5114 | **Safe**, and it is the version to quote. |
| Pairwise (two-fragment) wear comparison — job 29027773 | `juglet_pairs` | 0.5017 | **Safe.** Same job number, different dataset config, in band. |
| Early "deploy" Juglet numbers (2024-style, 3 draws) | `juglet`, `juglet_deploy` | 2.49 | Rotation usable, **seating meaningless**; superseded anyway. |

### Verdict on job 29027773's wear comparison

**It does not need re-running, because it already has been.** The nine-fragment wear
comparison exists twice:

```
                       out of band (29027773, 0.0408)   in band (29308186, 0.5114)
baseline                    85.4   [67.9-88.0]  9/9        56.8  [37.7-77.5]  7/9
wear v1                     62.9   [46.2-75.0]  9/9        59.6  [38.4-70.5]  7/9
wear v2                     74.5   [50.8-85.9]  9/9        62.2  [32.5-80.1]  7/9
```

The in-band version is the one to quote, and it says clearly: **wear training moves
nothing** — 56.8 / 59.6 / 62.2, a spread of 5.4° against a 17° noise floor (ticket 01).

The out-of-band version *looks* like it says something different: wear v1 appears to
improve the baseline by 22.5°, which is just over the 17° threshold. **Do not quote that.**
The draw ranges overlap almost completely (67.9–88.0 against 46.2–75.0), it is five draws
against five, and it exists only at a stored size the model was never trained for and the
ladder never tested. One marginal effect appearing solely in the broken condition is what
an artefact looks like, not what a finding looks like.

So: the honest reading of the wear experiments is **the in-band one — wear training
changes nothing on the Juglet** — and that is unchanged by this audit. What the audit
removes is the temptation to reach for the 22.5° number later.

### One thing the audit found outside the Juglet

`model.anchor_free` is **`false` in every one of the 141 runs**, without exception. So
`tora/eval/evaluator.py:74`'s anchor-aligning ICP has never executed in this project, and
in anchor-free *data* mode the sampler pins the anchor to ground truth while the encoder
is shown that fragment at the origin. Job 28228263 puts the net effect below the noise
floor (ticket 02), so nothing needs redoing — recorded on the map's fog list, not here.

Also worth knowing before any future comparison is built: **out-of-band storage is
widespread, not a Juglet quirk.** The fresh/held-out ceramic sets (`lorav*_fresh_*`,
`wearft2_fresh_*`, `heldout_norm_*`) span 0.319–0.413 with **2 of 6 objects below the
floor**, and the 30-object sweeps (`lorav_sweep_*`, `wearft2_sweep_*`, `erosion_sweep_*`,
`levers_*`, `sel10_*`, `refine_src_*`) span 0.319–0.413 with **10 of 30 below it**. Every
`pairs_real_*`, `real_heldout_*` and `fractura_*` run is stored in millimetres
(15.4–243.5) and is far outside anything tested. `scaleladder_B_normalized`,
`juglet_pairs_*`, `thinwalled_*`, `*_vessels_*`, `piececount_baseline_28198773` and
`bestofN_24289835` are all in band.

## Answer

**A stored size far below the trained band does not damage the reassembly. It breaks the
sherds-seated measure and nothing else.** The prediction written into the job header
before submitting — that rotation would climb steadily as the rung fell away from 0.5 —
**failed**, and that is the result.

**Which of the three this is: the measurement was broken**, for one family of runs
(`juglet_norm`) on one of the two measures. Not the method, and not the reference.

Job **30130045**, 12m 23s, exit 0:0. Eight pots, ten draws each, five rungs; only the
`scales` number fed to the model changes between rows, asserted by
`scripts/check_scale_conditioning.py` (*every compared tensor matched to 0.00e+00*).

```
scale  band  blue_pot galli_pot n_bottle1 n_bottle2 n_bottle3 n_bottle4 pink_bowl  plate   ALL
0.040   no     11.4     29.7      53.6      4.4      81.6      8.1       1.9      48.8    25.2
0.080   no     17.9     28.2      59.6      4.4      79.7      8.1       1.6      43.0    24.0
0.150   no     33.0     30.0      65.4      4.4      82.2      8.1       2.0      46.4    30.0
0.250   no     46.1     27.4      61.7      4.6      84.2      8.0       1.4      47.9    30.7
0.500  yes     33.8     32.6      62.8      4.7      79.0      8.1       1.9      51.6    25.2
```

The ladder is **flat and non-monotone**. Seven of the eight pots move by only a few
degrees across a twelvefold change in stored size — `narrow_bottle2` 4.4→4.7,
`narrow_bottle4` 8.1→8.1, `pink_bowl` 1.9→1.9, `galli_pot` 29.7→32.6, `narrow_bottle3`
81.6→79.0, `plate` 48.8→51.6, `narrow_bottle1` 53.6→62.8. The single pot that does move,
`blue_pot` (11.4 → 46.1), moves the **wrong way**: it is *better* at the smallest size,
and it is also the pot with the widest draw-to-draw scatter on the in-band ladder
(sd 18°), so even that is likely sampler luck rather than scale.

**The render agrees, and it was made before this was written.**
`artifacts/ladder_down_ends.png` draws all eight pots at scale 0.04 beside scale 0.50
against the correct assembly, two orthographic views each. There is no visible
difference between the two ends: `blue_pot`, `pink_bowl`, `narrow_bottle2`,
`narrow_bottle4`, `galli_pot` and `plate` sit close to correct at both sizes;
`narrow_bottle1` is scattered at both; `narrow_bottle3` has the same piece flying off at
both.

### What this settles, and what it does not

Settled: **candidate 4 on `intent/O8` is ruled out.** Nothing about the Juglet's failure
is caused by its stored size, and the `juglet_norm` runs at 0.0408 were not handicapped
in their *reconstruction*. What those runs cannot support is any statement about
fragments seated, because at that size everything counts as seated (the audit above:
9 of 9 on every draw of every arm while the same runs report sherds turned 85° out of
true).

Not settled by this ticket, and not its question: why `narrow_bottle1` and
`narrow_bottle3` fail at every scale.

### How much weight this can bear

Eight objects, ten draws each, five rungs, one trained model — 400 draws. The flatness is
consistent across seven of eight objects and confirmed by eye, which is as strong as a
negative result gets here. It is one checkpoint, so it says "this model is insensitive to
the size number", not "no model could be".

### Submitted 2026-09-06 — job 30130045

```
ARMS= RUNGS="0.08 0.16 0.3 0.5 1" LADDER_DRAWS=10 \
    sbatch scripts/hpc/eval_scale_ladder.slurm
```

Rung m gives scale 0.5*m, so the rungs are 0.04, 0.08, 0.15, 0.25 and 0.5 as the in-band
control. 0.04 is where the `juglet_norm` family sits.

**Stated before the result arrives, so it can fail.** If a too-small stored size damages
the reconstruction, rotation should climb steadily as the rung falls away from 0.5, with
0.04 clearly worse than 0.5. **If the downward ladder is flat, small sizes are harmless to
the reconstruction — only the seating measure breaks — and candidate 4 on `intent/O8` is
ruled out.** Read the rotation column, not a seating count: the job now refuses to print
the fragments-seated summary when arms A/B did not run, precisely because that count
saturates below the band.

### What is still owed on this ticket

The audit answers "which conclusions rest on out-of-band runs". It does **not** answer the
ticket's actual question — *does* a too-small scale damage the result? — because nothing
below 0.5 has ever been run as a controlled rung. The `juglet_norm` runs sit at 0.0408 and
do read worse in rotation than `juglet_gt` at 0.511 (85.4° vs 56.8° baseline), but they
differ in the dataset config as well as the scale, so that is a hint and not a measurement.
The downward ladder (criterion 2) is what settles it, and it needs GPU.

### How much weight this can bear

The scale figures are read straight out of each run's own recorded `scales`, so they are
facts about the runs, not estimates. The claim that the seating measure saturates at
0.0408 rests on 7 runs × 3–5 draws all returning exactly 9 of 9, against in-band runs of
the same object returning 3–9 — that is a strong pattern, but it is one object. The
in-band wear comparison is 5 draws per arm on one pot with one checkpoint: enough to say
"no readable movement", not enough to say "wear training cannot help".
