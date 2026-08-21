"""Does a uniform recession cost the curve anything? It should not.

The conservator, 2026-08-20: "if erosion/recession is uniform, I don't see it
will affect the curve."

That is right, and it is worth stating why. A uniform offset along the surface
normal moves every point by the same amount, so the deviation of any point from
its neighbours is unchanged and relief at every scale survives exactly. Curve
damage can only come from the offset being UNEVEN.

And the earlier damage did come from that. Recession's depth was capped at 0.35x
the distance to the 48th nearest vertex, computed PER VERTEX -- a sampling-density
figure that varied across the surface, so the retreat varied with it. That cap is
now one number per piece from a real wall estimate.

This checks it before anything is built on it. Measured on Breaking Bad vessels,
which is where recession is the only tool that does anything, with blue_pot as a
fine-mesh control.

  gap     mean separation at the joins -- must OPEN, that is the point
  curve   normal relief at 1.6%, 3.2% and 6.4% of object -- must NOT move
  spread  how UNEVEN the retreat was, as a fraction of its own mean. This is
          the mechanism, not a symptom: it is the only way recession can cost
          the curve, so it is reported beside the damage rather than inferred
          from it.

THE INSTRUMENT, and why it is built this way. Two faults were found in the
earlier spectrum test and both apply here:

  The measurement window must not move with the dose. Re-selecting break-face
  points after wear picks a different, smaller set as the joins open, so the
  curve is compared between two different pieces of surface. The vertex indices
  are chosen ONCE on the fresh geometry and reused; recession moves vertices
  without changing their count, so they map one to one.

  The ruler must not be rebuilt after the thing it measures has changed. Local
  normals are fitted ONCE on the fresh band and reused for the worn one, so a
  change in relief cannot hide inside a co-rotating frame.

Radii are all above twice the point spacing on these meshes, so they are
readable; anything finer would be measuring the sampling.

PASS is curve within a few percent while the gap opens. If the curve moves, the
retreat is still uneven somewhere and the cause needs finding before this feeds
a training set.

Usage:
  python scripts/test_recession_curve.py --bbad dataset/breaking_bad_vol.hdf5 \
      --fine dataset/real_heldout_norm.hdf5 --render artifacts/recession_curve.png
"""

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wear_ops import _band_mask, _local_mean, recede_surface  # noqa: E402

RADII = [0.016, 0.032, 0.064]
DOSES = [0.0005, 0.0010, 0.0020]


def effective_pieces(sizes):
    p = np.asarray(sizes, float)
    p = p / p.sum()
    return 1.0 / float((p ** 2).sum())


def load_bbad(path, cats, want=4, min_eff=4.0):
    out = []
    with h5py.File(path, "r") as h:
        ev = h["everyday"]
        for c in cats:
            if c not in ev or len(out) >= want:
                continue
            for o in sorted(ev[c].keys()):
                node = ev[c][o]
                got = False
                for fr in sorted(node.keys()):
                    grp = node[fr]
                    keys = sorted(grp.keys())
                    if len(keys) < 3:
                        continue
                    if effective_pieces([grp[k]["vertices"].shape[0]
                                         for k in keys]) < min_eff:
                        continue
                    out.append((f"{c}/{o[:8]}",
                                [(np.asarray(grp[k]["vertices"][:], np.float64),
                                  np.asarray(grp[k]["faces"][:], np.int64))
                                 for k in keys]))
                    got = True
                    break
                if got or len(out) >= want:
                    break
    return out


def load_fine(path, dsname, obj):
    with h5py.File(path, "r") as h:
        grp = h[dsname][obj]
        g = grp["pieces"] if "pieces" in grp else grp
        keys = sorted(g.keys(), key=lambda s: int(s) if s.isdigit() else s)
        return [(np.asarray(g[k]["vertices"][:], np.float64),
                 np.asarray(g[k]["faces"][:], np.int64)) for k in keys]


def band_windows(pieces, size, seed=0, max_pts=60000):
    """Fixed break-face vertex indices, chosen once on the FRESH geometry.

    Returns (piece index, vertex indices) per join, plus the neighbour piece so
    the gap can be re-measured on the same vertices after wear.
    """
    rng = np.random.default_rng(seed)
    tau = 0.02 * size
    wins = []
    for i, (vi, _) in enumerate(pieces):
        for j, (vj, _) in enumerate(pieces):
            if j <= i:
                continue
            ai = (np.arange(len(vi)) if len(vi) <= max_pts
                  else rng.choice(len(vi), max_pts, False))
            bj = (np.arange(len(vj)) if len(vj) <= max_pts
                  else rng.choice(len(vj), max_pts, False))
            d, _ = cKDTree(vj[bj]).query(vi[ai], workers=-1)
            sel = d < tau
            if sel.sum() > 400:
                wins.append((i, ai[sel], j, bj))
    return wins


