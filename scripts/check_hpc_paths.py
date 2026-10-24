#!/usr/bin/env python3
"""Check every job script in scripts/hpc/ can be sbatch'd from anywhere.

Jobs are submitted from scripts/hpc/ in the canonical checkout (or through
new_run.sh, which submits from a run directory), never from copies in the outer
TORA/ folder. That only works if a script does not depend on the directory it
was submitted from, so this fails any .slurm/.sbatch whose Slurm --output or
--error is missing or relative, or that reads $SLURM_SUBMIT_DIR.

    python scripts/check_hpc_paths.py      # exit 0 = every script is location-free
"""
import re
import sys
from pathlib import Path

HPC = Path(__file__).resolve().parent / "hpc"
DIRECTIVE = re.compile(r"^#SBATCH\s+(?:--(output|error)[= ]|-(o|e)\s+)(\S+)")


def problems(path):
    found = {}
    out = []
    for n, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
        m = DIRECTIVE.match(line.strip())
        if m:
            kind = "output" if (m.group(1) or m.group(2)) in ("output", "o") else "error"
            found[kind] = m.group(3)
            if not m.group(3).startswith("/"):
                out.append(f"line {n}: --{kind} is relative ({m.group(3)})")
        elif "SLURM_SUBMIT_DIR" in line and not line.lstrip().startswith("#"):
            out.append(f"line {n}: reads $SLURM_SUBMIT_DIR")
    if "output" not in found:
        out.append("no #SBATCH --output (Slurm would write slurm-<id>.out where it was submitted)")
    return out


def main():
    bad = 0
    scripts = sorted(p for p in HPC.iterdir() if p.suffix in (".slurm", ".sbatch"))
    for p in scripts:
        for msg in problems(p):
            print(f"{p.name}: {msg}")
            bad += 1
    print(f"{len(scripts)} job scripts, {bad} problem(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
