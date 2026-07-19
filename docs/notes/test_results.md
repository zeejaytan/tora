# TORA Follow-up Experiments

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

### The same failure cliff, shifted earlier

Failure rate (rot_bon ≥ 30°) as a function of piece count:

| Pieces | Thin-walled (in-domain) | Artifact (zero-shot) |
|---|---|---|
| 2 | 0.0 % | **0.4 %** |
| 3-5 | 0.4 % | **8.4 %** |
| 6-10 | 19 % | **42 %** |
| 11-20 | 48 % | **70 %** |

The cliff isn't *later* on artifact — it's at the same ~6-piece mark, but **twice as steep**. Already at 3-5 pieces we see a 20× jump in failure rate vs in-domain. Mean rot_err at 6-10 pieces: 26.48° on artifact vs ~15° on thin-walled. Archaeological-style fractures hurt TORA even before combinatorial complexity kicks in.

### Confidence gate still works — with reduced coverage

| Gate (`std` across 3 gens) | Coverage | Mean rot_bon° | Fail@30° | Fail@10° |
|---|---|---|---|---|
| `std < 0.5°` | **54.7 %** | **0.59°** | 0.1 % | 0.4 % |
| `std < 1°` | 64.6 % | 0.99° | 0.5 % | 1.3 % |
| `std < 2°` | 69.9 % | 1.79° | 1.5 % | 3.4 % |
| `std < 5°` | 81.2 % | 4.49° | 5.3 % | 11.6 % |
| No gate | 100.0 % | 8.30° | 11.4 % | 23.0 % |

Compared to thin-walled (Test 3):
- **Coverage at `std < 0.5°` drops from 64 % → 55 %** — fewer samples pass the strict gate.
- **But on the passing subset, performance is equally clean** — 0.1 % hard-fail vs thin-walled's 0.0 %, mean 0.59° vs 0.56°.

