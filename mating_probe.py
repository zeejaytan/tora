"""C2 — paper-faithful mating linear probe on TORA's ON-PATH features.

Replaces the dead `overlap_head` readout (`overlap_head_probe.py`). Confirmed
against the TORA paper (arXiv 2604.04050v1): the overlap/mating prediction is a
**linear probe of teacher-feature quality** (App. 0.A.1) — *"This probe evaluates
whether the teacher features encode contact-aware geometry and part-to-part
interaction cues. A point is labeled as mating (positive) if it has at least one
neighbor from a different part within an adaptive overlap threshold."* — and NOT
a module in the assembly pipeline. The pipeline uses only the frozen encoder's
per-point conditioning features **c** (`_encode()` -> `out_dict["point"]`).

So this script applies the paper's own methodology to the features TORA actually
conditions on: fit a linear probe c -> P(mating) and report AUC. High AUC means
the conditioning features encode contact geometry; a collapse on worn rims would
be TORA's analogue of GARF's Exp-10 fracture-response blindness (H3).

Arms (run one dataset per invocation, like overlap_head_probe.py):
  synthetic fresh breaks  -- INSTRUMENT VALIDATION, must reach AUC >= 0.75
  fresh real ceramics     -- real, un-worn
  juglet_norm             -- real, worn (the object under test)

IMPORTANT — use SCALE-NORMALIZED splits (juglet_norm, real_heldout_norm,
pairs_real_norm). The mating label uses an adaptive distance threshold; on raw
scan-unit data it degenerates (the old probe saw ~100% "true overlap", making
AUC undefined). This script therefore REFUSES to report AUC when the label rate
is degenerate, rather than emitting a meaningless number.

Usage (mirrors sample.py's Hydra CLI):
  python mating_probe.py ckpt_path=.../bbad_everyday_cka.ckpt \
      data_root=.../dataset data=zeroshot/juglet_norm
"""

import logging
import warnings

import hydra
import lightning as L
import torch
from omegaconf import DictConfig

from tora.utils import load_checkpoint_for_module

logger = logging.getLogger("MatingProbe")
warnings.filterwarnings("ignore", module="lightning")
warnings.filterwarnings("ignore", category=FutureWarning)

# Label rates outside this band mean the adaptive threshold has degenerated
# (all-positive / all-negative); AUC would be undefined or meaningless.
MIN_RATE, MAX_RATE = 0.005, 0.95
VALIDATION_GATE = 0.75  # required AUC on the labeled synthetic arm


def _move(batch: dict, device: torch.device) -> dict:
    return {k: (v.to(device) if torch.is_tensor(v) else v) for k, v in batch.items()}


def _roc_auc(y: torch.Tensor, s: torch.Tensor) -> float:
    """Rank-based AUC (Mann-Whitney U), no sklearn dependency."""
    pos, neg = s[y == 1], s[y == 0]
    if pos.numel() == 0 or neg.numel() == 0:
        return float("nan")
    comb = torch.cat([pos, neg])
    order = comb.argsort()
    ranks = torch.empty_like(order, dtype=torch.float64)
    ranks[order] = torch.arange(1, comb.numel() + 1, dtype=torch.float64, device=comb.device)
    n_p, n_n = pos.numel(), neg.numel()
    return ((ranks[:n_p].sum() - n_p * (n_p + 1) / 2) / (n_p * n_n)).item()


