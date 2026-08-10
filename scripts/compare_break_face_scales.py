"""Does simulated wear produce break faces like a real worn sherd?

Now answerable, because the conservator's hand reassembly tells us exactly which
faces touch on a genuinely worn pot. Before that there was nothing real to
compare simulated wear against.

The conservator's framing, which this measures directly (2026-08-10):

    besides the teeth that lock into each other (fresh breakage), there is also
    the CURVE of the fractured surface, which can infer shared_faces for worn
    sherds.

Two different things live on a break face at two different scales:

    TEETH  fine asperities, the interlock of a fresh break. Sub-millimetre.
           This is what GARF reads, and what wear is expected to destroy.

    CURVE  the overall shape of the break surface -- how it bows, twists and
           runs across the sherd. Centimetre scale. A break face is not flat,
           and its curve should survive abrasion that erases the teeth.

If the curve survives on real worn material, then worn sherds still carry a
usable mating signal and GARF can be taught to read it. If it does not, no
training will help and the honest answer is that the information is gone.

And it tests our simulation against that: a wear model that suppresses BOTH
scales, or neither, does not resemble real wear however plausible its roughness
number looks.

METHOD. For each pair of touching fragments the contact band is taken from the
ground-truth assembly. The band surface is then smoothed at a series of radii,
and the deviation removed at each step is the amount of structure living at that
scale -- a roughness spectrum rather than a single figure. Comparing spectra
between a real worn pot and a simulated one shows whether wear was applied at
the right scale, which a single roughness number cannot.

Complementarity is measured too: how closely the two faces agree where they
meet. Teeth that interlock give a tight fit; a worn pair sits looser.

Usage:
  python scripts/compare_break_face_scales.py \
      --sets juglet_gt=dataset/juglet_gt.hdf5:juglet_gt \
             fresh=dataset/real_heldout_norm.hdf5:real_heldout_norm:ceramics__blue_pot
"""

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np
import trimesh
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wear_ops import apply_wear  # noqa: E402

# radii as a fraction of object size: teeth at the bottom, curve at the top
RADII = [0.004, 0.008, 0.016, 0.032, 0.064]


def load(spec):
    """'path:dataset[:object]' -> list of (verts, faces), assembled."""
    parts = spec.split(":")
    path, dsname = parts[0], parts[1]
    want = parts[2] if len(parts) > 2 else ""
    with h5py.File(path, "r") as h:
        ds = h[dsname]
        obj = want or sorted(ds.keys())[0]
        grp = ds[obj]
        g = grp["pieces"] if "pieces" in grp else grp
        keys = sorted(g.keys(), key=lambda s: int(s) if s.isdigit() else s)
        return obj, [(np.asarray(g[k]["vertices"][:], dtype=np.float64),
                      np.asarray(g[k]["faces"][:], dtype=np.int64)) for k in keys]


def scale_spectrum(pts, size):
    """Structure remaining at each scale, as a fraction of object size.

    At radius R the surface is replaced by the local mean of its neighbours
    within R. What that removes is the structure finer than R. Reporting the
    residual at increasing R gives the amount of relief living at each scale.
    """
    tree = cKDTree(pts)
    out = []
    for rf in RADII:
        R = rf * size
        idx = tree.query_ball_point(pts, R)
        keep = [i for i, nb in enumerate(idx) if len(nb) >= 4]
        if len(keep) < 50:
            out.append(float("nan"))
            continue
        sm = np.array([pts[idx[i]].mean(axis=0) for i in keep])
        out.append(float(np.linalg.norm(pts[keep] - sm, axis=1).mean()) / size * 100)
    return out


def analyse(name, pieces, band_frac=0.02, max_pts=40000, seed=0):
    allv = np.concatenate([v for v, _ in pieces], axis=0)
    size = float(np.linalg.norm(allv.max(0) - allv.min(0)))
    rng = np.random.default_rng(seed)
    tau = band_frac * size

    spectra, gaps, n_pairs = [], [], 0
    for i, (vi, _) in enumerate(pieces):
        for j, (vj, _) in enumerate(pieces):
            if j <= i:
                continue
            a = vi if len(vi) <= max_pts else vi[rng.choice(len(vi), max_pts, False)]
            b = vj if len(vj) <= max_pts else vj[rng.choice(len(vj), max_pts, False)]
            d, _ = cKDTree(b).query(a, workers=-1)
            band = a[d < tau]
            if len(band) < 300:
                continue                      # these two do not touch
            n_pairs += 1
            spectra.append(scale_spectrum(band, size))
            gaps.append(float(d[d < tau].mean()) / size * 100)

    if not spectra:
        print(f"  {name}: no touching pairs found")
        return None
    sp = np.nanmean(np.array(spectra), axis=0)
    print(f"  {name:<22s} {n_pairs:>3d} touching pairs   "
          + "  ".join(f"{v:6.3f}" for v in sp)
          + f"   gap {np.mean(gaps):.3f}%")
    return sp


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gt", required=True, help="path:dataset[:object] of the REAL worn pot")
    ap.add_argument("--sim", required=True, help="path:dataset[:object] to wear synthetically")
    args = ap.parse_args()

    print("Structure on the break face at each scale (% of object size).")
    print("Small radii = the TEETH of a fresh break; large = the CURVE of the face.")
    print()
    print(f"  {'set':<22s} {'pairs':>3s}   "
          + "  ".join(f"{100*r:5.1f}%" for r in RADII) + "     gap")
    print("  " + "-" * 78)

    name_gt, gt = load(args.gt)
    s_gt = analyse(f"REAL worn ({name_gt})", gt)

    name_s, sim = load(args.sim)
    s_fresh = analyse(f"fresh ({name_s})", sim)

    levels = [
        ("light",    dict(smoothing=0.3, smoothing_passes=1, recession=0.0006,
                          chip_count=2, chip_size=0.0022)),
        ("moderate", dict(smoothing=0.6, smoothing_passes=1, recession=0.0012,
                          chip_count=3, chip_size=0.0045)),
        ("heavy",    dict(smoothing=1.0, smoothing_passes=3, recession=0.0020,
                          chip_count=4, chip_size=0.0090)),
    ]
    sims = {}
    for lname, kw in levels:
        sims[lname] = analyse(f"simulated {lname}", apply_wear(sim, **kw))

    if s_gt is None or s_fresh is None:
        return

    print()
    print("  Which simulated level looks most like the real worn pot, per scale:")
    print(f"  {'scale':>8s} {'REAL':>8s} {'fresh':>8s} "
          + "".join(f"{k:>10s}" for k in sims))
    for k, rf in enumerate(RADII):
        row = f"  {100*rf:>7.1f}% {s_gt[k]:>8.3f} {s_fresh[k]:>8.3f} "
        row += "".join(f"{(sims[n][k] if sims[n] is not None else float('nan')):>10.3f}"
                       for n in sims)
        print(row)

    print()
    print("  Reading it:")
    print("   * If REAL is far below fresh at the SMALL radii but close to it at")
    print("     the LARGE ones, the teeth are gone and the curve survives -- so a")
    print("     worn sherd still carries a mating signal, and GARF can be taught")
    print("     to read the curve instead of the teeth.")
    print("   * A simulated level matches real wear only if it lands near REAL at")
    print("     EVERY scale. Matching the average while suppressing the wrong")
    print("     scale is what a single roughness number would hide.")


if __name__ == "__main__":
    main()
