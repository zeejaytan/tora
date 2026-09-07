# What is the number the model is told about the pot's size? — measured, job 30185814

**Date:** 2026-09-07 · **Ticket:** `.scratch/eval-readout/issues/04` · **Answers:** O2
**Job:** 30185814, `sapphire`, CPU only, COMPLETED 0:0, 3.5 minutes. No model loaded.
**Script:** `scripts/measure_scale_conditioning.py`, `scripts/hpc/measure_scale_conditioning.slurm`
**Artifacts:** `eval_runs/scale_band_30185814/*.json`, `artifacts/scale_band/*.png`

## The short version

**The warning on the wear table is real, and my explanation for why it might be
spurious was wrong.** The six pots the wear test was scored on really do sit at the
very bottom of what the model was ever trained on — two of them below it entirely.

**But it cannot have produced the wear result.** The size number is held fixed across
the wear ladder for each pot — the largest drift is 2.0% between a fresh pot and its
most heavily abraded version. The fresh-versus-worn comparison is paired, at the same
handicap on both sides. What the out-of-band conditioning can do is push both numbers
(0.843 fresh, 0.645 worn) down together; it cannot open a twenty-point gap between them.

**Which of the three: the measurement was broken** — one of our own constants, not the
model and not the reference. And the direction is the opposite of the one I predicted.

## What was being asked

`docs/notes/WEAR_TEST_RESULTS.md` §4 carried a ⚠️ we wrote and never tested: the fresh
and worn-sweep rows were scored at "a stored object size of 0.319–0.383, at or below the
trained floor of 0.375". Since those two rows are the whole evidence for wear being a
cause, the flag had to be settled before anything else was built on them.

TORA is not only shown the sherds. It is also **told how big the pot is** — one number
per object, fed into the flow model at every step of the reconstruction
(`tora/modeling/tora.py`; `PointCloudEncodingManager` turns it into a code attached to
all 5000 points, `flow_model/embedding.py:151`). If we scored those runs while telling
the model a size it had never trained on, the model was handicapped before the wear
question was asked.

## What was eliminated first, by reading the code and not by a job

**Augmentation is not running at evaluation.** `dataset.py:428` applies the 0.75–1.25
size jitter only `if self.random_scale_range is not None`, and `datamodule.py` passes
`random_scale_range` to the **training** dataset alone (line 152). The validation dataset
in the same branch, the `"validate"` branch and the `["test", "predict"]` branch all omit
it, so the dataset default `None` applies. Evaluation reads a fixed, deterministic value.

## The hypothesis that was tested, and refuted

The band we judge runs against — `[0.375, 0.625]`, hard-coded identically in
`readout.py`, `check_scale_conditioning.py` and `audit_run_provenance.py` — was
**arithmetic, not observation**: `0.5 × [0.75, 1.25]`, where 0.5 is the *mesh* storage
convention.

But `scales` is not the mesh's max|v|. `dataset.py:427` takes it from the **sampled
5000-point cloud**, after `center_pcd` re-centres on the point centroid and `_make_y_up`
swaps axes. Points scattered over a surface do not land on the mesh's furthest vertex,
so I expected the pipeline value to come out **below** 0.5 — which would have made the
band too high, the warning spurious, and the table fine.

**It comes out above 0.5.** Re-centring on the centroid moves the object off the origin
it was normalised about, and that pushes the extreme coordinate outward by more than the
sampling loses. Measured on 400 objects drawn from the 35,114 in the Breaking Bad
`everyday` train split — the corpus `bbad_everyday_cka.ckpt` was trained on:

| | base `scales` (no jitter) |
|---|---|
| min | 0.4929 |
| p5 | 0.5022 |
| median | **0.5446** |
| p95 | 0.6313 |
| max | 0.7116 |

Applying the 0.75–1.25 jitter the train split alone receives, **what the model was
actually told during training** spans **0.375 → 0.811**, median 0.550.

**So the assumed floor of 0.375 was right — to 0.0001 (measured minimum 0.3751) — and
right by luck**, two errors cancelling. The assumed **ceiling of 0.625 was wrong**: the
true ceiling is 0.811. Nothing load-bearing was flagged for being too large, so no
published number moves, but all three copies of the constant have been corrected.