def gap_of(pieces, wins, size):
    """Mean join separation, on the FIXED vertex set."""
    gaps = []
    for i, ai, j, bj in wins:
        d, _ = cKDTree(pieces[j][0][bj]).query(pieces[i][0][ai], workers=-1)
        gaps.append(float(d.mean()) / size * 100)
    return float(np.mean(gaps)) if gaps else float("nan")


def frames_of(pieces, wins, k=24):
    """Local normals fitted ONCE on the fresh band, reused for every dose."""
    frames = []
    for i, ai, _, _ in wins:
        pts = pieces[i][0][ai]
        _, nb = cKDTree(pts).query(pts, k=min(k, len(pts)), workers=-1)
        P = pts[nb] - pts[:, None, :]
        nrm = np.linalg.eigh(np.einsum("nki,nkj->nij", P, P))[1][:, :, 0]
        frames.append(nrm)
    return frames


def curve_of(pieces, wins, frames, size):
    """Normal relief at the coarse radii, averaged over break faces."""
    rows = []
    for (i, ai, _, _), nrm in zip(wins, frames):
        pts = pieces[i][0][ai]
        row = []
        for rf in RADII:
            d = pts - _local_mean(pts, pts.copy(), rf * size)
            row.append(float(np.abs((d * nrm).sum(axis=1)).mean()) / size * 100)
        rows.append(row)
    return np.mean(np.array(rows), axis=0)


def retreat_of(fresh, worn, wins, frames, size):
    """Per-vertex retreat along the fresh normal, in percent of object size.

    This is the quantity the whole question turns on. Returned unbinned so its
    evenness can be looked at rather than summarised.
    """
    out = []
    for (i, ai, _, _), nrm in zip(wins, frames):
        dv = worn[i][0][ai] - fresh[i][0][ai]
        out.append((dv * nrm).sum(axis=1) / size * 100)
    return out


def run(name, pieces, render_to=None):
    allv = np.concatenate([v for v, _ in pieces], axis=0)
    size = float(np.linalg.norm(allv.max(0) - allv.min(0)))
    masks = [_band_mask(pieces, i, pieces[i][0]) for i in range(len(pieces))]
    wins = band_windows(pieces, size)
    if not wins:
        print(f"  {name:<22s} no measurable joins")
        return None
    frames = frames_of(pieces, wins)
    g0 = gap_of(pieces, wins, size)
    c0 = curve_of(pieces, wins, frames, size)
    print(f"  {name:<22s} {'fresh':<9s} {g0:>7.3f}% "
          + "".join(f"{v:>9.3f}" for v in c0))

    keep = None
    for dose in DOSES:
        worn = recede_surface(pieces, recession_frac=dose, masks=masks)
        gw = gap_of(worn, wins, size)
        cw = curve_of(worn, wins, frames, size)
        ret = np.concatenate(retreat_of(pieces, worn, wins, frames, size))
        m = float(np.abs(ret).mean())
        spread = float(np.abs(ret).std() / max(m, 1e-12))
        dc = 100 * (cw / np.maximum(c0, 1e-12) - 1)
        print(f"  {'':<22s} {100 * dose:<8.2f}% {gw:>7.3f}% "
              + "".join(f"{v:>9.3f}" for v in cw)
              + "   curve " + " ".join(f"{d:+.1f}%" for d in dc)
              + f"   gap {100 * (gw / g0 - 1):+.1f}%"
              + f"   retreat {m:.4f}% spread {spread:.2f}")
        if dose == DOSES[1]:
            keep = (name, pieces, worn, wins, frames, size, ret)

    if render_to is not None and keep is not None:
        return keep
    return None


