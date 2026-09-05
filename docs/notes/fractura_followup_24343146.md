# TORA Fractura follow-up (job 24343146) — A + B + C combined analysis

> **⚠️ Corrected 2026-09-05 — every rotation and translation figure below moved,
> and one conclusion reversed.** The evaluator summed each fragment's error over
> the *loose* fragments but divided by *all* of them, so every number carried one
> free zero for the anchor. The fix is ×n/(n−1) per object, which is largest where
> the break is simplest: ×1.91 on the `bones` subset (2.2 fragments on average),
> ×1.36 on `egg`, ×1.29 on `ceramics`, but only ×1.13 on `bone_syn_pig` and ×1.11
> on `bone_syn_rib`. **The subsets are therefore not shifted by a common factor —
> the ranking between them changes.**
>
> Everything below is recomputed from the stored per-object result files
> (`artifacts/notes_recheck/fractura_*`), not scaled by hand. The original tables
> are kept as written; corrected ones sit beside them.
>
> **The one reversal:** on `bones`, best-of-10 appeared to leave only 62.5 % of
> objects worse than 10°. It is **93.8 %** — 15 of 16 two- and three-piece bones
> are still more than 10° out after ten attempts. The apparent success was the
> free zero.
>
> **And a warning that applies to every gate table in this note:** the confidence
> gate thresholds a *standard deviation of the diluted numbers*, so the gate itself
> was diluted by the same factor. `std < 0.5°` on `bones` is about `std < 1°` on
> the corrected scale. **Compare gate rows at matched coverage, never at matched
> threshold.**

Sources:
- Baseline (N=3, anchor-fixed): job 24342475
- Test A (N=10, anchor-fixed): job 24343146, dirs `fractura_<subset>_BoN10_24343146/`
- Test C (N=3, anchor-free):    job 24343146, dirs `fractura_<subset>_anchorfree_24343146/`

## Test A — Best-of-N=10 sweep

Mean rotation_error (degrees) and normalised translation_error (trans/scale) per subset.

| Subset | n | parts | rot N=3 (base) | rot N=3 (A run) | rot N=10 | Δ(10−3) | trans norm N=10 |
|---|---|---|---|---|---|---|---|
| bone_syn_pig | 21 | 10.8 | 45.65 | 45.54 | 40.58 | -4.96 | 0.212 |
| bone_syn_rib | 11 | 17.7 | 43.36 | 43.80 | 39.40 | -4.40 | 0.127 |
| ceramics | 8 | 5.9 | 53.96 | 59.32 | 49.33 | -9.99 | 0.223 |
| egg | 3 | 4.0 | 37.95 | 41.52 | 36.82 | -4.70 | 0.301 |
| bones | 16 | 2.2 | 19.93 | 21.65 | 16.18 | -5.48 | 0.109 |

`rot N=3 (base)` is the original anchor-fixed BoN=3 run from job 24342475; `rot N=3 (A run)` is the same metric recomputed on the new BoN=10 job restricted to the first 3 generations — they should match modulo random seed.

**Corrected (2026-09-05), free anchor removed:**

| Subset | n | parts | ×factor | rot N=3 (base) | rot N=3 (A run) | rot N=10 | Δ(10−3) | trans norm N=10 |
|---|---|---|---|---|---|---|---|---|
| bone_syn_pig | 21 | 10.8 | 1.132 | **50.48** | **50.42** | **44.94** | −5.48 | 0.236 |
| bone_syn_rib | 11 | 17.7 | 1.110 | **45.76** | **46.34** | **41.60** | −4.74 | 0.135 |
| ceramics | 8 | 5.9 | 1.290 | **68.90** | **75.74** | **62.44** | −13.30 | 0.280 |
| egg | 3 | 4.0 | 1.361 | **51.26** | **54.98** | **48.96** | −6.02 | 0.395 |
| bones | 16 | 2.2 | 1.906 | **36.73** | **40.21** | **29.49** | −10.71 | 0.198 |

**What changed in the ranking.** On the old ruler `bones` looked like the one
subset TORA could nearly handle — 19.93°, less than half of every other subset.
Corrected it is **36.73°**, in the same band as the others. The two- and
three-piece bones were flattered most by the free zero precisely because they
have the fewest fragments to spread it over. In plain terms: **there was never a
Fractura subset that TORA reassembled acceptably.** The best mean result anywhere
in this table is 29.49° — a fragment typically turned a third of a right angle
from where it belongs, which is unmistakably wrong to the eye.

