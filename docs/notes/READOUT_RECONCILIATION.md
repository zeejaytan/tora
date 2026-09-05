# Reconciling the new read-out against runs we have already published

**2026-09-05.** `scripts/readout.py` is now the single place an evaluation run is read.
Before any table is rebuilt with it, this is the check that it reads *our* files rather
than only its own fixtures — the failure the whole exercise exists to prevent is a column
that matches for the wrong reason, which is the exact shape of the last two units bugs.

**Which of the three this is: the ruler.** No model was re-run and no reference changed.
The assemblies are the same assemblies. What changed is what we read off them.

## What was reconciled

| | run | why |
|---|---|---|
| control | `scaleladder_*_29891327` (8 runs, job 29891327) | already corrected by `summarise_scale_ladder.py`; its figures **must not move** |
| test | `lorav3_juglet_baseline_29880370` | read by an **uncorrected** reader (`summarise_juglet_draws.py`); its figures must rise by exactly n/(n-1) |
| flags | `juglet_norm_baseline_27859890` | stored size 0.041, and scored before the unit-box fix |

Only `results/*.json` and `.hydra/config.yaml` were fetched — under a megabyte in total,
in `artifacts/reconcile/` (gitignored). Nothing was recomputed on the cluster.

## The control held

All 72 cells of the scale-ladder table in `FRACTURA_WHY_IT_FAILS.md` were regenerated
through the module and compared with the published figures. **The largest difference
anywhere in the table is 0.048°**, which is the rounding of the published one-decimal
values. Every pot, every rung, unchanged:

```
scale fed in   published ALL   module ALL
      0.500          30.8        30.8
      1.000          23.9        23.9
      2.500          30.3        30.3
      5.000          25.7        25.7
     15.000          44.6        44.6
     50.000          74.9        74.9
     69.217          81.2        81.2   <- as shipped, millimetres
    100.000          77.8        77.8
```

That is the point of the control: `summarise_scale_ladder.py` already applied the
correction by hand, so a module that agrees with it is applying the same correction, and
one that disagreed would have been wrong.

The health flags behaved as they should on the same eight runs: the normalised rung at
0.500 is **silent**, and every other rung is flagged as outside the band the model was
trained on — the as-shipped millimetre run per pot at 44.7 to 120.1.

## The uncorrected reader moved by exactly the predicted factor

`summarise_juglet_draws.py` publishes **55.7°** for `lorav3_juglet_baseline_29880370`.
The module reads **62.7°**. Every draw moves by the same ratio, and the ratio is
n/(n-1) = 9/8 to six decimal places — not merely "higher":

```
draw   as published   corrected    ratio    seating
  0        58.24        65.52     1.125000   4 of 9 sherds seated (1 free)
  1        55.72        62.68     1.125000   6 of 9
  2        59.88        67.36     1.125000   5 of 9
  3        53.92        60.67     1.125000   5 of 9
  4        54.26        61.04     1.125000   5 of 9
median     55.72        62.68     1.125000
```

**What the seven degrees mean.** 55.7° reads as a bad but ambiguous result. 62.7° sits
squarely in the range this project has been calling collapsed (40–70°), well clear of the
10–35° range where the residual is symmetry rather than error. The correction does not
change the verdict on this pot; it removes the room to argue about it.

**And the eight degrees the Juglet was quoted at.** The figures "31.4 / 33.5 / 58.2"
that appear in `intent/O8` and in `.scratch/juglet-cause/` as three separate baseline
runs are generation-0 values, not run means, and the three runs turn out to share
effectively identical `.hydra` settings — so they are repeats of one condition, and the
spread they were quoted to demonstrate is mostly the spread between *draws*. That belongs
to `.scratch/juglet-cause/issues/01`, which has been corrected in place; it is noted here
because it was found while doing this.

## One unexplained difference, and it was worth finding

`juglet_norm_baseline_27859890` reports **9 of 9 sherds seated on every draw** while the
same draws are turned **52° to 80°**. Every sherd cannot be correctly placed and turned
sixty degrees at once. The module raises both of its flags on that run:

```
model size input outside the trained band: 0.04075 not in [0.375, 0.625]
scored before the unit-box threshold fix
```

