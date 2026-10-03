"""Join Layer 2 (break-gap) scores to the answer key, with synthetic spins and controls.

Ticket .scratch/attempt-ranker/issues/02; read-outs and decision rule are fixed in
.scratch/attempt-ranker/preregistration-l2.md, whose commit this prints. Key side: reads
the run files (labels), the dataset (true assembly) and the id map.

  read-out 1  AUC, wrongly turned vs right-way sherd gaps, 19 real near-misses
  read-out 2  AUC, spun vs unspun sherd gaps, 18 synthetic spins of the 2 genuine
  read-out 3  least-sure sherd is a wrongly turned one, of 19
  read-out 4  worst-sherd gap: genuine vs near-misses; A worse than B
  read-out 5  ranks of the genuine, Layer 1 alone vs Layers 1+2
  controls    spins on the true assembly (AUC >= 0.9), 1-3 mm moves forgiven

Usage: python scripts/l2_report.py --bundles B --l2 juglet_l2.json --ranks ranks.json \\
    --key idmap.json --report report.json --hdf5 X --object O \\
    --prereg .scratch/attempt-ranker/preregistration-l2.md --out l2_report.json
"""
import argparse
import json
import sys
import tempfile
from math import comb
from pathlib import Path

import h5py
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import l2_measure as L  # noqa: E402
from own_place import SEAT_PCT, score_draw  # noqa: E402
from rank_convert import kabsch  # noqa: E402
from rank_report import prereg_commit  # noqa: E402
from readout import unit_box_scale  # noqa: E402

A_RUN, A_T = "rwlora_eval_worn_d400_ds1_juglet_gt_31835636", 19     # garf_juglet_spun_t06
B_RUN, B_T = "rwlora_eval_noise_d100_ds1_juglet_gt_31835635", 19    # garf_juglet_genuine_t06
SHIFT_MM = (1.0, 3.0)
SHIFT_DRAWS = 5


def gaps(row):
    return [np.inf if s["gap"] is None else s["gap"] for s in row["sherds"]]


def auc(pos, neg):
    """Chance a 'pos' value is larger than a 'neg' one (ties count half)."""
    pos, neg = np.asarray(pos, float), np.asarray(neg, float)
    if not len(pos) or not len(neg):
        return float("nan")
    gt = (pos[:, None] > neg[None, :]).mean()
    eq = (pos[:, None] == neg[None, :]).mean()
    return float(gt + 0.5 * eq)


def short(run):
    p = Path(run).parts
    return p[-4] if len(p) >= 4 else run