The agreement-based confidence score generalises across dataset shifts. You lose coverage (the model is confident less often) but not calibration (when it *is* confident, it's still right). This is the key result for practical deployment.

### Interpretation

1. **TORA generalises to out-of-distribution fractures, with ~3° rotation penalty.** Not catastrophic, but visible.
2. **Piece-count cliff sharpens under domain shift**: the same cliff exists, but is ~2× steeper at every bucket. Zero-shot high-piece-count samples are essentially unrecoverable (70 % fail at 11-20 pieces).
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

### The cliff *does* shift outward — for moderate piece counts

Failure rate (rot_bon ≥ 30°), per-bucket × N:

| Pieces | N | N=1 | N=3 | N=5 | N=10 |
|---|---|---|---|---|---|
| 2 | 2012 | 0.0 % | 0.0 % | 0.0 % | 0.0 % |
| 3-5 | 1095 | 2.6 % | 0.8 % | 0.5 % | **0.1 %** |
| **6-10** | 437 | **35.5 %** | 24.7 % | 18.8 % | **12.4 %** |
| **11-29** | 345 | **59.7 %** | 49.0 % | 43.5 % | **35.7 %** |

- **6-10 pieces**: failure rate cut from 35.5 % (N=1) → 12.4 % (N=10). **~3× improvement** — the model can solve these *if* given enough tries.
- **11-29 pieces**: 59.7 % → 35.7 %. Halved, but still catastrophic. More retries help but don't fix the regime.
- **3-5 pieces**: 2.6 % → 0.1 %. Almost entirely cleaned up by N=10.

The cliff doesn't move; it's blunted. With enough retries TORA can eventually find the right answer for moderate-piece problems, but high-piece problems remain fundamentally limited.

### Hard regime detail (≥6 pieces only, N = 782)

| Metric | N=1 | N=3 | N=5 | N=10 | Δ |
|---|---|---|---|---|---|
| rotation_error (°) | 28.74 | 22.99 | 20.83 | **18.29** | −10.45 |
| recall@5° | 0.165 | 0.215 | 0.238 | 0.272 | +0.107 |
| recall@1cm | 0.128 | 0.165 | 0.184 | 0.216 | +0.088 |

Hard regime gains the most from extra retries in *absolute* terms (10° rotation reduction!), but absolute performance stays low — recall@5° tops out at 27 % even with N=10.

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

On the **confident 64 %** of inputs TORA commits **zero hard failures** and mean error is **sub-degree**. The remaining 36 % of inputs account for essentially *all* of the 6.5 % hard-failure rate.

### Result — hard regime only (≥6 pieces, N = 782)

This is where the failure cliff kicks in. Without any gate, nearly a third of these fail.

| Gate | N accepted | Coverage | Mean rot_bon° | p90° | Fail@30° | Fail@10° |
|---|---|---|---|---|---|---|
| `std < 0.5°` | 72 | 9.2 % | 3.09° | 3.70° | 1.4 % | 6.9 % |
| `std < 1°` | 115 | 14.7 % | 5.77° | 16.13° | 4.3 % | 15.7 % |
| `std < 2°` | 181 | 23.1 % | 10.32° | 34.56° | 11.6 % | 29.8 % |
| `std < 5°` | 416 | 53.2 % | 18.66° | 44.89° | 26.0 % | 55.3 % |
| No gate | 782 | 100.0 % | 22.55° | 46.86° | 31.8 % | 69.1 % |

The gate still works but coverage collapses: at `std < 1°`, only **15 %** of hard samples pass — and even on those the hard-fail rate is 4.3 %, not zero. The confidence signal is **informative but weaker** when the input is already difficult.

### Agreement gate as a failure predictor

Treating `rot_bon ≥ 30°` as ground-truth failure, use `std ≥ K` as the predictor.

| Gate | Precision | Recall | F1 |
|---|---|---|---|
| `std ≥ 1°` | 25.8 % | **98.0 %** | 40.9 % |
| `std ≥ 2°` | 29.9 % | 91.7 % | 45.0 % |
| `std ≥ 5°` | 31.4 % | 56.9 % | 40.4 % |
| `std ≥ 10°` | 21.7 % | 12.3 % | 15.7 % |

**Read as a safety filter, not a failure classifier**: `std ≥ 1°` catches 98 % of true failures (almost nothing slips through) at the cost of flagging many benign cases too. The ratio is what you want for *abstention* — you'd rather over-flag and send borderline cases to a human than let a failure through.

### Alternative: using `range(rot_err)` instead of `std`

`range` (max − min across 3 gens) is more intuitive and slightly more conservative:

| Gate | Coverage | Mean rot_bon° | Fail@30° | Fail@10° |
|---|---|---|---|---|
| `range < 1°` | 56.4 % | 0.53° | 0.0 % | 0.2 % |
| `range < 2°` | 73.7 % | 0.69° | 0.1 % | 0.6 % |
| `range < 5°` | 80.5 % | 1.26° | 0.8 % | 2.3 % |
| `range < 10°` | 86.6 % | 2.52° | 2.5 % | 6.1 % |

`range < 1°` keeps 56 % coverage with **0 hard failures** and 0.2 % soft-fail rate. Stricter than `std < 0.5°` on coverage but equally clean.

### Headline

> On the 64 % of inputs where TORA's 3 generations agree within 0.5°, it is **effectively perfect** (0 hard failures, mean error 0.56°, p90 = 1.24°). All of the dataset-wide 6.5 % failure rate lives in the other 36 %.

### Practical protocol

1. **Run inference N ≥ 3 times** per input (different random noise each time).
2. **Compute per-sample agreement**: `std` or `range` of the rotation-error against GT, or — if no GT — a proxy like pairwise Chamfer distance between predicted assemblies.
3. **Accept only confident predictions** (std < 0.5° or range < 1°). Send the rest for human review.
4. On the accepted subset, treat TORA's output as trustworthy.

### Caveat for the 40-piece tray

This analysis computed `std` on ground-truth-referenced error (`rot_err_gen_i` vs GT). In production on your tray you don't have GT. Substitute: pairwise Chamfer distance between the N predicted assemblies, or per-part pose-vector variance across generations. The findings above validate that *agreement across generations* is a usable signal — the specific statistic can vary.

Also: because most thin-walled hard cases (≥6 pieces) are in the "low agreement" bucket by nature, expect the tray's 40-piece regime to have **low coverage** even with aggressive retries. You'll get a few sherds where the model is confident (accept those) and many where it isn't (defer to archaeologist). This is the realistic outcome.
