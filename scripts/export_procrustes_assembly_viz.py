#!/usr/bin/env python3
"""Export TORA Procrustes assembly proposal PNGs (paper-faithful visual QA).

At inference, TORA fits per-part SE(3) from scattered input ``pointclouds`` (P_k)
to the flow endpoint ``x_hat`` via SVD (arXiv:2604.04050v1, Eq. 2). Default eval
PNGs plot only the flow endpoint (*_generation*.png). This wrapper re-runs
``sample.py`` with ``save_procrustes_assembly=true``, which saves
``*_proposed_assembly*.png``: the scattered input after those rigid transforms.

Example (Juglet deploy):

  cd /data/gpfs/projects/punim2657/TORA/repo
  python scripts/export_procrustes_assembly_viz.py \\
    --ckpt ../checkpoints/bbad_everyday_cka.ckpt \\
    --data-root ../dataset \\
    --log-dir ../eval_runs/juglet_procrustes_viz
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


REPO_DIR = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ckpt",
        required=True,
        help="Path to TORA checkpoint (.ckpt)",
    )
    parser.add_argument(
        "--data-root",
        required=True,
        help="TORA dataset root (HDF5 shards)",
    )
    parser.add_argument(
        "--log-dir",
        required=True,
        help="Output directory (visualizations/ and results/ created under it)",
    )
    parser.add_argument(
        "--data",
        default="zeroshot/juglet_deploy",
        help="Hydra data config name (default: zeroshot/juglet_deploy)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1,
    )
    parser.add_argument(
        "--num-workers",
        type=int,
        default=4,
    )
    parser.add_argument(
        "--image-size",
        type=int,
        default=512,
    )
    args = parser.parse_args()

    cmd = [
        sys.executable,
        "sample.py",
        f"ckpt_path={args.ckpt}",
        f"data_root={args.data_root}",
        f"data={args.data}",
        f"data.batch_size={args.batch_size}",
        f"data.num_workers={args.num_workers}",
        f"log_dir={args.log_dir}",
        "+visualizer._target_=tora.visualizer.FlowVisualizationCallback",
        "+visualizer.renderer=mitsuba",
        f"+visualizer.image_size={args.image_size}",
        "+visualizer.max_samples_per_batch=1",
        "+visualizer.center_points=true",
        "+visualizer.save_trajectory=false",
        "+visualizer.save_procrustes_assembly=true",
    ]

    print("Running:", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=REPO_DIR, check=True)
    viz_dir = Path(args.log_dir) / "visualizations"
    print(f"\nDone. Procrustes proposal PNGs: {viz_dir}/")
    print("  Compare *_proposed_assembly*.png vs *_input.png and *_generation*.png")


if __name__ == "__main__":
    main()
