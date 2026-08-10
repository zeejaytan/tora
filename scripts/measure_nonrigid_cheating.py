"""How much did the model have to DEFORM the sherds to make that picture?

Conservator's observation, 2026-08-10: for wear_v2 on the Juglet, generation05
looks like a convincing closed vessel while proposed_assembly05 -- the same
attempt with the sherds kept rigid -- splays apart. The nicer picture is the
less trustworthy one.

That is not a rendering quirk. The flow model moves every point independently;
nothing requires a fragment to stay rigid. So it can assemble a plausible pot by
stretching and bending sherds into place. The Procrustes step then asks the only
physically possible question -- with each sherd at its true, unaltered shape,
where does it go? -- and the difference between the two answers is exactly how
much the model cheated.

This measures that difference per fragment:

    residual   how far each point sits from where a rigid placement of its own
               fragment would put it, as a fraction of object size. Zero means
               the model moved that sherd like a solid object. Large means it
               deformed it.

    spread     the same residual expressed against the fragment's own size, so a
               small sherd distorted badly is not hidden by a large one placed
               well.

Why it matters beyond one picture: every "the shape is there" judgement made
from a generation render is only as good as this number. A low residual means
the render can be trusted as a reassembly. A high one means the render shows a
pot the sherds cannot actually form, and reading it as progress would be reading
the model's wishful thinking as a result.

Usage:
  python scripts/measure_nonrigid_cheating.py --npz <eval_run>/clouds/*.npz
"""

import argparse
import glob
import sys
from pathlib import Path

import numpy as np


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--npz", required=True, nargs="+",
                    help="assembly npz files (globs allowed)")
    ap.add_argument("--label", default="")
    args = ap.parse_args()

    paths = []
    for p in args.npz:
        paths.extend(sorted(glob.glob(p)))
    if not paths:
        print("no npz files matched")
        return

    for path in paths:
        d = np.load(path, allow_pickle=True)
        pred = d["generations_pred"]          # (K, N, 3) raw model output
        prop = d["generations_proposed"]      # (K, N, 3) rigid placement
        ppp = d["points_per_part"]
        ppp = ppp[ppp > 0]
        scale = float(np.linalg.norm(prop.reshape(-1, 3).max(0)
                                     - prop.reshape(-1, 3).min(0)))

        name = str(d["name"]) if "name" in d.files else Path(path).stem
        print(f"\n{args.label or name}  ({len(ppp)} fragments, "
              f"{pred.shape[0]} attempts)")
        print("  How far the raw output sits from a RIGID placement of the same")
        print("  sherd. 0% = moved like a solid object; large = deformed.")
        print(f"    {'attempt':>8s} {'mean':>8s} {'worst frag':>12s} "
              f"{'frags > 2%':>11s}")

        bounds = np.concatenate([[0], np.cumsum(ppp)])
        worst_overall = 0.0
        for k in range(pred.shape[0]):
            per_frag = []
            for a, b in zip(bounds[:-1], bounds[1:]):
                r = np.linalg.norm(pred[k, a:b] - prop[k, a:b], axis=1)
                per_frag.append(float(r.mean()) / scale * 100.0)
            per_frag = np.asarray(per_frag)
            worst_overall = max(worst_overall, float(per_frag.max()))
            print(f"    {k + 1:>8d} {per_frag.mean():>7.2f}% "
                  f"{per_frag.max():>11.2f}% {int((per_frag > 2.0).sum()):>11d}")

        print(f"  worst single fragment across all attempts: {worst_overall:.2f}%")
        if worst_overall > 2.0:
            print("  => the raw renders show sherds DEFORMED into place. Judge the")
            print("     proposed_assembly images; the generation ones flatter the")
            print("     model by letting fragments bend.")
        else:
            print("  => fragments moved essentially rigidly; the raw renders and")
            print("     the rigid ones should agree, and either can be trusted.")


if __name__ == "__main__":
    main()
