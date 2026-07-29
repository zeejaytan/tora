"""Judge a reassembly the way a potter's wheel does: is it a surface of revolution?

First attempt at ground-truth-free selection failed (job 28287458): crude
geometric proxies -- contact, compactness, connectivity -- cannot rank a single
pot's own attempts (all |rho| < 0.15, none significant). The reason is now
clear: every attempt at one pot uses the SAME fragments, so they are all about
equally compact and equally touching. Those measures test *togetherness*, not
*whether the shape is right*.

What a conservator actually judges is different in kind. A wheel-thrown vessel is
a SURFACE OF REVOLUTION: every fragment must lie on one common axis, at a radius
that varies smoothly with height, with roughly constant wall thickness. A correct
reassembly satisfies that; a wrong one cannot, however tightly its pieces are
packed.

These are also precisely the form cues that SURVIVE abrasion (C2b: form channel
0.88 under wear vs break-surface 0.71), which is why the wear-trained model
improved. Selecting on them is consistent with the mechanism, not a fresh guess.

Features (all ground-truth-free):
  axis_residual     scatter of radius about the fitted profile — low = a clean
                    surface of revolution
  profile_smooth    how smoothly radius varies with height — a real vessel
                    profile is smooth, a wrong assembly is stepped
  thickness_cv      variation in wall thickness — pottery is near-constant
  radial_gap        largest hole in angular coverage around the axis — a
                    correctly closed vessel wraps its axis

Usage:
  from vessel_features import vessel_features
  feats = vessel_features(points)         # (N,3) assembled cloud
"""

import numpy as np


def _fit_axis(pts: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Estimate the vessel's axis of revolution.

    For a surface of revolution the axis is the direction of LEAST variance of
    the surface normals' spread — practically, the principal axis of the point
    cloud is a good estimate for a pot standing on its base, so use PCA and take
    the component that best explains height rather than girth.
    """
    c = pts.mean(0)
    x = pts - c
    # principal axes; for a vessel the axis of revolution is the one where the
    # cross-sectional spread is most circular
    _, _, vt = np.linalg.svd(x, full_matrices=False)
    best, best_score = vt[0], -np.inf
    for ax in vt:
        h = x @ ax
        perp = x - np.outer(h, ax)
        r = np.linalg.norm(perp, axis=1)
        ang = np.arctan2(perp[:, 1] if abs(ax[1]) < 0.9 else perp[:, 0],
                         perp[:, 2] if abs(ax[2]) < 0.9 else perp[:, 0])
        # circular symmetry: radius should be roughly independent of angle
        bins = np.clip(((ang + np.pi) / (2 * np.pi) * 12).astype(int), 0, 11)
        means = [r[bins == b].mean() for b in range(12) if (bins == b).sum() > 5]
        if len(means) < 4:
            continue
        score = -float(np.std(means) / (np.mean(means) + 1e-9))
        if score > best_score:
            best_score, best = score, ax
    return c, best / (np.linalg.norm(best) + 1e-12)


def vessel_features(pts: np.ndarray, n_bands: int = 12) -> dict:
    """Surface-of-revolution quality of an assembled point cloud. No ground truth."""
    c, ax = _fit_axis(pts)
    x = pts - c
    h = x @ ax                                   # height along the axis
    perp = x - np.outer(h, ax)
    r = np.linalg.norm(perp, axis=1)             # radius from the axis
    scale = float(np.linalg.norm(pts.max(0) - pts.min(0))) + 1e-9

    # slice into height bands; within a band a true vessel has near-constant radius
    lo, hi = np.percentile(h, 2), np.percentile(h, 98)
    edges = np.linspace(lo, hi, n_bands + 1)
    resid, prof, cover = [], [], []
    for i in range(n_bands):
        m = (h >= edges[i]) & (h < edges[i + 1])
        if m.sum() < 20:
            continue
        rb = r[m]
        resid.append(float(np.std(rb) / (np.mean(rb) + 1e-9)))
        prof.append(float(np.mean(rb)))
        # angular coverage around the axis within this band
        u = perp[m]
        e1 = np.array([1.0, 0.0, 0.0])
        if abs(ax @ e1) > 0.9:
            e1 = np.array([0.0, 1.0, 0.0])
        e1 = e1 - ax * (ax @ e1)
        e1 /= np.linalg.norm(e1) + 1e-12
        e2 = np.cross(ax, e1)
        ang = np.arctan2(u @ e2, u @ e1)
        occ = np.zeros(16, bool)
        occ[np.clip(((ang + np.pi) / (2 * np.pi) * 16).astype(int), 0, 15)] = True
        # largest run of empty angular sectors = biggest hole in the wall
        gap, run = 0, 0
        for k in list(occ) * 2:
            run = 0 if k else run + 1
            gap = max(gap, run)
        cover.append(gap / 16.0)

    if len(prof) < 4:
        return {"axis_residual": 1.0, "profile_smooth": 1.0,
                "thickness_cv": 1.0, "radial_gap": 1.0}

    prof = np.array(prof)
    # smoothness of the profile curve: second difference, scaled
    d2 = np.diff(prof, 2) if len(prof) > 2 else np.array([0.0])
    profile_smooth = float(np.mean(np.abs(d2)) / (np.mean(prof) + 1e-9))

    # wall thickness proxy: spread of radius within a band already captures
    # thickness plus misplacement; report its variation across bands
    thickness_cv = float(np.std(resid) / (np.mean(resid) + 1e-9))

    return {
        "axis_residual": float(np.mean(resid)),
        "profile_smooth": profile_smooth,
        "thickness_cv": thickness_cv,
        "radial_gap": float(np.mean(cover)),
    }
