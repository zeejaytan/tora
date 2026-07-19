# TORA Fractura follow-up (job 24343146) — A + B + C combined analysis

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

### Best-of-N curve per subset

| Subset | N=1 | N=3 | N=5 | N=10 | Δ(10−1) |
|---|---|---|---|---|---|
| bone_syn_pig | 48.36 | 45.54 | 44.75 | 40.58 | -7.78 |
| bone_syn_rib | 50.85 | 43.80 | 41.42 | 39.40 | -11.45 |
| ceramics | 67.87 | 59.32 | 57.18 | 49.33 | -18.54 |
| egg | 53.92 | 41.52 | 40.92 | 36.82 | -17.10 |
| bones | 28.45 | 21.65 | 18.91 | 16.18 | -12.28 |

## Test B — Agreement-gate analysis

For each subset and run, std(rot_err) across generations is computed per sample, then samples are filtered by `std < threshold`. Reported on the *passing* subset.

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

## Cross-test rotation summary

| Subset | n | base N=3 | A N=10 | C anchor-free N=3 |
|---|---|---|---|---|
| bone_syn_pig | 21 | 45.65 | 40.58 | 45.97 |
| bone_syn_rib | 11 | 43.36 | 39.40 | 39.40 |
| ceramics | 8 | 53.96 | 49.33 | 58.67 |
| egg | 3 | 37.95 | 36.82 | 37.11 |
| bones | 16 | 19.93 | 16.18 | 24.18 |
