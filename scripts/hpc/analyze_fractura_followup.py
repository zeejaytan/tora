"""Post-hoc analysis for the Fractura follow-up batch.

Reads per-sample JSONs from three runs:
- Baseline N=3, anchor-fixed (job 24342475): fractura_<subset>_24342475/results/
- Test A: N=10, anchor-fixed (current job):  fractura_<subset>_BoN10_<job>/results/
- Test C: N=3,  anchor-free  (current job):  fractura_<subset>_anchorfree_<job>/results/

For each subset and run, computes:
- mean & median rotation_error / translation_error (best-of-N)
- recall@5deg, recall@10deg, recall@1cm, recall@5cm (best-of-N)
- agreement-gate coverage and accuracy at std<0.5/1/2/5 thresholds
- BoN curve N=1..10 (only for N=10 run)

Writes a markdown report.
"""

from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from pathlib import Path
from statistics import mean, median, stdev
from typing import Dict, List

import numpy as np

SUBSETS = ["bone_syn_pig", "bone_syn_rib", "ceramics", "egg", "bones"]


def load_run(results_dir: Path) -> Dict[str, List[dict]]:
    """Group per-sample JSONs by sample name."""
    files = sorted(results_dir.glob("*.json"))
    per_sample: Dict[str, List[dict]] = defaultdict(list)
    for f in files:
        d = json.loads(f.read_text())
        per_sample[d.get("name", str(f))].append(d)
    # Sort generations within sample by generation_idx
    for k in per_sample:
        per_sample[k].sort(key=lambda x: x.get("generation_idx", 0))
    return per_sample


def best_of_n(gens: List[dict], n: int, key: str = "rotation_error") -> float:
    """Return min of `key` over the first n generations."""
    sub = gens[:n]
    return min(g[key] for g in sub)


def aggregate(per_sample: Dict[str, List[dict]], n: int) -> dict:
    """Best-of-N aggregate over a set of samples."""
    rot, trans, pa, r5d, r10d, r1cm, r5cm = [], [], [], [], [], [], []
    chamfer = []
    n_parts = []
    scales = []
    for name, gens in per_sample.items():
        idxs = list(range(min(n, len(gens))))
        # Best-of-N selection by rotation_error
        rots = [gens[i]["rotation_error"] for i in idxs]
        best_idx = idxs[int(np.argmin(rots))]
        g = gens[best_idx]
        rot.append(g["rotation_error"])
        trans.append(g["translation_error"])
        pa.append(g["part_accuracy"])
        r5d.append(g["recall_at_5deg"])
        r10d.append(g["recall_at_10deg"])
        r1cm.append(g["recall_at_1cm"])
        r5cm.append(g["recall_at_5cm"])
        chamfer.append(g.get("object_chamfer", float("nan")))
        n_parts.append(g.get("num_parts", 0))
        s = g.get("scales")
        if isinstance(s, list):
            s = float(np.mean(s))
        scales.append(float(s) if s is not None else float("nan"))
    norm_trans = [t / s if s and not np.isnan(s) and s > 0 else float("nan")
                  for t, s in zip(trans, scales)]
    return {
        "n_samples": len(per_sample),
        "rot_mean": float(np.mean(rot)),
        "rot_median": float(np.median(rot)),
        "trans_mean": float(np.mean(trans)),
        "trans_norm_mean": float(np.nanmean(norm_trans)),
        "scale_mean": float(np.nanmean(scales)),
        "part_acc": float(np.mean(pa)),
        "r@5deg": float(np.mean(r5d)),
        "r@10deg": float(np.mean(r10d)),
        "r@1cm": float(np.mean(r1cm)),
        "r@5cm": float(np.mean(r5cm)),
        "chamfer_mean": float(np.nanmean(chamfer)),
        "n_parts_mean": float(np.mean(n_parts)),
        "fail@30": float(np.mean([1.0 if r >= 30 else 0.0 for r in rot])),
        "fail@10": float(np.mean([1.0 if r >= 10 else 0.0 for r in rot])),
    }


def gate_analysis(per_sample: Dict[str, List[dict]], thresholds=(0.5, 1.0, 2.0, 5.0)) -> dict:
    """Compute std(rot_err) per sample, then accuracy at gate thresholds."""
    sample_stats = []
    for name, gens in per_sample.items():
        rots = [g["rotation_error"] for g in gens]
        if len(rots) < 2:
            continue
        std_r = float(np.std(rots, ddof=1)) if len(rots) > 1 else 0.0
        bon = float(min(rots))
        sample_stats.append((std_r, bon))
    n = len(sample_stats)
    if n == 0:
        return {"n_samples": 0, "thresholds": []}
    out = {"n_samples": n, "thresholds": []}
    for thr in thresholds:
        passed = [bon for s, bon in sample_stats if s < thr]
        cov = len(passed) / n
        if passed:
            mean_rot = float(np.mean(passed))
            fail30 = float(np.mean([1.0 if r >= 30 else 0.0 for r in passed]))
            fail10 = float(np.mean([1.0 if r >= 10 else 0.0 for r in passed]))
        else:
            mean_rot = float("nan")
            fail30 = float("nan")
            fail10 = float("nan")
        out["thresholds"].append({
            "thr_deg": thr,
            "coverage": cov,
            "mean_rot": mean_rot,
            "fail@30": fail30,
            "fail@10": fail10,
            "n_passed": len(passed),
        })
    # No-gate baseline
    all_bon = [bon for _, bon in sample_stats]
    out["no_gate"] = {
        "coverage": 1.0,
        "mean_rot": float(np.mean(all_bon)),
        "fail@30": float(np.mean([1.0 if r >= 30 else 0.0 for r in all_bon])),
        "fail@10": float(np.mean([1.0 if r >= 10 else 0.0 for r in all_bon])),
        "n_passed": n,
    }
    return out


