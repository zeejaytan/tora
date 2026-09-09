# The erosion ladder on the eight Fractura ceramics (ticket 11, job 30293058)

**Run:** `sbatch scripts/hpc/eval_erosion_ceramics.slurm`, job **30293058**,
`sacct: COMPLETED|0:0|2026-09-09T16:34:44` — 4 min queued, 15 min running,
`gpu-a100-short`. Baseline arm `bbad_everyday_cka.ckpt` (synthetic-only training,
so no real pot was ever in it). 8 pots × 5 abrasion levels × 10 attempts = 40
saved clouds, 48 MB, fetched to `artifacts/wearsig_ceramics/` (gitignored).

## What this was for

Ticket 09 asked whether abrasion breaks a pot the way the Juglet is broken, and
answered on **one** object. The cause was not the method and not the instrument:
`build_erosion_sweep.py` says in its own docstring that it wears "pots TORA CAN
currently rebuild", but the job that ran it passed **no `--objects` filter** and
sourced `real_heldout_norm.hdf5` — six objects, **three of them bones**. The
selection step in the design was never executed. The Fractura `ceramics` group
holds **eight** real pots; five had never been on the ladder.

## Gates (all passed before any result was read)

| gate | result |
|---|---|
| checkout postdates the scoring fix `0d6a85f` | PASS (`0ff5c23`) |
| every ceramic normalised to max abs vertex = 0.5 before erosion | PASS |
| scale did not drift across any ladder | PASS, worst 0.415% (`narrow_bottle3`) |

The ceramics arrive in **raw scan units** (max abs vertex 54.9–187.3, varying
3.4× between pots). `scales` is a **conditioning input** to the flow model, not
bookkeeping, so the source was normalised **once, before erosion**;
`--normalize` on the build was deliberately not used, because it recomputes the
factor per variant *after* erosion and would have put a second changing thing in
the experiment.

## The unworn control, stated before the ladder was read

Four of the eight pots place every fragment correctly at zero abrasion. Four do
not, and are **excluded from the reading** — they cannot show a wear-induced
transition because they are already broken.

| pot | fragments | worst loose sherd at e000 | verdict |
|---|---|---|---|
| `narrow_bottle4` | 4 | **2.4%** | control PASSES |
| `narrow_bottle2` | 3 | **2.8%** | control PASSES |
| `pink_bowl` | 3 | **3.3%** | control PASSES |
| `blue_pot` | 5 | **4.0%** | control PASSES |
| `narrow_bottle3` | 4 | 33.7% | excluded |
| `galli_pot` | 10 | 47.3% | excluded |
| `plate` | 6 | 56.4% | excluded |
| `narrow_bottle1` | 12 | 94.0% | excluded |

Four pots with a valid control, against ticket 09's one. The bar is 5.0% of pot
size; a correct assembly sits at 2–3%.

## Did the simulated wear actually reach the Juglet's condition?

**This is the question that decides what the ladder can be read for**, and on
half the surviving pots the answer is no. The Juglet's own measured roughness is
`relief_p90` **0.171** (lower = more worn).

| pot | e000 | e025 | e050 | e075 | e100 | reached the Juglet's wear? |
|---|---|---|---|---|---|---|
| `blue_pot` | 0.225 | 0.204 | **0.170** | 0.140 | 0.118 | **yes, from e050** |
| `pink_bowl` | 0.213 | 0.207 | 0.182 | **0.152** | 0.134 | **yes, from e075** |
| `narrow_bottle4` | 0.323 | 0.294 | 0.265 | 0.253 | 0.244 | **no — plateaus at 0.244** |
| `narrow_bottle2` | 0.228 | 0.217 | 0.180 | 0.272 | 0.369 | **no — and the number inverts** |

`narrow_bottle4` survives every rung, but it was **never worn to the Juglet's
condition** — the operator stops well above it. Its survival is therefore not
evidence that Juglet-level abrasion leaves a pot assemblable. This is exactly the
failure mode that made GARF's Exp 7 uninterpretable, recurring here on two of
four pots.

## A measurement defect found in the calibration, and confirmed by looking

On `narrow_bottle2` and `narrow_bottle3` the calibration number **rises** under
increasing abrasion — the opposite of smoothing. It is not mesh damage: vertex
displacement is clean and monotone on every pot at every rung, and inverted
triangles stay below **0.1%** even at full strength.

Rendering the break surface, coloured by the per-sample relief that `relief_p90`
is the 90th percentile of, shows what is happening
(`artifacts/wearsig_ceramics/renders/narrow_bottle{2,3,4}_band.png`):

- **`narrow_bottle2`** — the interior of the break face is already smooth (flat
  black) at e000, so the mollifier has no relief to remove. What it does instead
  is round the **rim**, and where the feathered band meets untouched surface it
  leaves a raised edge. That new crease is sharp, and a 90th-percentile statistic
  is dominated by exactly such a minority of sharp samples. Restricting the
  measurement to the fracture band makes it worse, not better (0.396 at e050 →
  **0.629** at e100), which confirms the band boundary as the source.
