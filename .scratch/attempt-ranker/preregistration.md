# Pre-registration: U17 ranker, Layer 1, Juglet (ticket 01)

Committed **before** the labelled run. The report prints the commit hash of this file;
any change after that hash is a new pre-registration and must say why.

## What is being tested

GARF's 1,400 Juglet attempts (7 arms × 10 evaluation runs × 20 attempts), ranked by
`scripts/rank_attempts.py` from attempt bundles alone. Success, per U17: a genuine full
reassembly (all 9 sherds in their own place and the right way round) in the **top 5**.
Random choice does that with probability 1 − C(1398,5)/C(1400,5) ≈ **0.71%**.

The labels (computed only in the report, from `own_place.score_draw` on the run files):

- **genuine**: own place 9/9 and right way round 9/9. Expected 2 (noise_d100 ds1 #19,
  worn_d400_s7 ds4 #11, per `jug_t06_rescore.json`).
- **near-miss**: own place 9/9 but fewer than 9 the right way round. Expected 19.

If the recomputed labels do not give 2 and 19, the report stops and says so: the ruler
changed, not the ranker.

## Layer 1 cut-offs (fixed)

| Setting | Value | Source |
|---|---|---|
| Height bin | 7 mm | SfS++ profile bins |
| Profile deviation limit | 7 mm | SfS++ rejection threshold |
| A sherd's outer wall in a bin | 95th percentile of its radii there | chosen; outer face, robust to break-face points |
| Attempt deviation | 90th percentile of \|sherd wall − smoothed profile\| over (sherd, bin) cells | chosen |
| Smoothing | median over 3 neighbouring bins | chosen |
| Smallest cell | 20 points | chosen |
| Axis fit | normal lines passing closest to one line; trimmed least squares keeping 80%; lines within ~17° of the axis direction skipped | chosen |
| Axis search | 1,500 directions, best 10 polished, then refined on a frozen kept set until it stops changing | chosen for frame invariance (below) |
| Inside-out | `check_inside_out.rule_flag` against the attempt's centre | tora juglet-cause/14 |
| Pass | deviation ≤ 7 mm **and** no sherd inside out | |
| Order | passing first, then by deviation, smallest first | |
| Least-sure sherd | first inside-out sherd if any, else largest deviation | |
| Pot size | longest box side = 65 mm (1 dataset unit = 70.71 mm) | Juglet measurement |

The Juglet is handmade, outside SfS++'s wheel-thrown assumption. The 7 mm limit is **not**
tuned on it; whatever it does is reported as found.

## What was looked at before this file was committed

- The correct assembly (the dataset's sherds as scanned): deviation 1.53 mm, axis fit
  2.47 mm, no sherd inside out, so it passes. This was the ruler check.
- 40 bundles from `noise_d100` ds1 (one of which is a genuine attempt), used only to test
  that a moved attempt scores the same. No labels were joined to them and no ranks were
  read against labels. The one change this caused was to the axis optimiser: it had
  stopped at points up to 1.2° apart in different frames, moving a deviation by 0.18 mm.
  No cut-off changed.

## Gates (must pass in the same job, before ranking)

- `check_attempt_ranker.py`: **moved**, where every attempt tested, moved once more,
  scores within 0.05 mm with the same pass, inside-out list and least-sure sherd. **Fence**,
  where the ranker runs with an audit hook that kills it on opening any data file outside
  its bundles; a probe opening the dataset file and the id map must be killed.
- `rank_convert.py --check`: rebuilt attempts score identically to the originals.

## Reported, whatever the outcome

Rank of each genuine attempt; top-5 hit; the 0.71% baseline; how many attempts Layer 1
drops; the rank of each of the 19 near-misses, with its largest sherd turn. Layer 1 is not
expected to separate near-misses from genuine attempts (U17 fact 2); that is Layer 2's job
(ticket 02).
