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

REWIRED 2026-09-05. Every number here now comes from scripts/readout.py, the one
place a run is read. WHAT MOVED:

  every rotation figure in this report GREW. The stored `rotation_error` is
  summed over the non-anchor fragments and divided by ALL of them, so the free
  anchor is a zero in the average. The correction is n/(n-1), and n differs by
  subset here -- the ceramics, the egg and the two bone sets do not have the
  same piece count -- so this report's whole point, comparing subsets side by
  side, was distorted by a DIFFERENT factor in every row. Small-k subsets moved
  most.

  the translation column changed denominator. It was trans/scale, the object's
  own stored scale. It is now `gap_object_fraction`, which names what it divided
  by, because a run scored after the unit-box fix already stores a fraction and
  dividing it again would be wrong.

  recall@5deg / recall@10deg are RENAMED, not recomputed. They were never a
  fraction of fragments. `Evaluator._recall_at_thresholds` thresholds a
  per-OBJECT mean, so each is 0 or 1 for a whole object on one draw. They print
  as `pot<5d` / `pot<10d`: the share of attempts in which the WHOLE object
  averaged under the threshold.

Reconciliation: docs/notes/READOUT_RECONCILIATION.md.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean, median, stdev
from typing import Dict, List

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from readout import format_flags, read_run, weight  # noqa: E402

SUBSETS = ["bone_syn_pig", "bone_syn_rib", "ceramics", "egg", "bones"]


def load_run(results_dir: Path):
    """Every draw of one run, grouped by sample, read through the module.

    Accepts either a run directory or its results/ subdirectory, because every
    call site in this file passes the latter.
    """
    run_dir = Path(results_dir)
    if run_dir.name == "results":
        run_dir = run_dir.parent
    per_sample = defaultdict(list)
    for rec in read_run(run_dir):
        per_sample[rec.object_name].append(rec)
    for k in per_sample:
        per_sample[k].sort(key=lambda r: r.draw)
    return per_sample


def best_of_n(gens, n: int) -> float:
    """Lowest turn in degrees over the first n draws.

    Best-of-N reports only the best draw of N; the average over draws is the
    honest number. It is here because this batch was designed around a BoN
    curve, and it is labelled as such everywhere it is printed.
    """
    return min(r.turn_deg for r in gens[:n])


def aggregate(per_sample, n: int) -> dict:
    """Best-of-N aggregate over a set of samples, via the module."""
    rot, gap, pa, pot5, pot10, r1cm, r5cm = [], [], [], [], [], [], []
    chamfer, n_parts, scales = [], [], []
    seated, free, earned = [], [], []
    denoms = set()
    for name, gens in per_sample.items():
        picks = gens[:n]
        if not picks:
            continue
        # best-of-N selection on the CORRECTED turn, not the diluted one
        g = min(picks, key=lambda r: r.turn_deg)
        rot.append(g.turn_deg)
        gap.append(g.gap_object_fraction)
        denoms.add(g.gap_denominator)
        pa.append(g.seated_fraction)
        seated.append(float(g.seated))
        free.append(float(g.floor))
        earned.append(max(0.0, g.seated - g.floor) / g.placed
                      if g.placed else float("nan"))
        # per-OBJECT 0/1, so the mean over samples is a share of OBJECTS
        pot5.append(g.pot_under(5))
        pot10.append(g.pot_under(10))
        r1cm.append(g.raw.get("recall_at_1cm", float("nan")))
        r5cm.append(g.raw.get("recall_at_5cm", float("nan")))
        chamfer.append(g.raw.get("object_chamfer", float("nan")))
        n_parts.append(g.n_fragments)
        scales.append(g.model_scale)
    return {
        "n_samples": len(per_sample),
        "rot_mean": float(np.mean(rot)),
        "rot_median": float(np.median(rot)),
        "gap_mean": float(np.nanmean(gap)),
        "trans_norm_mean": float(np.nanmean(gap)),
        "gap_denominators": ", ".join(sorted(denoms)) or "unknown",
        "scale_mean": float(np.nanmean(scales)),
        "part_acc": float(np.mean(pa)),
        "seated_mean": float(np.mean(seated)),
        "free_mean": float(np.mean(free)),
        "earned_mean": float(np.nanmean(earned)),
        "pot<5d": float(np.nanmean(pot5)),
        "pot<10d": float(np.nanmean(pot10)),
        "r@1cm": float(np.nanmean(r1cm)),
        "r@5cm": float(np.nanmean(r5cm)),
        "chamfer_mean": float(np.nanmean(chamfer)),
        "n_parts_mean": float(np.mean(n_parts)),
        "fail@30": float(np.mean([1.0 if r >= 30 else 0.0 for r in rot])),
        "fail@10": float(np.mean([1.0 if r >= 10 else 0.0 for r in rot])),
    }


