"""Score an agent's blind reassembly against the conservator's answer, on two rulers.

Ticket `.scratch/agent-assembly/issues/03`. Runs on Spartan, where the answer key is.

INPUT. `--runs` holds one folder per agent run, each with the `final.json` that `aw_env.py
finish` wrote (a 4x4 pose per anonymous part id). `--secret` is prep_tasks.py's secret folder.

ALIGNMENT. The scene has no fixed frame, so one rigid move is allowed for the whole assembly
before scoring. Two are reported:
  anchor  the largest sherd laid exactly on its home; the others scored from it (the paper's
          Fantastic Breaks protocol, and how every Juglet run here is read). The anchor
          always counts, so on a pair the contest is over ONE sherd.
  best    one rigid move fitted to all sherds at once (no sherd gets a free seat).

OUR RULER (glossary, `own_place.py`). Distances are in mm on the real 65 mm pot, and the
tolerance is the one used for every Juglet result: 7.07% of pot size, 4.6 mm, for a pair too.
  own place        the sherd's chamfer to ITS home under readout.TAU in the whole-pot unit box
  right way round  own place AND its points a median under 4.6 mm from their own home points
  turn, offset     degrees the sherd is turned from home; mm its centre is off

THE PAPER'S RULER (AssemblyWorld App. A.3). The largest part's principal-axis box diagonal is
scaled to 1; a part is correct if the squared two-way chamfer of 1,000 surface samples to its
target is at most 0.01; success means every part correct. Printed beside ours so the two can
be read against each other, never mixed.

A picture is written beside each run (`look.png`: placed sherds in colour over the answer in
grey, three views). Read it before any number from it is reported.

Usage (Spartan):
  python scripts/agent_assembly/score_tasks.py --secret ../agent_assembly/tasks_v1/secret \
      --runs ../agent_assembly/runs_v1 --out ../agent_assembly/scores_v1
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import trimesh
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prep_tasks import load_pieces  # noqa: E402

TAU = 0.01                          # readout.TAU
SEAT_PCT = 100.0 * np.sqrt(TAU / 2)  # 7.07 % of pot size


def kabsch(src, dst):
    cs, cd = src.mean(0), dst.mean(0)
    U, _, Vt = np.linalg.svd((src - cs).T @ (dst - cd))
    D = np.diag([1, 1, np.sign(np.linalg.det(Vt.T @ U.T))])
    R = Vt.T @ D @ U.T
    return R, cd - R @ cs


def angle_deg(R):
    return float(np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1))))


def chamfer(a, b):
    d1, _ = cKDTree(b).query(a)
    d2, _ = cKDTree(a).query(b)
    return float((d1 ** 2).mean() + (d2 ** 2).mean())


def sample(mesh, n, seed):
    pts, fid = trimesh.sample.sample_surface(mesh, n, seed=seed)
    return pts


def score_run(final, sec, meshes, pot_longest, mm):
    s = sec["shared_scale"]
    parts = sec["parts"]
    ids = sorted(parts)
    gt, placed, smp_gt, smp_pl = {}, {}, {}, {}
    for p in ids:
        k = parts[p]["sherd"]
        F = np.asarray(final["T"][p]) @ np.asarray(parts[p]["gt_to_scene"])
        V = np.asarray(meshes[k].vertices)
        gt[p] = V
        placed[p] = s * trimesh.transform_points(V, F)
        X = sample(meshes[k], 5000, seed=k)
        smp_gt[p] = X
        smp_pl[p] = s * trimesh.transform_points(X, F)
    anchor = max(ids, key=lambda p: meshes[parts[p]["sherd"]].area)

    # the paper's normalisation: largest part's PCA-box diagonal = 1 (task parts only)
    def pca_diag(V):
        c = V - V.mean(0)
        _, _, vt = np.linalg.svd(c, full_matrices=False)
        q = c @ vt.T
        return float(np.linalg.norm(q.max(0) - q.min(0)))
    paper_scale = max(pca_diag(gt[p]) for p in ids)

    out = {"anchor": anchor}
    for mode in ("anchor", "best"):
        if mode == "anchor":
            R, t = kabsch(placed[anchor], gt[anchor])
        else:
            R, t = kabsch(np.vstack([placed[p] for p in ids]), np.vstack([gt[p] for p in ids]))
        rows = []
        for p in ids:
            P = placed[p] @ R.T + t
            Xp = smp_pl[p] @ R.T + t
            Rk, _ = kabsch(P, gt[p])
            point_pct = 100 * float(np.median(np.linalg.norm(P - gt[p], axis=1))) / pot_longest
            cd_pot = chamfer(Xp / pot_longest, smp_gt[p] / pot_longest)
            own = cd_pot <= TAU
            sub = np.random.default_rng(0).choice(len(Xp), 1000, replace=False)
            cd_paper = chamfer(Xp[sub] / paper_scale, smp_gt[p][sub] / paper_scale)
            rows.append({
                "part": p, "sherd": parts[p]["sherd"], "anchor": p == anchor,
                "own_place": bool(own),
                "right_way_round": bool(own and point_pct <= SEAT_PCT),
                "turn_deg": round(angle_deg(Rk), 1),
                "offset_mm": round(float(np.linalg.norm(P.mean(0) - gt[p].mean(0))) * mm, 2),
                "point_mm": round(point_pct / 100 * pot_longest * mm, 2),
                "paper_correct": bool(cd_paper <= 0.01),
                "paper_cd": round(cd_paper, 5),
            })
        n = len(rows)
        out[mode] = {
            "sherds": rows, "n": n,
            "own_place": sum(r["own_place"] for r in rows),
            "right_way_round": sum(r["right_way_round"] for r in rows),
            "paper_pa": round(100 * sum(r["paper_correct"] for r in rows) / n, 1),
            "paper_success": all(r["paper_correct"] for r in rows),
        }
    return out, smp_pl, smp_gt, anchor


def look(path, placed, gt, title):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as e:
        print(f"  (no picture: {e})")
        return
    R, t = kabsch(np.vstack(list(placed.values())), np.vstack(list(gt.values())))
    cols = plt.cm.tab10(np.arange(10))
    fig = plt.figure(figsize=(15, 5))
    for v, (el, az) in enumerate([(20, -60), (20, 30), (85, -90)]):
        ax = fig.add_subplot(1, 3, v + 1, projection="3d")
        for k, p in enumerate(sorted(gt)):
            g = gt[p][::2]
            q = (placed[p] @ R.T + t)[::2]
            ax.scatter(*g.T, s=0.3, c="0.75")
            ax.scatter(*q.T, s=0.6, color=cols[k % 10], label=p)
        ax.view_init(el, az)
        ax.set_box_aspect(np.ptp(np.vstack(list(gt.values())), axis=0))
        ax.set_axis_off()
    fig.axes[0].legend(markerscale=10, fontsize=7, loc="upper left")
    fig.suptitle(title + "  (grey = conservator's reassembly; colour = agent, best overall fit)")
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--secret", required=True)
    ap.add_argument("--runs", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    cache, table = {}, []
    for fj in sorted(Path(a.runs).glob("*/final.json")):
        final = json.loads(fj.read_text())
        sec = json.loads((Path(a.secret) / f"{final['task']}.json").read_text())
        if sec["h5"] not in cache:
            _, pieces = load_pieces(sec["h5"])
            meshes = [trimesh.Trimesh(v, f, process=False) for v, f in pieces]
            allv = np.vstack([v for v, _ in pieces])
            cache[sec["h5"]] = (meshes, float((allv.max(0) - allv.min(0)).max()))
        meshes, longest = cache[sec["h5"]]
        res, placed, gt, anchor = score_run(final, sec, meshes, longest, sec["mm_per_unit"])
        run = fj.parent.name
        res["run"], res["task"] = run, final["task"]
        (out / f"{run}.json").write_text(json.dumps(res, indent=1))
        A, B = res["anchor"], res["best"]
        look(out / f"{run}_look.png", placed, gt,
             f"{run}: right way round {B['right_way_round']}/{B['n']} (best fit)")
        line = (f"{run:28s} {final['task']:12s} n={A['n']}  anchor: own {A['own_place']}/{A['n']}"
                f" rwr {A['right_way_round']}/{A['n']} paperPA {A['paper_pa']:5.1f}"
                f" SR {int(A['paper_success'])} | best: own {B['own_place']}/{B['n']}"
                f" rwr {B['right_way_round']}/{B['n']} | worst non-anchor turn "
                f"{max([r['turn_deg'] for r in A['sherds'] if not r['anchor']] or [0]):.0f} deg,"
                f" offset {max([r['offset_mm'] for r in A['sherds'] if not r['anchor']] or [0]):.1f} mm")
        print(line)
        table.append(line)
    (out / "table.txt").write_text("\n".join(table) + "\n")


if __name__ == "__main__":
    main()
