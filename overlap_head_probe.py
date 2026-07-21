"""Introspect TORA's overlap-aware encoder head: real vs. synthetic fracture surfaces.

TORA's `PointCloudEncoder` (the frozen feature extractor feeding the flow
model) carries its own per-point `overlap_head` from its pretraining stage
(`config/pretrain.yaml`, `compute_overlap_points: true`) — a binary
classifier predicting whether a point sits on a cross-part contact/fracture
surface. It is not used by the flow model at inference time, but its trained
weights persist inside the deployed checkpoint (`feature_extractor.*`), so it
can be read out directly as a diagnostic, mirroring GARF's FracSeg
introspection (Exp 10, `GARF/docs/notes/JUGLET_ROOTCAUSE_FINDINGS.md`).

This script scores the head's firing rate and AUC-vs-ground-truth-overlap on
one zero-shot data split at a time. Ground truth overlap points come from the
same distance-threshold rule the pretraining stage used
(`PointCloudEncoder._compute_overlap_points`), applied to `pointclouds_gt`.

Lives at the repo root (like `sample.py`/`train.py`) so `import tora` resolves
— Python puts the invoking script's own directory on `sys.path`, not the cwd.

Usage (mirrors sample.py's Hydra CLI):
  python overlap_head_probe.py \\
    ckpt_path=.../bbad_everyday_cka.ckpt \\
    data_root=../dataset \\
    data=zeroshot/fractura/bones
"""

import logging
import warnings

import hydra
import lightning as L
import torch
from omegaconf import DictConfig

from tora.utils import load_checkpoint_for_module

logger = logging.getLogger("OverlapProbe")
warnings.filterwarnings("ignore", module="lightning")
warnings.filterwarnings("ignore", category=FutureWarning)


def _move_to_device(batch: dict, device: torch.device) -> dict:
    return {k: (v.to(device) if torch.is_tensor(v) else v) for k, v in batch.items()}


def _roc_auc(mask: torch.Tensor, prob: torch.Tensor) -> float:
    """Rank-based AUC without sklearn (avoids adding a new dependency)."""
    pos = prob[mask == 1]
    neg = prob[mask == 0]
    if pos.numel() == 0 or neg.numel() == 0:
        return float("nan")
    # Mann-Whitney U statistic via rank sum.
    combined = torch.cat([pos, neg])
    order = combined.argsort()
    ranks = torch.empty_like(order, dtype=torch.float64)
    ranks[order] = torch.arange(1, combined.numel() + 1, dtype=torch.float64)
    rank_sum_pos = ranks[: pos.numel()].sum()
    n_pos, n_neg = pos.numel(), neg.numel()
    auc = (rank_sum_pos - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)
    return auc.item()


@hydra.main(version_base="1.3", config_path="./config", config_name="sample")
def main(cfg: DictConfig):
    ckpt_path = cfg.get("ckpt_path")
    seed = cfg.get("seed", 42)
    L.seed_everything(seed, workers=True, verbose=False)

    datamodule = hydra.utils.instantiate(cfg.data)
    model = hydra.utils.instantiate(cfg.model)
    load_checkpoint_for_module(model, ckpt_path)
    model.eval()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)

    encoder = model.feature_extractor
    encoder.compute_overlap_points = True
    encoder.build_overlap_head = True
    encoder = encoder.to(device)
    encoder.eval()

    datamodule.setup("test")
    dataloaders = datamodule.test_dataloader()

    all_probs, all_masks = [], []
    n_objects = 0
    with torch.inference_mode():
        for dl in dataloaders:
            for batch in dl:
                batch = _move_to_device(batch, device)
                with torch.autocast(device_type=device.type, enabled=False):
                    out = encoder(batch)
                all_probs.append(out["overlap_prob"].detach().float().cpu())
                all_masks.append(out["overlap_mask"].detach().float().cpu())
                n_objects += batch["points_per_part"].shape[0]

    probs = torch.cat(all_probs)
    masks = torch.cat(all_masks)
    fired_pct = (probs > 0.5).float().mean().item() * 100
    true_overlap_pct = masks.mean().item() * 100
    auc = _roc_auc(masks, probs)

    dataset_names = ",".join(datamodule.dataset_names)
    print(f"\n=== Overlap-head probe: {dataset_names} ===")
    print(f"  n_objects: {n_objects}")
    print(f"  n_points scored: {probs.numel()}")
    print(f"  true overlap-point rate (GT, distance threshold): {true_overlap_pct:.3f}%")
    print(f"  fired rate (pred overlap_prob > 0.5): {fired_pct:.3f}%")
    print(f"  AUC (pred vs GT overlap mask): {auc:.4f}")
    print("=== end probe ===\n")


if __name__ == "__main__":
    main()