def bon_curve(per_sample: Dict[str, List[dict]], max_n: int = 10) -> List[dict]:
    """Mean best-of-N rotation_error for N = 1..max_n."""
    out = []
    n_avail = max_n
    for n in range(1, max_n + 1):
        rots = []
        for name, gens in per_sample.items():
            if len(gens) >= n:
                rots.append(min(g["rotation_error"] for g in gens[:n]))
        if rots:
            out.append({"N": n, "mean_rot": float(np.mean(rots))})
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--baseline-job", required=True, help="job id of N=3 anchor-fixed run (24342475)")
    p.add_argument("--followup-job", required=True, help="job id of this combined A+C job")
    p.add_argument("--eval-root", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()

    eval_root = Path(args.eval_root)
    base_job = args.baseline_job
    fu_job = args.followup_job

    runs = {}  # subset -> {"baseline": agg, "bon10": agg, "anchorfree": agg, "gate_*": gate, "bon_curve": curve}
    for sub in SUBSETS:
        baseline_dir = eval_root / f"fractura_{sub}_{base_job}" / "results"
        bon10_dir    = eval_root / f"fractura_{sub}_BoN10_{fu_job}" / "results"
        af_dir       = eval_root / f"fractura_{sub}_anchorfree_{fu_job}" / "results"

        entry = {}
        if baseline_dir.exists():
            ps = load_run(baseline_dir)
            entry["baseline_n3"] = aggregate(ps, n=3)
            entry["gate_baseline_n3"] = gate_analysis(ps)
        if bon10_dir.exists():
            ps = load_run(bon10_dir)
            entry["bon10_n10"] = aggregate(ps, n=10)
            entry["bon10_n3_subset"] = aggregate(ps, n=3)  # for direct N=3 vs N=10 comparison on same job
            entry["gate_bon10_n10"] = gate_analysis(ps)
            entry["gate_bon10_n3"] = gate_analysis(
                {k: v[:3] for k, v in ps.items()}
            )
            entry["bon_curve"] = bon_curve(ps, max_n=10)
        if af_dir.exists():
            ps = load_run(af_dir)
            entry["anchorfree_n3"] = aggregate(ps, n=3)
            entry["gate_anchorfree_n3"] = gate_analysis(ps)
        runs[sub] = entry

    # ----- Render markdown -----
    lines = []
    L = lines.append
    L(f"# TORA Fractura follow-up (job {fu_job}) — A + B + C combined analysis")
    L("")
    L(f"Sources:")
    L(f"- Baseline (N=3, anchor-fixed): job {base_job}")
    L(f"- Test A (N=10, anchor-fixed): job {fu_job}, dirs `fractura_<subset>_BoN10_{fu_job}/`")
    L(f"- Test C (N=3, anchor-free):    job {fu_job}, dirs `fractura_<subset>_anchorfree_{fu_job}/`")
    L("")

    # --- Test A: BoN headline ---
    L("## Test A — Best-of-N=10 sweep")
    L("")
    L("Mean rotation_error (degrees) and normalised translation_error (trans/scale) per subset.")
    L("")
    L("| Subset | n | parts | rot N=3 (base) | rot N=3 (A run) | rot N=10 | Δ(10−3) | trans norm N=10 |")
    L("|---|---|---|---|---|---|---|---|")
    for sub in SUBSETS:
        e = runs[sub]
        if "bon10_n10" not in e:
            L(f"| {sub} | — | — | — | — | — | — | — |")
            continue
        b = e.get("baseline_n3", {})
        s3 = e.get("bon10_n3_subset", {})
        s10 = e.get("bon10_n10", {})
        rot_b = b.get("rot_mean", float("nan"))
        rot_3 = s3.get("rot_mean", float("nan"))
        rot_10 = s10.get("rot_mean", float("nan"))
        tn = s10.get("trans_norm_mean", float("nan"))
        n_p = s10.get("n_parts_mean", 0.0)
        n_s = s10.get("n_samples", 0)
        L(f"| {sub} | {n_s} | {n_p:.1f} | {rot_b:.2f} | {rot_3:.2f} | {rot_10:.2f} | {rot_10-rot_3:+.2f} | {tn:.3f} |")
    L("")
    L("`rot N=3 (base)` is the original anchor-fixed BoN=3 run from job " + base_job +
      "; `rot N=3 (A run)` is the same metric recomputed on the new BoN=10 job restricted to "
      "the first 3 generations — they should match modulo random seed.")
    L("")

    # --- BoN curves per subset ---
    L("### Best-of-N curve per subset")
    L("")
    L("| Subset | N=1 | N=3 | N=5 | N=10 | Δ(10−1) |")
    L("|---|---|---|---|---|---|")
    for sub in SUBSETS:
        curve = runs[sub].get("bon_curve", [])
        if not curve:
            L(f"| {sub} | — | — | — | — | — |")
            continue
        cmap = {x["N"]: x["mean_rot"] for x in curve}
        n1 = cmap.get(1, float("nan"))
        n3 = cmap.get(3, float("nan"))
        n5 = cmap.get(5, float("nan"))
        n10 = cmap.get(10, float("nan"))
        L(f"| {sub} | {n1:.2f} | {n3:.2f} | {n5:.2f} | {n10:.2f} | {n10 - n1:+.2f} |")
    L("")

    # --- Test B: gating ---
    L("## Test B — Agreement-gate analysis")
    L("")
    L("For each subset and run, std(rot_err) across generations is computed per sample, "
      "then samples are filtered by `std < threshold`. Reported on the *passing* subset.")
    L("")
    for sub in SUBSETS:
        e = runs[sub]
        L(f"### {sub}")
        L("")
        for label, key in [
            ("baseline (N=3, anchor-fixed)", "gate_baseline_n3"),
            ("A run (N=3 subset)",          "gate_bon10_n3"),
            ("A run (N=10)",                "gate_bon10_n10"),
            ("C run (N=3, anchor-free)",    "gate_anchorfree_n3"),
        ]:
            if key not in e:
                continue
            g = e[key]
            L(f"**{label}** (n={g['n_samples']}):")
            L("")
            L("| Gate | Coverage | n passed | Mean rot° | Fail@30 | Fail@10 |")
            L("|---|---|---|---|---|---|")
            for t in g["thresholds"]:
                L(f"| std<{t['thr_deg']:.1f}° | {t['coverage']*100:5.1f}% | {t['n_passed']:3d} | "
                  f"{t['mean_rot']:.2f} | {t['fail@30']*100:5.1f}% | {t['fail@10']*100:5.1f}% |")
            ng = g["no_gate"]
            L(f"| no gate | 100.0% | {ng['n_passed']:3d} | {ng['mean_rot']:.2f} | "
              f"{ng['fail@30']*100:5.1f}% | {ng['fail@10']*100:5.1f}% |")
            L("")
        L("")

    # --- Test C: anchor-free vs anchor-fixed ---
    L("## Test C — Anchor-free vs anchor-fixed (both BoN=3)")
    L("")
    L("| Subset | n | parts | rot anchor-fixed | rot anchor-free | Δ | trans norm fixed | trans norm free |")
    L("|---|---|---|---|---|---|---|---|")
    for sub in SUBSETS:
        e = runs[sub]
        b = e.get("baseline_n3", {})
        af = e.get("anchorfree_n3", {})
        if not b or not af:
            L(f"| {sub} | — | — | — | — | — | — | — |")
            continue
        L(f"| {sub} | {b['n_samples']} | {b['n_parts_mean']:.1f} | "
          f"{b['rot_mean']:.2f} | {af['rot_mean']:.2f} | {af['rot_mean']-b['rot_mean']:+.2f} | "
          f"{b['trans_norm_mean']:.3f} | {af['trans_norm_mean']:.3f} |")
    L("")
    L("Δ > 0 means removing the anchor advantage hurt rotation; Δ ≈ 0 means the anchor wasn't doing "
      "the heavy lifting; Δ < 0 (unexpected) would mean anchor-fixed was actually a constraint.")
    L("")

    # --- Final cross-test headline (rotation only) ---
    L("## Cross-test rotation summary")
    L("")
    L("| Subset | n | base N=3 | A N=10 | C anchor-free N=3 |")
    L("|---|---|---|---|---|")
    for sub in SUBSETS:
        e = runs[sub]
        b = e.get("baseline_n3", {})
        a10 = e.get("bon10_n10", {})
        c = e.get("anchorfree_n3", {})
        n = b.get("n_samples", a10.get("n_samples", c.get("n_samples", 0)))
        L(f"| {sub} | {n} | "
          f"{b.get('rot_mean', float('nan')):.2f} | "
          f"{a10.get('rot_mean', float('nan')):.2f} | "
          f"{c.get('rot_mean', float('nan')):.2f} |")
    L("")

    out_path = Path(args.output)
    out_path.write_text("\n".join(lines))
    print(f"Wrote analysis to {out_path}")


if __name__ == "__main__":
    main()
