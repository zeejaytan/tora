# Why TORA looked bad on Fractura: two units bugs, one behind the other

**Resolved 2026-09-02. Read section 2 first — sections 1 and 3 onward are kept
as the record of how this was reasoned through, including where it went wrong.**

Started from a fair question: these eight ceramics were broken last week, not
dug up. Fresh edges, sharp and unworn. If TORA's weakness were worn fracture
surfaces, it should sail through these. It did not. So what was it?

Neither the fracture surfaces nor the pots. **Two separate unit-conversion
faults, stacked.** The first was in how the answers were scored: an absolute
0.01 tolerance applied to objects stored in millimetres, which pinned every
real object at exactly the free anchor. The second, found only after fixing the
first, was in what the model is *told*: the object's stored size is fed into
the network at every step of the reconstruction, and at 45–120 rather than the
0.5 it was trained on, it is meaningless to the network.

With both fixed, on the same eight pots with the same trained model: fragments
correctly seated go from **1.0% to 72.6%**, and three of the eight pots
reassemble completely. Job 29891327.

The order matters, and it is the trap: fixing the scoring bug and re-reading
the same run *felt* like confirmation that the model had genuinely failed. It
was not. The second bug was still in the run being re-read.

---

**Checked against the corrected ruler, 2026-09-05 — and this note already had
both rulers inside it.** A third measurement fault, unrelated to the two above,
runs through the eval code: `compute_transform_errors` sums rotation and
translation over the **non-anchor** fragments but divides by **all** of them, so
every stored `rotation_error` carries one free zero. The correction is
`x n/(n-1)`, a different factor for every pot — `x1.500` on the three-fragment
`pink_bowl`, `x1.091` on the twelve-fragment `narrow_bottle1`.

What that does to this note:

- **The finding is untouched.** Fragments seated (1.0% -> 72.6%, 4 of 390 ->
  283 of 390) was already anchor-subtracted, and regenerates **exactly**, pot
  for pot, from job 29891327's stored results. So does every seated count in the
  per-pot table. The scale cliff, the renders and the conclusion all stand.
- **The scale-ladder table below is already correct.** It is labelled
  "Non-anchor rotation error" and it means it: its `0.500` row *is* the
  corrected version of the per-pot table's `normalised` turn, and its `69.217`
  row *is* the corrected version of the `as shipped` turn. Read the ladder.
- **The per-pot table's turn column is on the old ruler**, as is the old
  rotation table's `rot, as reported` column and two sentences further down.
  Each is corrected in place below.
- **The hazard specific to this note:** it prints `as reported` and `non-anchor`
  side by side in one table. Those are the two rulers. Never quote a figure from
  one column against a figure from the other.

Recomputed from all 160 stored result files of job 29891327
(`artifacts/notes_recheck/scaleladder_{A_raw_mm,B_normalized}_29891327/`), which
reproduced every printed figure in this note before correcting it.

---

## 1. The "zero fragments placed" reading was the ruler, not the model

`tora/eval/evaluator.py` multiplies the point clouds back to the object's own
units before scoring, and `compute_part_acc` then thresholds squared chamfer at
a fixed `0.01` — documented in the source as "0.01 meter by default". The
tolerance is therefore an absolute physical distance, and it is only meaningful
if every dataset arrives in metres. They do not:

| subset | median scale | stored in |
|---|---|---|
| Breaking Bad vessels | 0.49 | normalised |
| Fractura bone_syn_pig / rib | 0.56 / 0.60 | normalised |
| Fractura ceramics (real) | 74 | millimetres |
| Fractura bones (real) | 24 | millimetres |
| Fractura egg (real) | 52 | millimetres |

A squared-CD threshold of 0.01 is a linear tolerance of 0.1 units. On Breaking
Bad that is 20% of the object's half-extent — generous. On a ceramic pot stored
in millimetres it is 0.1 mm on a vessel ~150 mm across, about 0.16% — roughly
125x tighter in linear terms. Nothing but the anchor can pass it, and the anchor
is clamped at ground truth by construction with chamfer ~0. Hence every real
Fractura object scoring *exactly* `1/n_parts`: 0.250 on the 4-part pots, 0.500
on the 2-part bones. That is the arithmetic of a free anchor, not a measurement.

