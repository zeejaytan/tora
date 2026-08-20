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
