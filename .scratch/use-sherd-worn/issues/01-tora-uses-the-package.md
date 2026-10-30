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
- [x] Equivalence job written: worn, rough and v3 smoke identical array by array; fine-scan on 3 objects with "neither" = 0 (see the arm D note below)
- [ ] Job passed and reviewed by the coordinator; only then merged

## Comments

**Module edit, 2026-10-30, Claude on Thinkbook16, by hand, not DeepSeek.**

verified: `git diff --quiet 1db3453 origin/master` on the four modules -> no difference, before the edit.
verified: scratchpad shimcheck.py (ast against origin/master) -> kept defs identical 6+6+8+6 = 26, other top-level statements identical, and all 26 removed names `is` the package object; `wear_ops.erode_fracture_band` is the package object through its unchanged line from `fracture_mesh_ops`.

`scripts/check_mesh_integrity.py` and `scripts/check_wall_estimator_noise.py` import these modules, so after the merge they need the package wherever they run.

verified: hidden check (lead, cloud) on 5e4d887 vs 67779bf -> all properties hold; install.sh pin reviewed.

**Equivalence job, 2026-10-30, Claude on Thinkbook16.** `scripts/hpc/sw05_equiv.slurm`, `scripts/compare_hdf5_arrays.py`, `scripts/compare_fine_scan_arms.py`. The coordinator has asked for 3259d06 to be submitted through `new_run.sh`, falling back to a plain `sbatch`. It installs the package into `$RUN_DIR/pydeps`, so the shared env is untouched.

The accepted criterion, "neither" = 0, changed, and the coordinator accepted the change (relay of 2026-10-30, 12:19Z). `blunt_asperities` divides each vertex's exposure by the standard deviation of all the exposure heights on the piece. A guard at that coarse fit changes that one number, and through it every vertex whose removed fraction is below 1, however far from the guarded vertex. So master without thinning against the package (B to C) can have "neither" above 0 without anything being wrong. A fourth arm, D, is the package with the exposure heights taken from B: B to D must have "neither" = 0 strictly, and B to C may have it only on a piece whose exposure divisor changed, with the largest such move reported. Pictures of the three largest moves per comparison land in `out/fine_scan/`.

verified: synthetic pair of 64800-vertex sheets, laptop, scratchpad tinytest.py and tinytest2.py -> no failures on the clean run; a planted stray vertex fails B-C and B-D with 1 in neither; a planted exposure change gives B-C 78 in neither with the divisor flagged and no failure, B-D 0 in neither. This tests the checks only and says nothing about pots.
verified: compare_hdf5_arrays on small files -> reordered groups and NaNs pass; a 1e-7 value change, an attribute change, a missing group and a manifest change each fail.

**Failed run, setup only, nothing tested (2026-10-30, Claude on Thinkbook16).** Job 34061924, run `TORA/runs/20261030-2319_3259d06_sw05equiv`, stopped in setup with exit 2:0. The job set `PYTHONNOUSERSITE=1`, which no other TORA job does, and TORA's numpy lives in `~/.local`, so the package could not import numpy and the job printed "sw05: wrong package". No arm built anything. My error. The line is gone; `--no-deps` stays, so both arms use the numpy master uses.

Where the log lands: through `new_run.sh`, `$RUN_DIR/logs/tora-sw05equiv-<job>.out` (it overrides the script's `--output`); through a plain `sbatch`, `TORA/logs/sw05equiv_<job>.log`.

rtree: neither compare script imports it, and it stays out of every arm. But the arms do reach it: `_chip_dish` and `_seal_once` call `trimesh.proximity.closest_point`, which needs rtree, inside `except Exception: pass`. rtree is not installed in this environment, so master and the package both skip those tests, as every existing TORA build has. The comparison is valid for that environment. The job prints which it found. Whether the package should declare rtree is a separate question, raised with the coordinator.

verified: `tail logs/tora-sw05equiv-34061924.out` -> ModuleNotFoundError numpy at sherd_worn/labelled.py:16, then "sw05: wrong package".
verified: login-node import probe with the run's pydeps and no PYTHONNOUSERSITE -> sherd_worn 0.1.0, numpy 2.2.6 from ~/.local; master arm `_proud_height` from wear_ops, switched arm from sherd_worn.wear; rtree absent. Read, not run: trimesh proximity.py:52 `mesh.triangles_tree`, util.py:1742 `import rtree`.
