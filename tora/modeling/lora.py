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
import types
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


# --- Batch-norm statistics are not covered by requires_grad ------------------
#
# Job 29527496 froze the encoder with requires_grad_(False) and the encoder
# changed anyway: 486 of its 492 tensors moved, led by
#   feature_extractor.encoder.dec.dec3.up.proj.1.running_var  max|diff| = 8.3e+06
#   ...embedding.stem.norm.num_batches_tracked                max|diff| = 1.9e+04
# Every one of those is a batch-norm running statistic, and 18,960 is just the
# number of batches that went past in 60 epochs.
#
# requires_grad only stops the OPTIMISER. A BatchNorm in train mode also updates
# running_mean / running_var / num_batches_tracked itself, inside forward(),
# with no gradient and no optimiser involved. The only thing that stops it is
# eval mode -- and Lightning calls model.train() at the top of every epoch,
# which puts it straight back.
#
# So the frozen encoder was silently recalibrating to our 371 vessels for the
# whole run, that drift was saved into the checkpoint, and no switch removes it.
# That is why "adapter off" did not reproduce the baseline: the control arm was
# not the base model. It made every number from that job uninterpretable --
# the adapter's effect and the encoder's drift cannot be told apart afterwards.


def _stay_in_eval(self, mode: bool = True):
    """A train() that refuses to leave eval mode.

    nn.Module.train() only sets self.training and recurses into children, so
    doing both with mode=False is the whole job -- and it survives Lightning
    calling model.train() again at every epoch boundary.
    """
    self.training = False
    for child in self.children():
        child.train(False)
    return self


_NORM_WITH_STATS = (nn.modules.batchnorm._BatchNorm,
                    nn.modules.instancenorm._InstanceNorm)


def freeze_norm_stats(model: nn.Module, verbose: bool = True):
    """Stop frozen normalisation layers from re-calibrating during training.

    Applies only to layers that (a) keep running statistics and (b) have no
    trainable parameter of their own -- a norm layer someone deliberately
    unfroze is left alone.

    Returns the list of module paths pinned to eval.
    """
    pinned = []
    for name, mod in model.named_modules():
        if not isinstance(mod, _NORM_WITH_STATS):
            continue
        if getattr(mod, "running_mean", None) is None:
            continue  # track_running_stats=False already: nothing to drift
        if any(p.requires_grad for p in mod.parameters(recurse=False)):
            continue  # being trained on purpose
        mod.eval()
        mod.train = types.MethodType(_stay_in_eval, mod)
        pinned.append(name)
    if verbose:
        print(f"[lora] pinned {len(pinned)} frozen norm layers to eval so their "
              f"running statistics cannot drift")
    return pinned


def assert_norms_stay_frozen(model: nn.Module) -> int:
    """Check the pin actually holds against a model.train() call.

    Cheap, and it is the assumption the whole on/off comparison rests on. Do
    not replace this with reading the code: the code looked right last time.
    """
    model.train()
    leaked = [n for n, m in model.named_modules()
              if isinstance(m, _NORM_WITH_STATS)
              and getattr(m, "running_mean", None) is not None
              and not any(p.requires_grad for p in m.parameters(recurse=False))
              and m.training]
    if leaked:
        raise RuntimeError(
            f"{len(leaked)} frozen norm layers went back into train mode after "
            f"model.train(), e.g. {leaked[:3]}. Their running statistics would "
            f"drift into the checkpoint and the adapter-off arm would not be "
            f"the base model.")
    return sum(1 for n, m in model.named_modules()
               if isinstance(m, _NORM_WITH_STATS) and not m.training)


def mark_trainable(model: nn.Module, train_head: bool = True,
                   head_names: Iterable[str] = ("final_mlp",),
                   verbose: bool = True):
    """Freeze everything except the adapters and, optionally, the pose head.

    GARF unfreezes the pose-prediction MLPs alongside the adapters; the rest of
    the backbone stays fixed.

    "Fixed" here means fixed, not merely excluded from the optimiser -- see
    freeze_norm_stats, which is called at the end. Leaving that out cost job
    29527496.
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
    # requires_grad does not freeze batch-norm running statistics. Do that too,
    # after the requires_grad pass so we can tell a deliberately-unfrozen norm
    # layer from a frozen one.
    freeze_norm_stats(model, verbose=verbose)

    total = sum(p.numel() for p in model.parameters())
    if verbose:
        print(f"[lora] trainable {trainable:,} of {total:,} parameters "
              f"({100 * trainable / max(total, 1):.2f}%)")
    return trainable


def lora_state_dict(model: nn.Module) -> dict:
    """Only the adapter tensors -- an adapter file, not a checkpoint.

    CLONED, and that is not defensive tidiness. `.detach().cpu()` on a tensor
    already on the CPU returns one SHARING STORAGE with the live parameter, so
    the dict tracks the model: keep training, or zero a weight, and the "saved"
    adapter changes with it. Caught by the round-trip check, which restored the
    weights to within 2.5e-01 of themselves rather than exactly.
    """
    return {k: v.detach().cpu().clone() for k, v in model.state_dict().items()
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
