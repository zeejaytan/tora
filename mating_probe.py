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


def _pca_reduce(x: torch.Tensor, dim: int) -> torch.Tensor:
    """Reduce features to `dim` principal components.

    Needed to compare feature sources FAIRLY: the Uni3D teacher emits 3072-d
    features while the frozen encoder emits 64-d. A higher-capacity probe can
    score better on noise alone, so both sources are cut to a common dimension
    before probing.
    """
    if x.shape[1] <= dim:
        return x
    xc = x - x.mean(0, keepdim=True)
    _, _, v = torch.pca_lowrank(xc, q=min(dim, min(xc.shape) - 1), niter=4)
    return xc @ v


def _fit_linear_probe(x: torch.Tensor, y: torch.Tensor, steps: int = 400, lr: float = 0.05,
                      weight_decay: float = 1e-3, shuffle_labels: bool = False):
    """Balanced, L2-regularised logistic regression; returns held-out AUC.

    `shuffle_labels=True` fits the identical probe on randomly permuted labels —
    the overfitting control. It must land near 0.5; anything higher means the
    probe has enough capacity to memorise noise and the real AUC is inflated.
    """
    g = torch.Generator().manual_seed(0)
    if shuffle_labels:
        y = y[torch.randperm(y.shape[0], generator=torch.Generator().manual_seed(1234))]
    perm = torch.randperm(x.shape[0], generator=g)
    x, y = x[perm], y[perm]
    n_tr = int(0.7 * x.shape[0])
    xtr, ytr, xte, yte = x[:n_tr], y[:n_tr], x[n_tr:], y[n_tr:]

    mu, sd = xtr.mean(0, keepdim=True), xtr.std(0, keepdim=True) + 1e-6
    xtr, xte = (xtr - mu) / sd, (xte - mu) / sd

    w = torch.zeros(x.shape[1], 1, requires_grad=True)
    b = torch.zeros(1, requires_grad=True)
    opt = torch.optim.Adam([w, b], lr=lr, weight_decay=weight_decay)
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

    # C2  : "encoder" = frozen RPF per-point conditioning features c (on-path).
    # C2b : "teacher" = frozen Uni3D whole-object teacher features — the
    #       macro-shape channel TORA aligns the flow backbone to (its actual
    #       contribution), and the channel GARF has no analogue of. Probing the
    #       teacher is exactly what the paper does in App. 0.A.1.
    # "flow" = the flow model's OWN intermediate features at the layer the CKA
    #   alignment targets (repa_layer, layer 3 of 6). This is the decisive arm:
    #   the Uni3D teacher is training-only and discarded at inference, so a high
    #   teacher score shows only what was AVAILABLE to transfer, not what TORA
    #   actually carries where placement is decided. Probing here answers
    #   "did the form structure transfer, or not?".
    source = str(cfg.get("probe_features", "encoder")).lower()
    if source not in ("encoder", "teacher", "flow"):
        raise ValueError("probe_features must be 'encoder', 'teacher' or 'flow'")
    if source == "teacher" and getattr(model, "teacher", None) is None:
        raise RuntimeError("teacher is None (use_repa disabled?) — cannot run the C2b arm")
    if source == "teacher":
        model.teacher = model.teacher.to(device).eval()

    feats, labels = [], []
    n_obj = 0
    with torch.inference_mode():
        for dl in datamodule.test_dataloader():
            for batch in dl:
                batch = _move(batch, device)
                with torch.autocast(device_type=device.type, enabled=False):
                    out = encoder(batch)
                point = out["point"]
                # Labels ALWAYS come from the same rule regardless of feature
                # source, so encoder-vs-teacher is a controlled comparison.
                mask = encoder._compute_overlap_points(batch, point).reshape(-1)
                if source == "encoder":
                    f = point["feat"].detach().float()
                elif source == "teacher":
                    t = model.teacher.extract_features(batch)[0]     # (B, N, D)
                    f = t.reshape(-1, t.shape[-1]).detach().float()
                else:
                    # Flow model's intermediate features at the aligned layer.
                    # These depend on the noisy state x_t, so evaluate at a fixed
                    # timestep (probe_t) built exactly as training does.
                    from tora.modeling.tora import compute_flow_target
                    x0 = batch["pointclouds_gt"]
                    B = x0.shape[0]
                    gen = torch.Generator(device="cpu").manual_seed(0)
                    x1 = torch.randn(x0.shape, generator=gen).to(x0.device)
                    tt = torch.full((B,), float(cfg.get("probe_t", 0.3)), device=x0.device)
                    x_t, _ = compute_flow_target(x0, x1, tt)
                    latent = model._encode(batch)
                    _, interm = model.flow_model(
                        x=x_t, timesteps=tt, latent=latent,
                        scales=batch["scales"], anchor_indices=batch["anchor_indices"])
                    if interm is None:
                        raise RuntimeError("flow model returned no intermediate "
                                           "representation (repa_layer unset?)")
                    f = interm.reshape(-1, interm.shape[-1]).detach().float()
                n = min(f.shape[0], mask.shape[0])
                feats.append(f[:n].cpu())
                labels.append(mask[:n].detach().cpu().float())
                n_obj += batch["points_per_part"].shape[0]

    x = torch.cat(feats)
    y = torch.cat(labels)
    rate = y.mean().item()

    name = ",".join(datamodule.dataset_names)
    src_label = {
        "encoder": "frozen RPF conditioning features c (on-path)",
        "teacher": "frozen Uni3D teacher features (training-only, NOT used at inference)",
        "flow": f"flow model intermediate @ aligned layer, t={cfg.get('probe_t', 0.3)} (on-path)",
    }[source]
    print(f"\n=== mating probe [{source}] — {src_label}: {name} ===")
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

    # Equalise probe capacity across feature sources (teacher is 3072-d, encoder
    # 64-d); a bigger probe scores better on noise alone, so cut to a common dim.
    common_dim = int(cfg.get("probe_dim", 64))
    if x.shape[1] > common_dim:
        x = _pca_reduce(x, common_dim)
        print(f"  reduced {x.shape[1]}-d (PCA) for a like-for-like comparison")
    print(f"  probe dim: {x.shape[1]} | train points: {int(0.7 * x.shape[0])}")

    auc, loss = _fit_linear_probe(x, y)
    auc_shuf, _ = _fit_linear_probe(x, y, shuffle_labels=True)
    print(f"  linear-probe AUC (held-out 30%): {auc:.4f}   [train BCE {loss:.4f}]")
    print(f"  shuffled-label control (must be ~0.5): {auc_shuf:.4f}"
          f"  {'OK' if abs(auc_shuf - 0.5) < 0.10 else '!! OVERFITTING — real AUC is inflated'}")
    is_validation_arm = any("synth" in n for n in datamodule.dataset_names)
    if is_validation_arm:
        print(f"  INSTRUMENT GATE (this labeled synthetic arm must reach AUC >= {VALIDATION_GATE}):"
              f" {'PASS' if auc >= VALIDATION_GATE else 'FAIL — do not interpret the other arms'}")
    else:
        print("  (not the validation arm — the AUC>=0.75 gate applies only to the labeled")
        print("   synthetic run; read this number against the synthetic and fresh-real arms.")
        print("   A drop on worn rims relative to fresh real fracture is the H3 signature.)")
    print("=== end probe ===\n")


if __name__ == "__main__":
    main()
