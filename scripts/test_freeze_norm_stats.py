"""Does the freeze actually freeze? Seconds on CPU, no checkpoint needed.

Job 29527496 spent 2h42m on an A100 and produced nine evaluation arms that had
to be thrown away, because 486 supposedly-frozen encoder tensors moved. Every
one was a batch-norm running statistic: `requires_grad_(False)` stops the
optimiser, and a BatchNorm in train mode recalibrates itself inside forward()
where the optimiser never looks.

This is the thirty-line version of that discovery, so it can never be made
again quietly. It builds a toy model with the same shape of problem -- a frozen
"encoder" with batch norm plus a trainable head -- and checks three things:

  1. WITHOUT the fix, the frozen statistics DO move. If this stops being true
     the test is no longer testing anything, so it is asserted, not assumed.
  2. WITH the fix, they do not move at all, through many forward passes.
  3. The fix survives model.train(), which Lightning calls every epoch. This is
     the part a one-off .eval() would miss, and it is how the bug got in.

Run:  python scripts/test_freeze_norm_stats.py
"""

import sys
from pathlib import Path

import torch
import torch.nn as nn

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tora.modeling.lora import (assert_freeze_holds, assert_norms_stay_frozen,
                                freeze_norm_stats, pin_encoder_frozen)


class Toy(nn.Module):
    """Frozen 'encoder' with batch norm, plus a trainable 'pose head'."""

    def __init__(self):
        super().__init__()
        self.encoder = nn.Sequential(nn.Linear(8, 8), nn.BatchNorm1d(8),
                                     nn.ReLU(), nn.Linear(8, 8),
                                     nn.BatchNorm1d(8))
        self.final_mlp = nn.Linear(8, 3)

    def forward(self, x):
        return self.final_mlp(self.encoder(x))


class ToyLikeTora(Toy):
    """Toy that un-freezes its own encoder every epoch, exactly as TORA does.

    `frozen_encoder` defaults to False in tora/modeling/tora.py and no config
    here sets it, so `_freeze_encoder()` takes the else-branch and switches
    requires_grad back ON for the whole encoder -- and `on_train_epoch_start`
    calls it at the top of every epoch. Any freeze applied at setup time is
    undone before the first batch, silently.
    """

    def __init__(self, frozen_encoder: bool = False):
        super().__init__()
        self.frozen_encoder = frozen_encoder
        self.feature_extractor = self.encoder

    def _freeze_encoder(self, eval_mode: bool = False):
        if self.frozen_encoder or eval_mode:
            self.feature_extractor.eval()
            for p in self.feature_extractor.parameters():
                p.requires_grad = False
        else:
            self.feature_extractor.train()
            for p in self.feature_extractor.parameters():
                p.requires_grad = True

    def on_train_epoch_start(self):
        self._freeze_encoder()


def stats(model):
    return {k: v.clone() for k, v in model.state_dict().items()
            if any(t in k for t in ("running_mean", "running_var",
                                    "num_batches_tracked"))}


def drift(before, after):
    """Largest absolute move of any running statistic, and how many moved."""
    moved = {k: float((after[k].float() - before[k].float()).abs().max())
             for k in before}
    n = sum(1 for d in moved.values() if d > 0.0)
    return n, max(moved.values()), moved


def freeze_grads(model):
    for p in model.encoder.parameters():
        p.requires_grad_(False)


def run(model, steps=20, batch=16):
    """Forward passes only -- no optimiser, so nothing here should teach it."""
    torch.manual_seed(0)
    for _ in range(steps):
        model(torch.randn(batch, 8) * 3.0 + 5.0)


def main():
    torch.manual_seed(0)

    # 1. The bug, reproduced. requires_grad alone.
    m = Toy()
    freeze_grads(m)
    m.train()
    before = stats(m)
    run(m)
    n, worst, _ = drift(before, stats(m))
    print(f"requires_grad only        : {n} statistics moved, worst {worst:.3e}")
    assert n > 0, ("the frozen statistics did not drift even without the fix, "
                   "so this test no longer reproduces the bug it guards")

    # 2. The fix.
    m = Toy()
    freeze_grads(m)
    freeze_norm_stats(m, verbose=False)
    m.train()
    before = stats(m)
    run(m)
    n, worst, moved = drift(before, stats(m))
    print(f"with freeze_norm_stats    : {n} statistics moved, worst {worst:.3e}")
    assert n == 0, f"statistics still drifting: {[k for k, d in moved.items() if d]}"

    # 3. The part a one-off .eval() would miss: Lightning calls train() every
    #    epoch, and that is what put the batch norms back the first time.
    for epoch in range(3):
        m.train()
        run(m)
    n, worst, moved = drift(before, stats(m))
    print(f"after 3 more model.train(): {n} statistics moved, worst {worst:.3e}")
    assert n == 0, f"the pin did not survive model.train(): {moved}"

    pinned = assert_norms_stay_frozen(m)
    print(f"assert_norms_stay_frozen  : {pinned} norm layers holding eval")

    # 4. A norm layer someone deliberately unfroze must be left alone -- the fix
    #    should not quietly disable training the user asked for.
    m2 = Toy()
    freeze_grads(m2)
    for p in m2.encoder[1].parameters():
        p.requires_grad_(True)
    pinned_paths = freeze_norm_stats(m2, verbose=False)
    assert "encoder.1" not in pinned_paths, \
        "pinned a norm layer that was deliberately left trainable"
    assert "encoder.4" in pinned_paths, "did not pin the frozen norm layer"
    print(f"deliberately-unfrozen norm: left alone (pinned {pinned_paths})")

    # 5. The bigger half, and the one that actually cost the run: the model
    #    un-freezing its own encoder at every epoch start.
    print()
    m3 = ToyLikeTora()
    freeze_grads(m3)
    n_before = sum(p.numel() for p in m3.parameters() if p.requires_grad)
    m3.on_train_epoch_start()
    n_after = sum(p.numel() for p in m3.parameters() if p.requires_grad)
    print(f"model unfreezes itself       : {n_before} trainable at setup, "
          f"{n_after} after one epoch start")
    assert n_after > n_before, ("the toy no longer reproduces the epoch-start "
                                "unfreeze it exists to guard against")

    #    The same model with the pin installed.
    m4 = ToyLikeTora()
    freeze_grads(m4)
    freeze_norm_stats(m4, verbose=False)
    pin_encoder_frozen(m4, verbose=False)
    n_before = sum(p.numel() for p in m4.parameters() if p.requires_grad)
    for _ in range(3):
        m4.on_train_epoch_start()
        run(m4)
    n_after = sum(p.numel() for p in m4.parameters() if p.requires_grad)
    print(f"with pin_encoder_frozen      : {n_before} trainable at setup, "
          f"{n_after} after 3 epoch starts")
    assert n_after == n_before, "the pin did not survive on_train_epoch_start()"
    assert_freeze_holds(m4, n_before)
    print("assert_freeze_holds          : passes against the real hooks")

    #    And it must FAIL on the unpinned model, or it is not a check.
    m5 = ToyLikeTora()
    freeze_grads(m5)
    n5 = sum(p.numel() for p in m5.parameters() if p.requires_grad)
    try:
        assert_freeze_holds(m5, n5)
    except RuntimeError:
        print("assert_freeze_holds unpinned : correctly refuses it")
    else:
        raise AssertionError("assert_freeze_holds passed a model whose encoder "
                             "un-freezes itself -- it is not checking anything")

    print()
    print("PASS -- frozen means frozen, through model.train() AND through the")
    print("        model's own epoch hooks.")


if __name__ == "__main__":
    main()
