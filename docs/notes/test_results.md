# TORA Follow-up Experiments

> ## ⚠️ CORRECTION (2026-09-05) — all three conclusions stand, but **every
> ## confidence-gate threshold in this note must be roughly doubled**
>
> **Which of the three: the measurement was broken.** The evaluator skipped the
> anchor fragment when summing but divided by the **total** fragment count
> (`eval/metrics.py:compute_transform_errors`, lines 245 and 293–295), so every
> stored `rotation_error` **and** `translation_error` carried a free zero:
> ×2.000 at two fragments, ×1.111 at ten. `recall@5°/10°/1cm/5cm` were then
> thresholded on those diluted means, so the two errors compound.
>
> **The consequence specific to this note.** Tests 1 and 3 are built on
> *thresholds*: "fail if ≥ 30°", "accept if the spread across generations is
> < 0.5°". A threshold on a diluted number is not the threshold it claims to be,
> and the **spread is diluted by the same factor as the values** — so a gate
> written as `std < 0.5°` was in practice about `std < 1°` on the corrected
> scale. **Coverage at the strictest gate falls from 64 % to 36 %** on
> thin-walled and from 58 % to 14 % at N=10 — not because the method got worse,
> but because the gate got stricter when the ruler was fixed.
>
> **Read the gate rows by matching coverage, not by matching the number written
> in the threshold column.** Corrected `std < 1°` reproduces almost exactly what
> was printed as `std < 0.5°`, and it still carries the finding: on the
> confident two-thirds, mean error **1.09°** and **0.3 %** hard failures.
>
> **All three headline conclusions survive** — the zero-shot gap is real but
> bounded, N=5 is the sweet spot, and the agreement gate is well calibrated
> across the domain shift. What moves is the size of each gap and the numeric
> value of every threshold.
>
> Recomputed, not estimated: all 61 648 result files for jobs 24194551,
> 24255302 and 24289835 were fetched back and every printed figure regenerates
> from them exactly. Ticket `.scratch/eval-readout/issues/03`; the full write-up
> of the bug is the 2026-09-05 banner in `TORA_GOOD_VS_BAD_ANALYSIS.md`.

Three tests proposed in [analysis_failure_patterns.md](analysis_failure_patterns.md) § "Next experiments worth running", using the pretrained `bbad_everyday_cka.ckpt` checkpoint.

| Test | Status | Job ID |
|---|---|---|
| 1. Zero-shot on `bbad_artifact` | ✅ done | 24255302 (1h 16m) |
| 2. Best-of-N sweep (N = 1, 3, 5, 10) | ✅ done | 24289835 (3h 41m) |
| 3. Confidence-gated accuracy | ✅ done (post-hoc analysis) | — |

---

## Test 1: Zero-shot on `bbad_artifact`

### Question
How much does TORA's accuracy drop when it's evaluated on a fracture distribution it was *not* trained on? Specifically, how close is the pretrained `bbad_everyday_cka.ckpt` to "archaeological conditions"?

### Method
- Checkpoint: `bbad_everyday_cka.ckpt` (trained on Breaking Bad *everyday* subset — household objects, simulated fractures).
- Eval set: 3738 samples from Breaking Bad *artifact* subset (Byzantine pottery / archaeological scans, real fractures), filtered to `max_parts <= 20` as per the shipped `config/data/zeroshot/bbad_artifact.yaml` (drops 2 samples → 3736 eval set, 3697 after pipeline filters).
- 3 stochastic generations per input.
- Same viz overrides as Test 3 (1 rendered sample per batch).

### Headline metrics (best-of-3 across 3697 samples)