def _fit_linear_probe(x: torch.Tensor, y: torch.Tensor, steps: int = 400, lr: float = 0.05):
    """Balanced logistic regression; returns held-out AUC."""
    g = torch.Generator().manual_seed(0)
    perm = torch.randperm(x.shape[0], generator=g)
    x, y = x[perm], y[perm]
    n_tr = int(0.7 * x.shape[0])
    xtr, ytr, xte, yte = x[:n_tr], y[:n_tr], x[n_tr:], y[n_tr:]

    mu, sd = xtr.mean(0, keepdim=True), xtr.std(0, keepdim=True) + 1e-6
    xtr, xte = (xtr - mu) / sd, (xte - mu) / sd

    w = torch.zeros(x.shape[1], 1, requires_grad=True)
    b = torch.zeros(1, requires_grad=True)
    opt = torch.optim.Adam([w, b], lr=lr)
    # class-balanced positive weight so a rare mating class isn't ignored
    pw = torch.tensor([(ytr == 0).sum().clamp(min=1).float() / (ytr == 1).sum().clamp(min=1).float()])
    for _ in range(steps):
        opt.zero_grad()
        loss = torch.nn.functional.binary_cross_entropy_with_logits(
            xtr @ w + b, ytr.unsqueeze(1).float(), pos_weight=pw)
        loss.backward()
        opt.step()
    with torch.no_grad():
        return _roc_auc(yte, (xte @ w + b).squeeze(1)), float(loss.item())


@hydra.main(version_base="1.3", config_path="./config", config_name="sample")
def main(cfg: DictConfig):
    L.seed_everything(cfg.get("seed", 42), workers=True, verbose=False)
    max_points = int(cfg.get("probe_max_points", 300_000))

    datamodule = hydra.utils.instantiate(cfg.data)
    model = hydra.utils.instantiate(cfg.model)
    load_checkpoint_for_module(model, cfg.get("ckpt_path"))
    model.eval()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)

    encoder = model.feature_extractor.to(device).eval()
    datamodule.setup("test")

    feats, labels = [], []
    n_obj = 0
    with torch.inference_mode():
        for dl in datamodule.test_dataloader():
            for batch in dl:
                batch = _move(batch, device)
                with torch.autocast(device_type=device.type, enabled=False):
                    out = encoder(batch)
                # On-path conditioning features c (what the flow DiT consumes)
                point = out["point"]
                f = point["feat"].detach().float()
                # Paper's mating label: >=1 neighbour from a different part
                # within the adaptive overlap threshold.
                mask = encoder._compute_overlap_points(batch, point).reshape(-1)
                n = min(f.shape[0], mask.shape[0])
                feats.append(f[:n].cpu())
                labels.append(mask[:n].detach().cpu().float())
                n_obj += batch["points_per_part"].shape[0]

    x = torch.cat(feats)
    y = torch.cat(labels)
    rate = y.mean().item()

    name = ",".join(datamodule.dataset_names)
    print(f"\n=== C2 mating probe (on-path conditioning features): {name} ===")
    print(f"  objects: {n_obj} | points: {x.shape[0]} | feature dim: {x.shape[1]}")
    print(f"  GT mating-label rate: {rate * 100:.2f}%")

    if not (MIN_RATE <= rate <= MAX_RATE):
        print(f"  !! DEGENERATE LABELS (outside [{MIN_RATE:.1%}, {MAX_RATE:.0%}]) — the adaptive")
        print("     threshold has collapsed for this split (raw scan units?). REFUSING to")
        print("     report AUC; use a scale-normalized split. No conclusion may be drawn.")
        print("=== end probe ===\n")
        return

    if x.shape[0] > max_points:
        idx = torch.randperm(x.shape[0], generator=torch.Generator().manual_seed(0))[:max_points]
        x, y = x[idx], y[idx]

    auc, loss = _fit_linear_probe(x, y)
    print(f"  linear-probe AUC (held-out 30%): {auc:.4f}   [train BCE {loss:.4f}]")
    print(f"  instrument gate (labeled synthetic arm must reach AUC >= {VALIDATION_GATE}):"
          f" {'PASS' if auc >= VALIDATION_GATE else 'below gate'}")
    print("  NOTE: interpret only against the synthetic control from the same sweep —")
    print("        a collapse on worn rims vs fresh ceramics is the H3 signature.")
    print("=== end probe ===\n")


if __name__ == "__main__":
    main()