def render(cases, out):
    """Look at the retreat itself, per vertex, before believing the table.

    THE VIEW MUST RESOLVE THE SCALE BEING TESTED. The first version of this
    drew a whole break face fresh against worn, and the two point clouds sat
    exactly on top of each other -- of course they did, the retreat is 0.09% of
    the object and the frame spanned 100% of it. A picture can answer the wrong
    question as convincingly as a statistic can. Four earlier views of wear
    failed the same way (docs/lessons.md).

    So the section is CROPPED to a few percent of object around one contact
    point, where a 0.09% movement is a visible fraction of the frame, and the
    join separation is drawn per vertex beside it rather than summarised.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    n = len(cases)
    fig, axes = plt.subplots(3, n, figsize=(4.4 * n, 11.0), squeeze=False)
    for col, (name, fresh, worn, wins, frames, size, ret) in enumerate(cases):
        i, ai, j, bj = wins[0]
        pts = fresh[i][0][ai]
        wp = worn[i][0][ai]
        nbr = fresh[j][0][bj]

        # TOP: a section CROPPED to where the movement is a visible fraction of
        # the frame. Centred on the contact point that moved most, so the panel
        # is showing the effect rather than a quiet corner of the face.
        ax = axes[0][col]
        seed = pts[int(np.argmax(np.abs(ret[:len(pts)])))] if len(ret) else pts[0]
        P = pts - seed
        near = np.abs(P).max(axis=1) < 0.06 * size
        Q = P[near]
        if len(Q) > 8:
            u = np.linalg.svd(Q.T @ Q)[0][:, 0]
            v = np.linalg.svd(Q.T @ Q)[0][:, 1]
        else:
            u, v = np.array([1.0, 0, 0]), np.array([0, 1.0, 0])
        w = np.cross(u, v)
        slab = near & (np.abs(P @ w) < 0.010 * size)
        for pset, colr, lab in ((pts, "#1f4e79", "fresh"),
                                (wp, "#c1440e", "worn")):
            D = pset - seed
            ax.scatter(D[slab] @ u / size * 100, D[slab] @ v / size * 100,
                       s=14, color=colr, label=lab, linewidths=0, alpha=0.75)
        Dn = nbr - seed
        nsel = (np.abs(Dn).max(axis=1) < 0.06 * size) & (np.abs(Dn @ w) < 0.010 * size)
        ax.scatter(Dn[nsel] @ u / size * 100, Dn[nsel] @ v / size * 100,
                   s=8, color="#999999", label="neighbour", linewidths=0, alpha=0.5)
        ax.set_aspect("equal")
        ax.tick_params(labelsize=7)
        ax.set_xlabel("% of object", fontsize=8)
        ax.set_title(f"{name}\nsection at the contact, cropped so 0.1% shows",
                     fontsize=9)
        ax.legend(fontsize=7, markerscale=1.6)

        # MIDDLE: the join separation itself, per vertex, fresh against worn.
        # This is the claim "the join opened", drawn rather than averaged.
        ax = axes[1][col]
        d0, _ = cKDTree(nbr).query(pts, workers=-1)
        dw, _ = cKDTree(worn[j][0][bj]).query(wp, workers=-1)
        bins = np.linspace(0, max(np.percentile(dw, 99), 1e-9) / size * 100, 70)
        ax.hist(d0 / size * 100, bins=bins, color="#1f4e79", alpha=0.65,
                label=f"fresh, mean {d0.mean() / size * 100:.3f}%")
        ax.hist(dw / size * 100, bins=bins, color="#c1440e", alpha=0.65,
                label=f"worn, mean {dw.mean() / size * 100:.3f}%")
        ax.set_xlabel("distance to the mating fragment, % of object", fontsize=8)
        ax.set_ylabel("vertices", fontsize=8)
        ax.tick_params(labelsize=7)
        ax.legend(fontsize=7)
        ax.set_title("did the join open", fontsize=9)

        # BOTTOM: the retreat, per vertex, unbinned. If it is uniform this is a
        # spike; a wide spread IS the mechanism that costs the curve.
        ax = axes[2][col]
        ax.hist(np.abs(ret), bins=80, color="#4a7c59")
        m = float(np.abs(ret).mean())
        ax.axvline(m, color="#c1440e", lw=1.2)
        ax.set_xlabel("retreat along the fresh normal, % of object", fontsize=8)
        ax.set_ylabel("vertices", fontsize=8)
        ax.tick_params(labelsize=7)
        ax.set_title(f"was the retreat even -- mean {m:.4f}%,  spread "
                     f"{np.abs(ret).std() / max(m, 1e-12):.2f} of mean",
                     fontsize=9)

    fig.suptitle(
        "Uniform recession: does it open the join without touching the curve?\n"
        "Each panel is drawn at a scale that can actually resolve a 0.1% "
        "movement.", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(out, dpi=140)
    print(f"\n  wrote {out}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bbad", required=True)
    ap.add_argument("--fine", default="")
    ap.add_argument("--fine-dataset", default="real_heldout_norm")
    ap.add_argument("--render", default="")
    args = ap.parse_args()

    print("Uniform recession should open the joins and leave the curve alone.")
    print()
    print(f"  {'object':<22s} {'dose':<9s} {'gap':>8s} "
          + "".join(f"{100 * r:>8.1f}%" for r in RADII))
    print("  " + "-" * 110)

    cases = []
    want = args.render or None
    for name, pieces in load_bbad(args.bbad, ["Vase", "Bowl", "Cup", "Mug"]):
        c = run(f"bbad {name}", pieces, render_to=want)
        if c:
            cases.append(c)
    if args.fine:
        for obj in ["blue_pot"]:
            c = run(f"fine {obj}", load_fine(args.fine, args.fine_dataset, obj),
                    render_to=want)
            if c:
                cases.append(c)

    print()
    print("  PASS is the gap opening while the curve holds within a few percent.")
    print("  If the curve moves, the retreat is still uneven somewhere.")

    if args.render and cases:
        render(cases[:3], args.render)


if __name__ == "__main__":
    main()
