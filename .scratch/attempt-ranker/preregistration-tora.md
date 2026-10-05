# Pre-registration: U17 ranker on TORA's Fractura attempts (ticket 06)

Committed **before** any TORA attempt is converted, ranked or scored. `scripts/u17_test.py`
prints this file's commit. Labels already exist (they had to, to pick the pots); no score
has been joined to them.

## What is being tested

The ranker exactly as calibrated on GARF (`calibration-fractura.md` Revision 3, run
32274553; held-out GARF test passed, ticket 05), unchanged, on a second method's attempts.
TORA's attempts: the 28 `u10_fractura_*` evaluation runs, 20 attempts each, pooled per pot
= 560 attempts per pot. Pooling all arms is a default, as GARF's 7 arms were pooled: the
question is whether the right attempt can be found, not which arm made it.

Labels: `TORA/rank_u17/tora_fractura_labels.json` (2026-10-05, `label_attempts.py` @
b5291fb; same ruler as GARF's).

| Pot | Sherds | Genuine | Near-miss | Random top 5 | Note |
|---|---|---|---|---|---|
| narrow_bottle3 | 4 | 9 | 34 | 7.8% | GARF's held-out test pot |
| plate | 6 | 5 | 71 | 4.4% | a GARF **calibration** pot: its geometry helped set the cut-off, though no TORA attempt did |

No other pot qualifies (genuine rare but present): blue_pot, narrow_bottle2/4, pink_bowl
right too often; galli_pot, narrow_bottle1 never right.

**Decision on attempt count (ticket 06):** 560 attempts per pot is enough; no TORA rerun.
Both qualifying pots have genuine attempts present and rare.

## Fixed settings

Identical to `preregistration-test.md` (2d07202): Layer 1 `--profile outer --cover-pct 2
--io-gate off --near-pct 12 --unjudged fail`, pass at **0.873% of pot**; Layer 2 gaps by
`l2_measure.py` (settings of `preregistration-l2.md`), unfixable flag **2.31%**; order
Layer 1 pass, worst-sherd gap, profile. Pot size nominal 100 mm. Job
`scripts/hpc/u17_test_tora.slurm` (convert with self-check, measure, rank, report, render).

## Read-outs and decision rule

Per pot, as in `preregistration-test.md`: best genuine rank and top-5 hit (Layer 1 alone,
Layers 1+2), random baseline, classes in the top 5, near-misses above the best genuine,
worst-gap AUC, genuine failed by Layer 1 and why, unfixable share.

- A pot **passes** if a genuine attempt is in the Layers 1+2 top 5.
- Ruler checks first, as before: genuine attempts failed as unjudged = broken measurement;
  genuine attempts failed on the profile cut-off are looked at (`l1_look --fail-pct`)
  before anything is reported. **Known risk:** plate has a flat floor, and galli_pot's
  flat base already made Layer 1 reject 10% of correct GARF attempts at the floor-to-wall
  corner (ticket 05). If that recurs it is read first as the same measure fault.
- Converter self-check must pass, or nothing is read.
- Every failure is named: method failed, measurement broken, or reference wrong.

**Prediction, written before the run:** narrow_bottle3 passes (GARF's top 20 were all
genuine). plate more likely misses than passes: 5 genuine against 71 near-misses, and on
GARF's plate attempts the gap test told turned sherds apart weakly (AUC 0.66). TORA may
also seat sherds less tightly than GARF, which the gap test depends on.

**Weight.** Two pots, one of them seen in calibration, one second method. A pass on
narrow_bottle3 says the ranker is not tied to GARF; it is still a lead for U17.
