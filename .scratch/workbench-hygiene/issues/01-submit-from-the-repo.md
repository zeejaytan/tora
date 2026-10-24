# 01: Submit from scripts/hpc/; retire the outer operational copies

**What to build:** Jobs are submitted from `scripts/hpc/` in the canonical checkout (or through `new_run.sh`), with absolute log paths; the untracked copies in the outer `TORA/` folder are diffed, archived and removed.

**Answers:** none (workbench routine).

**Blocked by:** None (can start immediately).

**Status:** done

Amendment 4.2. `AGENTS.md` says the operational copies are sbatch'd from the outer folder and synced by hand. Two copies drift. Diff each outer copy against its `scripts/hpc/` twin, commit real differences, then archive the copies under rule 13 and change `AGENTS.md`.

- [x] Every outer copy diffed; differences committed (40 found: 21 identical, 0 differ, 19 no twin, so nothing to commit)
- [x] Outer copies archived (proved) and removed (conservator's OK 2026-10-24; `TORA/attic/outer-job-scripts-20261024/`, 40/40 extracted and cmp'd, 0 left; `runs/index.tsv` row `outer-job-scripts-20261024`)
- [x] `AGENTS.md` Slurm paragraph rewritten; `scripts/check_hpc_paths.py` added (111 scripts, 0 relative log paths)

## Result (2026-10-24)

Read-outs in project files `tora-hygiene/`: `tora_hygiene_spartan01_table.tsv` (the diff),
`tora_hygiene_02_apply.txt` and `tora_hygiene_02_outer-job-scripts-20261024-INDEX.txt` (archive
and proof), `tora_hygiene_02_dry_no_twin_contents.txt` (the 19 no-twin scripts: one-line
wrappers that cd into the repo and run a repo script). Spartan scripts used:
`01_diff_outer_copies.sh`, `02_archive_outer_scripts.sh`. Left alone, for a later tidy: about
240 other loose files at the top of `TORA/` (logs, PNGs, ad-hoc `.py`).
