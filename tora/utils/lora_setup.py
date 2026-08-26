"""Wire the switchable adapters into training and sampling.

Gate C proved the adapter itself is reversible (`scripts/verify_lora_reversible.py`).
It did not connect it to anything: `train.py` had no way to turn one on, and
`sample.py` had no way to load one. This is that connection, in one place so the
two entry points cannot drift apart.

THE FAILURE THIS EXISTS TO PREVENT. `load_checkpoint_for_module` loads with
`strict=False`. Wrapping a projection in a LoRALinear renames its weight from
`...self_qkv_proj.weight` to `...self_qkv_proj.base.weight`. So if the wrapping
is applied on one side and not the other, the load does not fail -- it silently
loads nothing into every adapted layer, and evaluation runs on a half-random
model, or on the base model with an untrained adapter, while printing numbers
that look like results. `assert_adapter_present` refuses that: after a load it
checks the checkpoint actually carried adapter tensors, and that at least one of
them is non-zero. A freshly initialised adapter has B = 0 and is exactly the
base model, so "all zeros" and "no adapter at all" are the same thing, and both
must be caught rather than reported as an adapter result.

THE SECOND FAILURE, found the expensive way. Job 29527496 froze the encoder and
the encoder changed anyway -- 486 tensors, all of them batch-norm running
statistics, which update inside forward() and are untouched by requires_grad.
The adapter-off arm was therefore not the base model and the whole job had to be
discarded. `mark_trainable` now pins those layers to eval and
`assert_norms_stay_frozen` verifies the pin survives Lightning's per-epoch
`model.train()`. Checking a frozen thing is actually frozen is not paranoia
here; it is the only reason the on/off comparison means anything.
"""

from __future__ import annotations

import torch
from omegaconf import DictConfig

from tora.modeling.lora import (add_lora, assert_norms_stay_frozen,
                                mark_trainable, set_lora_enabled)


def lora_cfg(cfg: DictConfig) -> DictConfig | None:
    """The `lora` block if it is present AND enabled, else None."""
    lc = cfg.get("lora", None)
    if lc is None or not bool(lc.get("enabled", False)):
        return None
    return lc


def apply_lora_from_cfg(cfg: DictConfig, model, freeze: bool = True):
    """Wrap the attention projections and, when training, freeze the rest.

    Call AFTER the model is instantiated -- TORA loads `encoder_ckpt` and
    `flow_model_ckpt` in its own constructor, so the base weights must already
    be in place before anything is wrapped around them.

    `freeze=False` for sampling: nothing is being trained, and freezing there
    would only hide a mistake in what was meant to be trainable.
    """
    lc = lora_cfg(cfg)
    if lc is None:
        return []

    wrapped = add_lora(
        model,
        r=int(lc.get("r", 128)),
        alpha=int(lc.get("alpha", 256)),
        dropout=float(lc.get("dropout", 0.1)),
        last_n_blocks=int(lc.get("last_n_blocks", 1)),
    )
    if not wrapped:
        raise RuntimeError(
            "lora.enabled=true but no projection was wrapped. The placement "
            "assumption is wrong -- training would update nothing and look "
            "like a model that cannot learn.")

    if freeze:
        mark_trainable(model, train_head=bool(lc.get("train_head", True)))
        n_train = sum(p.numel() for p in model.parameters() if p.requires_grad)
        if n_train == 0:
            raise RuntimeError("nothing is trainable after freezing")
        # Freezing gradients is not freezing the model. Batch-norm layers
        # recalibrate themselves inside forward(), which is how job 29527496
        # moved 486 supposedly-frozen encoder tensors. Check the pin survives a
        # model.train() call, because Lightning makes one every epoch.
        n_pinned = assert_norms_stay_frozen(model)
        print(f"[lora] {n_pinned} norm layers hold eval mode through model.train()")

    return wrapped


def assert_adapter_present(model, ckpt_path: str) -> int:
    """Refuse to evaluate an 'adapter' that is absent or still at its identity.

    Returns the number of adapter tensors found. Raises if the checkpoint
    carried none, or if every one of them is zero -- which is the same model as
    no adapter at all, and must not be reported as an adapter result.
    """
    sd = torch.load(ckpt_path, map_location="cpu", weights_only=False)["state_dict"]
    got = [k for k in sd if "lora_A" in k or "lora_B" in k]
    want = [k for k, _ in model.state_dict().items()
            if "lora_A" in k or "lora_B" in k]
    if not want:
        raise RuntimeError("model has no adapter to check -- lora was not applied")
    if not got:
        raise RuntimeError(
            f"{ckpt_path} contains no adapter tensors, but the model was wrapped "
            f"for {len(want)}. Loading is non-strict, so this would have run "
            f"silently on unloaded weights.")

    missing = set(want) - set(got)
    if missing:
        raise RuntimeError(
            f"adapter shape mismatch: {len(missing)} expected tensors absent "
            f"from the checkpoint, e.g. {sorted(missing)[:3]}")

    live = {k: v for k, v in model.state_dict().items() if k in set(want)}
    nz = sum(1 for k in want if "lora_B" in k
             and float(live[k].abs().max()) > 0.0)
    if nz == 0:
        raise RuntimeError(
            "every lora_B in the loaded model is zero, so the adapter is "
            "exactly the base model. Either it never trained or it did not load.")
    print(f"[lora] adapter loaded: {len(want)} tensors, {nz} non-zero B blocks")
    return len(want)


def set_enabled(model, enabled: bool) -> int:
    """Switch every adapter on or off, for the on/off comparison."""
    n = set_lora_enabled(model, enabled)
    print(f"[lora] adapters {'ENABLED' if enabled else 'DISABLED'} ({n} layers)")
    return n