which together account for it exactly: the run was scored in stored units at a scale of
0.041, so the fixed 0.01 tolerance was enormous relative to the object and everything
passed. It is not a new finding — it is the units bug already documented in
`FRACTURA_WHY_IT_FAILS.md` — but it is the first time a reader has said so on its own
face instead of printing a perfect score with nothing beside it.

## Looking at it

![the reconciled Juglet](../../artifacts/reconcile/juglet_reconcile.png)

Regenerate with:

```bash
python scripts/render_assembly_grid.py \
    --runs "lorav3 baseline=artifacts/reconcile/lorav3_juglet_baseline_29880370/clouds" \
    --out artifacts/reconcile/juglet_reconcile.png
```

Draw 0 — the panel drawn, 4 of 9 seated, 65.5° corrected — is not a vessel. The neck and
handle sit roughly where they belong; three body sherds are turned out of the wall and
one hangs clear of the pot entirely. **The picture agrees with the corrected number and
not with the published one**: a table reading 58° for this draw invited "bad but close",
and the object is not close.

## Weight

Eight objects across eight rungs (400 draws) for the control; one object, five draws, one
trained model for the Juglet half. The control is strong — 72 cells agreeing to 0.05° is
not a coincidence. The Juglet half is one pot: it demonstrates that the correction applies
and by how much, not anything about pots in general.

## A second broken ruler, found while rewiring (2026-09-05)

Rewiring the last two scripts turned up a **different** measurement error, in the
cloud-side scoring rather than the run-json reading. Two scripts scored a reassembly
directly from the saved point clouds, and both did it with the wrong tolerance.

**What was wrong.** `scripts/score_assembly.py` and `scripts/refine_seating.py` each kept
their own copy of the seating metric and thresholded it at `0.01 / scale`. That is the
**withdrawn absolute metric** — a fixed hundredth in each dataset's own units, which is
2% of a Breaking Bad vessel and 0.014% of a millimetre-stored ceramic pot. It is the
units bug that faked a finding once already (jobs 27858648 / 27859890; see
`TORA_GOOD_VS_BAD_ANALYSIS.md`). It was not even a faithful copy of it: the tolerance is
compared against a **squared** distance, so converting it into the stored frame divides
by `scale²`, not `scale`. At a Breaking Bad scale of 0.5 the shipped threshold is 0.04 in
that frame; these scripts used 0.02, twice as strict.

**And one in the module itself.** `readout.chamfer` carried a `0.5` factor with a
docstring claiming it was what pytorch3d does. It is not. At the pinned version —
pytorch3d 0.7.8, the wheel named in `pyproject.toml`, which is what `compute_part_acc`
calls — `chamfer_distance(single_directional=False, point_reduction="mean")` returns
`cham_x + cham_y`, with no halving. The halved version made every cloud rescoring
**exactly twice as forgiving** as the evaluator it was being compared against.

It was caught because `score_assembly.py` had computed the same quantity independently,
without the halving, so the two disagreed by a factor of two on the same clouds. That is
the argument for one module: not that a single implementation is more likely to be right,
but that a second one disagreeing is the only thing that says it is wrong.

**Which of the three this is.** The measurement was broken — twice, in the same direction
of carelessness, and both times in the tolerance rather than the geometry. No method
result changed and no reference answer was in question.

**What must be rerun before it is quoted.** Anything scored from `clouds/*.npz`:
`scripts/rescore_part_acc.py` (its threshold sweep read as reaching a given accuracy at
half the threshold it really needs), `scripts/score_assembly.py --validate` (its
score-versus-truth correlations were measured against a seating far stricter than the
real one), and `scripts/refine_seating.py` (every before → after seating pair). The
run-json tables are untouched by this: they read stored fields and never recompute a
chamfer.

**The gate now holds both conventions.** `scripts/check_readout.py` asserts that the
chamfer sums both directions (two points 3 apart → 18.0, not 9.0) and that the unit-box
tolerance squares the size (a box of 2.0 → 0.04). Both are one-line assertions, and both
would have caught this on the day it was written.

## What this does not yet cover

Every reader now goes through the module and the rewiring is done; what remains is the
prose. No note has been rewritten. The notes that quote a figure which moved are listed
in `.scratch/eval-readout/issues/03`, and correcting them needs a decision about what the
corrected number now supports — that is not a mechanical edit.