The apparent gains from retrying (Δ) grow rather than shrink, because they are
scaled by the same factor: retrying still helps, and helps most on `ceramics` and
`bones`.

### Best-of-N curve per subset

| Subset | N=1 | N=3 | N=5 | N=10 | Δ(10−1) |
|---|---|---|---|---|---|
| bone_syn_pig | 48.36 | 45.54 | 44.75 | 40.58 | -7.78 |
| bone_syn_rib | 50.85 | 43.80 | 41.42 | 39.40 | -11.45 |
| ceramics | 67.87 | 59.32 | 57.18 | 49.33 | -18.54 |
| egg | 53.92 | 41.52 | 40.92 | 36.82 | -17.10 |
| bones | 28.45 | 21.65 | 18.91 | 16.18 | -12.28 |

**Corrected (2026-09-05):**

| Subset | N=1 | N=3 | N=5 | N=10 | Δ(10−1) |
|---|---|---|---|---|---|
| bone_syn_pig | **53.65** | **50.42** | **49.50** | **44.94** | −8.71 |
| bone_syn_rib | **53.86** | **46.34** | **43.78** | **41.60** | −12.26 |
| ceramics | **86.95** | **75.74** | **72.79** | **62.44** | −24.51 |
| egg | **72.71** | **54.98** | **54.09** | **48.96** | −23.75 |
| bones | **53.31** | **40.21** | **34.80** | **29.49** | −23.82 |

The *shape* of every curve is unchanged — most of the benefit arrives by N=3, the
rest trickles in — but the starting point is far worse than printed. A single
attempt on `ceramics` averages **87°**, which is close to a fragment placed at
random. Ten attempts bring it to 62°, still nowhere near assembled. **Retrying
does not rescue Fractura; it makes a bad answer slightly less bad.**

## Test B — Agreement-gate analysis

For each subset and run, std(rot_err) across generations is computed per sample, then samples are filtered by `std < threshold`. Reported on the *passing* subset.

> **Read this before the tables below.** The gate is a threshold on the spread of
> the same diluted numbers, so the *gate* was diluted too — by exactly the factor
> that diluted the values. A row labelled `std < 0.5°` on a two-piece object was in
> practice `std < 1°`. **Two gate rows are only comparable at matched coverage, not
> at matched threshold.** The corrected summary immediately below supersedes the
> twenty tables that follow it; those are kept as originally written, on the old
> ruler.

### Corrected agreement gate (2026-09-05) — the summary that supersedes the tables below

Only the rows where the gate actually accepted something are listed; every gate
not shown accepted **zero** objects. `Mean rot°` and both fail columns are on the
corrected ruler.

