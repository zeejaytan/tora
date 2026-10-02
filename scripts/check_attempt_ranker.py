"""Gates for the U17 ranker (rank_attempts.py), fed through its only input: bundles.

Ticket .scratch/attempt-ranker/issues/01. Exit 0 only if every gate passes.

  moved     each of N bundles, given one more random rigid move of the whole
            attempt, scores the same (profile within TOL_MM, same pass, same
            inside-out sherds, same least-sure sherd).
  fence     rank_attempts.py runs under an audit hook that kills it if it opens
            any data file outside --bundles (except its own --out). Its output
            must match an unfenced run. A positive control first proves the hook
            does kill a process that opens a forbidden file.

Usage: python scripts/check_attempt_ranker.py --bundles DIR [--n 6] \\
           [--forbid FILE ...]   (e.g. the dataset hdf5 and the key's idmap.json)
"""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rank_convert import random_rotation  # noqa: E402

TOL_MM = 0.05
DATA_EXT = {".npz", ".npy", ".json", ".hdf5", ".h5", ".ply", ".obj", ".txt", ".csv"}

FENCE = r"""
import sys, os
from pathlib import Path
allow = [Path(p).resolve() for p in sys.argv[1].split(os.pathsep)]
ext = set(sys.argv[2].split(","))
def hook(event, args):
    if event != "open" or not isinstance(args[0], (str, bytes, os.PathLike)):
        return
    p = Path(os.fsdecode(args[0])).resolve()
    if p.suffix.lower() in ext and not any(p == a or a in p.parents for a in allow):
        os.write(2, f"FENCE: opened {p}\n".encode())
        os._exit(97)
sys.addaudithook(hook)
script = sys.argv[3]
sys.argv = [script] + sys.argv[4:]
sys.path.insert(0, str(Path(script).parent))
import runpy
runpy.run_path(script, run_name="__main__")
"""


def fenced(allow, script, args):
    return subprocess.run([sys.executable, "-c", FENCE, __import__("os").pathsep.join(map(str, allow)),
                           ",".join(sorted(DATA_EXT)), str(script), *map(str, args)],
                          capture_output=True, text=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bundles", required=True, type=Path)
    ap.add_argument("--n", type=int, default=6)
    ap.add_argument("--seed", type=int, default=5)
    ap.add_argument("--forbid", nargs="*", type=Path, default=[])
    a = ap.parse_args()
    ok = True
    tmp = Path(tempfile.mkdtemp(prefix="rank_gate_"))
    try:
        # --- moved ---
        rng = np.random.default_rng(a.seed)
        src = sorted((a.bundles / "bundles").glob("*.npz"))[: a.n]
        for side in ("a", "b"):
            (tmp / side / "bundles").mkdir(parents=True)
            shutil.copy(a.bundles / "sherds.npz", tmp / side / "sherds.npz")
        for p in src:
            shutil.copy(p, tmp / "a" / "bundles" / p.name)
            b = np.load(p)
            G, g = random_rotation(rng), rng.uniform(-150, 150, 3)
            np.savez(tmp / "b" / "bundles" / p.name,
                     R=np.einsum("ij,kjl->kil", G, b["R"].astype(float)).astype(np.float32),
                     t=(b["t"].astype(float) @ G.T + g).astype(np.float32))
        res = {}
        for side in ("a", "b"):
            r = subprocess.run([sys.executable, str(HERE / "rank_attempts.py"), "--bundles",
                                str(tmp / side), "--out", str(tmp / f"{side}.json")],
                               capture_output=True, text=True)
            if r.returncode:
                print(r.stderr)
                return 1
            res[side] = {x["id"]: x for x in json.loads((tmp / f"{side}.json").read_text())["attempts"]}
        worst = 0.0
        for k, x in res["a"].items():
            y = res["b"][k]
            worst = max(worst, abs(x["profile_mm"] - y["profile_mm"]))
            same = (x["layer1_pass"] == y["layer1_pass"] and x["inside_out"] == y["inside_out"]
                    and x["least_sure"] == y["least_sure"])
            ok &= same
            if not same:
                print(f"moved: {k} differs: {x} vs {y}")
        ok &= worst <= TOL_MM
        print(f"moved: {len(src)} attempts, largest profile change {worst:.4f} mm "
              f"(tolerance {TOL_MM}) -> {'PASS' if ok else 'FAIL'}")

        # --- fence: positive control ---
        # code, not data: the Python install (package metadata is .json/.txt) and scripts/
        # (Spartan's numpy loads from ~/.local, the user site: job 32105506, 2026-10-02)
        import site
        allow = [tmp / "a", tmp / "fenced.json", HERE, Path(sys.prefix), Path(sys.base_prefix),
                 Path(site.getusersitepackages()), *map(Path, site.getsitepackages())]
        for f in a.forbid:
            probe = tmp / "probe.py"
            probe.write_text(f"open({str(f)!r}, 'rb').close()\n")
            r = fenced(allow, probe, [])
            caught = r.returncode == 97
            ok &= caught
            print(f"fence control: opening {f.name} is {'caught' if caught else 'NOT caught'}")
        # --- fence: the ranker itself ---
        r = fenced(allow, HERE / "rank_attempts.py",
                   ["--bundles", tmp / "a", "--out", tmp / "fenced.json"])
        if r.returncode:
            print(f"fence: ranker stopped (exit {r.returncode}): {r.stderr.strip()[-300:]}")
            ok = False
        else:
            f = {x["id"]: x for x in json.loads((tmp / "fenced.json").read_text())["attempts"]}
            same = all(f[k]["profile_mm"] == res["a"][k]["profile_mm"]
                       and f[k]["rank"] == res["a"][k]["rank"] for k in f)
            ok &= same
            print(f"fence: ranker opened nothing outside its bundles; output "
                  f"{'identical' if same else 'DIFFERS'}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("ALL GATES PASS" if ok else "GATE FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
