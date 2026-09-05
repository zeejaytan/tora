# 02: Reconcile the module against a run we have already published

**What to build:** Confidence that the module reads our actual files, not just its own
fixtures. Take one evaluation run whose numbers are already written into
`docs/notes/`, read it with the new module, and account for **every** column that
differs — what moved, by how much, and why. The output is a short written
reconciliation, not a passing test.

**Answers:** O8

**Blocked by:** 01

**Status:** done

## Why this is separate from the gate

The gate in ticket 01 proves the arithmetic. It cannot prove we are reading the right
field out of the right file, that `num_parts` means what we assume on a real run, or
that a run saved under an older evaluator has the layout we expect.

This is the ticket that catches a column matching **for the wrong reason** — which is
the failure the whole spec exists to prevent, and the exact shape of the last two units
bugs: a value that looked right in the place it was checked.

## Acceptance criteria

- [x] One already-published run is chosen and named, along with the note and section
      that reports it. Prefer a run with a **known** correction status so the expected
      direction is predictable — `summarise_scale_ladder.py`'s ladder run is the natural
      first choice because it was already corrected.
- [x] Every column the note reports is regenerated through `scripts/readout.py` and
      placed beside the published figure in a table: published, new, difference, cause.
- [x] **`summarise_scale_ladder.py`'s figures must not move.** They were already
      corrected. If any of them moves, stop and report — the module is wrong, and this
      ticket does not proceed to the second run.
- [x] A second run read by an **uncorrected** reader
      (`summarise_juglet_draws.py` or `audit_placement_metrics.py` on a Juglet run) is
      reconciled the same way. Its rotation figures are expected to rise by ×1.125;
      confirm the observed ratio matches `n/(n-1)` for that object rather than merely
      being "higher".
- [x] Any difference that is **not** explained by the anchor correction, the unit-box
      threshold flag, or the quantised seated count is written up as an open question
      before this ticket closes. An unexplained difference is a finding, not a rounding
      detail.
- [x] Confirm the health flags fire where the record says they should: the `juglet_norm`
      runs at model size 0.041 and the millimetre Fractura subsets at 24–120 raise
      flag (a); the `juglet_gt` runs at 0.511 do not.
- [x] **Render one assembly from the reconciled run** and confirm the picture agrees with
      what the corrected table now says about it. A table that changed while the pot
      still looks the same way it did is a table whose meaning needs restating in words.
- [x] The reconciliation is written into `docs/notes/` as a dated entry, not left in
      `.scratch/` — it is the record of what the instrument does to our published
      figures.
- [x] State which of the three this was.

## Result, 2026-09-05

**Which of the three: the ruler.** Nothing was re-run; the assemblies are unchanged.

Written up in `docs/notes/READOUT_RECONCILIATION.md`. In short:

- **Control held.** All 72 cells of the scale-ladder table in `FRACTURA_WHY_IT_FAILS.md`
  regenerate through the module with a largest difference of **0.048°** — the rounding of
  the published one-decimal figures. `summarise_scale_ladder.py` was already correct and
  the module agrees with it.
- **The uncorrected reader moved by exactly n/(n-1).** `summarise_juglet_draws.py`
  publishes 55.7° for `lorav3_juglet_baseline_29880370`; the module reads 62.7°, and
  every draw moves by 1.125000 — the ratio, not merely "higher".
- **Flags fire where the record says.** Silent on the normalised rung at 0.500; raised on
  every other rung (44.7–120.1 on the as-shipped millimetre run) and on `juglet_norm` at
  0.041.
- **One difference needed explaining and was explained.** `juglet_norm_baseline_27859890`
  reports 9 of 9 seated on every draw while turned 52–80°. Both flags fire on it together
  and account for it: scored in stored units at scale 0.041, so the fixed tolerance was
  enormous and everything passed. Already-known units bug, newly self-announcing.
- **Rendered.** Draw 0 of the Juglet run is not a vessel, which agrees with the corrected
  65.5° and not with the published 58.2°.

One defect in the module was found by this ticket and fixed: `format_flags` repeated a
per-run warning once per draw. `check_readout.py` now asserts a warning that applies to
every draw is printed once.

Provenance note: `.hydra/config.yaml` recovers checkpoint, seed, draw count, anchor mode,
dataset and point count on every run tried, including a run from July.