| Subset | Run | Gate | Coverage | n passed | Mean rot° | Fail@30 | Fail@10 |
|---|---|---|---|---|---|---|---|
| bone_syn_pig | baseline N=3 | std<5° | 23.8% | 5 | 37.16 | 40.0% | 100.0% |
| bone_syn_pig | baseline N=3 | no gate | 100.0% | 21 | 50.48 | 81.0% | 100.0% |
| bone_syn_pig | A N=3 | std<5° | 19.0% | 4 | 56.93 | 75.0% | 100.0% |
| bone_syn_pig | A N=3 | no gate | 100.0% | 21 | 50.42 | 81.0% | 95.2% |
| bone_syn_pig | A N=10 | std<5° | 4.8% | 1 | 56.22 | 100.0% | 100.0% |
| bone_syn_pig | A N=10 | no gate | 100.0% | 21 | 44.94 | 76.2% | 95.2% |
| bone_syn_pig | C N=3 free | std<0.5° | 4.8% | 1 | 77.88 | 100.0% | 100.0% |
| bone_syn_pig | C N=3 free | std<2° | 9.5% | 2 | 76.67 | 100.0% | 100.0% |
| bone_syn_pig | C N=3 free | std<5° | 28.6% | 6 | 73.38 | 100.0% | 100.0% |
| bone_syn_pig | C N=3 free | no gate | 100.0% | 21 | 50.91 | 85.7% | 100.0% |
| bone_syn_rib | baseline N=3 | std<0.5° | 9.1% | 1 | 7.22 | 0.0% | 0.0% |
| bone_syn_rib | baseline N=3 | std<5° | 54.5% | 6 | 35.52 | 50.0% | 50.0% |
| bone_syn_rib | baseline N=3 | no gate | 100.0% | 11 | 45.76 | 63.6% | 63.6% |
| bone_syn_rib | A N=3 | std<2° | 9.1% | 1 | 3.90 | 0.0% | 0.0% |
| bone_syn_rib | A N=3 | std<5° | 45.5% | 5 | 33.77 | 40.0% | 60.0% |
| bone_syn_rib | A N=3 | no gate | 100.0% | 11 | 46.34 | 63.6% | 81.8% |
| bone_syn_rib | A N=10 | std<2° | 9.1% | 1 | 3.90 | 0.0% | 0.0% |
| bone_syn_rib | A N=10 | std<5° | 27.3% | 3 | 23.93 | 33.3% | 33.3% |
| bone_syn_rib | A N=10 | no gate | 100.0% | 11 | 41.60 | 63.6% | 63.6% |
| bone_syn_rib | C N=3 free | std<5° | 18.2% | 2 | **8.02** | 0.0% | 0.0% |
| bone_syn_rib | C N=3 free | no gate | 100.0% | 11 | 41.76 | 63.6% | 72.7% |
| ceramics | baseline N=3 | std<5° | 12.5% | 1 | 70.65 | 100.0% | 100.0% |
| ceramics | baseline N=3 | no gate | 100.0% | 8 | 68.90 | 100.0% | 100.0% |
| ceramics | A N=3 | std<5° | 25.0% | 2 | 74.10 | 100.0% | 100.0% |
| ceramics | A N=10 | (none passed any gate) | — | 0 | — | — | — |
| ceramics | A N=10 | no gate | 100.0% | 8 | 62.44 | 100.0% | 100.0% |
| ceramics | C N=3 free | std<5° | 25.0% | 2 | 70.69 | 100.0% | 100.0% |
| ceramics | C N=3 free | no gate | 100.0% | 8 | 75.02 | 100.0% | 100.0% |
| egg | all four runs | (none passed any gate) | — | 0 | — | — | — |
| egg | baseline / A3 / A10 / C | no gate | 100.0% | 3 | 51.26 / 54.98 / 48.96 / 49.51 | 100.0% | 100.0% |
| bones | all four runs | (none passed any gate) | — | 0 | — | — | — |
| bones | baseline / A3 / A10 / C | no gate | 100.0% | 16 | 36.73 / 40.21 / 29.49 / 44.55 | 62.5 / 68.8 / 43.8 / 62.5% | 93.8% |

**What this says, in plain terms.** The agreement gate — "trust the answer when
several attempts agree with each other" — is the one tool that worked on Breaking
Bad thin-walled vessels, where it isolated a two-thirds slice of the data with
almost no failures. **On Fractura it does not work at all.**

- On `bones` and `egg` — 19 of the 59 objects, and the simplest breaks in the set
  — **no threshold ever accepts a single object.** The three runs never agree.
- On `ceramics` the gate accepts one or two objects and every one of them is a
  hard failure (>30°). It is worse than useless there: it selects confidently
  wrong answers.
- The only place it does its job is `bone_syn_rib`, where the anchor-free run's
  `std < 5°` accepts 2 of 11 objects at a genuine **8.0°** mean with no failures,
  and the baseline's `std < 0.5°` accepts a single object at 7.2°. Two objects is
  an anecdote, not a working gate.

**Which of the three this is:** the method genuinely failed here, and the gate
failed with it. It is not a measurement artefact — the corrected ruler is the one
being read — and there is no ground-truth problem, because Fractura ships real
scanned fragments with a known correct reassembly. What the anchor bug did was
hide *how badly*: it made `bones` look like a near-success and made a handful of
gate rows look survivable.

**The bones fail@10 reversal in full.** Old ruler, `bones`, best-of-10: 18.8 %
worse than 30° and 62.5 % worse than 10°, which reads as "a third of these are
essentially right". Corrected: **43.8 % worse than 30° and 93.8 % worse than 10°**
— 15 of 16 objects. One two-piece bone out of sixteen came back within 10°.

### The original tables (old ruler — kept as written, superseded above)

### bone_syn_pig

