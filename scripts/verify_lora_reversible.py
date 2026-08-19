"""Can the adapter be switched OFF and leave the base model unchanged?

Gate C of `WEAR_V3_PLAN.md`, and the check the whole idea rests on. The point of
an adapter is that a change can be attributed to it and undone. An adapter whose
"off" state differs from the base model -- even slightly -- gives neither: every
comparison between domains would carry an unknown offset, and a negative result
could not be distinguished from a plumbing error.

So this asserts EXACT equality, not closeness. LoRALinear initialises B to zero,
so a fresh adapter is the identity by construction rather than by tolerance, and
that claim should be checked against a real checkpoint rather than believed.

Four things are checked, in the order that they would fail:

  1. PLACEMENT   the adapters land on the projections intended, and those
                 projections are Linear layers. A silent miss would train
                 nothing and look like a model that cannot learn.
  2. IDENTITY    with a fresh adapter the output is bit-for-bit the base output.
  3. OFF SWITCH  after perturbing the adapter weights, disabling it returns the
                 output to bit-for-bit the base output. This is the one that
                 matters: it proves the switch, not just the initialisation.
  4. EFFECT      with the adapter enabled and perturbed, the output CHANGES.
                 Without this, 2 and 3 could both pass on an adapter that was
                 never wired in at all.

Usage:
  python scripts/verify_lora_reversible.py --ckpt /path/to/model.ckpt
"""

import argparse
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tora.modeling.lora import (LoRALinear, add_lora, lora_state_dict,  # noqa: E402
                                mark_trainable, set_lora_enabled)


def build_model(ckpt_path):
    """The DiT alone, on CPU, with its shape INFERRED from the checkpoint.

    Hard-coding the dimensions was the first attempt and it failed against every
    tensor in the file: the real model is 512 wide, not 256. Guessing an
    architecture to test a checkpoint against is how a verification passes on
    something that is not the model in use.
    """
    from tora.modeling.flow_model.dit import PointCloudDiT
    torch.manual_seed(0)

    inner, embed_dim, n_layers, n_heads = {}, 512, 4, 8
    if ckpt_path:
        sd = torch.load(ckpt_path, map_location="cpu", weights_only=False)
        sd = sd.get("state_dict", sd)
        inner = {k.split("flow_model.", 1)[1]: v for k, v in sd.items()
                 if "flow_model." in k}
        if inner:
            embed_dim = int(inner["final_mlp.0.weight"].shape[0])
            idx = [int(k.split(".")[1]) for k in inner
                   if k.startswith("transformer_layers.")]
            n_layers = max(idx) + 1 if idx else n_layers
            g = next((v for k, v in inner.items() if k.endswith("q_norm.gamma")),
                     None)
            if g is not None:
                n_heads = int(g.shape[0])
            print(f"inferred from checkpoint: embed_dim {embed_dim}, "
                  f"{n_layers} layers, {n_heads} heads")

    model = PointCloudDiT(
        in_dim=3, out_dim=3, embed_dim=embed_dim, num_layers=n_layers,
        num_heads=n_heads, use_vanilla_attn=True,
    )
    if inner:
        res = model.load_state_dict(inner, strict=False)
        bad = [k for k in res.missing_keys if "lora" not in k]
        print(f"loaded {len(inner)} tensors, {len(bad)} missing, "
              f"{len(res.unexpected_keys)} unexpected")
        if len(bad) > 8:
            print("  ** too many missing tensors; the architecture still does "
                  "not match and this verification would be meaningless **")
            sys.exit(2)
    model.eval()
    return model


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ckpt", default="")
    ap.add_argument("--rank", type=int, default=128)
    ap.add_argument("--alpha", type=int, default=256)
    args = ap.parse_args()

    model = build_model(args.ckpt)

    torch.manual_seed(1)
    B, N = 2, 64
    x = torch.randn(B, N, 3)
    t = torch.rand(B)
    ppp = torch.tensor([[N // 2, N // 2], [N // 2, N // 2]], dtype=torch.long)

    def run():
        with torch.no_grad():
            try:
                return model(x, t, ppp)
            except TypeError:
                return model(x, t)

    base = run().clone()
    print(f"base output {tuple(base.shape)}, "
          f"mean {base.mean():.6f}, std {base.std():.6f}")

    # 1. placement
    print("\n1. PLACEMENT")
    wrapped = add_lora(model, r=args.rank, alpha=args.alpha, dropout=0.0)
    n_mod = sum(isinstance(m, LoRALinear) for m in model.modules())
    ok_place = len(wrapped) == 4 and n_mod == 4
    print(f"   {len(wrapped)} projections wrapped, {n_mod} LoRALinear modules "
          f"-> {'PASS' if ok_place else 'FAIL'}")
    mark_trainable(model)

    # 2. identity at initialisation
    print("\n2. IDENTITY at initialisation")
    model.eval()
    fresh = run()
    d0 = (fresh - base).abs().max().item()
    ok_id = torch.equal(fresh, base)
    print(f"   max difference {d0:.3e} -> {'PASS (exact)' if ok_id else 'FAIL'}")

    # perturb, so the following two tests are not vacuous
    with torch.no_grad():
        for m in model.modules():
            if isinstance(m, LoRALinear):
                m.lora_B.normal_(0.0, 0.05)

    # 4. effect (run before 3 so the perturbation is shown to matter)
    print("\n3. EFFECT when enabled")
    on = run()
    d_on = (on - base).abs().max().item()
    ok_eff = d_on > 1e-6
    print(f"   max difference from base {d_on:.3e} -> "
          f"{'PASS (adapter does something)' if ok_eff else 'FAIL (not wired in)'}")

    # 3. the off switch
    print("\n4. OFF SWITCH after perturbation")
    n = set_lora_enabled(model, False)
    off = run()
    d_off = (off - base).abs().max().item()
    ok_off = torch.equal(off, base)
    print(f"   {n} adapters disabled, max difference {d_off:.3e} -> "
          f"{'PASS (exact)' if ok_off else 'FAIL'}")
    set_lora_enabled(model, True)

    # adapter file round trip
    print("\n5. ADAPTER FILE round trip")
    sd = lora_state_dict(model)
    nbytes = sum(v.numel() * v.element_size() for v in sd.values())
    before = run()
    with torch.no_grad():
        for m in model.modules():
            if isinstance(m, LoRALinear):
                m.lora_B.zero_()
    model.load_state_dict(sd, strict=False)
    after = run()
    ok_rt = torch.equal(before, after)
    print(f"   {len(sd)} tensors, {nbytes / 1e6:.1f} MB -> "
          f"{'PASS (exact)' if ok_rt else 'FAIL'}")

    allok = ok_place and ok_id and ok_eff and ok_off and ok_rt
    print(f"\n{'ALL PASS' if allok else 'FAILED'} -- an adapter that cannot be "
          f"switched off exactly is not switchable, and every")
    print("cross-domain comparison built on it would carry an unknown offset.")
    sys.exit(0 if allok else 1)


if __name__ == "__main__":
    main()