def gate_analysis(per_sample, thresholds=(0.5, 1.0, 2.0, 5.0)) -> dict:
    """Spread of the turn across draws per sample, then accuracy at gate thresholds.

    Both the spread and the gate move with the correction: a std computed on the
    diluted turn was itself diluted by the same n/(n-1), so a "std < 1 degree"
    gate was a stricter gate than it read as.
    """
    sample_stats = []
    for name, gens in per_sample.items():
        rots = [r.turn_deg for r in gens]
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


def bon_curve(per_sample, max_n: int = 10) -> List[dict]:
    """Mean best-of-N turn in degrees for N = 1..max_n."""
    out = []
    n_avail = max_n
    for n in range(1, max_n + 1):
        rots = []
        for name, gens in per_sample.items():
            if len(gens) >= n:
                rots.append(min(r.turn_deg for r in gens[:n]))
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
    pooled = []    # every record read, for the health flags and the weight line
    seen_dirs = []  # every run directory found, for the render commands
    for sub in SUBSETS:
        baseline_dir = eval_root / f"fractura_{sub}_{base_job}" / "results"
        bon10_dir    = eval_root / f"fractura_{sub}_BoN10_{fu_job}" / "results"
        af_dir       = eval_root / f"fractura_{sub}_anchorfree_{fu_job}" / "results"

        entry = {}
        if baseline_dir.exists():
            ps = load_run(baseline_dir)
            pooled.extend(r for v in ps.values() for r in v)
            seen_dirs.append(baseline_dir.parent)
            entry["baseline_n3"] = aggregate(ps, n=3)
            entry["gate_baseline_n3"] = gate_analysis(ps)
        if bon10_dir.exists():
            ps = load_run(bon10_dir)
            pooled.extend(r for v in ps.values() for r in v)
            seen_dirs.append(bon10_dir.parent)
            entry["bon10_n10"] = aggregate(ps, n=10)
            entry["bon10_n3_subset"] = aggregate(ps, n=3)  # for direct N=3 vs N=10 comparison on same job
            entry["gate_bon10_n10"] = gate_analysis(ps)
            entry["gate_bon10_n3"] = gate_analysis(
                {k: v[:3] for k, v in ps.items()}
            )
            entry["bon_curve"] = bon_curve(ps, max_n=10)
        if af_dir.exists():
            ps = load_run(af_dir)
            pooled.extend(r for v in ps.values() for r in v)
            seen_dirs.append(af_dir.parent)
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
    L("Mean turn in degrees on the fragments the model had to place, and the")
    L("offset as a fraction of the object, per subset. Both come from")
    L("`scripts/readout.py`; the turn is corrected for the free anchor, so it is")
    L("larger than the `rotation_error` stored in the result files.")
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

    # --- health of the runs this report was built from ---
    L("## How much weight this report can bear")
    L("")
    L(f"{weight(pooled)}.")
    L("")
    flags = format_flags(pooled)
    if flags:
        L("Health warnings across every run read:")
        L("")
        for line in flags:
            L(f"- **{line}**")
        L("")
    denoms = sorted({e[k].get("gap_denominators", "unknown")
                     for e in runs.values() for k in e
                     if isinstance(e[k], dict) and "gap_denominators" in e[k]})
    L(f"Offset is a fraction of the object; denominator: {', '.join(denoms) or 'unknown'}.")
    L("")
    L("A turn in degrees is an index to a picture. Draw the reassemblies before")
    L("quoting any row above:")
    L("")
    L("```bash")
    for d in seen_dirs:
        L('python scripts/render_assembly_grid.py '
          f'--runs "{d.name}={d.as_posix()}/clouds" '
          f'--out artifacts/{d.name}.png')
    L("```")
    L("")

    out_path = Path(args.output)
    out_path.write_text("\n".join(lines))
    print(f"Wrote analysis to {out_path}")


if __name__ == "__main__":
    main()