**baseline (N=3, anchor-fixed)** (n=21):

| Gate | Coverage | n passed | Mean rot° | Fail@30 | Fail@10 |
|---|---|---|---|---|---|
| std<0.5° |   0.0% |   0 | nan |   nan% |   nan% |
| std<1.0° |   0.0% |   0 | nan |   nan% |   nan% |
| std<2.0° |   0.0% |   0 | nan |   nan% |   nan% |
| std<5.0° |  28.6% |   6 | 38.47 |  50.0% |  83.3% |
| no gate | 100.0% |  21 | 45.65 |  76.2% |  95.2% |

**A run (N=3 subset)** (n=21):

| Gate | Coverage | n passed | Mean rot° | Fail@30 | Fail@10 |
|---|---|---|---|---|---|
| std<0.5° |   0.0% |   0 | nan |   nan% |   nan% |
| std<1.0° |   0.0% |   0 | nan |   nan% |   nan% |
| std<2.0° |   9.5% |   2 | 36.23 |  50.0% | 100.0% |
| std<5.0° |  19.0% |   4 | 52.74 |  75.0% | 100.0% |
| no gate | 100.0% |  21 | 45.54 |  81.0% |  95.2% |

**A run (N=10)** (n=21):

| Gate | Coverage | n passed | Mean rot° | Fail@30 | Fail@10 |
|---|---|---|---|---|---|
| std<0.5° |   0.0% |   0 | nan |   nan% |   nan% |
| std<1.0° |   0.0% |   0 | nan |   nan% |   nan% |
| std<2.0° |   0.0% |   0 | nan |   nan% |   nan% |
| std<5.0° |  14.3% |   3 | 50.01 |  66.7% |  66.7% |
| no gate | 100.0% |  21 | 40.58 |  71.4% |  90.5% |

**C run (N=3, anchor-free)** (n=21):

| Gate | Coverage | n passed | Mean rot° | Fail@30 | Fail@10 |
|---|---|---|---|---|---|
| std<0.5° |   4.8% |   1 | 70.80 | 100.0% | 100.0% |
| std<1.0° |   4.8% |   1 | 70.80 | 100.0% | 100.0% |
| std<2.0° |   9.5% |   2 | 68.94 | 100.0% | 100.0% |
| std<5.0° |  33.3% |   7 | 64.20 | 100.0% | 100.0% |
| no gate | 100.0% |  21 | 45.97 |  71.4% |  95.2% |


### bone_syn_rib

**baseline (N=3, anchor-fixed)** (n=11):

| Gate | Coverage | n passed | Mean rot° | Fail@30 | Fail@10 |
|---|---|---|---|---|---|
| std<0.5° |   9.1% |   1 | 5.77 |   0.0% |   0.0% |
| std<1.0° |   9.1% |   1 | 5.77 |   0.0% |   0.0% |
| std<2.0° |   9.1% |   1 | 5.77 |   0.0% |   0.0% |
| std<5.0° |  63.6% |   7 | 36.49 |  57.1% |  57.1% |
| no gate | 100.0% |  11 | 43.36 |  63.6% |  63.6% |

**A run (N=3 subset)** (n=11):

| Gate | Coverage | n passed | Mean rot° | Fail@30 | Fail@10 |
|---|---|---|---|---|---|
| std<0.5° |   0.0% |   0 | nan |   nan% |   nan% |
| std<1.0° |   0.0% |   0 | nan |   nan% |   nan% |
| std<2.0° |   9.1% |   1 | 3.12 |   0.0% |   0.0% |
| std<5.0° |  45.5% |   5 | 31.30 |  40.0% |  60.0% |
| no gate | 100.0% |  11 | 43.80 |  63.6% |  81.8% |

**A run (N=10)** (n=11):

| Gate | Coverage | n passed | Mean rot° | Fail@30 | Fail@10 |
|---|---|---|---|---|---|
| std<0.5° |   0.0% |   0 | nan |   nan% |   nan% |
| std<1.0° |   0.0% |   0 | nan |   nan% |   nan% |
| std<2.0° |  18.2% |   2 | 4.07 |   0.0% |   0.0% |
| std<5.0° |  27.3% |   3 | 22.61 |  33.3% |  33.3% |
| no gate | 100.0% |  11 | 39.40 |  63.6% |  63.6% |

