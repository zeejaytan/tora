"""Switchable low-rank adapters, so one base model can serve several domains.

The conservator's proposal, 2026-08-18: train adapters that can be turned on and
off per data source rather than fine-tuning one set of weights for everything.

Why that is the right shape for this problem, and not just convenient: wear_v1
bought its gains on worn material by LOSING them on fresh -- 88% down to 79%.
One set of weights forced to serve fresco fracture, synthetic vessels and real
archaeological pottery will trade them off against each other in exactly that
way, and there is no knob to undo it afterwards. An adapter has a knob.

PLACEMENT follows GARF, the sibling method in this workspace, which fine-tunes
the same way: adapters in the self-attention and global-attention projections of
the FINAL transformer block, with the pose-prediction MLP unfrozen and
everything else fixed. GARF reports 5-10 domain-specific objects being enough
for substantial gains, specifically on thin-shell material, which is our case.
Rank 128, alpha 256, dropout 0.1.

WHY NOT `peft`. It is built around HuggingFace model layouts and injecting it
into a bespoke DiT needs its own validation before it can be trusted. The
requirement here is that an adapter can be switched OFF and leave the base model
bit-for-bit unchanged; with sixty lines under our own control that is true by
construction -- B is initialised to zero, so a fresh adapter is exactly the
identity -- and `verify_lora_reversible.py` checks it against a real checkpoint
rather than asserting it.
"""

from __future__ import annotations

import math
from typing import Iterable

import torch
import torch.nn as nn


class LoRALinear(nn.Module):
    """A frozen Linear with a trainable low-rank correction that can be disabled.

    y = base(x) + enabled * (alpha / r) * B(A(dropout(x)))

    B starts at zero, so before any training this is EXACTLY base(x) -- not
    approximately, not to within a tolerance. That matters: an adapter whose
    "off" state differs from the base model cannot be used to attribute a change
    to the adapter.
    """

    def __init__(self, base: nn.Linear, r: int = 128, alpha: int = 256,
                 dropout: float = 0.1):
        super().__init__()
        self.base = base
        for p in self.base.parameters():
            p.requires_grad_(False)

        self.r = int(r)
        self.scaling = float(alpha) / float(r)
        self.enabled = True
        self.lora_dropout = nn.Dropout(dropout) if dropout > 0 else nn.Identity()
        self.lora_A = nn.Parameter(torch.empty(self.r, base.in_features))
        self.lora_B = nn.Parameter(torch.zeros(base.out_features, self.r))
        nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.base(x)
        if not self.enabled:
            return out
        h = self.lora_dropout(x) @ self.lora_A.t() @ self.lora_B.t()
        return out + h.to(out.dtype) * self.scaling

    def extra_repr(self) -> str:
        return f"r={self.r}, scaling={self.scaling:.3f}, enabled={self.enabled}"


# The projections GARF adapts, named as they appear in tora/modeling/flow_model.
TARGETS = ("self_qkv_proj", "self_out_proj",
           "global_qkv_proj", "global_out_proj")


def add_lora(model: nn.Module, r: int = 128, alpha: int = 256,
             dropout: float = 0.1, last_n_blocks: int = 1,
             targets: Iterable[str] = TARGETS, verbose: bool = True):
    """Wrap the attention projections of the last N transformer blocks.

    Returns the list of wrapped module paths, so a caller can record exactly
    what was adapted rather than trusting a count.
    """
    layers = None
    for name, mod in model.named_modules():
        if name.endswith("transformer_layers") and isinstance(mod, nn.ModuleList):
            layers = mod
            break
    if layers is None:
        raise RuntimeError("no transformer_layers ModuleList found in the model")

    chosen = list(range(len(layers)))[-max(1, last_n_blocks):]
    wrapped = []
    for bi in chosen:
        block = layers[bi]
        for t in targets:
            base = getattr(block, t, None)
            if base is None:
                continue
            if isinstance(base, LoRALinear):
                continue
            if not isinstance(base, nn.Linear):
                raise RuntimeError(f"block {bi}.{t} is {type(base).__name__}, "
                                   f"not nn.Linear -- placement assumption wrong")
            setattr(block, t, LoRALinear(base, r=r, alpha=alpha, dropout=dropout))
            wrapped.append(f"transformer_layers.{bi}.{t}")
    if verbose:
        print(f"[lora] wrapped {len(wrapped)} projections in block(s) {chosen}")
        for w in wrapped:
            print(f"[lora]   {w}")
    return wrapped


def set_lora_enabled(model: nn.Module, enabled: bool) -> int:
    n = 0
    for m in model.modules():
        if isinstance(m, LoRALinear):
            m.enabled = bool(enabled)
            n += 1
    return n


def mark_trainable(model: nn.Module, train_head: bool = True,
                   head_names: Iterable[str] = ("final_mlp",),
                   verbose: bool = True):
    """Freeze everything except the adapters and, optionally, the pose head.

    GARF unfreezes the pose-prediction MLPs alongside the adapters; the rest of
    the backbone stays fixed.
    """
    for p in model.parameters():
        p.requires_grad_(False)
    trainable = 0
    for m in model.modules():
        if isinstance(m, LoRALinear):
            m.lora_A.requires_grad_(True)
            m.lora_B.requires_grad_(True)
            trainable += m.lora_A.numel() + m.lora_B.numel()
    if train_head:
        for name, mod in model.named_modules():
            if any(name.endswith(h) for h in head_names):
                for p in mod.parameters():
                    p.requires_grad_(True)
                    trainable += p.numel()
    total = sum(p.numel() for p in model.parameters())
    if verbose:
        print(f"[lora] trainable {trainable:,} of {total:,} parameters "
              f"({100 * trainable / max(total, 1):.2f}%)")
    return trainable


def lora_state_dict(model: nn.Module) -> dict:
    """Only the adapter tensors -- an adapter file, not a checkpoint."""
    return {k: v.detach().cpu() for k, v in model.state_dict().items()
            if "lora_A" in k or "lora_B" in k}


def load_lora_state_dict(model: nn.Module, sd: dict, strict: bool = True):
    missing = model.load_state_dict(sd, strict=False)
    if strict:
        got = {k for k in sd}
        want = {k for k in model.state_dict() if "lora_A" in k or "lora_B" in k}
        if got != want:
            raise RuntimeError(
                f"adapter does not match the model: {len(want - got)} expected "
                f"tensors missing, {len(got - want)} unexpected")
    return missing
