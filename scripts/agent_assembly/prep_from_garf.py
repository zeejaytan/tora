"""Start the agent from GARF's own Juglet attempts (AssemblyWorld's GARF -> agent order).

Ticket `.scratch/agent-assembly/issues/05`. Runs on Spartan: the answer key never leaves it.

WHAT THIS REPRODUCES. AssemblyWorld App. D: "For GARF-to-Agent, the predicted poses
initialize the original meshes with no preceding interaction history. Astra receives the
original no-reference prompt". So each task here is one saved GARF attempt: every sherd moved
by the rigid pose GARF gave it, nothing else said. The agent gets the same prompt as before.

WHICH ATTEMPTS. Saved GARF Juglet attempts (`clouds/*.npz` of rwlora_arm runs) are scored with
own_place.score_draw on the solid cloud (each true sherd rigidly placed). For each own-place
count in --pick (default 8, 7, 6 of 9) the attempt with the most sherds right way round is
taken, from different presentations where possible: GARF near-misses an agent might tidy.

FRAMES. A saved cloud is in GARF's normalised frame. One similarity (scale, turn, shift) maps
it onto the conservator's reassembly in the HDF5 file, fitted on the sherd centres and refined
on closest points (a dense surface sample), sherd by sherd; the fit residual is printed in mm and the attempt refused
above --max-fit-mm. GARF's pose for sherd k (Kabsch of its home points onto its placed points,
exact for the solid cloud) is carried through that similarity into the HDF5 frame. The whole
attempt is then stood with the pot's long axis along +Z, given a random yaw, scaled by the
paper's shared scale (twice the largest sherd radius) and set on the floor. The 4x4 map from
answer-key to scene goes in the secret file exactly as prep_tasks.py writes it, so
score_tasks.py scores these runs unchanged, and an untouched scene (T = identity) scores as
GARF's own attempt: that is the baseline each run is read against.

Usage (Spartan, tora env):
  python scripts/agent_assembly/prep_from_garf.py --h5 dataset/juglet_gt.hdf5 \
      --runs '/data/gpfs/projects/punim2657/GARF/logs/rwlora/rwlora_eval_*juglet_gt_3183563[56]/version_0' \
      --out ../agent_assembly/tasks_v1 --pot-mm 65
"""

import argparse
import glob
import json
import string
import sys
from pathlib import Path

import numpy as np
import trimesh
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
from prep_tasks import lighten, load_pieces  # noqa: E402
from own_place import score_draw  # noqa: E402
from readout import part_slices  # noqa: E402


def umeyama(src, dst, scale=True):
    """Similarity (s, R, t) with dst ~ s R src + t."""
    ms, md = src.mean(0), dst.mean(0)
    a, b = src - ms, dst - md
    U, D, Vt = np.linalg.svd(b.T @ a / len(src))
    S = np.diag([1, 1, np.sign(np.linalg.det(U @ Vt))])
    R = U @ S @ Vt
    s = float(np.trace(np.diag(D) @ S) / a.var(0).sum()) if scale else 1.0
    return s, R, md - s * R @ ms


def fit_frame(gt, slices, meshes, iters=30, dense=200000):
    """Similarity taking GARF's normalised cloud onto the HDF5 sherds; residual in HDF5 units.

    Closest points come from a dense surface sample of each sherd (KD-tree), so no rtree is
    needed; the sample spacing is printed beside the residual and bounds its resolution.
    """
    surf = [trimesh.sample.sample_surface(m, dense, seed=k)[0] for k, m in enumerate(meshes)]
    trees = [cKDTree(p) for p in surf]
    spacing = max(np.sqrt(m.area / dense) for m in meshes)
    cg = np.array([gt[a:b].mean(0) for a, b in slices])
    cm = np.array([p.mean(0) for p in surf])
    s, R, t = umeyama(cg, cm)
    for _ in range(iters):
        X = s * gt @ R.T + t
        Y = np.vstack([surf[k][trees[k].query(X[a:b])[1]] for k, (a, b) in enumerate(slices)])
        s, R, t = umeyama(gt, Y)
    X = s * gt @ R.T + t
    res = np.concatenate([trees[k].query(X[a:b])[0] for k, (a, b) in enumerate(slices)])
    return s, R, t, float(np.median(res)), float(np.percentile(res, 95)), spacing


def kabsch(src, dst):
    s, R, t = umeyama(src, dst, scale=False)
    return R, t


def candidates(run_globs):
    out = []
    for pat in run_globs:
        for run in sorted(glob.glob(pat)):
            for npz in sorted(Path(run, "clouds").glob("*.npz")):
                with np.load(npz, allow_pickle=True) as d:
                    gt, ppp = d["pts_gt"].astype(float), d["points_per_part"]
                    for g, pred in enumerate(d["generations_proposed"]):
                        dr = score_draw(gt, pred.astype(float), ppp)
                        out.append({"run": run, "npz": str(npz), "attempt": g,
                                    "own": dr.own, "rwr": dr.oriented, "n": dr.n})
    return out