**C run (N=3, anchor-free)** (n=11):

| Gate | Coverage | n passed | Mean rot° | Fail@30 | Fail@10 |
|---|---|---|---|---|---|
| std<0.5° |   0.0% |   0 | nan |   nan% |   nan% |
| std<1.0° |   0.0% |   0 | nan |   nan% |   nan% |
| std<2.0° |   0.0% |   0 | nan |   nan% |   nan% |
| std<5.0° |  36.4% |   4 | 7.48 |   0.0% |   0.0% |
| no gate | 100.0% |  11 | 39.40 |  63.6% |  63.6% |


### ceramics

**baseline (N=3, anchor-fixed)** (n=8):

| Gate | Coverage | n passed | Mean rot° | Fail@30 | Fail@10 |
|---|---|---|---|---|---|
| std<0.5° |   0.0% |   0 | nan |   nan% |   nan% |
| std<1.0° |   0.0% |   0 | nan |   nan% |   nan% |
| std<2.0° |  12.5% |   1 | 64.76 | 100.0% | 100.0% |
| std<5.0° |  12.5% |   1 | 64.76 | 100.0% | 100.0% |
| no gate | 100.0% |   8 | 53.96 | 100.0% | 100.0% |

**A run (N=3 subset)** (n=8):

| Gate | Coverage | n passed | Mean rot° | Fail@30 | Fail@10 |
|---|---|---|---|---|---|
| std<0.5° |   0.0% |   0 | nan |   nan% |   nan% |
| std<1.0° |   0.0% |   0 | nan |   nan% |   nan% |
| std<2.0° |   0.0% |   0 | nan |   nan% |   nan% |
| std<5.0° |  25.0% |   2 | 61.95 | 100.0% | 100.0% |
| no gate | 100.0% |   8 | 59.32 | 100.0% | 100.0% |

**A run (N=10)** (n=8):

| Gate | Coverage | n passed | Mean rot° | Fail@30 | Fail@10 |
|---|---|---|---|---|---|
| std<0.5° |   0.0% |   0 | nan |   nan% |   nan% |
| std<1.0° |   0.0% |   0 | nan |   nan% |   nan% |
| std<2.0° |   0.0% |   0 | nan |   nan% |   nan% |
| std<5.0° |   0.0% |   0 | nan |   nan% |   nan% |
| no gate | 100.0% |   8 | 49.33 | 100.0% | 100.0% |

**C run (N=3, anchor-free)** (n=8):

| Gate | Coverage | n passed | Mean rot° | Fail@30 | Fail@10 |
|---|---|---|---|---|---|
| std<0.5° |   0.0% |   0 | nan |   nan% |   nan% |
| std<1.0° |   0.0% |   0 | nan |   nan% |   nan% |
| std<2.0° |   0.0% |   0 | nan |   nan% |   nan% |
| std<5.0° |  25.0% |   2 | 50.10 | 100.0% | 100.0% |
| no gate | 100.0% |   8 | 58.67 | 100.0% | 100.0% |


### egg

**baseline (N=3, anchor-fixed)** (n=3):

| Gate | Coverage | n passed | Mean rot° | Fail@30 | Fail@10 |
|---|---|---|---|---|---|
| std<0.5° |   0.0% |   0 | nan |   nan% |   nan% |
| std<1.0° |   0.0% |   0 | nan |   nan% |   nan% |
| std<2.0° |   0.0% |   0 | nan |   nan% |   nan% |
| std<5.0° |   0.0% |   0 | nan |   nan% |   nan% |
| no gate | 100.0% |   3 | 37.95 | 100.0% | 100.0% |

**A run (N=3 subset)** (n=3):

| Gate | Coverage | n passed | Mean rot° | Fail@30 | Fail@10 |
|---|---|---|---|---|---|
| std<0.5° |   0.0% |   0 | nan |   nan% |   nan% |
| std<1.0° |   0.0% |   0 | nan |   nan% |   nan% |
| std<2.0° |   0.0% |   0 | nan |   nan% |   nan% |
| std<5.0° |  33.3% |   1 | 62.32 | 100.0% | 100.0% |
| no gate | 100.0% |   3 | 41.52 |  66.7% | 100.0% |

**A run (N=10)** (n=3):