## Where the evaluation sets actually sit

Every object we score real pots on:

| object | `scales` | position in the training distribution |
|---|---|---|
| `plate` | 0.3210 | **below everything training showed** |
| `coxae` | 0.3324 | **below everything training showed** |
| `vert9` | 0.3804 | lowest 0.2% |
| `galli_pot` | 0.3848 | lowest 0.5% |
| `limb3` | 0.4094 | lowest 4.3% |
| `blue_pot` | 0.4096 | lowest 4.3% |

Rendered as `artifacts/scale_band/scale_band.png`: the six sit in or under the left-hand
tail of the training histogram, not inside its body.

**In plain terms:** every real pot we have scored is presented to the model as an
unusually small object, and two of them as smaller than any object it has ever seen. The
model was trained almost entirely on Breaking Bad synthetic objects, which arrive at a
different size through the same pipeline than our real scans do — `normalize_real_hdf5.py`
puts them on the mesh convention (max|v| = 0.5), but that is not the convention the
conditioning input is measured in.

## Why the wear finding survives it

`build_erosion_sweep.py` deliberately does not renormalise between wear strengths, and
the measurement confirms it did what it says. Across the whole erosion ladder, per pot:

| pot | e000 | e100 | drift |
|---|---|---|---|
| `blue_pot` | 0.4120 | 0.4070 | −1.23% |
| `coxae` | 0.3329 | 0.3328 | −0.01% |
| `galli_pot` | 0.3849 | 0.3852 | +0.08% |
| `limb3` | 0.4085 | 0.4024 | −1.51% |
| `plate` | 0.3212 | 0.3205 | −0.21% |
| `vert9` | 0.3839 | 0.3763 | −1.98% |

And the "fresh held-out" set matches the sweep's own unworn variants to within 0.9% per
object, so the two rows of §4 are the same pots at the same conditioning.

**The handicap is a constant offset applied equally to both sides of the comparison.**
Seating falls 0.843 → 0.645 while the size input moves by at most 2%. That is what a
paired comparison is for, and it is why the ⚠️ is a caveat on the *absolute level* of
both numbers rather than a threat to the difference between them.

What it does mean: **the wear result is a lower bound measured on a handicapped model**,
and repeating the sweep with the objects re-normalised into the middle of the trained
band would very likely lift both numbers. That is the correct next experiment, and it is
now specified rather than guessed.

## The harness agrees with the runs it is auditing

The reconstruction reproduces, object by object, the `scales` the 29308186 runs saved
themselves — the strongest available check that the script measures the same quantity:

| object | run 29308186 | this measurement | difference |
|---|---|---|---|
| `blue_pot` | 0.4101 | 0.4096 | 0.1% |
| `limb3` | 0.4096 | 0.4094 | 0.05% |
| `galli_pot` | 0.3854 | 0.3848 | 0.2% |
| `vert9` | 0.3833 | 0.3804 | 0.8% |
| `coxae` | 0.3316 | 0.3324 | 0.2% |
| `plate` | 0.3194 | 0.3210 | 0.5% |
| the Juglet (`juglet_gt`) | 0.5114 | 0.5114 | 0.0% |

The residual is the Poisson surface-sampling seed. It also reproduces `readout.py`'s
already-recorded figure of **0.041** for `juglet_norm`, from an independent path.

## A side finding, and it is a picture rather than a number

`juglet_norm.hdf5` — the file the earlier "normalised Juglet" runs used
(`eval_juglet_normalized.slurm`, `eval_juglet_wear_trained.slurm:57`,
`eval_juglet_wear_v2.slurm:60`) — hands the model **0.0408**, eleven times below the
trained floor. `juglet_gt.hdf5`, which the §4 rows use, hands it **0.5114**, comfortably
inside. §4's Juglet rows are therefore sound.

The cause was rendered before being reported (`artifacts/scale_band/juglet_layouts.png`,
and at the object's own scale in `juglet_layouts_zoom.png`, because the first view was
too coarse to resolve it). **Both files store max|v| = 0.5 and both hold the same nine
sherds in the same arrangement.** The difference is where the origin is:

| | per-axis max abs coord | object centre | reach from its own centre |
|---|---|---|---|
| `juglet_norm` | (0.055, 0.021, **0.500**) | (0.037, −0.002, **−0.480**) | **0.050** |
| `juglet_gt` | (0.296, 0.276, 0.500) | (−0.013, −0.021, −0.075) | **0.575** |

`juglet_norm` was normalised by distance **from the file's origin**, and the pot sits
0.48 away from that origin — so the 0.5 it was scaled to is almost entirely the offset,
and dividing by it shrank the pot to about a **tenth** of its intended size. The
geometry, the assembly problem and the model's predictions are unaffected; only the size
the model is *told* is wrong, and it is wrong by a factor of eleven.

**Which of the three, for that one: the measurement was broken** — the normalisation
that was introduced to fix a threshold problem introduced a conditioning problem, and
`juglet_gt` already fixed it.

## What changed as a result

- `scripts/readout.py`: `TRAINED_SCALE_BAND` → `(0.375, 0.811)`, measured, with the
  derivation replaced by the measurement; new `TRAINED_SCALE_P5 = 0.413` and a
  `FLAG_SCALE_RARE` for runs inside the band but in its lowest 5% — which is where every
  real pot we own actually sits.
- `scripts/check_scale_conditioning.py`, `scripts/audit_run_provenance.py`: the same
  constant, corrected in both.
- `docs/notes/WEAR_TEST_RESULTS.md` §4: the ⚠️ restated with the measured numbers.

## What this does not settle

It does not say what the model would do on these pots if they were conditioned in the
middle of the trained band. That is one GPU job and is now a well-posed question:
re-run the sweep with the objects rescaled so `scales` lands near 0.55, and see whether
both the fresh and worn seating figures rise. If they rise together, the wear finding is
confirmed at full strength. If the gap closes, the wear finding was partly an artefact of
scoring a handicapped model — and that would be worth knowing.

**Ticketed 2026-09-07:** `.scratch/eval-readout/issues/05-does-the-out-of-band-size-cost-anything.md`.
Writing it turned up prior art that narrows the question and lowers the expected payoff,
which is worth recording here rather than in the ticket alone. Two scale ladders have
already varied this exact input on real pots — job **29891327** upward (flat from 0.5 to 5,
collapse only between 15 and 50) and job **30130045** downward (rungs 0.04 to 0.5: **flat
and non-monotone**, eight pots, ten draws each, with renders at the two ends
indistinguishable). Three of the six sweep pots were in the second. On that evidence the
model is close to insensitive to the size it is told, and the handicap probably costs
nothing.

**Two things keep the job worth running.** Both ladders were read in **rotation** — the
metric wear moves by about 3°, against a ±27.7° between-pot floor — which is the same
mistake the wear analysis made before the conservator caught it; the wear finding lives in
**seating**, and seating has never been read across a scale ladder. And both ladders used
**fresh** pots, so whether out-of-band conditioning interacts with *wear* is untested. That
interaction is the only thing that could bend the §4 gap, and it is what ticket 05 measures.

One worry can be dropped: **the seating measure cannot be distorted by `scales` at all.**
`part_accuracy`, the field `readout.py` reads, is computed in the unit-box frame
(`tora/eval/evaluator.py:87`), independent of the conditioning value. The 9-of-9 saturation
seen at 0.041 in `.scratch/juglet-cause/issues/03-low-side-out-of-band-scale.md` was
`part_accuracy_absolute`, the pre-`0d6a85f` scoring.

**Measured 2026-09-07, job 30187601.** Correcting the size input to 0.550 lifts fresh
seating by **+7.5 points** (95% CI [+0.8, +17.1]) and moves worn seating by **−1.6**
(CI [−18.1, +9.5]), against draw scatter of ±16–20. The prior was right that the model is
close to insensitive to this number; the fresh gain barely clears zero and rests on six
pots. **The handicap is not what is wrong with §4** — the ruler is. Job 29308186 predates
`0d6a85f` by two weeks, so §4 is scored on the retired size-dependent metric, which is
most generous exactly where these pots sit: `coxae` at `scales` 0.3316 scores 0.950 old
and 0.050 corrected on the same ten draws. Full read-out in
`.scratch/eval-readout/issues/05-does-the-out-of-band-size-cost-anything.md`.