| Metric | Artifact (zero-shot) avg | Artifact (zero-shot) BoN | Thin-walled (in-domain) BoN | Absolute gap |
|---|---|---|---|---|
| part_accuracy | 0.928 | 0.943 | 0.973 | **−3.0 pp** |
| rotation_error | 11.14° | **8.30°** | 5.30° | **+3.0°** |
| translation_error | 2.79 cm | 2.11 cm | 1.38 cm | +0.7 cm |
| recall@5° | 0.681 | 0.719 | 0.820 | **−10.1 pp** |
| recall@10° | 0.728 | 0.770 | 0.849 | −7.9 pp |
| recall@1cm | 0.661 | 0.702 | 0.793 | −9.1 pp |
| recall@5cm | 0.786 | 0.829 | 0.894 | −6.5 pp |
| object_chamfer | 0.0002 m | 0.0002 m | 0.0000 m | negligible |

The zero-shot gap is **real but bounded**: ~3° more rotation error, ~6-10 pp drop in recall at tight tolerances. Object-chamfer stays near zero (assembled *silhouette* is still correct — it's pose, not shape, that degrades).

**Corrected 2026-09-05**, recomputed from the same result files. `part_accuracy`
is restated as **seating** — the fraction of the *loose* fragments placed, with
the free anchor removed, so it starts at zero rather than at 1/n:

| Metric | Artifact avg | Artifact BoN | Thin-walled BoN | Absolute gap |
|---|---|---|---|---|
| fragments seated (loose) | 0.909 | **0.930** | **0.970** | **−4.0 pp** |
| mean turn | 14.30° | **10.36°** | **6.16°** | **+4.2°** |
| mean offset | 3.64 cm | **2.69 cm** | **1.65 cm** | **+1.04 cm** |
| recall@5° | — | **0.690** | **0.807** | **−11.7 pp** |
| recall@10° | — | **0.745** | **0.843** | −9.8 pp |
| recall@1cm | — | **0.665** | **0.760** | −9.5 pp |
| recall@5cm | — | **0.801** | **0.885** | −8.4 pp |
| object_chamfer | 0.00024 m | — | 0.00003 m | unchanged |

**The conclusion is unchanged and the gap is about 40 % larger than printed.**
On archaeological-style fractures the method leaves the average sherd **10°
out rather than 6°** and about **2.7 cm out of place rather than 1.7 cm** —
both of which a conservator would see immediately on a 15 cm vessel. Every one
of the four recall rows widens, because they threshold the diluted means and so
were doubly flattered. Object-chamfer is untouched by this bug (it does not go
through the anchor loop) and its reading stands: the assembled *outline* is
right; it is pose that degrades.

### The same failure cliff, shifted earlier

Failure rate (rot_bon ≥ 30°) as a function of piece count:

| Pieces | Thin-walled (in-domain) | Artifact (zero-shot) |
|---|---|---|
| 2 | 0.0 % | **0.4 %** |
| 3-5 | 0.4 % | **8.4 %** |
| 6-10 | 19 % | **42 %** |
| 11-20 | 48 % | **70 %** |

The cliff isn't *later* on artifact — it's at the same ~6-piece mark, but **twice as steep**. Already at 3-5 pieces we see a 20× jump in failure rate vs in-domain. Mean rot_err at 6-10 pieces: 26.48° on artifact vs ~15° on thin-walled. Archaeological-style fractures hurt TORA even before combinatorial complexity kicks in.

Corrected 2026-09-05 — the 30° bar applied to the corrected turn:

| Pieces | N (art) | Thin-walled **corrected** | Artifact **corrected** | mean turn, artifact |
|---|---|---|---|---|
| 2 | 1849 | 0.0 % | **0.9 %** | 1.74° |
| 3-5 | 1223 | 0.7 % | **12.5 %** | 10.88° |
| 6-10 | 450 | 24.5 % | **47.8 %** | 30.53° |
| 11-20 | 175 | 51.8 % | **73.7 %** | 45.83° |

**The finding holds throughout and every number is worse.** At three to five
fragments — the everyday conservation case — archaeological-style breaks fail
**one time in eight** against one time in 140 for simulated household breaks:
an **18× penalty**, not 20×, and on a base rate that itself doubled. From six
fragments up, **roughly half** of real-style breaks come out with the average
sherd more than 30° from correct, and at eleven-plus it is **three in four**.
Mean turn at 6-10 pieces is **30.5° on artifact against 18.7° on thin-walled**.

### Confidence gate still works — with reduced coverage

| Gate (`std` across 3 gens) | Coverage | Mean rot_bon° | Fail@30° | Fail@10° |
|---|---|---|---|---|
| `std < 0.5°` | **54.7 %** | **0.59°** | 0.1 % | 0.4 % |
| `std < 1°` | 64.6 % | 0.99° | 0.5 % | 1.3 % |
| `std < 2°` | 69.9 % | 1.79° | 1.5 % | 3.4 % |
| `std < 5°` | 81.2 % | 4.49° | 5.3 % | 11.6 % |
| No gate | 100.0 % | 8.30° | 11.4 % | 23.0 % |

> **⚠️ Corrected 2026-09-05 — the threshold values are not transferable; the
> coverages are.** The spread across generations is diluted by the same factor
> as the values it is a spread of, so a gate written `std < 0.5°` was in
> practice about `std < 1°` on the corrected scale. On the corrected ruler:
>
> | Gate (`std` across 3 gens) | Coverage | Mean turn | Fail@30° | Fail@10° |
> |---|---|---|---|---|
> | `std < 0.5°` | **30.9 %** | 1.10° | 0.2 % | 1.0 % |
> | `std < 1°` | **57.7 %** | 1.24° | 0.5 % | 1.1 % |
> | `std < 2°` | 66.7 % | 1.93° | 1.3 % | 2.9 % |
> | `std < 5°` | 77.5 % | 4.97° | 5.3 % | 11.1 % |
> | No gate | 100.0 % | 10.36° | 13.9 % | 25.5 % |
>
> **The corrected `std < 1°` row is what the printed `std < 0.5°` row was
> describing**: 58 % coverage, half a percent of hard failures. Compare rows at
> matched coverage, not matched threshold, and the finding is intact.

Compared to thin-walled (Test 3):
- **Coverage at `std < 0.5°` drops from 64 % → 55 %** — fewer samples pass the strict gate.
- **But on the passing subset, performance is equally clean** — 0.1 % hard-fail vs thin-walled's 0.0 %, mean 0.59° vs 0.56°.

*(Corrected 2026-09-05: at the matched corrected gate `std < 1°`, coverage drops
**68 % → 58 %** from thin-walled to artifact, and hard-fail on the passing subset
is **0.5 % vs 0.3 %** with mean turn **1.24° vs 1.09°**. Same comparison, same
verdict.)*

The agreement-based confidence score generalises across dataset shifts. You lose coverage (the model is confident less often) but not calibration (when it *is* confident, it's still right). This is the key result for practical deployment.

### Interpretation

1. **TORA generalises to out-of-distribution fractures, with ~3° rotation penalty.** Not catastrophic, but visible. *(Corrected 2026-09-05: **~4.2°**, on a base that is itself larger — 6.2° in-domain, 10.4° zero-shot.)*
2. **Piece-count cliff sharpens under domain shift**: the same cliff exists, but is ~2× steeper at every bucket. Zero-shot high-piece-count samples are essentially unrecoverable (70 % fail at 11-20 pieces). *(Corrected: **74 %**.)*
3. **Agreement-gate remains well-calibrated zero-shot**: confidence is meaningful even outside the training distribution. This validates the practical protocol across domains.
4. **For the 40-piece tray**: artifact is the closest proxy we have to archaeological breaks. Even here, >20 pieces appears so rarely that TORA has essentially no evidence of behaviour in that regime. Expect zero-shot + high-piece-count = worst-of-both-worlds.

### Files
- SLURM script: [eval_artifact_zeroshot.slurm](eval_artifact_zeroshot.slurm)
- Log: [tora_artifact_24255302.log](tora_artifact_24255302.log)
- Per-sample JSONs: `eval_runs/artifact_zeroshot_24255302/results/`
- Viz (PNGs): `eval_runs/artifact_zeroshot_24255302/visualizations/` (1 sample per batch × 232 batches × 5 views ≈ 1160 PNGs)

---

## Test 2: Best-of-N sweep

### Question
Does running TORA more times (more stochastic retries) push the failure cliff outward, or does it just reduce variance on the easy regime where the model already works?

### Method
- One run with `model.n_generations=10` on full thin-walled (3889 samples × 10 generations = 38,890 result JSONs).
- N=1/3/5/10 curves derived post-hoc by filtering `generation_idx < N` per sample and recomputing best-of-N statistics — no need for separate jobs.
- Same checkpoint and config as Tests 1 & 3.

### Best-of-N curves — full thin-walled

| Metric | N=1 | N=3 | N=5 | N=10 | Δ(10−1) |
|---|---|---|---|---|---|
| rotation_error (°) | 7.12 | 5.39 | 4.79 | **4.12** | **−3.01** |
| translation_error (cm) | 1.86 | 1.41 | 1.25 | 1.07 | −0.80 |
| part_accuracy | 0.966 | 0.972 | 0.975 | 0.978 | +0.011 |
| recall@5° | 0.793 | 0.822 | 0.832 | 0.843 | +0.050 |
| recall@1cm | 0.757 | 0.793 | 0.805 | 0.818 | +0.061 |

10× compute buys ~3° lower rotation error and ~5 pp recall@5°. Real but not huge.

Corrected 2026-09-05:

| Metric | N=1 | N=3 | N=5 | N=10 | Δ(10−1) |
|---|---|---|---|---|---|
| mean turn (°) | **8.45** | **6.26** | **5.52** | **4.69** | **−3.76** |
| mean offset (cm) | **2.24** | **1.67** | **1.47** | **1.25** | −0.99 |
| fragments seated (loose) | **0.962** | **0.969** | **0.972** | **0.975** | +0.013 |
| recall@5° | **0.770** | **0.809** | **0.821** | **0.832** | +0.062 |
| recall@1cm | **0.693** | **0.758** | **0.778** | **0.797** | **+0.104** |

**Same shape, slightly larger payoff.** Ten tries buys **3.8° and about a
centimetre** rather than 3.0° and 0.8 cm. The one row that changes character is
`recall@1cm`: corrected, retries lift it by **10 points rather than 6**, because
the offsets it thresholds were the most flattered by the free zero.

### The cliff *does* shift outward — for moderate piece counts

Failure rate (rot_bon ≥ 30°), per-bucket × N:

| Pieces | N | N=1 | N=3 | N=5 | N=10 |
|---|---|---|---|---|---|
| 2 | 2012 | 0.0 % | 0.0 % | 0.0 % | 0.0 % |
| 3-5 | 1095 | 2.6 % | 0.8 % | 0.5 % | **0.1 %** |
| **6-10** | 437 | **35.5 %** | 24.7 % | 18.8 % | **12.4 %** |
| **11-29** | 345 | **59.7 %** | 49.0 % | 43.5 % | **35.7 %** |

Corrected 2026-09-05:

| Pieces | N | N=1 | N=3 | N=5 | N=10 |
|---|---|---|---|---|---|
| 2 | 2012 | 0.2 % | 0.0 % | 0.0 % | 0.0 % |
| 3-5 | 1095 | **3.0 %** | 1.6 % | 1.1 % | **0.4 %** |
| **6-10** | 437 | **38.9 %** | 30.7 % | 23.8 % | **17.4 %** |
| **11-29** | 345 | **62.9 %** | 52.5 % | 47.5 % | **41.2 %** |

- **6-10 pieces**: 38.9 % → 17.4 %. **~2.2× improvement**, not 3× — retries help substantially but less than printed.
- **11-29 pieces**: 62.9 % → 41.2 %. Cut by a third, not halved. **Still catastrophic**, and this is the row that matters for a real tray.
- **3-5 pieces**: 3.0 % → 0.4 %. Still essentially cleaned up by N=10.

**The correction is largest at low piece count, so it compresses exactly the
retry gains this table was drawn to celebrate.** Direction and recommendation
unchanged; the payoff is about a third smaller than reported.

The cliff doesn't move; it's blunted. With enough retries TORA can eventually find the right answer for moderate-piece problems, but high-piece problems remain fundamentally limited.

### Hard regime detail (≥6 pieces only, N = 782)

| Metric | N=1 | N=3 | N=5 | N=10 | Δ |
|---|---|---|---|---|---|
| rotation_error (°) | 28.74 | 22.99 | 20.83 | **18.29** | −10.45 |
| recall@5° | 0.165 | 0.215 | 0.238 | 0.272 | +0.107 |
| recall@1cm | 0.128 | 0.165 | 0.184 | 0.216 | +0.088 |

Corrected 2026-09-05:

| Metric | N=1 | N=3 | N=5 | N=10 | Δ |
|---|---|---|---|---|---|
| mean turn (°) | **31.74** | **25.35** | **22.94** | **20.13** | **−11.61** |
| recall@5° | 0.151 | 0.199 | 0.219 | **0.252** | +0.101 |
| recall@1cm | 0.109 | 0.146 | 0.166 | **0.192** | +0.083 |

Hard regime gains the most from extra retries in *absolute* terms (10° rotation reduction!), but absolute performance stays low — recall@5° tops out at 27 % even with N=10.

*(Corrected: **11.6°** of gain, and the ceiling is **25 %**, not 27 %. On six or
more fragments, ten retries still leave the average sherd **20° out — a fifth of
a right angle — and three quarters of these objects never come within 5°.**)*

### Diminishing returns

Mean best-of-K rotation error vs K (full thin-walled):

| N | Mean rot° | Δ vs N−1 |
|---|---|---|
| 1 | 7.13 | — |
| 2 | 5.99 | −1.13 |
| **3** | **5.39** | **−0.60** |
| 4 | 5.02 | −0.38 |
| **5** | **4.80** | **−0.22** |
| 6 | 4.61 | −0.19 |
| 7 | 4.43 | −0.17 |
| 8 | 4.31 | −0.12 |
| 9 | 4.21 | −0.10 |
| **10** | **4.12** | **−0.09** |

Corrected 2026-09-05 — **8.45 / 7.01 / 6.26 / 5.80 / 5.52 / 5.29 / 5.08 / 4.93 /
4.80 / 4.69°** at N = 1…10, with steps −1.44, −0.75, −0.46, −0.28, −0.23, −0.21,
−0.15, −0.13, −0.11. The decay shape is identical and **N=5 remains the
practical sweet spot**: N=1→5 captures 2.93° of the 3.76° total, N=5→10 adds
0.83° for twice the compute.

Marginal gain decays roughly inversely. Going from N=1→3 saves 1.7° (cheap). N=3→5 saves 0.6° (modest). N=5→10 saves 0.7° but at 2× compute (expensive). N=5 is the practical sweet spot.

In the hard regime the same shape holds but with a longer tail (N=10 is still gaining 0.37°/step), suggesting that **on hard inputs, even N>10 might continue to help** — though absolute performance stays poor.

### Confidence gate scales with N

Comparing the gate behaviour at N=3 (Test 3) vs N=10 (this test):

| Gate (`std` across all N gens) | Coverage (N=3) | Coverage (N=10) | Mean rot°(N=10) | Fail@30°(N=10) |
|---|---|---|---|---|
| `std < 0.5°` | 64.2 % | **57.8 %** | **0.21°** | **0.0 %** |
| `std < 1°` | 74.9 % | 70.6 % | 0.27° | 0.0 % |
| `std < 2°` | 79.4 % | 75.2 % | 0.33° | 0.0 % |
| `std < 5°` | 88.9 % | 82.4 % | 0.89° | 0.3 % |

> **⚠️ Corrected 2026-09-05 — this is the table the correction changes most.**
> A spread across ten generations is diluted exactly as the values are, so the
> strict gate tightens sharply once the ruler is fixed:
>
> | Gate (`std` across all N gens) | Coverage (N=10) | Mean turn (N=10) | Fail@30° |
> |---|---|---|---|
> | `std < 0.5°` | **13.7 %** | 0.58° | 0.0 % |
> | `std < 1°` | **61.3 %** | 0.39° | 0.0 % |
> | `std < 2°` | 72.4 % | 0.47° | 0.0 % |
> | `std < 5°` | 80.5 % | 0.92° | 0.3 % |
>
> **`std < 0.5°` at N=10 is no longer a usable gate — it accepts one input in
> seven.** The corrected `std < 1°` row is the one to use: **61 % coverage, mean
> turn 0.39°, not a single hard failure in 2383 accepted objects.** The
> conclusion below — more retries give a smaller, cleaner confident set — is
> unchanged; only the number to type into the threshold has moved.

Two effects:

1. **Coverage drops slightly** (64 % → 58 % at the strictest gate) — with 10 samples there's more chance one will disagree, so fewer pass the strict threshold.
2. **But on the passing subset, accuracy *improves*** — mean rot°: 0.56° (N=3) → 0.21° (N=10), since the larger ensemble has a better best-of-N estimate.

Net: more retries → smaller, *cleaner* confident set. If your goal is "high-precision when confident, defer otherwise", N=10 is strictly better than N=3 at the cost of 3.3× compute.

### Headlines

1. **N=5 is the production sweet spot.** N=1→5 captures most of the gain (7.13° → 4.80°); N=5→10 only adds 0.67° for 2× compute.
2. **The cliff is blunted but not eliminated.** Even at N=10, 36 % of high-piece samples fail.
3. **Best-of-N is a free axis of improvement** — only requires more inference passes, no training, no architecture change.
4. **Confidence gate gets *more* selective and *more* accurate with more retries** — useful for production safety, not for raising raw average performance.
5. **Implication for the 40-piece tray**: budget for ≥5 retries per assembly attempt. Combine with `std < 1°` agreement gate for the cleanest practical workflow.

### Files
- SLURM script: [eval_bestofN.slurm](eval_bestofN.slurm)
- Log: [tora_bestofN_24289835.log](tora_bestofN_24289835.log)
- Per-sample JSONs (3889 × 10 = 38,890): `eval_runs/bestofN_24289835/results/`

---

## Test 3: Confidence-gated accuracy

### Question
If we only accept TORA's output when its 3 stochastic generations agree with each other, how accurate is the *accepted* subset — and what coverage do we pay for that accuracy?

### Method
- Dataset: 3889 thin-walled pottery samples with 3 generations each, from [eval_runs/thinwalled_24194551/results/](eval_runs/thinwalled_24194551/results/).
- Per sample, compute `std(rot_err)` across the 3 generations — the **agreement score**. Low std = generations agree = "confident" prediction.
- Apply an agreement gate: accept a sample only if `std < threshold`.
- Report the accepted subset's metrics + what fraction of the dataset it covers.
- Pure post-hoc analysis, no GPU.

### Result — overall (all piece counts, N = 3889)

| Gate | Coverage | Mean rot_bon° | p90° | Fail@30° | Fail@10° |
|---|---|---|---|---|---|
| `std < 0.5°` | **63.9 %** | **0.56°** | 1.24° | **0.0 %** | 0.3 % |
| `std < 1°` | 75.3 % | 0.77° | 1.47° | 0.2 % | 0.9 % |
| `std < 2°` | 80.0 % | 1.19° | 1.68° | 0.7 % | 2.1 % |
| `std < 5°` | 88.2 % | 2.92° | 4.06° | 3.2 % | 7.4 % |
| No gate | 100.0 % | 5.30° | 21.22° | 6.5 % | 15.1 % |

Corrected 2026-09-05:

| Gate | Coverage | Mean turn | p90 | Fail@30° | Fail@10° |
|---|---|---|---|---|---|
| `std < 0.5°` | **36.5 %** | 1.03° | 2.07° | **0.0 %** | 0.5 % |
| **`std < 1°`** | **67.6 %** | **1.09°** | **2.12°** | **0.3 %** | 0.8 % |
| `std < 2°` | 77.6 % | 1.53° | 2.41° | 0.8 % | 2.0 % |
| `std < 5°` | 86.4 % | 3.23° | 4.39° | 3.3 % | 6.8 % |
| No gate | 100.0 % | 6.16° | 24.54° | 7.7 % | 15.7 % |

On the **confident 64 %** of inputs TORA commits **zero hard failures** and mean error is **sub-degree**. The remaining 36 % of inputs account for essentially *all* of the 6.5 % hard-failure rate.

*(Corrected: the same claim is carried by the `std < 1°` row — **on the confident
68 % of inputs the method hard-fails 3 times in a thousand and the average sherd
is about one degree out**, against a 7.7 % failure rate ungated. The printed
`std < 0.5°` gate now accepts only 37 %; it is stricter than intended, not
better.)*

### Result — hard regime only (≥6 pieces, N = 782)

This is where the failure cliff kicks in. Without any gate, nearly a third of these fail.

| Gate | N accepted | Coverage | Mean rot_bon° | p90° | Fail@30° | Fail@10° |
|---|---|---|---|---|---|---|
| `std < 0.5°` | 72 | 9.2 % | 3.09° | 3.70° | 1.4 % | 6.9 % |
| `std < 1°` | 115 | 14.7 % | 5.77° | 16.13° | 4.3 % | 15.7 % |
| `std < 2°` | 181 | 23.1 % | 10.32° | 34.56° | 11.6 % | 29.8 % |
| `std < 5°` | 416 | 53.2 % | 18.66° | 44.89° | 26.0 % | 55.3 % |
| No gate | 782 | 100.0 % | 22.55° | 46.86° | 31.8 % | 69.1 % |

Corrected 2026-09-05:

| Gate | N accepted | Coverage | Mean turn | p90 | Fail@30° | Fail@10° |
|---|---|---|---|---|---|---|
| `std < 0.5°` | 63 | 8.1 % | 2.95° | 3.89° | **0.0 %** | 6.3 % |
| `std < 1°` | 104 | 13.3 % | 5.81° | 13.14° | 4.8 % | 13.5 % |
| `std < 2°` | 166 | 21.2 % | 11.25° | 38.49° | 13.9 % | 28.3 % |
| `std < 5°` | 380 | 48.6 % | 19.83° | 49.09° | 28.4 % | 54.2 % |
| No gate | 782 | 100.0 % | **24.84°** | 50.78° | **37.2 %** | 70.5 % |

The gate still works but coverage collapses: at `std < 1°`, only **15 %** of hard samples pass — and even on those the hard-fail rate is 4.3 %, not zero. The confidence signal is **informative but weaker** when the input is already difficult.

*(Corrected: 13 % coverage, 4.8 % hard-fail. The ungated hard regime is worse
than printed — **37 % of six-or-more-fragment objects fail outright and the
average one is 25° out.** The section's conclusion is unchanged and firmer: on
genuinely hard inputs, agreement between runs buys you a small, still-imperfect
accepted set.)*

### Agreement gate as a failure predictor

Treating `rot_bon ≥ 30°` as ground-truth failure, use `std ≥ K` as the predictor.

| Gate | Precision | Recall | F1 |
|---|---|---|---|
| `std ≥ 1°` | 25.8 % | **98.0 %** | 40.9 % |
| `std ≥ 2°` | 29.9 % | 91.7 % | 45.0 % |
| `std ≥ 5°` | 31.4 % | 56.9 % | 40.4 % |
| `std ≥ 10°` | 21.7 % | 12.3 % | 15.7 % |

*(Corrected 2026-09-05 — **23.3 % / 97.7 % / 37.6 %**, **31.6 % / 91.7 % /
47.0 %**, **35.9 % / 63.0 % / 45.7 %**, **28.3 % / 19.3 % / 23.0 %**. The
load-bearing row is unmoved: `std ≥ 1°` still catches **98 % of true failures**.
This is the most robust result in the note, and the one that works without any
ground truth.)*

**Read as a safety filter, not a failure classifier**: `std ≥ 1°` catches 98 % of true failures (almost nothing slips through) at the cost of flagging many benign cases too. The ratio is what you want for *abstention* — you'd rather over-flag and send borderline cases to a human than let a failure through.

### Alternative: using `range(rot_err)` instead of `std`

`range` (max − min across 3 gens) is more intuitive and slightly more conservative:

| Gate | Coverage | Mean rot_bon° | Fail@30° | Fail@10° |
|---|---|---|---|---|
| `range < 1°` | 56.4 % | 0.53° | 0.0 % | 0.2 % |
| `range < 2°` | 73.7 % | 0.69° | 0.1 % | 0.6 % |
| `range < 5°` | 80.5 % | 1.26° | 0.8 % | 2.3 % |
| `range < 10°` | 86.6 % | 2.52° | 2.5 % | 6.1 % |

Corrected 2026-09-05 — again the threshold roughly doubles, the behaviour does not:

| Gate | Coverage | Mean turn | Fail@30° | Fail@10° |
|---|---|---|---|---|
| `range < 1°` | 30.5 % | 1.03° | 0.0 % | 0.4 % |
| **`range < 2°`** | **61.1 %** | **1.08°** | **0.2 %** | 0.7 % |
| `range < 5°` | 78.3 % | 1.61° | 1.0 % | 2.3 % |
| `range < 10°` | 85.1 % | 2.91° | 2.8 % | 5.9 % |

`range < 1°` keeps 56 % coverage with **0 hard failures** and 0.2 % soft-fail rate. Stricter than `std < 0.5°` on coverage but equally clean.

*(Corrected: use **`range < 2°`** — 61 % coverage, 0.2 % hard failures. It is the
same gate the printed `range < 1°` row described.)*

### Headline

> On the 64 % of inputs where TORA's 3 generations agree within 0.5°, it is **effectively perfect** (0 hard failures, mean error 0.56°, p90 = 1.24°). All of the dataset-wide 6.5 % failure rate lives in the other 36 %.

> **Corrected 2026-09-05:** on the **68 %** of inputs where the three runs agree
> **within 1°**, the method is effectively perfect — **3 hard failures per
> thousand, mean error 1.09°, p90 2.12°**. Essentially all of the dataset-wide
> **7.7 %** failure rate lives in the other 32 %. Same headline; the agreement
> threshold that delivers it is **1°, not 0.5°**.

### Practical protocol

1. **Run inference N ≥ 3 times** per input (different random noise each time).
2. **Compute per-sample agreement**: `std` or `range` of the rotation-error against GT, or — if no GT — a proxy like pairwise Chamfer distance between predicted assemblies.
3. **Accept only confident predictions** (std < 0.5° or range < 1°). Send the rest for human review.
   *(Corrected 2026-09-05: **std < 1° or range < 2°** on figures produced by the
   fixed evaluator. The older thresholds were computed on numbers carrying a free
   zero; applied to corrected numbers they reject roughly half of what they
   should accept.)*
4. On the accepted subset, treat TORA's output as trustworthy.

### Caveat for the 40-piece tray

This analysis computed `std` on ground-truth-referenced error (`rot_err_gen_i` vs GT). In production on your tray you don't have GT. Substitute: pairwise Chamfer distance between the N predicted assemblies, or per-part pose-vector variance across generations. The findings above validate that *agreement across generations* is a usable signal — the specific statistic can vary.

Also: because most thin-walled hard cases (≥6 pieces) are in the "low agreement" bucket by nature, expect the tray's 40-piece regime to have **low coverage** even with aggressive retries. You'll get a few sherds where the model is confident (accept those) and many where it isn't (defer to archaeologist). This is the realistic outcome.
