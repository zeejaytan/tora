# 01: Submit from scripts/hpc/; retire the outer operational copies

**What to build:** Jobs are submitted from `scripts/hpc/` in the canonical checkout (or through `new_run.sh`), with absolute log paths; the untracked copies in the outer `TORA/` folder are diffed, archived and removed.

**Answers:** none (workbench routine).

**Blocked by:** None (can start immediately).

**Status:** ready-for-agent

Amendment 4.2. `AGENTS.md` says the operational copies are sbatch'd from the outer folder and synced by hand. Two copies drift. Diff each outer copy against its `scripts/hpc/` twin, commit real differences, then archive the copies under rule 13 and change `AGENTS.md`.

- [ ] Every outer copy diffed; differences committed
- [ ] Outer copies archived (proved) and removed
- [ ] `AGENTS.md` Slurm paragraph rewritten