class Bench:
    """Measures hand-made bundles with l2_measure, sherds as in the real bundles."""

    def __init__(self, bundles: Path, pot_mm):
        L._init(str(bundles), pot_mm)
        z = np.load(bundles / "sherds.npz")
        self.v = [z[f"v{j}"].astype(float) for j in range(int(z["k"]))]
        self.tmp = Path(tempfile.mkdtemp())
        self.n = 0

    def measure(self, R, t):
        self.n += 1
        p = self.tmp / f"x{self.n}.npz"
        np.savez(p, R=np.asarray(R, np.float32), t=np.asarray(t, np.float32))
        return gaps(L.measure(p))

    def spin(self, R, t, j):
        """Sherd j turned 180 deg about its own wall direction through its centre."""
        R, t = np.array(R, float), np.array(t, float)
        x = self.v[j] @ R[j].T + t[j]
        c = x.mean(0)
        w = np.linalg.svd(x - c, full_matrices=False)[2][2]
        S = 2 * np.outer(w, w) - np.eye(3)
        R[j], t[j] = S @ R[j], S @ (t[j] - c) + c
        return R, t

    def shift(self, R, t, rng):
        t = np.array(t, float)
        d = rng.normal(size=t.shape)
        d /= np.linalg.norm(d, axis=1, keepdims=True)
        return R, t + d * rng.uniform(*SHIFT_MM, size=(len(t), 1))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    for k in ("bundles", "l2", "ranks", "key", "report", "hdf5", "prereg", "out"):
        ap.add_argument(f"--{k}", required=True, type=Path)
    ap.add_argument("--object", required=True)
    ap.add_argument("--pot-mm", type=float, default=None, help="if sherds.npz has no pot_mm")
    a = ap.parse_args()
    commit = prereg_commit(a.prereg)

    l2 = {r["id"]: r for r in json.loads(a.l2.read_text())["attempts"]}
    rk = {r["id"]: r for r in json.loads(a.ranks.read_text())["attempts"]}
    idmap = json.loads(a.key.read_text())
    rep = json.loads(a.report.read_text())
    if set(l2) != set(rk):
        sys.exit("Layer 2 scores and Layer 1 ranks cover different attempts")
    where = {(short(v["run"]), v["attempt"]): (aid, v["run"]) for aid, v in idmap.items()}

    def wrong_sherds(run, t):
        d = np.load(run, allow_pickle=True)
        dr = score_draw(d["pts_gt"].astype(float), d["generations_proposed"][t].astype(float),
                        d["points_per_part"])
        return [j for j, pp in enumerate(dr.point_pct) if pp >= SEAT_PCT]

    gen = [where[(g["run"], g["attempt"])] for g in rep["genuine"]]
    near = [where[(r["run"], r["attempt"])] for r in rep["near_miss"]]
    if len(gen) != 2 or len(near) != 19:
        sys.exit(f"labels changed: {len(gen)} genuine, {len(near)} near-miss")

    # read-outs 1 and 3: real near-misses
    bad, good, named, per_near = [], [], 0, []
    for aid, run in near:
        g = gaps(l2[aid])
        w = wrong_sherds(run, idmap[aid]["attempt"])
        bad += [g[j] for j in w]
        good += [g[j] for j in range(len(g)) if j not in w]
        least = int(np.argmax(g))
        named += least in w
        per_near.append(dict(run=short(run), attempt=idmap[aid]["attempt"], wrong=w,
                             gaps=[round(x, 2) if np.isfinite(x) else None for x in g],
                             least_sure=least, worst=max(g)))
    chance3 = float(np.mean([len(p["wrong"]) / len(p["gaps"]) for p in per_near]))

    # read-out 2: synthetic spins of the genuine; small-move control on the genuine
    B = Bench(a.bundles, a.pot_mm)
    rng = np.random.default_rng(29)
    spun_g, unspun_g, syn_worst, gen_shift = [], [], [], []
    for aid, _ in gen:
        b = np.load(a.bundles / "bundles" / f"{aid}.npz")
        for j in range(len(B.v)):
            g = B.measure(*B.spin(b["R"], b["t"], j))
            spun_g.append(g[j])
            unspun_g += [x for k, x in enumerate(g) if k != j]
            syn_worst.append(max(g))
        for _ in range(SHIFT_DRAWS):
            gen_shift.append(max(B.measure(*B.shift(b["R"], b["t"], rng))))

    # controls on the true assembly
    with h5py.File(a.hdf5, "r") as f:
        grp = f[a.object]["pieces"]
        vgt = [grp[str(i)]["vertices"][:].astype(float) for i in range(len(grp))]
    pot = L._S[0]
    mm = pot / unit_box_scale(np.concatenate(vgt))
    TR, TT, fit = [], [], 0.0
    for vn, vg in zip(B.v, vgt):
        r, t = kabsch(vn, vg * mm)
        fit = max(fit, float(np.linalg.norm(vn @ r.T + t - vg * mm, axis=1).max()))
        TR.append(r), TT.append(t)
    if fit > 0.01 * pot:
        sys.exit(f"true assembly rebuilt badly: {fit:.3f} mm")
    truth = B.measure(TR, TT)
    t_spun, t_unspun, t_spin_worst = [], [], []
    for j in range(len(B.v)):
        g = B.measure(*B.spin(TR, TT, j))
        t_spun.append(g[j])
        t_unspun += [x for k, x in enumerate(g) if k != j]
        t_spin_worst.append(max(g))
    t_shift = [max(B.measure(*B.shift(TR, TT, rng))) for _ in range(SHIFT_DRAWS)]

    # read-out 5: ranks
    worst = {aid: max(gaps(r)) for aid, r in l2.items()}
    order = sorted(rk, key=lambda i: (not rk[i]["layer1_pass"], worst[i], rk[i]["profile_mm"]))
    rank12 = {aid: n + 1 for n, aid in enumerate(order)}
    n = len(order)
    a_id, b_id = where[(A_RUN, A_T)][0], where[(B_RUN, B_T)][0]

    fin = lambda x: round(float(x), 3) if np.isfinite(x) else None
    q = lambda x: [fin(v) for v in np.percentile(np.asarray(x, float), [25, 50, 75])]
    out = dict(
        prereg_commit=commit, pot_mm=pot, units="percent of pot size",
        readout1_auc_real=round(auc(bad, good), 3), readout1_n=[len(bad), len(good)],
        readout1_wrong_q=q(bad), readout1_right_q=q(good),
        readout2_auc_synthetic=round(auc(spun_g, unspun_g), 3),
        readout2_spun_q=q(spun_g), readout2_unspun_q=q(unspun_g),
        readout3_named=named, readout3_of=len(near), readout3_chance=round(chance3, 3),
        readout4=dict(genuine_worst=[fin(worst[i]) for i, _ in gen],
                      real_near_worst_q=q([worst[i] for i, _ in near]),
                      synthetic_near_worst_q=q(syn_worst),
                      A_worst=fin(worst[a_id]), B_worst=fin(worst[b_id]),
                      A_below_B=bool(worst[a_id] > worst[b_id] or rank12[a_id] > rank12[b_id])),
        readout5=dict(genuine=[dict(run=short(r), attempt=idmap[i]["attempt"],
                                    layer1=rk[i]["rank"], layers12=rank12[i]) for i, r in gen],
                      top5_layer1=any(rk[i]["rank"] <= 5 for i, _ in gen),
                      top5_layers12=any(rank12[i] <= 5 for i, _ in gen),
                      random_top5=round(1 - comb(n - 2, 5) / comb(n, 5), 4),
                      near_above_best_genuine_12=sum(rank12[i] < min(rank12[g] for g, _ in gen)
                                                     for i, _ in near)),
        control_truth=dict(gaps=[fin(x) for x in truth], worst=fin(max(truth)),
                           spin_auc=round(auc(t_spun, t_unspun), 3),
                           spun=[fin(x) for x in t_spun], spin_worst_q=q(t_spin_worst),
                           shift_worst=[fin(x) for x in t_shift], rebuild_mm=round(fit, 4)),
        control_genuine_shift_worst=[fin(x) for x in gen_shift],
        near_misses=[{**p, "worst": fin(p["worst"]), "rank12": rank12[i], "rank1": rk[i]["rank"]}
                     for p, (i, _) in zip(per_near, near)])
    a.out.write_text(json.dumps(out, indent=1))

    c = out["control_truth"]
    med_spin = np.median(t_spin_worst)
    print(f"pre-registration {commit}; Juglet, gaps in % of pot (1% = {pot / 100:.2f} mm)")
    print(f"CONTROL spins on true assembly: AUC {c['spin_auc']} (need >= 0.9); true sherds "
          f"worst {c['worst']}, spun sherds {c['spun']}")
    print(f"CONTROL 1-3 mm moves: truth worst {c['shift_worst']}, genuine worst "
          f"{out['control_genuine_shift_worst']}; must stay below {med_spin:.2f}")
    print(f"1  real near-misses: AUC {out['readout1_auc_real']} ({len(bad)} wrong vs "
          f"{len(good)} right-way sherds; q25/50/75 {q(bad)} vs {q(good)})")
    print(f"2  synthetic spins:  AUC {out['readout2_auc_synthetic']} (spun {q(spun_g)} vs "
          f"unspun {q(unspun_g)})")
    print(f"3  least-sure sherd is a wrong one: {named} of {len(near)} (chance {chance3 * len(near):.1f})")
    r4 = out["readout4"]
    print(f"4  worst gap: genuine {r4['genuine_worst']}; real near q {r4['real_near_worst_q']}; "
          f"synthetic q {r4['synthetic_near_worst_q']}; A {r4['A_worst']} vs B {r4['B_worst']}"
          f" -> A below B: {r4['A_below_B']}")
    for g in out["readout5"]["genuine"]:
        print(f"5  genuine {g['run']} #{g['attempt']}: rank {g['layer1']} (Layer 1) -> "
              f"{g['layers12']} (Layers 1+2) of {n}")
    r5 = out["readout5"]
    print(f"   top 5: Layer 1 {r5['top5_layer1']}, Layers 1+2 {r5['top5_layers12']} "
          f"(random {100 * r5['random_top5']:.2f}%); near-misses above best genuine "
          f"{r5['near_above_best_genuine_12']} of 19")
    earns = out["readout1_auc_real"] >= 0.75 and any(g["layers12"] < g["layer1"]
                                                     for g in r5["genuine"])
    print(f"decision rule: Layer 2 {'EARNS' if earns else 'does NOT earn'} its place on the "
          f"Juglet -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
