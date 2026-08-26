"""What, other than the adapter, did an adapter run actually change?

Written because the control arm of job 29527496 failed. Switching the adapter
off was supposed to reproduce the untouched baseline exactly, and it did not:
on the six held-out fresh objects it read part accuracy 0.928 against the
baseline's 0.854, and the fraction of fragments landing within 10 degrees of
correct went from 0.278 to 0.000. Those are not rounding differences.

Two explanations, and they lead in opposite directions:

  1. THE SWITCH IS BROKEN. Disabling the adapter does not restore the base
     behaviour, in which case every number from that job is uninterpretable and
     the LoRA plumbing has to be fixed before anything is rerun.

  2. THE SWITCH IS FINE AND THE CLAIM WAS WRONG. `train_head=true` unfreezes the
     pose-prediction MLP, exactly as GARF's `modules_to_save` does. Those weights
     TRAIN, they are saved into the checkpoint, and no switch turns them off.
     "Adapter off" would then mean "adapter off, retrained pose head still in",
     which is a legitimate arm but is NOT the baseline, and describing it as
     bit-for-bit the base model was my error, not the code's.

This tells them apart by reading the two checkpoints rather than by reasoning
about them: it reports every tensor that differs, grouped by which part of the
model it belongs to. If the only differences outside the adapter are in
`final_mlp`, explanation 2 holds and the fix is to the experiment design. If
frozen backbone weights moved, explanation 1 holds and the fix is to the code.

THE ANSWER IT GAVE (job 29620633, on job 29527496's checkpoint): explanation 1.
486 of the encoder's 492 tensors had moved, led by batch-norm running statistics
-- `dec.dec3.up.proj.1.running_var` off by 8.3e+06, `num_batches_tracked` off by
18,960, which is simply the number of batches 60 epochs put through it.
`requires_grad_(False)` stops the optimiser; it does not stop a BatchNorm from
recalibrating itself inside forward(). The frozen encoder had been quietly
retuning to the training vessels the entire run, that drift was saved, and
nothing switches it off. Fixed in `tora/modeling/lora.py::freeze_norm_stats`.

Because it caught something three rounds of reading the code did not, this is
now a GATE and not only a diagnostic: `--fail-on-frozen` exits non-zero, and the
job script runs it between training and evaluation so a leaked freeze costs one
training run instead of a training run plus nine evaluations plus the writing-up.

Usage:
  python scripts/diff_adapter_checkpoint.py --base BASE.ckpt --trained TRAINED.ckpt
  python scripts/diff_adapter_checkpoint.py --base B --trained T --fail-on-frozen
"""

import argparse
import sys
from collections import defaultdict

import torch


def group_of(key: str) -> str:
    """Which part of the model a tensor belongs to, for the summary."""
    if "lora_A" in key or "lora_B" in key:
        return "ADAPTER (expected to differ)"
    if "final_mlp" in key:
        return "POSE HEAD final_mlp (differs only if train_head=true)"
    if key.startswith("feature_extractor"):
        return "FROZEN encoder"
    if key.startswith("flow_model"):
        return "FROZEN flow backbone"
    if key.startswith("teacher") or key.startswith("projector"):
        return "FROZEN teacher / projector"
    return "other"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", required=True)
    ap.add_argument("--trained", required=True)
    ap.add_argument("--atol", type=float, default=0.0,
                    help="0 means bit-for-bit, which is what the claim was")
    ap.add_argument("--fail-on-frozen", action="store_true",
                    help="exit 1 if any frozen weight moved, so this can gate a "
                         "job before it spends an A100 on uninterpretable arms")
    args = ap.parse_args()

    b = torch.load(args.base, map_location="cpu", weights_only=False)["state_dict"]
    t = torch.load(args.trained, map_location="cpu", weights_only=False)["state_dict"]

    print(f"base    {args.base}\n          {len(b)} tensors")
    print(f"trained {args.trained}\n          {len(t)} tensors\n")

    # The adapter renames weights (foo.weight -> foo.base.weight), so compare on
    # the base model's names with that rename undone.
    def canon(k):
        return k.replace(".base.weight", ".weight").replace(".base.bias", ".bias")

    t_canon = {}
    for k, v in t.items():
        t_canon.setdefault(canon(k), []).append((k, v))

    changed = defaultdict(list)
    same = defaultdict(int)
    absent = []

    for k, bv in b.items():
        hits = t_canon.get(k)
        if not hits:
            absent.append(k)
            continue
        tk, tv = hits[0]
        if not torch.is_tensor(bv) or not torch.is_tensor(tv):
            continue
        if bv.shape != tv.shape:
            changed[group_of(tk)].append((tk, float("nan")))
            continue
        d = float((bv.float() - tv.float()).abs().max())
        if d > args.atol:
            changed[group_of(tk)].append((tk, d))
        else:
            same[group_of(tk)] += 1

    # Adapter tensors exist only in the trained file; count them separately.
    only_trained = [k for k in t if k not in b and canon(k) not in b]
    n_lora = sum(1 for k in only_trained if "lora_A" in k or "lora_B" in k)

    print(f"{len(only_trained)} tensors exist only in the trained file "
          f"({n_lora} of them adapter tensors)\n")
    if absent:
        print(f"{len(absent)} base tensors have no counterpart, e.g. {absent[:3]}\n")

    print("WHAT MOVED")
    print("-" * 72)
    for g in sorted(set(list(changed) + list(same))):
        n_ch = len(changed.get(g, []))
        n_sm = same.get(g, 0)
        mark = "  <-- " if n_ch and g.startswith("FROZEN") else "      "
        print(f"{mark}{g}: {n_ch} changed, {n_sm} identical")
        for k, d in sorted(changed.get(g, []), key=lambda x: -x[1])[:4]:
            print(f"          {k}  max|diff| = {d:.3e}")
    print("-" * 72)

    frozen_moved = sum(len(v) for g, v in changed.items() if g.startswith("FROZEN"))
    head_moved = sum(len(v) for g, v in changed.items() if "final_mlp" in g)

    print()
    if frozen_moved:
        print(f"*** {frozen_moved} FROZEN weights moved. The freeze leaked -- this is")
        print("*** a code fault, and the on/off comparison cannot be trusted.")
        stats = [k for g, v in changed.items() if g.startswith("FROZEN")
                 for k, _ in v
                 if any(t in k for t in ("running_mean", "running_var",
                                         "num_batches_tracked"))]
        if stats:
            print(f"*** {len(stats)} of them are batch-norm running statistics,")
            print("*** which update inside forward() and ignore requires_grad.")
            print("*** See tora/modeling/lora.py::freeze_norm_stats.")
        if args.fail_on_frozen:
            sys.exit(1)
    elif head_moved:
        print(f"The only non-adapter change is the pose head ({head_moved} tensors).")
        print("The switch works. 'Adapter off' means 'adapter off, retrained pose")
        print("head still in' -- a real arm, but NOT the untouched baseline.")
        print("To get a true base-model control, either set train_head=false or")
        print("compare against the baseline checkpoint directly, as this job did.")
    else:
        print("Nothing outside the adapter moved. Switching it off should give")
        print("the base model exactly; if evaluation disagrees, the difference is")
        print("in sampling, not in the weights.")


if __name__ == "__main__":
    main()