The fix, in `tora/eval/metrics.py`, restores the frame the threshold was
stated in. Breaking Bad: *"We re-scale each of them to fit a unit-length box for
parameter choice consistency. This normalization scheme allows our method to be
scale invariant"* (Sellan et al. 2022), and *"we set tau = 0.01 following [20]"*.
So tau lives inside a unit-length box. `unit_box_scale` divides both clouds by
the longest side of the **ground truth** bounding box before thresholding —
ground truth, never the prediction, because a scattered prediction has a bigger
box than the object it is trying to rebuild and would be handed a more forgiving
tolerance for failing. `scripts/check_metric_scale_invariance.py` is the gate:
the same geometry stored in millimetres, metres and normalised must score the
same number, and it does (0.600 in all three, where the old absolute metric
ranged 0.400–1.000).

This is the same bug found and resolved once already in jobs 27858648 / 27859890
(see the correction header of `TORA_GOOD_VS_BAD_ANALYSIS.md`);
`real_heldout_norm.hdf5` was built in response, but the raw Fractura subsets were
never rebuilt normalised, so scoring them directly reproduced the identical
broken reading.

### Fixing the ruler did not rescue the result

**Correction, 2026-09-02.** An earlier version of this section reported that
blue_pot went from 0% to 38% and narrow_bottle4 from 0% to 40% once rescored,
and concluded "fragments do land in roughly the right region." **That was wrong
and is withdrawn.** The offline rescorer used a fixed threshold of 0.04 derived
from assuming the dataloader frame has a bounding box of side 2 (max|coord| = 1
implies a half-extent of 1). It does not: `center_pcd` centres by centroid, not
by bounding-box centre, so narrow_bottle4's box side is **1.695**, and the
correct equivalent is ≈0.0287 — the threshold used was about 40% too loose. A
`t=0.16` column, 5.6× looser than the benchmark, was printed beside it and read
as if it bracketed the answer.

Rescored correctly with the evaluator's own `unit_box_scale`, off all eight
saved objects of job 29888540:

```
pot                parts   anchor floor   raw pred   proposed
narrow_bottle4         4         25.0%      25.0%      25.0%
blue_pot               5         20.0%      30.0%      20.0%
narrow_bottle3         4         25.0%      25.0%      25.0%
narrow_bottle1        12          8.3%       8.3%      10.0%
pink_bowl              3         33.3%      33.3%      33.3%
plate                  6         16.7%      16.7%      16.7%
narrow_bottle2         3         33.3%      33.3%      33.3%
galli_pot             10         10.0%      10.0%      13.0%
MEAN                             21.5%      22.7%      22.0%
```

At the benchmark's own tolerance, correctly applied, the model seats essentially
nothing beyond the free anchor: 22.7% against a 21.5% floor is roughly one extra
fragment across eighty attempts.

**Superseded, later the same day.** The paragraph that stood here concluded
"the failure it was hiding is real" and warned against stopping at "the metric
was broken." That warning was right in spirit and wrong on the facts: there was
a *second* units bug one level deeper, in what the model is told about the
object rather than in how the answer is scored. Section 2 has it. Correcting
that one takes these same eight pots from 1.0% of fragments seated to 72.6%.

What still stands from this section: the scoring threshold really was broken,
fixing it really was necessary, and it really would have faked the same reading
on any future dataset stored in millimetres. What does not stand is the
inference drawn from the corrected number — 22.7% against a 21.5% floor was
measured on a run whose model input was still corrupted, so it was never a
measurement of what TORA can do with these pots.

## 2. RESOLVED, 2026-09-02: the ceramics failure was the storage units

**This section previously read "There is a real failure, and rotation error
shows it." That conclusion is withdrawn for every Fractura subset stored in
millimetres.** Job **29891327** settled it.

### What was actually wrong

`scales` — the object's size in whatever units its file happened to use — is
not metric bookkeeping. `tora/modeling/tora.py` reads it out of the batch and
passes it into the flow model at **every denoising step**, and the encoding
manager turns it into a sinusoidal code attached to **all 5000 points**
(`tora/modeling/flow_model/embedding.py:151`). It is a conditioning **input**.

Breaking Bad objects arrive at max|v| = 0.5 and training jitters that by
(0.75, 1.25), so the model has only ever seen this input in roughly
**[0.375, 0.625]**. The eight ceramics are stored in millimetres and arrive at
**45.3 – 120.5** — 100–190× outside the band, and far past the point where an
encoding topping out at 2^9 still separates one value from the next.

