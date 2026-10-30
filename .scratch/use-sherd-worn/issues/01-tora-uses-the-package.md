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

- [ ] `git diff 1db3453 origin/master` is empty for the four modules before the edit
- [ ] 26 copied functions become one import block per module; every other def byte-identical
- [ ] `sherd-worn` pinned to v0.1.0 where TORA lists dependencies
- [ ] Equivalence job written: worn, rough and v3 smoke identical array by array; fine-scan on 3 objects with "neither" = 0
- [ ] Job passed and reviewed by the coordinator; only then merged

## Comments
