"""Draw the fragments ON THEIR OWN, looking straight down the vessel's axis.

Every view of this question so far has shown the vessel ASSEMBLED, and assembled
is the one arrangement in which a ring and a sherd look alike -- both are just a
patch of colour on a wall. That is why a 300-degree cutoff, then an arc/rise
ratio, then two renders all failed to settle it.

Looking down the axis at ONE fragment answers it with nothing left to interpret:

    a sherd is an ARC          it lifts off the pot sideways
    a ring is a CLOSED HOOP    it would have to be slid over the pot to fit

That is a topological difference, not a matter of degree, so no threshold and no
viewpoint can soften it. The grey outline behind each fragment is the whole
vessel's footprint, so how much of the circle the fragment takes is visible
rather than inferred.

Two breaks are drawn: the one with the most fragments wrapping past 260 degrees
and the one with the fewest. Both are already in bbad_vessels. The question the
picture has to answer is whether the first kind should be trained on.

Usage:
  python scripts/show_ring_problem.py --src dataset/bbad_vessels.hdf5 \
      --out artifacts/ring_problem.png
"""

import argparse
import json
from pathlib import Path

import h5py
import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

N_FRAG = 5


def axis_frame(allv):
    P = allv - allv.mean(axis=0)
    U = np.linalg.svd(P.T @ P)[0]
    return U[:, 0], U[:, 1], U[:, 2]


def wrap_degrees(theta):
    occ = np.zeros(360, dtype=bool)
    occ[np.clip(((np.degrees(theta) + 180.0) % 360.0).astype(int), 0, 359)] = True
    if occ.all():
        return 360.0
    if not occ.any():
        return 0.0
    start = int(np.argmax(occ))
    r = np.roll(occ, -start)
    longest = run = 0
    for v in r:
        run = 0 if v else run + 1
        longest = max(longest, run)
    return float(360 - longest)


def load_parts(grp):
    pg = grp["pieces"]
    keys = sorted(pg.keys(), key=lambda s: int(s) if s.isdigit() else s)
    return [np.asarray(pg[k]["vertices"][:], dtype=np.float64) for k in keys]


def sub(q, n):
    return q if len(q) <= n else q[::max(1, len(q) // n)]


def draw_block(axes, parts, head, sub_head, colour):
    """One assembled panel, then N_FRAG fragments alone from directly above."""
    allv = np.concatenate(parts, axis=0)
    ctr = allv.mean(axis=0)
    s = float(np.abs(allv - ctr).max()) + 1e-12
    ax, e1, e2 = axis_frame(allv)

    # the whole vessel seen from above, drawn behind every fragment for scale
    Q = (allv - ctr) / s
    foot = np.c_[Q @ e1, Q @ e2]
    foot = sub(foot, 9000)

    order = sorted(range(len(parts)), key=lambda i: -len(parts[i]))[:N_FRAG]

    a = axes[0]
    for i, p in enumerate(parts):
        q = sub((p - ctr) / s, 4000)
        a.scatter(q @ e1, q @ ax, s=1.3, alpha=0.8, linewidths=0,
                  color=plt.cm.tab20(i % 20))
    a.set_title(f"{head}\n{sub_head}\nassembled, side on — "
                f"every fragment looks alike here",
                fontsize=9.5, color=colour)
    a.set_xlim(-1.12, 1.12); a.set_ylim(-1.12, 1.12)

    for k, i in enumerate(order):
        a = axes[1 + k]
        a.scatter(foot[:, 0], foot[:, 1], s=0.7, alpha=0.16, linewidths=0,
                  color="#9aa5ad")
        q = sub((parts[i] - ctr) / s, 6000)
        u, v = q @ e1, q @ e2
        w = wrap_degrees(np.arctan2(v, u))
        a.scatter(u, v, s=2.2, alpha=0.85, linewidths=0,
                  color=plt.cm.tab20(i % 20))
        verdict = "CLOSED HOOP" if w >= 300 else ("almost closed" if w >= 260
                                                  else "arc — a sherd")
        a.set_title(f"fragment {k + 1} alone, from above\n"
                    f"{w:.0f}° round   {verdict}", fontsize=9,
                    color=colour if w >= 260 else "#2f6f7e")
        a.set_xlim(-1.12, 1.12); a.set_ylim(-1.12, 1.12)

    for a in axes:
        a.set_aspect("equal")
        a.set_xticks([]); a.set_yticks([])


def pick(dg, manifest, tags):
    scored = []
    for t in tags:
        parts = load_parts(dg[t])
        if len(parts) < 4:
            continue
        allv = np.concatenate(parts, axis=0)
        ctr = allv.mean(axis=0)
        _, e1, e2 = axis_frame(allv)
        ws = []
        for p in parts:
            q = p - ctr
            ws.append(wrap_degrees(np.arctan2(q @ e2, q @ e1)))
        scored.append((float(np.mean([w >= 260 for w in ws])), t))
    scored.sort(key=lambda r: -r[0])
    return scored[0], scored[-1]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", required=True)
    ap.add_argument("--dataset", default="bbad_vessels")
    ap.add_argument("--manifest", default="")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    manifest = json.loads(
        Path(args.manifest or (str(args.src) + ".manifest.json")).read_text())
    h = h5py.File(args.src, "r")
    dg = h[args.dataset]
    tags = [t for t in dg.keys() if t.endswith("__fresh")]
    (bf, bad), (gf, good) = pick(dg, manifest, tags)
    print(f"worst {bad}  {100 * bf:.0f}% of fragments wrap past 260 deg")
    print(f"best  {good}  {100 * gf:.0f}%")

    fig, axes = plt.subplots(2, 1 + N_FRAG, figsize=(3.3 * (1 + N_FRAG), 7.6))
    for tag, row, head, colour, frac in (
            (bad, 0, "WHAT THE SET CONTAINS NOW", "#b8342a", bf),
            (good, 1, "WHAT WE WANT IT TO CONTAIN", "#2e6f3e", gf)):
        m = manifest.get(tag, {})
        draw_block(axes[row], load_parts(dg[tag]),
                   f"{head} — {m.get('category', '?')}/"
                   f"{m.get('object', '?')[:8]}",
                   f"{100 * frac:.0f}% of its fragments go right round",
                   colour)

    fig.suptitle(
        "The same two breaks, assembled (left) and taken apart (right).\n"
        "Assembled, a ring and a sherd are both just a patch of colour. "
        "From above, one closes and one does not —\n"
        "and a fragment that closes would have to be slid over the pot to "
        "fit, which is not how a pot comes apart.", fontsize=12.5)
    fig.tight_layout(rect=(0, 0, 1, 0.87))
    fig.savefig(args.out, dpi=125)
    print(f"\n  wrote {args.out}")


if __name__ == "__main__":
    main()
