"""Break gap of the TRUE assembly, measured exactly as l2_measure.py measures attempts.

Answer-key side (reads the dataset hdf5): the floor a correct join reaches with this ruler
(resampling spacing, break finder). In percent of pot size, so no real size is needed.

Usage: python scripts/l2_truth.py --hdf5 dataset/x.hdf5 --object grp/obj [...] --out truth.json
"""
import argparse
import json
import sys
from pathlib import Path

import h5py
import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import l2_measure as L  # noqa: E402
from readout import unit_box_scale  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--hdf5", required=True, type=Path)
    ap.add_argument("--object", required=True, nargs="+")
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    out = {}
    with h5py.File(a.hdf5, "r") as f:
        for obj in a.object:
            g = f[obj]["pieces"]
            scans = [(g[str(i)]["vertices"][:], g[str(i)]["faces"][:]) for i in range(len(g))]
            box = unit_box_scale(np.concatenate([v for v, _ in scans]))
            rng = np.random.default_rng(L.SEED)
            sh = [L.prep_sherd(v * 100.0 / box, fc, 100.0, rng) for v, fc in scans]
            rows = []
            for j, s in enumerate(sh):
                Q = np.concatenate([x["p"] for k, x in enumerate(sh) if k != j])
                gp, cl, n = L.gap(s["p"], cKDTree(Q))
                rows.append(dict(gap=gp, close=cl, contact=n, wall_pct=round(s["thick"], 3)))
            out[obj] = rows
            g_ = [r["gap"] for r in rows if r["gap"] is not None]
            print(f"{obj}: {len(sh)} sherds, true gap % of pot median {np.median(g_):.2f} "
                  f"(range {min(g_):.2f}-{max(g_):.2f}), wall {np.median([s['thick'] for s in sh]):.2f}%")
    a.out.write_text(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
