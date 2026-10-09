"""Turn a method's saved attempts into attempt bundles for the U17 ranker.

Ticket .scratch/attempt-ranker/issues/01. This is the ONLY piece of the ranker that
may read the answer key. It writes three things:

  <out>/sherds.npz         every sherd's full-detail scan in a neutral frame of its
                           own (centred, randomly turned), in mm. The scans in the
                           dataset sit in their correct assembled positions, so
                           handing them over as they are would hand over the answer.
  <out>/bundles/<id>.npz   one per attempt: R (k,3,3), t (k,3) placing each neutral
                           sherd where the attempt put it, after one random rigid
                           move of the whole attempt. <id> is opaque.
  <key>/idmap.json         <id> -> run file, attempt index. Read by the report
                           only; keep <key> outside <out>.

The attempt placement comes from the rigid "solid" cloud (generations_proposed):
each sherd there is the true sherd moved as one piece, so its move is recovered
exactly (Kabsch on the point correspondence) and applied to the full scan.

Self-check (--check N): rebuild N attempts from the bundles alone, undo the
global move, and score them with own_place.score_draw against the run's own
labels; every sherd must agree with scoring the original attempt.

Usage (from the tora repo root):
  python scripts/rank_convert.py --runs 'GLOB/clouds/0.npz' \\
      --hdf5 dataset/juglet_gt.hdf5 --object juglet_gt/Juglet-000 --pot-mm 65 \\
      --out RUN/bundles_dir --key RUN/key_dir [--check 40]
"""
import argparse
import glob
import json
import secrets
import sys
from pathlib import Path

import h5py
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from own_place import score_draw  # noqa: E402
from readout import part_slices, unit_box_scale  # noqa: E402

# rebuilt-vs-saved tolerance, % of pot size (was 0.2 mm: Juglet max 0.17%, Fractura
# blue_pot 0.32% on a nominal 100 mm pot, job 32144323; rounding, labels all agreed)
CHECK_PCT = 0.5
SHIFT_PCT = 0.5   # % of pot
CENTRE_PCT = 3.0   # sampled points vs mesh vertices shift a centre a little, not more


def kabsch(a, b):
    ca, cb = a.mean(0), b.mean(0)
    u, _, vt = np.linalg.svd((a - ca).T @ (b - cb))
    d = np.sign(np.linalg.det(vt.T @ u.T))
    r = vt.T @ np.diag([1, 1, d]) @ u.T
    return r, cb - r @ ca


def random_rotation(rng):
    q = rng.normal(size=4)
    q /= np.linalg.norm(q)
    w, x, y, z = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def load_scans(hdf5, obj):
    with h5py.File(hdf5, "r") as f:
        g = f[obj]["pieces"]
        n = len(g)
        return [(g[str(i)]["vertices"][:], g[str(i)]["faces"][:]) for i in range(n)]


def area_centre(v, f):
    """A mesh's centre weighted by surface area, as the run's evenly sampled cloud weights it.

    A plain vertex mean leans towards wherever the mesh is densest; on GARF's galli_pot
    (small base sherds) that put sherd centres 3.2% of pot off their own clouds' (job
    32331355) although the two are the same pot in the same frame.
    """
    a, b, c = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
    w = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)
    return ((a + b + c) / 3 * w[:, None]).sum(0) / w.sum()


def run_frame(gt, sl, scans, run):
    """Scale k and shift o with gt / k - o in the dataset scans' frame: (1, 0) if they agree.

    The placement is read off the run's cloud and applied to the dataset's scans, so
    the two must share units and origin. TORA's Fractura clouds are about 3.1 times the
    dataset's scale (plate: box 1.892 vs 0.605); read unscaled, every sherd kept its
    size while the moves between them grew 3.1 times, so sherds drifted apart (job
    32329999, void). A shift does the same harm whenever sherds turn by different
    amounts. A scale within 5% and a shift within SHIFT_PCT of pot are point sampling
    (cloud points vs mesh vertices), not a change of frame, and are left alone so
    GARF's bundles stay as they were. Either way each sherd's centre must then agree
    with its scan's within CENTRE_PCT of pot size.
    """
    allv = np.concatenate([v for v, _ in scans])
    size = unit_box_scale(allv)
    k = unit_box_scale(gt) / size
    if abs(k - 1) < 0.05:
        k = 1.0
    cg = np.array([gt[s:e].mean(0) for s, e in sl]) / k
    cs = np.array([area_centre(v, f) for v, f in scans])
    o = (cg - cs).mean(0)
    if 100 * np.linalg.norm(o) / size < SHIFT_PCT:
        o = np.zeros(3)
    off = 100 * np.linalg.norm(cg - o - cs, axis=1).max() / size
    if off > CENTRE_PCT:
        sys.exit(f"{run}: sherd layout differs from the scans by {off:.1f}% of pot "
                 f"after scale {k:.4f} and shift {np.round(o, 4).tolist()}; not the same "
                 f"pot, or not a uniform scale")
    if (k != 1.0 or o.any()) and run not in _SAID:
        _SAID.add(run)
        print(f"{run}: clouds are {k:.4f} x the scans' scale, shifted "
              f"{np.round(o, 4).tolist()}; undone (sherd centres agree to {off:.2f}% of pot)")
    return k, o


