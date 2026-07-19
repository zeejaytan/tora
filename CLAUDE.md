# CLAUDE.md — TORA (project)

Follow the workspace root **`../AGENTS.md`** / **`../CLAUDE.md`** (laptop ↔ GitHub ↔ Spartan) for all shared rules. Same overlay as **`AGENTS.md`** in this folder — the fork/upstream/`REMOTE_ROOT` table and Slurm-script conventions live there.

Edit and commit on the laptop; Spartan is pull-only (`git pull --ff-only`) and runs Slurm via `scripts/remote/*`. Heavy data (checkpoints, `dataset/`, `eval_runs/`, logs) stays on Spartan; `artifacts/` is the local, gitignored rsync landing zone.