def pick(cands, wants):
    chosen, used = [], set()
    for w in wants:
        pool = [c for c in cands if c["own"] == w]
        if not pool:
            print(f"  no GARF attempt with own place {w}")
            continue
        fresh = [c for c in pool if c["run"] not in used] or pool
        c = max(fresh, key=lambda c: (c["rwr"], -c["attempt"]))
        chosen.append(c)
        used.add(c["run"])
    return chosen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--h5", required=True)
    ap.add_argument("--runs", nargs="+", required=True, help="globs of GARF run dirs holding clouds/")
    ap.add_argument("--out", required=True)
    ap.add_argument("--pick", default="8,7,6")
    ap.add_argument("--pot-mm", type=float, default=65.0)
    ap.add_argument("--faces", type=int, default=30000)
    ap.add_argument("--seed", type=int, default=5)
    ap.add_argument("--max-fit-mm", type=float, default=0.5)
    a = ap.parse_args()

    name, pieces = load_pieces(a.h5)
    full = [trimesh.Trimesh(v, f, process=False) for v, f in pieces]
    allv = np.vstack([v for v, _ in pieces])
    ext = allv.max(0) - allv.min(0)
    mm = a.pot_mm / float(ext.max())
    light = [lighten(m, a.faces)[0] for m in full]

    cands = candidates(a.runs)
    print(f"{len(cands)} GARF attempts scored (solid cloud)")
    hist = {}
    for c in cands:
        hist[(c["own"], c["rwr"])] = hist.get((c["own"], c["rwr"]), 0) + 1
    print("  own place / right way round : attempts  ->",
          ", ".join(f"{o}/{r}:{n}" for (o, r), n in sorted(hist.items(), reverse=True)))
    chosen = pick(cands, [int(x) for x in a.pick.split(",")])

    out = Path(a.out)
    (out / "secret").mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(a.seed)
    # stand the pot's long axis up: a proper permutation taking that axis to +Z
    up = int(np.argmax(ext))
    P = np.eye(3)[[(up + 1) % 3, (up + 2) % 3, up]]
    radius = max(np.linalg.norm(m.vertices - m.vertices.mean(0), axis=1).max() for m in full)
    s_scene = 2.0 * radius

    for ti, c in enumerate(chosen):
        tname = f"garf_{string.ascii_lowercase[ti]}"
        with np.load(c["npz"], allow_pickle=True) as d:
            gt = d["pts_gt"].astype(float)
            pred = d["generations_proposed"][c["attempt"]].astype(float)
            slices = part_slices(d["points_per_part"])
        if len(slices) != len(full):
            raise SystemExit(f"{c['npz']}: {len(slices)} sherds in cloud, {len(full)} in {a.h5}")
        s, R, t, med, p95, sp = fit_frame(gt, slices, full)
        print(f"  {tname}: {c['run']} attempt {c['attempt']}: own {c['own']}/{c['n']}, right way round "
              f"{c['rwr']}/{c['n']}; frame fit median {med * mm:.3f} mm, 95% {p95 * mm:.3f} mm "
              f"(sample spacing {sp * mm:.3f} mm)")
        if med * mm > a.max_fit_mm:
            raise SystemExit(f"frame fit {med * mm:.3f} mm > {a.max_fit_mm}; refusing")
        G = []
        for k, (i0, i1) in enumerate(slices):
            Rk, tk = kabsch(gt[i0:i1], pred[i0:i1])
            # h -> n = (R^T (h - t))/s ; n' = Rk n + tk ; h' = s R n' + t
            A = R @ Rk @ R.T
            M = np.eye(4)
            M[:3, :3] = A
            M[:3, 3] = -A @ t + s * R @ tk + t
            G.append(M)
        yaw = rng.uniform(-np.pi, np.pi)
        Rz = np.array([[np.cos(yaw), -np.sin(yaw), 0], [np.sin(yaw), np.cos(yaw), 0], [0, 0, 1]])
        L = np.eye(4)
        L[:3, :3] = Rz @ P / s_scene
        maps = [L @ M for M in G]
        pts = np.vstack([trimesh.transform_points(full[k].vertices, maps[k]) for k in range(len(full))])
        lo, hi = pts.min(0), pts.max(0)
        shift = np.array([-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]])
        for M in maps:
            M[:3, 3] += shift
        anchor = int(np.argmax([m.area for m in full]))
        print(f"    anchor sherd {anchor} moved by GARF: "
              f"{np.linalg.norm(G[anchor][:3, 3]) * mm:.2f} mm, "
              f"{np.degrees(np.arccos(np.clip((np.trace(G[anchor][:3, :3]) - 1) / 2, -1, 1))):.1f} deg")
        ids = [f"part_{x}" for x in rng.permutation(list(string.ascii_lowercase))[:len(full)]]
        pdir = out / "public" / tname / "pieces"
        pdir.mkdir(parents=True, exist_ok=True)
        for pid, k in zip(ids, range(len(full))):
            m = light[k].copy()
            m.apply_transform(maps[k])
            m.export(pdir / f"{pid}.ply")
        (out / "public" / tname / "task.json").write_text(json.dumps({
            "task": tname, "parts": sorted(ids),
            "conventions": "scene units; world up +Z; parts start where another method placed them",
        }, indent=1))
        (out / "secret" / f"{tname}.json").write_text(json.dumps({
            "task": tname, "object": name, "h5": str(Path(a.h5).resolve()),
            "mm_per_unit": mm, "shared_scale": s_scene, "seed": a.seed,
            "garf": {k: c[k] for k in ("run", "npz", "attempt", "own", "rwr")},
            "frame_fit_mm": {"median": med * mm, "p95": p95 * mm},
            "parts": {pid: {"sherd": int(k), "gt_to_scene": maps[k].tolist()}
                      for pid, k in zip(ids, range(len(full)))},
        }, indent=1))
        print(f"    task {tname}: parts {ids}")


if __name__ == "__main__":
    main()