`scripts/normalize_real_hdf5.py` asserted the opposite in its header —
*"TRAINING AND INFERENCE ARE UNAFFECTED by this"* — which is why the raw-unit
subsets were never re-run. That sentence was false and has been corrected.

### The experiment

`scripts/hpc/eval_scale_ladder.slurm`, one job, one settings set. Two dataset
knobs restate the object *before* the [-1, 1] normalisation, which is exactly
what saving the scan in other units would do.
`scripts/check_scale_conditioning.py` runs first and asserts that nothing but
`scales` moves — it passed with every compared tensor **bit-identical
(0.00e+00)** on all eight pots, so a change in score cannot come from the
geometry shifting.

Non-anchor rotation error, degrees, median of 10 draws (5 on the intermediate
rungs). Only the size number differs between rows:

```
scale fed in  band  blue_pot galli_pot   nb1    nb2    nb3    nb4  pink_bowl  plate    ALL
      0.500    yes     30.5      34.8   62.3    4.3   81.8    7.8       2.4   48.7   30.8
      1.000     no     20.3      39.9   60.6    4.3   71.8    8.0       2.8   30.1   23.9
      2.500     no     45.5      39.1   73.4    4.1   73.4    7.2       3.1   28.7   30.3
      5.000     no     18.3      29.6   65.6    4.6   79.5    7.7       2.0   46.2   25.7
     15.000     no     45.4      59.1   77.2    8.5   41.7   13.3       3.0   62.4   44.6
     50.000     no     90.4      74.3   82.7   54.5   74.5   74.6      76.8   69.8   74.9
     69.217     no     83.5      66.2   87.5   82.7   90.6   71.7      85.8   88.2   81.2   <- as shipped
    100.000     no     90.4      73.9   77.8   73.7  105.9   76.0      73.5   77.7   77.8
```

The curve is flat from 0.5 to 5, bends at 15, and has collapsed by 50. It is
not a gentle degradation: there is a **cliff between scale 15 and scale 50**,
and every real Fractura subset sits on the far side of it.

### What the model can actually do with these pots

Fragments seated, at the benchmark's own tolerance in the corrected unit-box
frame, anchor subtracted. Same pots, same checkpoint, same seed:

| pot | frags | as shipped (mm) | normalised | turn, mm to normalised |
|---|---|---|---|---|
| blue_pot | 5 | 0 of 4 | **4 of 4** | 66.8° → 24.4° |
| galli_pot | 10 | 0 of 9 | **7 of 9** | 59.5° → 31.4° |
| narrow_bottle1 | 12 | 0 of 11 | **4.5 of 11** | 80.2° → 57.1° |
| narrow_bottle2 | 3 | 0 of 2 | **2 of 2** | 55.1° → 2.8° |
| narrow_bottle3 | 4 | 0 of 3 | **2.5 of 3** | 68.0° → 61.3° |
| narrow_bottle4 | 4 | 0 of 3 | **3 of 3** | 53.8° → 5.9° |
| pink_bowl | 3 | 0 of 2 | **2 of 2** | 57.2° → 1.6° |
| plate | 6 | 0 of 5 | **3 of 5** | 73.5° → 40.6° |
| **pooled** | | **4 of 390 (1.0%)** | **283 of 390 (72.6%)** | 60.4° → 26.7° |

**Corrected turn column, 2026-09-05.** The seated counts above need no change.
The turn column does — and its corrected values are already printed one table
up, as the ladder's `69.217` and `0.500` rows. Restated here so that the two
tables cannot be read against each other:

| pot | frags | seated, normalised | turn as shipped | turn normalised |
|---|---|---|---|---|
| blue_pot | 5 | 4 of 4 | 83.6° | **30.5°** |
| galli_pot | 10 | 7 of 9 | 66.2° | **34.9°** |
| narrow_bottle1 | 12 | 4.5 of 11 | 87.5° | **62.3°** |
| narrow_bottle2 | 3 | 2 of 2 | 82.7° | **4.3°** |
| narrow_bottle3 | 4 | 2.5 of 3 | 90.6° | **81.8°** |
| narrow_bottle4 | 4 | 3 of 3 | 71.7° | **7.8°** |
| pink_bowl | 3 | 2 of 2 | 85.9° | **2.4°** |
| plate | 6 | 3 of 5 | 88.2° | **48.7°** |
| **pooled** | | **283 of 390 (72.6%)** | **81.2°** | **30.8°** |

