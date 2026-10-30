# 01: TORA imports its wear code from sherd-worn

**What to build:** `wear_ops.py`, `fracture_mesh_ops.py`, `write_u10_worn.py` and `compare_wear_severity.py`
stop holding their own copy of the 26 functions released as `sherd-worn` v0.1.0 and import them instead.
Every other function stays byte-identical and no importing script changes. Two comparison scripts and one
Slurm job show what the switch changes. Do not merge until that run has passed and the coordinator has reviewed it.

**Answers:** none
**Blocked by:** None - can start immediately
**Status:** in-progress
**Working in:** laptop chat, Remote Control (2026-10-30) (2026-10-30)
**Branch:** 01-tora-uses-the-package, in /c/PR/worktrees/tora/01

**Why:** sherd-worn ticket 05 (`sherd-worn/.scratch/release/issues/05-tora-csc-use-the-package.md`) holds the
decision and the plan. TORA and the package must not drift apart as two copies, and the conservator chose to take
the skin-spike fix in `_proud_height`.

- [x] `git diff 1db3453 origin/master` is empty for the four modules before the edit
- [x] 26 copied functions become one import block per module; every other def byte-identical
- [x] `sherd-worn` pinned to v0.1.0 where TORA lists dependencies
- [ ] Equivalence job written: worn, rough and v3 smoke identical array by array; fine-scan on 3 objects with "neither" = 0
- [ ] Job passed and reviewed by the coordinator; only then merged

## Comments

**Module edit, 2026-10-30, Claude on Thinkbook16, by hand, not DeepSeek.**

verified: `git diff --quiet 1db3453 origin/master` on the four modules -> no difference, before the edit.
verified: scratchpad shimcheck.py (ast against origin/master) -> kept defs identical 6+6+8+6 = 26, other top-level statements identical, and all 26 removed names `is` the package object; `wear_ops.erode_fracture_band` is the package object through its unchanged line from `fracture_mesh_ops`.

`scripts/check_mesh_integrity.py` and `scripts/check_wall_estimator_noise.py` import these modules, so after the merge they need the package wherever they run.