_SAID = set()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--runs", required=True, nargs="+", help="saved-attempt npz files or globs")
    ap.add_argument("--hdf5", required=True, type=Path)
    ap.add_argument("--object", required=True, help="object key inside the hdf5")
    ap.add_argument("--pot-mm", type=float, required=True,
                    help="pot size (longest box side) in mm; sets the unit")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--key", required=True, type=Path)
    ap.add_argument("--seed", type=int, default=17)
    ap.add_argument("--move-mm", type=float, default=100.0,
                    help="largest random shift of a whole attempt")
    ap.add_argument("--check", type=int, default=0, help="self-check N attempts")
    a = ap.parse_args()
    if a.key.resolve() in a.out.resolve().parents or a.key.resolve() == a.out.resolve():
        sys.exit("--key must be outside --out: the ranker is handed --out")

    runs = sorted({f for g in a.runs for f in glob.glob(g)})
    if not runs:
        sys.exit(f"no runs match {a.runs}")
    rng = np.random.default_rng(a.seed)
    scans = load_scans(a.hdf5, a.object)
    allv = np.concatenate([v for v, _ in scans])
    mm = a.pot_mm / unit_box_scale(allv)          # dataset unit -> mm

    # neutral frame per sherd: x_neutral = N_j (x_gt - c_j) * mm
    neutral = []
    for v, f in scans:
        c = v.mean(0)
        nrot = random_rotation(rng)
        neutral.append((c, nrot))
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "bundles").mkdir(exist_ok=True)
    a.key.mkdir(parents=True, exist_ok=True)
    sh = {}
    for j, ((v, f), (c, nrot)) in enumerate(zip(scans, neutral)):
        sh[f"v{j}"] = ((v - c) @ nrot.T * mm).astype(np.float32)
        sh[f"f{j}"] = f.astype(np.int32)
    np.savez_compressed(a.out / "sherds.npz", k=len(scans), units="mm", pot_mm=a.pot_mm, **sh)

    idmap, checks = {}, []
    for run in runs:
        d = np.load(run, allow_pickle=True)
        if "name" in d.files and str(d["name"]) != a.object:
            sys.exit(f"{run} holds {d['name']}, not {a.object}")
        sl = list(part_slices(d["points_per_part"]))
        if len(sl) != len(scans):
            sys.exit(f"{run}: {len(sl)} sherds in the attempt, {len(scans)} scans")
        k, o = run_frame(d["pts_gt"].astype(float), sl, scans, run)
        gt = d["pts_gt"].astype(float) / k - o
        for t, pred in enumerate(d["generations_proposed"].astype(float) / k - o):
            gr, gtr = random_rotation(rng), rng.uniform(-a.move_mm, a.move_mm, 3)
            R, T = [], []
            for j, (s, e) in enumerate(sl):
                r, tt = kabsch(gt[s:e], pred[s:e])          # gt frame -> attempt
                c, nrot = neutral[j]
                # x_att(mm) = gr @ (r @ (nrot.T @ x_n / mm + c) + tt) * mm + gtr
                R.append(gr @ r @ nrot.T)
                T.append(gr @ (r @ c + tt) * mm + gtr)
            aid = secrets.token_hex(8)
            np.savez(a.out / "bundles" / f"{aid}.npz", R=np.array(R, np.float32),
                     t=np.array(T, np.float32))
            idmap[aid] = {"run": str(Path(run).as_posix()), "attempt": t}
            if len(checks) < a.check:
                checks.append((aid, run, t, gr, gtr))
    (a.key / "idmap.json").write_text(json.dumps(idmap, indent=0))
    print(f"{len(idmap)} attempts from {len(runs)} runs, {len(scans)} sherds, "
          f"1 unit = {mm:.3f} mm -> {a.out}")

    bad = 0
    for aid, run, t, gr, gtr in checks:
        d = np.load(run, allow_pickle=True)
        ppp = d["points_per_part"]
        k, o = run_frame(d["pts_gt"].astype(float), list(part_slices(ppp)), scans, run)
        gt = d["pts_gt"].astype(float) / k - o
        pred = d["generations_proposed"][t].astype(float) / k - o
        b = np.load(a.out / "bundles" / f"{aid}.npz")
        rebuilt = np.empty_like(gt)
        for j, (s, e) in enumerate(part_slices(ppp)):
            c, nrot = neutral[j]
            xn = (gt[s:e] - c) @ nrot.T * mm                   # this sherd, neutral
            xa = xn @ b["R"][j].astype(float).T + b["t"][j]    # placed, moved
            rebuilt[s:e] = ((xa - gtr) @ gr) / mm              # global move undone
        resid = np.linalg.norm(rebuilt - pred, axis=1).max() * mm
        o, r_ = score_draw(gt, pred, ppp), score_draw(gt, rebuilt, ppp)
        same = o.status == r_.status and o.oriented == r_.oriented
        bad += (not same) or resid > CHECK_PCT * a.pot_mm / 100
        print(f"check {aid}: max point gap {resid:.3f} mm ({100 * resid / a.pot_mm:.2f}% of pot), own/oriented "
              f"{sum(x == 'own' for x in o.status)}/{o.oriented} -> "
              f"{sum(x == 'own' for x in r_.status)}/{r_.oriented} {'ok' if same else 'DIFFERS'}")
    if checks:
        print(f"self-check: {len(checks) - bad}/{len(checks)} agree")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