The pooled turn is the median across all eighty pot-draws, which is the
convention the original row used; it is not fragment-weighted, so it sits below
the average of the per-pot medians. The three-fragment pots move most, because
they were being flattered most.

In plain terms, on the corrected ruler: the pots that work are left turned about
**2 to 8 degrees** out of true — a tilt you would have to look for. The three
that do not work sit at **49 to 82 degrees**, between a half and a full right
angle, which is a fragment stuck on the wrong way round. The pooled **30.8
degrees** is not a typical pot; it is the two groups averaged together.


Three of the eight pots go to a complete reassembly on the typical attempt.
Fragment offset drops from about a third of the pot to 1–2% on those three.

### Looked at, not just measured

- **blue_pot as shipped:** the five fragments compacted into a flat slab, the
  green wall sheared out of the body, nothing seated. **Normalised:** a closed
  cylindrical pot with the rim fragments sitting on the rim. Against ground
  truth it is the same vessel.
- **pink_bowl as shipped:** three fragments overlapping through each other at
  roughly right angles. **Normalised:** a clean hemisphere, indistinguishable
  from ground truth at this viewing scale.

Renders: `artifacts/scaleladder_29891327/`.

### Which of the three this is

**The measurement was broken — twice, at two different depths.** First the
scoring threshold (section 1), then the model's own input. TORA can reassemble
these pots. It was being handed a description of the object it has no
vocabulary for, at every step of the reconstruction. This is not the method
failing on real fracture surfaces.

### What this does and does not overturn

- **Overturned:** every Fractura row of the old rotation table that was stored
  in millimetres — ceramics, real bones, egg. Those numbers measured the
  handicap, not the material. They must be re-run normalised before being
  quoted again.
- **Strengthened:** the real-versus-simulated refutation. The *real* bones
  carried this handicap (stored at 24) and still beat the *simulated* bones
  that did not (stored at 0.56). Removing the handicap can only widen that gap.
- **Untouched and still unexplained:** `bone_syn_pig` (61.4°) and
  `bone_syn_rib` (64.4°) are already normalised, and `coxae` fails at 85.7°
  normalised. Bones are a separate problem and this finding does not reach them.
- **Still open:** narrow_bottle1, narrow_bottle3 and plate remain poor even
  normalised (57°, 61°, 41°). Whatever else is hard about these pots, it is
  not the units. **Corrected 2026-09-05: 62°, 81.8°, 48.7° — narrow_bottle3 is
  worse than it looked, and is now the worst of the eight.**

### The old table, for the record

Rotation error is a scale-invariant *measurement* — the angle between two
orientations does not care what units the file used. What the model was *told*
about the object's size is a separate matter, and that is what these rows
confounded.

**The `rot, as reported` column is the diluted ruler; `rot, non-anchor` is
the corrected one** (2026-09-05). Two measurements of the same runs. Quote
the second.

| run | objects | rot, as reported | rot, non-anchor | status |
|---|---|---|---|---|
| Breaking Bad vessels (synthetic) | 107 | 20.9° | 22.4° | stands |
| real held-out pots, normalised | 6 | 29.9° | 35.9° | stands |
| Fractura bones — REAL fracture | 16 | 28.3° | 52.3° | **stored in mm — invalid** |
| Fractura egg — REAL fracture | 3 | 42.5° | 56.6° | **stored in mm — invalid** |
| Fractura bone_syn_pig — SIMULATED | 21 | 55.4° | 61.4° | stands (normalised) |
| Fractura bone_syn_rib — SIMULATED | 11 | 61.5° | 64.4° | stands (normalised) |
| Fractura ceramics — REAL fracture | 8 | 61.4° | 79.1° | **superseded: 30.8° normalised** (quoted as 26.7° until 2026-09-05, which was the old ruler) |

### Do not let this happen a third time

`scripts/check_scale_conditioning.py` proves the knob is clean but does not
stop anyone feeding the model an out-of-band size. Any future zero-shot subset
should have its `scales` checked against [0.375, 0.625] before its score is
read — the cliff is between 15 and 50, so anything past ~15 is already
compromised.

