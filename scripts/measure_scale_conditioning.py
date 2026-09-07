"""Measure the `scales` conditioning input the model was actually trained on.

WHY. `scales` is a real input, not bookkeeping: tora/modeling/tora.py feeds it to
the flow model at every denoising step and PointCloudEncodingManager turns it into
a sinusoidal code attached to all N points (flow_model/embedding.py:151). Three
scripts judge a run by whether its `scales` fell inside a "trained band" of
[0.375, 0.625] -- scripts/readout.py:59, scripts/check_scale_conditioning.py:45,
scripts/audit_run_provenance.py:22. That band is ARITHMETIC, not observation:
0.5 x [0.75, 1.25], where 0.5 is the MESH convention (Breaking Bad stores
max|v| = 0.5) and 0.75-1.25 is the training jitter.

But `scales` is not the mesh's max|v|. dataset.py:427 computes it as
np.max(np.abs(pts_gt)) on the SAMPLED 5000-point cloud, AFTER center_pcd (which
re-centres on the point-cloud centroid, not the mesh's origin) and _make_y_up.
Sampled points do not reach the extreme vertex, and re-centring moves the extremes
again. So the observed value and the band it is judged against may be measured on
different things, and nobody has ever measured the first one.

This script measures it. Augmentation off, jitter off, one thread, so what comes
out is the deterministic base value; the training band is then that distribution
times the jitter range the datamodule actually applies to the TRAIN split only
(datamodule.py:152 -- val, validate and test/predict all omit it).

Run on Spartan (needs the tora env, CPU only -- no model is loaded):

  python scripts/measure_scale_conditioning.py \
      --data $DATA_ROOT/everyday.hdf5 --dataset-name everyday \
      --up-axis z --split train --max-parts 64 --sample 400
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from tora.data.dataset import PointCloudDataset

# The band three scripts currently assume, derived on paper from the mesh convention.
ASSUMED_LO, ASSUMED_HI = 0.375, 0.625
JITTER = (0.75, 1.25)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--dataset-name", required=True)
    ap.add_argument("--split", default="train")
    ap.add_argument("--up-axis", default="y")
    ap.add_argument("--min-parts", type=int, default=2)
    ap.add_argument("--max-parts", type=int, default=64)
    ap.add_argument("--num-points", type=int, default=5000)
    ap.add_argument("--sample", type=int, default=400,
                    help="objects to draw (0 = every object). Sampling is uniform "
                         "without replacement over the split, seeded.")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out-json", default=None)
    a = ap.parse_args()

    ds = PointCloudDataset(
        split=a.split,
        data_path=a.data,
        dataset_name=a.dataset_name,
        up_axis=a.up_axis,
        min_parts=a.min_parts,
        max_parts=a.max_parts,
        anchor_free=False,
        num_points_to_sample=a.num_points,
        min_points_per_part=20,
        random_scale_range=None,     # measure the base value, not base x jitter
        disable_augmentation=True,   # and nothing else that moves per draw
        num_threads=1,
    )

    n_total = len(ds)
    rng = np.random.default_rng(a.seed)
    if a.sample and a.sample < n_total:
        idx = np.sort(rng.choice(n_total, size=a.sample, replace=False))
    else:
        idx = np.arange(n_total)

    print(f"{a.dataset_name} [{a.split}]: {n_total} objects, measuring {len(idx)}")

    scales, names = [], []
    for k, i in enumerate(idx):
        np.random.seed(a.seed + int(i))   # sampling of surface points is stochastic
        s = ds[int(i)]
        scales.append(float(s["scales"]))
        names.append(str(s["name"]).split("/")[-1])
        if (k + 1) % 50 == 0:
            print(f"  {k+1}/{len(idx)}", flush=True)

    v = np.asarray(scales)
    q = {p: float(np.percentile(v, p)) for p in (0, 5, 25, 50, 75, 95, 100)}

    # The band the model was actually conditioned on during training: the base
    # distribution stretched by the jitter the train dataset alone receives.
    band_lo = q[5] * JITTER[0]
    band_hi = q[95] * JITTER[1]
    hard_lo = q[0] * JITTER[0]
    hard_hi = q[100] * JITTER[1]

    print()
    print("base `scales` (no jitter, augmentation off)")
    print(f"  min    {q[0]:.4f}")
    print(f"  p5     {q[5]:.4f}")
    print(f"  median {q[50]:.4f}")
    print(f"  p95    {q[95]:.4f}")
    print(f"  max    {q[100]:.4f}")
    print(f"  mean   {v.mean():.4f}   sd {v.std(ddof=1):.4f}   n {len(v)}")
    print()
    print(f"assumed band (three scripts):        [{ASSUMED_LO:.3f}, {ASSUMED_HI:.3f}]")
    print(f"measured band, p5-p95 x jitter:      [{band_lo:.3f}, {band_hi:.3f}]")
    print(f"measured band, full range x jitter:  [{hard_lo:.3f}, {hard_hi:.3f}]")
    print()
    lo_gap = ASSUMED_LO - band_lo
    print(f"the assumed floor sits {lo_gap:+.3f} above the measured p5 floor")

    lowest = np.argsort(v)[:5]
    print("\nlowest five objects")
    for i in lowest:
        print(f"  {names[i]:28s} {v[i]:.4f}")

    if a.out_json:
        Path(a.out_json).write_text(json.dumps({
            "dataset": a.dataset_name, "split": a.split, "data": a.data,
            "n_total": int(n_total), "n_measured": int(len(v)),
            "quantiles": q, "mean": float(v.mean()), "sd": float(v.std(ddof=1)),
            "jitter": list(JITTER),
            "measured_band_p5_p95": [band_lo, band_hi],
            "measured_band_full": [hard_lo, hard_hi],
            "assumed_band": [ASSUMED_LO, ASSUMED_HI],
            "scales": {n: s for n, s in zip(names, scales)},
        }, indent=2))
        print(f"\nwrote {a.out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
