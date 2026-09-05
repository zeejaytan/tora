# 02: Reconcile the module against a run we have already published

**What to build:** Confidence that the module reads our actual files, not just its own
fixtures. Take one evaluation run whose numbers are already written into
`docs/notes/`, read it with the new module, and account for **every** column that
differs — what moved, by how much, and why. The output is a short written
reconciliation, not a passing test.

**Answers:** O8

**Blocked by:** 01

**Status:** ready-for-agent

## Why this is separate from the gate

The gate in ticket 01 proves the arithmetic. It cannot prove we are reading the right
field out of the right file, that `num_parts` means what we assume on a real run, or
that a run saved under an older evaluator has the layout we expect.

This is the ticket that catches a column matching **for the wrong reason** — which is
the failure the whole spec exists to prevent, and the exact shape of the last two units
bugs: a value that looked right in the place it was checked.

## Acceptance criteria

- [ ] One already-published run is chosen and named, along with the note and section
      that reports it. Prefer a run with a **known** correction status so the expected
      direction is predictable — `summarise_scale_ladder.py`'s ladder run is the natural
      first choice because it was already corrected.
- [ ] Every column the note reports is regenerated through `scripts/readout.py` and
      placed beside the published figure in a table: published, new, difference, cause.
- [ ] **`summarise_scale_ladder.py`'s figures must not move.** They were already
      corrected. If any of them moves, stop and report — the module is wrong, and this
      ticket does not proceed to the second run.
- [ ] A second run read by an **uncorrected** reader
      (`summarise_juglet_draws.py` or `audit_placement_metrics.py` on a Juglet run) is
      reconciled the same way. Its rotation figures are expected to rise by ×1.125;
      confirm the observed ratio matches `n/(n-1)` for that object rather than merely
      being "higher".
- [ ] Any difference that is **not** explained by the anchor correction, the unit-box
      threshold flag, or the quantised seated count is written up as an open question
      before this ticket closes. An unexplained difference is a finding, not a rounding
      detail.
- [ ] Confirm the health flags fire where the record says they should: the `juglet_norm`
      runs at model size 0.041 and the millimetre Fractura subsets at 24–120 raise
      flag (a); the `juglet_gt` runs at 0.511 do not.
- [ ] **Render one assembly from the reconciled run** and confirm the picture agrees with
      what the corrected table now says about it. A table that changed while the pot
      still looks the same way it did is a table whose meaning needs restating in words.
- [ ] The reconciliation is written into `docs/notes/` as a dated entry, not left in
      `.scratch/` — it is the record of what the instrument does to our published
      figures.
- [ ] State which of the three this was.
