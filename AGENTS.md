# AGENTS.md — TORA (project)

Follow the workspace root **`../AGENTS.md`** (laptop ↔ GitHub ↔ Spartan) for all shared rules. This file only adds TORA-specific paths and domain notes.

## TORA paths

| Role | Value |
|------|--------|
| GitHub fork (`origin`) | `zeejaytan/tora` |
| Upstream | `NahyukLEE/tora` |
| Spartan checkout (`REMOTE_ROOT`) | `/data/gpfs/projects/punim2657/TORA/repo` |
| Spartan working area (untracked) | `/data/gpfs/projects/punim2657/TORA/` — launch dir for Slurm; holds `checkpoints/`, `dataset/`, `eval_runs/`, `envs/tora` (conda), logs |
| SSH | `Host spartan`, user `zhuojiat` |
| Remote helpers | `scripts/remote/pull_and_sbatch.sh`, `job_status.sh`, `fetch_artifacts.sh` |

Default branch is **`master`**. Heavy data on Spartan only: checkpoints, `dataset/`, `eval_runs/`, `raw/`, logs. Local rsync landing zone: `artifacts/`.

**Write rules:** new analysis/code → `scripts/`; versioned Slurm → `scripts/hpc/`; method notes → `docs/notes/`; fetched samples → `artifacts/` (not source); HPC paths → `CLAUDE.local.md`. Do not add files at the TORA root.

**Slurm scripts:** the versioned copies live in `scripts/hpc/`; the *operational* copies live untracked in the outer `TORA/` folder on Spartan and are sbatch'd from there (their log/output paths assume that). When editing a job script, edit `scripts/hpc/` here, push, and update the outer copy on Spartan to match — or switch to sbatching the repo copy.

Typical loop:

```bash
git push origin HEAD
./scripts/remote/job_status.sh
./scripts/remote/fetch_artifacts.sh some/remote/path ./artifacts/
```

## Domain / debugging

TORA is a 3D fracture assembly method (evaluated zero-shot on fractura/juglet/thinwalled sets here). `tora.eval.spatial` is referenced by training-time probing callbacks but absent upstream — its re-exports are disabled in `tora/eval/__init__.py`; do not "fix" imports by re-adding them. Analysis notes live in `docs/notes/`.

## Agent skills

Configured here so this repo works when opened on its own, not only from the `C:\PR`
umbrella. The full text of each convention lives at the workspace root; these are the
parts an agent needs before it can act.

- **Issue tracker — local markdown.** One feature per directory: the spec at
  `.scratch/<feature>/spec.md`, tickets one per file at
  `.scratch/<feature>/issues/<NN>-<slug>.md`, numbered from `01` in dependency order.
  Every ticket carries an **`Answers:`** line naming the question in `intent/` it exists
  to settle -- `O1` for this project, `U6` for the workspace, or `none` for routine
  work. Conventions and the ticket template: `../docs/agents/issue-tracker.md`.
- **Triage labels.** `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`,
  `wontfix`, recorded as a `Status:` line near the top of the ticket. Details:
  `../docs/agents/triage-labels.md`.
- **Domain docs — single-context.** Three different things, kept apart: **this file** is
  how to work here and the traps; **`CONTEXT.md`** at the repo root is the glossary, and
  `/domain-modeling` creates it lazily when the first term is actually resolved — do not
  create it empty; **`../docs/glossary.md`** is the cross-project measurement vocabulary
  (`part_acc`, chamfer distance, best-of-N) and outranks any local redefinition. ADRs go
  under `docs/adr/`. Details: `../docs/agents/domain.md`.
- **Intent.** [`intent/`](intent/) holds what we are trying to establish and what would
  settle it -- prefix **`O`**, permanent, numbers never reused. `/to-intent` opens a
  question or writes a finished ticket's result back into one. Check the loop is wired
  with `python ../scripts/check_intent_links.py`.

**Do not run `/setup-matt-pocock-skills` in this repo.** It would replace the above with
its own defaults, and its ticket template has no `Answers:` line -- tickets would stop
being connected to the question they exist to answer, silently.
