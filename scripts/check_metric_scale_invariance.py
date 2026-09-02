"""Gate: part accuracy must not change when the same object is stored in other units.

This is the check that three paragraphs of prose failed to enforce. The evaluator
used to rescale point clouds into each object's own stored units and then apply
Breaking Bad's tau = 0.01 there. Breaking Bad states tau in a unit-length box
("We re-scale each of them to fit a unit-length box ... This normalization
scheme allows our method to be scale invariant", Sellan et al. 2022), so doing
it in millimetres asked a ceramic fragment to land within 0.1 mm on a 150 mm
pot -- about 125x tighter than the synthetic case. Every real Fractura object
scored exactly 1/n_parts, which is the free anchor, and that was read as the
model failing. See docs/notes/FRACTURA_WHY_IT_FAILS.md.

The property that was violated is simple enough to assert directly: take one
object, store it in metres, in millimetres and in the normalized frame, and the
score must not move. Anything that reintroduces an absolute length will fail
here rather than three months later in a result read-out.

Run on Spartan (needs torch + pytorch3d), from anywhere:
  python scripts/check_metric_scale_invariance.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import torch

from tora.eval.metrics import compute_part_acc, unit_box_scale

# A pot roughly 150 mm across, stored three ways. 61.0 is the median scale the
# real Fractura ceramics actually arrive with; 0.5 is Breaking Bad's.
UNITS = {
    "normalized (dataloader frame)": 1.0,
    "Breaking Bad convention": 0.5,
    "millimetres (Fractura real)": 61.0,
    "metres": 0.061,
    "absurd but legal": 12345.0,
}


def make_object(seed: int = 0, n_parts: int = 5, n_pts: int = 300):
    """One object in the dataloader frame, plus a prediction that is partly wrong.

    The prediction must be neither perfect nor hopeless: if every fragment
    passed, or none did, the test would still pass with the threshold broken.
    """
    g = torch.Generator().manual_seed(seed)
    parts = [torch.rand(n_pts, 3, generator=g) * 0.6 - 0.3 for _ in range(n_parts)]
    centres = torch.tensor([[0.0, 0.0, 0.0], [0.7, 0.1, 0.0], [-0.6, 0.2, 0.1],
                            [0.1, 0.7, -0.2], [0.0, -0.7, 0.3]])[:n_parts]
    gt = torch.cat([p + c for p, c in zip(parts, centres)], dim=0)

    # displace some fragments and leave others seated
    offsets = torch.zeros(n_parts, 3)
    offsets[1] = torch.tensor([0.02, 0.0, 0.0])     # near-perfect
    offsets[2] = torch.tensor([0.35, 0.1, 0.0])     # clearly wrong
    if n_parts > 3:
        offsets[3] = torch.tensor([0.9, -0.4, 0.5])  # hopeless
    pred = torch.cat([p + c + o for p, c, o in zip(parts, centres, offsets)], dim=0)

    ppp = torch.tensor([[n_pts] * n_parts])
    return gt.unsqueeze(0), pred.unsqueeze(0), ppp


def main() -> int:
    gt, pred, ppp = make_object()

    scores, abs_scores = {}, {}
    for name, s in UNITS.items():
        g, p = gt * s, pred * s
        unit = unit_box_scale(g).view(1, 1, 1)
        acc, _ = compute_part_acc(g / unit, p / unit, ppp)
        scores[name] = float(acc[0])
        acc_abs, _ = compute_part_acc(g, p, ppp)          # the old behaviour
        abs_scores[name] = float(acc_abs[0])

    print(f"{'stored as':32s}  {'fixed tau in unit box':>22s}  {'absolute (old)':>15s}")
    for name in UNITS:
        print(f"{name:32s}  {scores[name]:22.3f}  {abs_scores[name]:15.3f}")

    ok = True

    vals = set(round(v, 6) for v in scores.values())
    if len(vals) != 1:
        print("\nFAIL: part accuracy moved when only the storage unit changed.")
        print("      The threshold is absolute again. Fix the evaluator, not this test.")
        ok = False

    only = next(iter(vals))
    if only in (0.0, 1.0):
        print(f"\nFAIL: every fragment scored the same ({only}), so this proves nothing.")
        print("      Adjust the offsets in make_object so some pass and some do not.")
        ok = False

    if len(set(round(v, 6) for v in abs_scores.values())) == 1:
        print("\nFAIL: the absolute metric did NOT move across units, so this test")
        print("      cannot tell the two apart and would pass on a broken evaluator.")
        ok = False

    if ok:
        print(f"\nPASS: {only:.3f} in every unit, while the old absolute metric ranged "
              f"{min(abs_scores.values()):.3f}-{max(abs_scores.values()):.3f}.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
