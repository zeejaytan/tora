# 03: The five summarisers become views, and say what moved

**What to build:** Every script that prints a table about a reassembly draws its numbers
from the one module, so two of our own readers can no longer disagree about the same
run. The command lines stay exactly as they are — `docs/notes/` cites them — and each
script records, in its own docstring, which of its figures moved and by how much.

**Answers:** O8

**Blocked by:** 02

**Status:** ready-for-agent

## Why this is last, and why it is the bulk of the work

This is the ticket where published numbers change. It comes after the module has been
checked against a real run, so that when a figure moves we already know the instrument
is sound and the movement is the correction doing its job.

The mechanical part — deleting each script's own arithmetic and calling the module — is
small. The judgement is in the rest: five scripts, each cited by at least one note, each
of whose tables now reads differently, and each needing a sentence that a reader six
months from now can use to tell which version of a number they are looking at.

## Acceptance criteria

- [ ] These five delegate to `scripts/readout.py` and keep their existing command-line
      interfaces unchanged:
  - [ ] `scripts/audit_placement_metrics.py`
  - [ ] `scripts/summarise_juglet_draws.py`
  - [ ] `scripts/summarise_ceramics_arms.py`
  - [ ] `scripts/summarise_scale_ladder.py`
  - [ ] `scripts/analyze_piececount_sweep.py`
- [ ] No arithmetic on `rotation_error`, on part accuracy thresholds, or on anchor
      handling survives outside the module. Grep proves it: the corrected field name is
      the only one any of these five reads.
- [ ] Each script's docstring gains a dated paragraph naming **which of its figures
      moved and by how much** — the actual ratio observed, not the theoretical one.
- [ ] `summarise_scale_ladder.py` produces byte-identical output to before. It was
      already correct; if it changes, stop.
- [ ] Every view prints, beneath its table, the exact `scripts/render_juglet_attempts.py`
      or `scripts/render_assembly_grid.py` invocation that draws the rows above it —
      so looking is the default path rather than the extra step.
- [ ] Every view prints the weight the table can bear: how many objects, how many draws,
      how many trained models. A single-object table says so on its face.
- [ ] `scripts/check_readout.py` still passes, and `python scripts/check_intent_links.py`
      reports zero errors.
- [ ] The notes that cite a figure which moved are **listed** with the affected section —
      not rewritten here. Correcting them is separate work and needs the conservator's
      call on what the corrected number now supports.
- [ ] Confirm juglet-map ticket 02 can now be run honestly: rotation against fragment
      count across the eight fresh pots plus the Juglet, every row on the same ruler.
- [ ] State which of the three this was.