| Gate | Coverage | n passed | Mean rot° | Fail@30 | Fail@10 |
|---|---|---|---|---|---|
| std<0.5° |   0.0% |   0 | nan |   nan% |   nan% |
| std<1.0° |   0.0% |   0 | nan |   nan% |   nan% |
| std<2.0° |   0.0% |   0 | nan |   nan% |   nan% |
| std<5.0° |   0.0% |   0 | nan |   nan% |   nan% |
| no gate | 100.0% |   3 | 36.82 |  66.7% | 100.0% |

**C run (N=3, anchor-free)** (n=3):

| Gate | Coverage | n passed | Mean rot° | Fail@30 | Fail@10 |
|---|---|---|---|---|---|
| std<0.5° |   0.0% |   0 | nan |   nan% |   nan% |
| std<1.0° |   0.0% |   0 | nan |   nan% |   nan% |
| std<2.0° |   0.0% |   0 | nan |   nan% |   nan% |
| std<5.0° |  33.3% |   1 | 27.70 |   0.0% | 100.0% |
| no gate | 100.0% |   3 | 37.11 |  33.3% | 100.0% |


### bones

**baseline (N=3, anchor-fixed)** (n=16):

| Gate | Coverage | n passed | Mean rot° | Fail@30 | Fail@10 |
|---|---|---|---|---|---|
| std<0.5° |   0.0% |   0 | nan |   nan% |   nan% |
| std<1.0° |   0.0% |   0 | nan |   nan% |   nan% |
| std<2.0° |   0.0% |   0 | nan |   nan% |   nan% |
| std<5.0° |  12.5% |   2 | 23.97 |  50.0% | 100.0% |
| no gate | 100.0% |  16 | 19.93 |  18.8% |  93.8% |

**A run (N=3 subset)** (n=16):

| Gate | Coverage | n passed | Mean rot° | Fail@30 | Fail@10 |
|---|---|---|---|---|---|
| std<0.5° |   0.0% |   0 | nan |   nan% |   nan% |
| std<1.0° |   0.0% |   0 | nan |   nan% |   nan% |
| std<2.0° |   0.0% |   0 | nan |   nan% |   nan% |
| std<5.0° |  18.8% |   3 | 32.54 |  66.7% | 100.0% |
| no gate | 100.0% |  16 | 21.65 |  31.2% |  81.2% |

**A run (N=10)** (n=16):

| Gate | Coverage | n passed | Mean rot° | Fail@30 | Fail@10 |
|---|---|---|---|---|---|
| std<0.5° |   0.0% |   0 | nan |   nan% |   nan% |
| std<1.0° |   0.0% |   0 | nan |   nan% |   nan% |
| std<2.0° |   0.0% |   0 | nan |   nan% |   nan% |
| std<5.0° |   0.0% |   0 | nan |   nan% |   nan% |
| no gate | 100.0% |  16 | 16.18 |  18.8% |  62.5% |

**C run (N=3, anchor-free)** (n=16):

| Gate | Coverage | n passed | Mean rot° | Fail@30 | Fail@10 |
|---|---|---|---|---|---|
| std<0.5° |   0.0% |   0 | nan |   nan% |   nan% |
| std<1.0° |   0.0% |   0 | nan |   nan% |   nan% |
| std<2.0° |   0.0% |   0 | nan |   nan% |   nan% |
| std<5.0° |  12.5% |   2 | 25.95 |  50.0% | 100.0% |
| no gate | 100.0% |  16 | 24.18 |  43.8% |  68.8% |


## Test C — Anchor-free vs anchor-fixed (both BoN=3)

| Subset | n | parts | rot anchor-fixed | rot anchor-free | Δ | trans norm fixed | trans norm free |
|---|---|---|---|---|---|---|---|
| bone_syn_pig | 21 | 10.8 | 45.65 | 45.97 | +0.32 | 0.227 | 0.228 |
| bone_syn_rib | 11 | 17.7 | 43.36 | 39.40 | -3.95 | 0.134 | 0.149 |
| ceramics | 8 | 5.9 | 53.96 | 58.67 | +4.71 | 0.243 | 0.290 |
| egg | 3 | 4.0 | 37.95 | 37.11 | -0.84 | 0.238 | 0.244 |
| bones | 16 | 2.2 | 19.93 | 24.18 | +4.26 | 0.106 | 0.120 |