- **`narrow_bottle3`** — relief is roughly **twice** every other pot at every
  rung and uniform across the whole face, and the height profile is
  high-frequency noise with no underlying fracture form. This mesh is
  noise-dominated, which is also why it never assembles.

**Consequence:** the `relief_p90` calibration column is **not trustworthy on a
piece whose break face is already smooth**, because the mollifier's own feather
boundary then supplies more relief than it removes. The wear is still being
applied correctly — displacement confirms that — but the number stops reporting
it. Anything that reads achieved wear off this statistic needs to check the sign
first.

A contributing defect, found by reading the operator: `erode_fracture_band`
mollifies onto at most `knn=48` of `n_self_samples=20000` surface samples, so
beyond a certain strength the effective kernel **saturates** at the radius that
holds 48 samples, and further strength only raises the blend weight. Measured,
the requested radius exceeds that radius from e075 on **for every pot**.

## The reading, per pot, up its own ladder

No pooled mean anywhere: agreement between attempts correlates with fragment
count at **r = −0.87** in this run, so any cross-pot tally is partly just counting
pieces. `e100` is excluded by the ticket's own rule — a pot that has collapsed
must read as scattered whatever the mechanism.

| pot | e000 | e025 | e050 | e075 |
|---|---|---|---|---|
| `blue_pot` | assembled 4.0% | **exchange** 13.8% → 4.0% relabelled, 9/10 | assembled 3.8% | scattered 8.3% |
| `pink_bowl` | assembled 3.3% | assembled 3.3% | **scattered 11.9%** | **scattered 12.1%** |
| `narrow_bottle2` | assembled 2.8% | assembled 2.8% | assembled 2.8% | assembled 2.8% |
| `narrow_bottle4` | assembled 2.4% | assembled 2.4% | assembled 2.3% | assembled 2.4% |

**Ticket 09 reproduced exactly, from a different source file.** `blue_pot` at
e025 loses 13.8% of pot size to a two-chip name swap that relabelling returns to
4.0%, in **9 of 10** attempts — against ticket 09's 14.2% → 4.0%, 9 of 10, on
`real_heldout_norm.hdf5`. The instrument is sound and the earlier observation
stands.

**But the conclusion drawn from it does not.** `pink_bowl` fails a different way,
and it fails at the wear level that matters: at e050 and e075 the worst sherd is
11.9–12.1% of pot size, **relabelling gains nothing** (11.9% → 11.9%), and the
**true naming still wins in 10 of 10 attempts**. Nothing has been given the wrong
name; a fragment is simply in the wrong place. That is scattering — the Juglet's
shape — and e075 is past the Juglet's own roughness.

Seen against the fuller ladder, `blue_pot`'s exchange is the **light-wear** mode
(e025, relief 0.204, well short of the Juglet) and its own ladder has gone to
scattering by e075. `pink_bowl` never exchanges at all.

**The prediction recorded before the run was half wrong and is left standing.** It
said exchange would be the common pattern at light and moderate wear. At light
wear on `blue_pot`, yes. At the Juglet's own wear level, no — what happens there
is scattering.

## Which of the three

**The measurement was broken, in one specific and bounded place** — the
`relief_p90` calibration inverts on smooth-faced pieces, for the reason rendered
above. Everything else held: the method did not fail, the instrument reproduced
ticket 09 from an independent file, all three gates passed, and the reference
answers are the Fractura ground truth, which is not in doubt.

## How much weight this bears

**A lead, not a conclusion.** Four pots carry a valid unworn control, up from one.
But only **two** of those were actually worn to the Juglet's condition, and they
are the whole basis of the shape claim. Of those two, one (`pink_bowl`) scatters
unambiguously and one (`blue_pot`) exchanges at light wear and is borderline at
the readable rungs. The other two plateaued above the Juglet's roughness and
answer nothing either way.

So: **n = 2**, against ticket 09's n = 1. The direction has reversed, which is
worth more than the count, but a Fractura ceramic sweep still cannot carry a
claim about one excavated juglet on its own.

## Renders (the result was looked at before it was written)

- `artifacts/wearsig_ceramics/renders/ladder_sherd_placement.png` — the four
  controlled pots at both ends of their ladders. Whole-pot outline is not
  admissible on this material, so the lower row of each block is the measured
  quantity itself, **per sherd, unbinned**, and it is the same quantity
  `check_wear_failure_shape.py` reports. The **median** draw of ten is drawn, so
  the picture and the figure describe the same attempt — attempt 0 alone would
  have shown `blue_pot`'s worst sherd at 135% against a reported 8.3%, because
  the draws disagree 5/10 there.
- `artifacts/wearsig_ceramics/renders/narrow_bottle{2,3,4}_band.png` — the break
  surfaces behind the calibration defect. `narrow_bottle4` is the control that
  behaves: interior relief darkens under wear, which is smoothing working.

## Reproduce

```bash
./scripts/remote/pull_and_sbatch.sh scripts/hpc/eval_erosion_ceramics.slurm
./scripts/slurm_poll.sh <JOBID>
# then, on the laptop
scp spartan:<log_dir>/clouds/*.npz artifacts/wearsig_ceramics/
python scripts/check_wear_failure_shape.py --clouds artifacts/wearsig_ceramics
```