## What this rules out

**It is not wear.** Every Fractura object is a fresh break. The original
intuition was right on this point.

**It is not real-versus-simulated fracture surface.** Fractura's *simulated*
pig and rib bones fail at 61–64° while already normalised; Fractura's *real*
bones scored 52° while carrying the units handicap. The real subset was the
handicapped one and still came out ahead.

**It was not the ceramics' fracture surfaces at all.** Normalised, the same
eight pots go from 1.0% of fragments seated to 72.6%, and three of them
reassemble completely. See section 2.

**It is not piece count or object complexity.** Within the ceramics, per-pot
rotation error was flat against fragment count in the millimetre run — a
three-fragment bowl came out 78° wrong. That flatness was itself the tell: the
pots were not failing in proportion to their difficulty, they were all being
handed the same corrupted size input. Normalised, error does track difficulty:
the 3-fragment bowl and bottle land at 1.6° and 2.8° while the 12-fragment
bottle stays at 57°. **Corrected 2026-09-05: 2.4°, 4.3° and 62°. The point
holds, and is in fact sharper — the free-anchor dilution was largest on exactly
the few-fragment pots that score best, so it was flattening the very trend this
paragraph is drawing.**

The split was by **dataset**, and the dataset boundary was the units boundary:
everything stored in millimetres was bad, everything normalised was fine, and
our own real pots (35.9°, normalised) sat with the good group all along.

## What has not been tested

Naming these so the above is not mistaken for a full answer:

- **Orientation convention.** The Fractura configs set no `up_axis`, so they
  default to `y`. If Fractura is stored z-up this is a systematic global
  rotation. Against this: the training pipeline randomises the global rotation
  (`init_rot`), so the model should be object-pose invariant, and our own y-up
  real pots score fine. Worth ten minutes, not more.
- **Scan noise and mesh density.** Artec Spider at 0.05 mm produces surfaces
  unlike anything in Breaking Bad. This would affect real subsets only, and the
  simulated bones are also bad — so it cannot be the whole story.
- **Point budget.** 5000 points are shared across the object, allocated by
  area; blue_pot's smallest fragment gets 107. This was previously dismissed
  because error did not track piece count — but that flatness was the units bug
  masking everything else. Normalised, error *does* track fragment count
  (12-fragment bottle 57°, 3-fragment bowl 1.6°), so the point budget is back
  on the list as a candidate for the three pots that are still poor.
- **How Fractura's ground truth poses were established.** The GARF paper does
  not document it. The conservator has confirmed the ceramics are in correct
  assembly, which closes this for the ceramics but not for the bones and eggs.
- **The renders.** Four have been looked at across the two arms: blue_pot and
  pink_bowl, as shipped and normalised (section 2). Both show the same thing —
  an interpenetrating slab in the millimetre run, a coherent vessel in the
  normalised one. Four is not sixteen.

## Weight this can bear

**The units finding is the firm part.** Eight pots, 10 draws each, one
checkpoint, and a controlled comparison: same file, same meshes, same seed,
same settings, one job — with a gate asserting that every tensor except the
size number was bit-identical between the two arms. An eight-rung ladder shows
where the cliff is (between 15 and 50) rather than only that the endpoints
differ. That is about as tight as this can be made without a second checkpoint,
and it is a statement about the software, not about ceramics.

**What it does not establish** is how well TORA reassembles real broken pottery.
72.6% of fragments seated on eight modern breaks, one model, is a lead. These
are fresh fractures with no burial wear, so they still say nothing about the
buried-sherd case — the Juglet remains the only object here that is both really
broken and really worn. And three of the eight pots stay poor normalised.

**One methodological point worth keeping.** The only reason this cost 13 GPU
minutes rather than another week is that `eval_ceramics_arms.slurm` had been
changed to save every sample's point clouds (`max_samples_per_batch: 8`), so a
scoring mistake could be repaired from disk. That paid for itself twice.

**And the pattern to distrust.** Both errors here were units errors, both
survived rounds of numeric checking, and both produced numbers that looked like
a scientific finding. The second one hid *behind the first*: fixing the ruler
and re-reading the same corrupted run felt like confirmation. A flat result
across objects of very different difficulty is a symptom of a broken input, not
evidence of a uniform weakness.