Δ > 0 means removing the anchor advantage hurt rotation; Δ ≈ 0 means the anchor wasn't doing the heavy lifting; Δ < 0 (unexpected) would mean anchor-fixed was actually a constraint.

**Corrected (2026-09-05):**

| Subset | n | parts | rot anchor-fixed | rot anchor-free | Δ | trans norm fixed | trans norm free |
|---|---|---|---|---|---|---|---|
| bone_syn_pig | 21 | 10.8 | **50.48** | **50.91** | +0.43 | 0.254 | 0.255 |
| bone_syn_rib | 11 | 17.7 | **45.76** | **41.76** | −4.00 | 0.142 | 0.159 |
| ceramics | 8 | 5.9 | **68.90** | **75.02** | +6.12 | 0.301 | 0.366 |
| egg | 3 | 4.0 | **51.26** | **49.51** | −1.74 | 0.316 | 0.323 |
| bones | 16 | 2.2 | **36.73** | **44.55** | +7.82 | 0.192 | 0.220 |

**Both columns needed the same correction, so this comparison survives intact.**
The anchor-free run is *not* free of the bug: the evaluator skips the anchor
fragment's own error in both modes and divides by the total either way. The
factors are per-object and identical on both sides, so every Δ is simply the old
Δ scaled up, and the signs and the conclusion are unchanged — removing the anchor
advantage costs a little on `bones` and `ceramics`, costs nothing on
`bone_syn_pig`, and (still unexpectedly) helps on `bone_syn_rib`.

The one thing that does change is the size of the penalty: on `bones` it is
**+7.8°**, not +4.3°. Against a baseline that is itself 36.7°, that is a
meaningful extra handicap on the simplest breaks in the set.

## Cross-test rotation summary

| Subset | n | base N=3 | A N=10 | C anchor-free N=3 |
|---|---|---|---|---|
| bone_syn_pig | 21 | 45.65 | 40.58 | 45.97 |
| bone_syn_rib | 11 | 43.36 | 39.40 | 39.40 |
| ceramics | 8 | 53.96 | 49.33 | 58.67 |
| egg | 3 | 37.95 | 36.82 | 37.11 |
| bones | 16 | 19.93 | 16.18 | 24.18 |

**Corrected (2026-09-05):**

| Subset | n | base N=3 | A N=10 | C anchor-free N=3 |
|---|---|---|---|---|
| bone_syn_pig | 21 | **50.48** | **44.94** | **50.91** |
| bone_syn_rib | 11 | **45.76** | **41.60** | **41.76** |
| ceramics | 8 | **68.90** | **62.44** | **75.02** |
| egg | 3 | **51.26** | **48.96** | **49.51** |
| bones | 16 | **36.73** | **29.49** | **44.55** |

## What this note supports, and what it does not (2026-09-05)

**It supports:** TORA does not reassemble any Fractura subset. The best cell in
the whole document is 29.5° — ten attempts on two- and three-piece bones — and
even there only one object in sixteen finished within 10°. Retrying helps
consistently and helps most where the answer is worst, but never enough to
matter. The agreement gate, which is a reliable safety net on Breaking Bad
thin-walled vessels, is not one here: on more than half these objects it never
fires at all, and on `ceramics` everything it accepts is wrong.

**It does not support** any statement that `bones` is a subset TORA handles. That
reading came entirely from the free-anchor zero on two-piece objects.

**How much weight it can bear:** not much per subset. `egg` is three objects,
`ceramics` eight, `bone_syn_rib` eleven. Only `bone_syn_pig` (21) and `bones`
(16) carry any statistical weight, and both are synthetic or two-piece. The
across-the-board size of the failure is the durable finding; per-subset ordering
is not.

**What would change the answer:** nothing in this note has been rendered.
Rotation error is a stand-in for "does it look assembled", and at these
magnitudes the stand-in is safe — 30–90° means visibly scattered — but the two
objects `bone_syn_rib` passes at 8° should be drawn before anyone leans on them.

**Caveat carried from the recheck:** `ceramics`, `egg` and `bones` are stored in
millimetres (scales 18.6–243), so their `recall_at_1cm` / `recall_at_5cm` columns
read "within 0.01 mm" and are always zero. They are meaningless here and are not
quoted above; only the two synthetic bone subsets (scales ≈0.51–0.62) are in the
unit the recall thresholds assume.
