"""U20 ticket 01: the join fingerprint -- how a set of reassembled sherds' joins vary.

pr-workspace `.scratch/uneven-wear/issues/01-juglet-join-fingerprint.md`, question U20.

WHAT IT MEASURES. On each object (the Juglet's hand reassembly `juglet_gt`, and round-3 CSC
copies beside it), per join and pooled:

  gap           p10 / p50 / p90 of the distance from a join dot to the neighbouring sherd's
                SURFACE, in % of the object's bounding-box diagonal (the unit sherd-worn doses
                in, and the unit of `write_u10_worn.py --measure`) and in mm;
  touching      share of join dots whose gap is at most one sampling spacing (what the scan
                cannot tell from contact);
  corr. length  the distance along the join over which the gap stays alike: the first lag at
                which the gap's correlation between two join dots falls below 1/e (mm, and in
                sampling spacings). A join opened by a rigid tilt reads about a third of the
                join's length (self-test: 2.6 mm on a 10 mm ramp); patchy wear reads about a
                quarter of the patch wavelength (0.55 mm for 2 mm ribs); noise about a spacing;
  per sherd     each sherd's median gap and touching share, and how much those differ from
                sherd to sherd (p90/p10 of the per-sherd medians, and their coefficient of
                variation).

ONE RULER FOR EVERY OBJECT. Mesh vertices are not used as dots: the CSC copies' break faces
are triangulated at 1.3-8.9 mm while their skins are fine, so vertex dots would weigh the
skins and say nothing about the face. Every sherd is instead sampled uniformly over its area at
the same RELATIVE spacing, `SPACING_FRAC` of the object's longest side -- the Juglet's own scan
spacing (0.295 mm pooled nearest-dot on 65 mm, tora `.scratch/wear-ruler-v2/brief.md`). So the
Juglet is read at its own scan resolution and every CSC pot at the same fraction of its size.

WHICH DOTS ARE JOIN. A sampled dot on sherd i is a join dot when another sherd's surface lies
within `--cut` of it (2% of the diagonal, `write_u10_worn.py`'s `--gap-cut`) AND that surface
faces back at it (dot of the two face normals below `TWIN_DOT`): a break face against its
twin, not the skin beside the join, whose neighbour skin points the same way.

OVERLAP IS EXCLUDED, NOT MEASURED (conservator, 2026-11-07: the Juglet's overlap is most likely
manual error in the hand-set pose). A dot is inside when the neighbour's generalised
winding number there is over one half (closed meshes; the closest face's sign was wrong on
30-40% of the CSC copies' join dots in job 34481077, at rim edges of their large break-face
triangles), unless it lies within 1% of a scan spacing of the surface (touching: the clean
copies' twin faces coincide). Inside dots and every dot within one scan spacing of one are
dropped. The share of join left is printed; under a third, the fingerprint is called weak.
The inside test has its own control: join dots pushed a quarter spacing into their own sherd
must read inside, pushed out must read outside, at 95% or better, else nothing is read. Since the same pose error that pushes sherds into each other opens gaps beside
the overlap, the Juglet's spread is an UPPER bound.

The Juglet is also reported without the joins of sherds 2 and 7 (`--drop-sherds`), which
need 5-11 degrees to clear the overlap (job 30422501) and may carry most of the pose error.

THE PICTURE. For two joins per object (the longest kept join, and the most spread one), three
cuts straight across the join through both meshes (black this sherd, blue the neighbour), at a
scale where 0.1 mm is at least 10 px (checked and printed), and one face-on panel with each
join dot coloured by its gap and excluded dots grey.

    python scripts/measure_join_fingerprint.py --selftest
    python scripts/measure_join_fingerprint.py --out DIR \
        --object juglet=<juglet_gt.hdf5>:juglet_gt::65 \
        --object clean_p148_d00=<csc_whole20miss_clean.hdf5>:csc_whole20miss_clean:p148_d00 ...

`--object NAME=FILE:GROUP:TAG[:LONGEST_MM]`: TAG empty takes the first object in the group;
LONGEST_MM scales the object so its longest side is that many mm (the Juglet); without it,
the group's `mm_per_unit` attribute is used (CSC copies).
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

SPACING_FRAC = 0.295 / 65.0   # the Juglet's scan spacing, as a fraction of its longest side
TWIN_DOT = -0.5               # neighbour's face normal must point back at the dot
CUT_FRAC = 0.02               # write_u10_worn.py --gap-cut
WEAK_SHARE = 1.0 / 3.0
MIN_JOIN = 100                # kept dots for a join (or a sherd) to get its own row


# ---------------------------------------------------------------- geometry

def closest_on_triangles(p, a, b, c):
    """Closest point on triangle (a, b, c) to p; all (..., 3), broadcast (Ericson, RTCD 5.1.5)."""
    ab, ac, ap = b - a, c - a, p - a
    d1, d2 = (ab * ap).sum(-1), (ac * ap).sum(-1)
    bp = p - b
    d3, d4 = (ab * bp).sum(-1), (ac * bp).sum(-1)
    cp = p - c
    d5, d6 = (ab * cp).sum(-1), (ac * cp).sum(-1)
    va, vb, vc = d3 * d6 - d5 * d4, d5 * d2 - d1 * d6, d1 * d4 - d3 * d2
    with np.errstate(divide="ignore", invalid="ignore"):
        den = va + vb + vc
        den = np.where(np.abs(den) < 1e-30, 1e-30, den)
        q = a + ab * (vb / den)[..., None] + ac * (vc / den)[..., None]
        t_bc = (d4 - d3) / np.where(np.abs((d4 - d3) + (d5 - d6)) < 1e-30, 1e-30,
                                    (d4 - d3) + (d5 - d6))
        t_ac = d2 / np.where(np.abs(d2 - d6) < 1e-30, 1e-30, d2 - d6)
        t_ab = d1 / np.where(np.abs(d1 - d3) < 1e-30, 1e-30, d1 - d3)
    cases = [  # later rows override earlier ones: widest region first, vertices last
        ((va <= 0) & (d4 - d3 >= 0) & (d5 - d6 >= 0), b + (c - b) * t_bc[..., None]),
        ((vb <= 0) & (d2 >= 0) & (d6 <= 0), a + ac * t_ac[..., None]),
        ((d6 >= 0) & (d5 <= d6), c),
        ((vc <= 0) & (d1 >= 0) & (d3 <= 0), a + ab * t_ab[..., None]),
        ((d3 >= 0) & (d4 <= d3), b), ((d1 <= 0) & (d2 <= 0), a)]
    for m, r in cases:
        q = np.where(m[..., None], np.broadcast_to(r, q.shape), q)
    return q


class Surface:
    """A closed sherd mesh, outward wound, that answers 'closest point, which face'."""

    def __init__(self, v, f):
        tri = v[f]
        vol = float(np.einsum("ij,ij->i", tri[:, 0], np.cross(tri[:, 1], tri[:, 2])).sum())
        if vol < 0:                       # make it outward wound
            f = f[:, ::-1].copy()
            tri = v[f]
        self.v, self.f, self.tri = v, f, tri
        fn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        self.area_f = 0.5 * np.linalg.norm(fn, axis=1)
        self.fn = fn / (np.linalg.norm(fn, axis=1, keepdims=True) + 1e-30)
        self.vtree = cKDTree(v)
        self.ctree = cKDTree(tri.mean(axis=1))
        flat = f.ravel()
        order = np.argsort(flat, kind="stable")
        start = np.searchsorted(flat[order], np.arange(len(v) + 1))
        width = int(np.diff(start).max())
        adj = np.full((len(v), width), -1)
        for r in range(width):
            has = start[:-1] + r < start[1:]
            adj[has, r] = order[start[:-1][has] + r] // 3
        self.adj = adj
        self.volume = abs(vol) / 6.0
        self.area = float(self.area_f.sum())

    def closest(self, p, kv=6, kc=8, chunk=4000):
        """(unsigned distance, signed distance, face index) for each point."""
        n = len(p)
        dist, sgn, face = np.empty(n), np.empty(n), np.empty(n, np.int64)
        kv, kc = min(kv, len(self.v)), min(kc, len(self.f))
        for s in range(0, n, chunk):
            q = p[s:s + chunk]
            _, iv = self.vtree.query(q, k=kv)
            _, ic = self.ctree.query(q, k=kc)
            cand = np.concatenate([self.adj[iv.reshape(len(q), -1)].reshape(len(q), -1),
                                   ic.reshape(len(q), -1)], axis=1)
            ok = cand >= 0
            cf = np.where(ok, cand, 0)
            t = self.tri[cf]
            cp = closest_on_triangles(q[:, None], t[..., 0, :], t[..., 1, :], t[..., 2, :])
            d = np.linalg.norm(q[:, None] - cp, axis=-1)
            d = np.where(ok, d, np.inf)
            k = d.argmin(axis=1)
            r = np.arange(len(q))
            fi = cf[r, k]
            dist[s:s + chunk] = d[r, k]
            face[s:s + chunk] = fi
            side = np.einsum("ij,ij->i", q - cp[r, k], self.fn[fi])
            sgn[s:s + chunk] = np.where(side < 0, -d[r, k], d[r, k])
        return dist, sgn, face

    def sample(self, count, rng):
        w = self.area_f / self.area_f.sum()
        fi = rng.choice(len(self.f), size=int(count), p=w)
        r1, r2 = rng.random(len(fi)), rng.random(len(fi))
        flip = r1 + r2 > 1
        r1, r2 = np.where(flip, 1 - r1, r1), np.where(flip, 1 - r2, r2)
        t = self.tri[fi]
        pts = t[:, 0] + r1[:, None] * (t[:, 1] - t[:, 0]) + r2[:, None] * (t[:, 2] - t[:, 0])
        return pts, self.fn[fi]


def winding(q, tri, budget=4_000_000):
    """Generalised winding number (Van Oosterom-Strackee); ~1 inside a closed mesh, ~0 out."""
    w = np.empty(len(q))
    step = max(1, budget // len(tri))
    for s in range(0, len(q), step):
        d = tri[None] - q[s:s + step, None, None, :]
        a, b, c = d[:, :, 0], d[:, :, 1], d[:, :, 2]
        la, lb, lc = (np.linalg.norm(x, axis=2) for x in (a, b, c))
        num = np.einsum("mfi,mfi->mf", a, np.cross(b, c))
        den = (la * lb * lc + np.einsum("mfi,mfi->mf", a, b) * lc +
               np.einsum("mfi,mfi->mf", b, c) * la + np.einsum("mfi,mfi->mf", c, a) * lb)
        w[s:s + step] = np.arctan2(num, den).sum(axis=1) / (2.0 * np.pi)
    return w


# ---------------------------------------------------------------- measurement

def corr_length(pts, g, sp, rng, n_max=3000, max_lag=120):
    """First lag (mm) at which the gap's correlation between two dots falls below 1/e."""
    if len(g) > n_max:
        s = rng.choice(len(g), n_max, replace=False)
        pts, g = pts[s], g[s]
    var = float(g.var())
    if var <= (0.01 * sp) ** 2 or len(g) < 50:
        return dict(mm=None, spacings=None, note="no variation")
    pr = cKDTree(pts).query_pairs(max_lag * sp, output_type="ndarray")
    if not len(pr):
        return dict(mm=None, spacings=None, note="no pairs")
    lag = np.linalg.norm(pts[pr[:, 0]] - pts[pr[:, 1]], axis=1)
    prod = (g[pr[:, 0]] - g.mean()) * (g[pr[:, 1]] - g.mean())
    b = np.minimum((lag / sp).astype(int), max_lag - 1)
    cnt = np.bincount(b, minlength=max_lag)
    c = np.bincount(b, weights=prod, minlength=max_lag) / np.maximum(cnt, 1) / var
    good = cnt >= 30
    centres = (np.arange(max_lag) + 0.5) * sp
    below = np.where(good & (c < np.exp(-1)))[0]
    if not len(below):
        return dict(mm=None, spacings=None, note="stays above 1/e to " +
                    format(max_lag * sp, ".1f") + " mm")
    k = int(below[0])
    prev = [i for i in range(k) if good[i]]
    if prev:   # linear interpolation between the last bin above and the first below
        p = prev[-1]
        x = centres[p] + (c[p] - np.exp(-1)) / max(c[p] - c[k], 1e-12) * (centres[k] - centres[p])
    else:
        x = centres[k]
    return dict(mm=float(x), spacings=float(x / sp), note="")


def pct(x, q=(10, 50, 90)):
    return [float(v) for v in np.percentile(x, q)] if len(x) else [None] * len(q)


def load_object(spec):
    import h5py
    name, rest = spec.split("=", 1)
    parts = rest.split(":")
    path, group, tag = parts[0], parts[1], parts[2] if len(parts) > 2 else ""
    longest = float(parts[3]) if len(parts) > 3 and parts[3] else None
    with h5py.File(path, "r") as h:
        tags = sorted(t for t in h[group] if "pieces" in h[group][t])
        tag = tag or tags[0]
        if tag not in h[group]:
            raise SystemExit(f"{name}: {tag} not in {path}:{group}; there are {tags}")
        g = h[group][tag]
        keys = sorted(g["pieces"].keys(), key=lambda s: (len(s), s))
        V = [np.asarray(g["pieces"][k]["vertices"][:], np.float64) for k in keys]
        F = [np.asarray(g["pieces"][k]["faces"][:], np.int64) for k in keys]
        names = ([x.decode() if isinstance(x, bytes) else str(x) for x in g["pieces_names"][()]]
                 if "pieces_names" in g else keys)
        allv = np.concatenate(V)
        if longest is not None:
            mm = longest / float((allv.max(0) - allv.min(0)).max())
            how = f"longest side set to {longest} mm"
        else:
            mm = float(g.attrs["mm_per_unit"])
            how = "mm_per_unit attribute"
    return dict(name=name, path=path, group=group, tag=tag, keys=keys, names=names,
                pieces=[(v * mm, f) for v, f in zip(V, F)], mm_per_unit=mm, scale_from=how)


def measure(obj, cut_frac=CUT_FRAC, seed=0, drop=(), n_control=3000):
    """Join dots of every sherd, signed gaps, exclusion, and the fingerprint (all in mm)."""
    rng = np.random.default_rng(seed)
    S = [Surface(v, f) for v, f in obj["pieces"]]
    allv = np.concatenate([s.v for s in S])
    longest = float((allv.max(0) - allv.min(0)).max())
    D = float(np.linalg.norm(allv.max(0) - allv.min(0)))
    sp_t = SPACING_FRAC * longest
    cut = cut_frac * D
    walls = [2.0 * s.volume / s.area for s in S]
    dots = []
    for i, s in enumerate(S):
        # area / spacing^2 random dots: about four per scan-spacing square (median nearest dot
        # about half the scan spacing), so short joins still carry enough dots to read. Denser
        # than the scan only interpolates its triangles; every threshold stays the scan spacing.
        n = int(np.ceil(s.area / sp_t ** 2))
        p, nrm = s.sample(n, rng)
        best = np.full(len(p), np.inf)
        sgn, own = np.full(len(p), np.nan), np.full(len(p), -1)
        nq = np.zeros_like(p)
        for j, t in enumerate(S):
            if j == i:
                continue
            near = t.vtree.query(p, distance_upper_bound=cut + 2 * np.sqrt(
                t.area_f.max() * 2))[0] < np.inf
            near &= np.all((p > t.v.min(0) - cut) & (p < t.v.max(0) + cut), axis=1)
            if not near.any():
                continue
            d, sd, fi = t.closest(p[near])
            idx = np.where(near)[0]
            better = d < best[idx]
            ii = idx[better]
            best[ii], sgn[ii], own[ii] = d[better], sd[better], j
            nq[ii] = t.fn[fi[better]]
        twin = np.einsum("ij,ij->i", nrm, nq)
        join = (best <= cut) & (twin < TWIN_DOT)
        dots.append(dict(p=p, n=nrm, d=best, s=sgn, own=own, join=join, count=len(p)))
    sp = float(np.median(np.concatenate([
        cKDTree(x["p"]).query(x["p"][rng.choice(len(x["p"]), min(4000, len(x["p"])),
                                                   replace=False)], k=2)[0][:, 1]
        for x in dots])))
    # INSIDE is decided by the generalised winding number of the neighbour, not by the sign of
    # its closest face: job 34481077 found that sign wrong on 30-40% of the CSC copies' join dots
    # (their break faces are a few large triangles, so the closest feature is often a rim edge
    # whose skin face points sideways). A dot within EPS of the surface is touching, not inside:
    # the clean copies' twin faces coincide exactly, where the winding number is 0.5 either way.
    eps = 0.01 * sp_t
    agree = tot = 0
    for i, x in enumerate(dots):
        inside = np.zeros(len(x["p"]), bool)
        for j in np.unique(x["own"][x["join"]]):
            k = np.where(x["join"] & (x["own"] == j) & (x["d"] > eps))[0]
            if len(k):
                w = winding(x["p"][k], S[int(j)].tri) > 0.5
                inside[k] = w
                agree += int(np.sum(w == (x["s"][k] < 0)))
                tot += len(k)
        x["inside"] = inside
        x["s"] = np.where(inside, -x["d"], x["d"])
    # exclusion: inside the neighbour, and every dot within one scan spacing of an inside dot
    for x in dots:
        near_in = np.zeros(len(x["p"]), bool)
        if x["inside"].any():
            near_in = cKDTree(x["p"][x["inside"]]).query(
                x["p"], distance_upper_bound=sp_t)[0] < np.inf
        x["kept"] = x["join"] & ~x["inside"] & ~near_in

    # CONTROL on the winding number itself: each sherd's own join dots pushed a quarter scan
    # spacing in along its own normal must read inside it, pushed out must read outside, >= 95%
    ins_ok, out_ok = [], []
    for i, x in enumerate(dots):
        k = np.where(x["join"])[0]
        if not len(k):
            continue
        k = rng.choice(k, min(len(k), max(1, n_control // len(S))), replace=False)
        ins_ok.append(winding(x["p"][k] - 0.25 * sp_t * x["n"][k], S[i].tri) > 0.5)
        out_ok.append(winding(x["p"][k] + 0.25 * sp_t * x["n"][k], S[i].tri) < 0.5)
    control = None
    if ins_ok:
        pin = 100.0 * float(np.mean(np.concatenate(ins_ok)))
        pout = 100.0 * float(np.mean(np.concatenate(out_ok)))
        control = dict(pushed_in_reads_inside_pct=pin, pushed_out_reads_outside_pct=pout,
                       checked=int(sum(len(a) for a in ins_ok)),
                       face_sign_agrees_pct=100.0 * agree / max(tot, 1),
                       trusted=bool(pin >= 95.0 and pout >= 95.0))

    def summarise(sel_pairs):
        rows, pool = [], []
        per_sherd = {}
        for (i, j) in sel_pairs:
            parts = []
            for a, b in ((i, j), (j, i)):
                x = dots[a]
                m = x["join"] & (x["own"] == b)
                parts.append((a, m))
            jn = sum(int(m.sum()) for _, m in parts)
            ins = sum(int((dots[a]["inside"] & m).sum()) for a, m in parts)
            kept = [(a, m & dots[a]["kept"]) for a, m in parts]
            kn = sum(int(m.sum()) for _, m in kept)
            g = np.concatenate([dots[a]["d"][m] for a, m in kept])
            P = np.concatenate([dots[a]["p"][m] for a, m in kept])
            for a, m in kept:
                per_sherd.setdefault(a, []).append(dots[a]["d"][m])
            pool.append(g)
            if jn == 0:
                continue
            ext = 0.0
            if len(P) > 2:
                c = P - P.mean(0)
                ax = np.linalg.eigh(c.T @ c)[1][:, -1]
                ext = float(np.ptp(c @ ax))
            r = dict(join=f"{i}-{j}", dots=jn, inside_pct=100.0 * ins / jn,
                     kept=kn, kept_pct=100.0 * kn / jn, length_mm=ext)
            if kn >= MIN_JOIN:
                r.update(gap_mm=pct(g), gap_pct_diag=[v / D * 100 for v in pct(g)],
                         touching_pct=100.0 * float(np.mean(g <= sp_t)),
                         corr=corr_length(P, g, sp, rng))
            rows.append(r)
        g = np.concatenate(pool) if pool else np.zeros(0)
        jd = sum(r["dots"] for r in rows)
        sh = []
        for a in sorted(per_sherd):
            x = np.concatenate(per_sherd[a])
            if len(x) >= MIN_JOIN:
                sh.append(dict(sherd=a, name=obj["names"][a], kept=int(len(x)),
                               median_mm=float(np.median(x)),
                               touching_pct=100.0 * float(np.mean(x <= sp_t))))
        med = np.array([r["median_mm"] for r in sh])
        corr_all = [r["corr"]["mm"] for r in rows if r.get("corr") and r["corr"]["mm"]]
        pooled = dict(
            join_dots=jd, kept=int(len(g)), kept_pct=100.0 * len(g) / max(jd, 1),
            inside_pct=100.0 * sum(r["dots"] * r["inside_pct"] / 100 for r in rows) / max(jd, 1),
            gap_mm=pct(g), gap_pct_diag=[v / D * 100 if v is not None else None
                                         for v in pct(g)],
            p90_over_p10=(float(np.percentile(g, 90) / np.percentile(g, 10))
                          if len(g) and np.percentile(g, 10) > 0.1 * sp_t else None),
            touching_pct=100.0 * float(np.mean(g <= sp_t)) if len(g) else None,
            corr_mm_median_over_joins=float(np.median(corr_all)) if corr_all else None,
            joins_with_corr=f"{len(corr_all)} of {sum(1 for r in rows if 'corr' in r)}",
            sherd_median_p90_over_p10=(float(np.percentile(med, 90) / np.percentile(med, 10))
                                       if len(med) >= 3 and np.percentile(med, 10) > 0.1 * sp_t
                                       else None),
            sherd_median_cv=float(med.std() / med.mean()) if len(med) >= 3 else None)
        pooled["weak"] = bool(pooled["kept_pct"] < 100 * WEAK_SHARE)
        return dict(pooled=pooled, joins=rows, sherds=sh)

    pairs = sorted({tuple(sorted((i, int(j)))) for i, x in enumerate(dots)
                    for j in np.unique(x["own"][x["join"]])})
    out = dict(object=obj["name"], file=obj["path"], group=obj["group"], tag=obj["tag"],
               sherds=len(S), mm_per_unit=obj["mm_per_unit"], scale_from=obj["scale_from"],
               longest_mm=longest, diag_mm=D, wall_mm_median=float(np.median(walls)),
               spacing_target_mm=sp_t, spacing_mm=sp, cut_mm=cut,
               dots=int(sum(x["count"] for x in dots)), control=control,
               all=summarise(pairs))
    if drop:
        out["without"] = dict(drop_sherds=list(drop), **summarise(
            [p for p in pairs if p[0] not in drop and p[1] not in drop]))
    return out, S, dots


# ---------------------------------------------------------------- picture

def render(obj, res, S, dots, out_png, n_rows=2):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import trimesh
    from matplotlib.collections import LineCollection

    rows = [r for r in res["all"]["joins"] if "gap_mm" in r]
    if not rows:
        print("  render: no join with enough kept dots; nothing drawn")
        return None
    longest = max(rows, key=lambda r: r["kept"])
    spread = max(rows, key=lambda r: (r["gap_mm"][2] - r["gap_mm"][0]))
    pick = [longest] + ([spread] if spread is not longest and n_rows > 1 else [])
    wall = res["wall_mm_median"]
    sp = res["spacing_mm"]
    fig, axes = plt.subplots(len(pick), 4, figsize=(26, 8.5 * len(pick)), squeeze=False,
                             gridspec_kw=dict(width_ratios=[1, 1, 1, 1.6]))
    out = []
    for row, r in enumerate(pick):
        i, j = map(int, r["join"].split("-"))
        x = dots[i]
        m = x["join"] & (x["own"] == j)
        P, N = x["p"][m], x["n"][m]
        kept = x["kept"][m]
        g = x["d"][m]
        c0 = P[kept][np.argmin(np.linalg.norm(P[kept] - np.median(P[kept], 0), axis=1))] \
            if kept.any() else P[0]
        near = np.linalg.norm(P - c0, axis=1) < max(3.0, 1.5 * wall)
        loc = P[near] - P[near].mean(0)
        vec = np.linalg.eigh(loc.T @ loc)[1]
        n0, e_al = vec[:, 0], vec[:, 2]
        if np.mean(N[near] @ n0) < 0:
            n0 = -n0
        Fr = np.column_stack([e_al, np.cross(n0, e_al), n0])
        X = max(1.5, 1.2 * r["gap_mm"][2] + 0.3)
        H = wall / 2.0 + 0.8
        for col, a in enumerate((-wall, 0.0, wall)):
            ax = axes[row, col]
            for s, colour in ((S[i], "k"), (S[j], "#2e6fd1")):
                tm = trimesh.Trimesh(s.v, s.f, process=False)
                seg = trimesh.intersections.mesh_plane(tm, Fr[:, 0], c0 + Fr[:, 0] * a)
                if len(seg) == 0:
                    continue
                s2 = (np.asarray(seg) - c0) @ Fr
                keep = np.all((np.abs(s2[:, :, 2]) < X + 0.5) & (np.abs(s2[:, :, 1]) < H + 0.5),
                              axis=1)
                ax.add_collection(LineCollection(s2[keep][:, :, [2, 1]], colors=colour, lw=1.3))
            ax.set_xlim(-X, X)
            ax.set_ylim(-H, H)
            ax.set_aspect("equal")
            ax.axvline(0, color="0.85", lw=0.6)
            ax.set_title(f"{res['object']}: sherd {i} (black) against {j} (blue),\ncut at "
                         f"{a:+.1f} mm along the join", fontsize=10)
            ax.set_xlabel("mm, out of this sherd's break face ->", fontsize=9)
            if col == 0:
                ax.set_ylabel(f"mm, across the wall (median wall {wall:.2f} mm)", fontsize=9)
        ax = axes[row, 3]
        q = (P - c0) @ Fr
        W = max(6.0, 3.0 * wall)
        w = (np.abs(q[:, 0]) < W) & (np.abs(q[:, 1]) < H + 1.0)
        ax.scatter(q[w & ~kept, 0], q[w & ~kept, 1], s=10, c="0.75", lw=0)
        vmax = max(r["gap_mm"][2], 2 * sp)
        sc = ax.scatter(q[w & kept, 0], q[w & kept, 1], c=g[w & kept], cmap="viridis",
                        vmin=0.0, vmax=vmax, s=12, lw=0)
        ax.set_xlim(-W, W)
        ax.set_aspect("equal")
        ax.set_title(f"face-on, {2 * W:.0f} mm of sherd {i}'s face against {j}: gap coloured, "
                     f"excluded (overlap) grey\nkept {r['kept_pct']:.0f}% of join; gap p10/p50/p90 "
                     + "/".join(f"{v:.2f}" for v in r["gap_mm"]) + " mm; touching "
                     f"{r['touching_pct']:.0f}%", fontsize=10)
        ax.set_xlabel("mm, along the break", fontsize=9)
        fig.colorbar(sc, ax=ax, shrink=0.7, label="gap to the neighbour's surface, mm")
        out.append(dict(join=r["join"]))
    fig.suptitle(f"{res['object']}: joins cut straight across through both sherds' surfaces "
                 f"(left three) and seen face-on (right). Sampling spacing {sp:.3f} mm.",
                 fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.canvas.draw()
    ppm = float(np.median([axes[k, c].get_window_extent().width /
                           (2 * axes[k, c].get_xlim()[1])
                           for k in range(len(pick)) for c in range(3)]))
    # a wide window (an open worn join) is saved at a higher dpi so 0.1 mm still spans 10 px
    dpi = fig.dpi * max(1.0, 110.0 / ppm)
    ppm *= dpi / fig.dpi
    fig.savefig(out_png, dpi=dpi, facecolor="white")
    plt.close(fig)
    ok = 0.1 * ppm >= 10
    print(f"  render {out_png}: {ppm:.0f} px per mm in the cuts, 0.1 mm = {0.1 * ppm:.0f} px -> "
          + ("RESOLVES 0.1 mm" if ok else "DOES NOT RESOLVE 0.1 mm -- do not read"))
    return dict(png=str(out_png), px_per_mm=ppm, resolves_0p1mm=bool(ok), joins=out)


# ---------------------------------------------------------------- self-test

def _box(lo, hi):
    import trimesh
    m = trimesh.creation.box(bounds=[lo, hi])
    return np.asarray(m.vertices, np.float64), np.asarray(m.faces, np.int64)


def _subdivided_box(lo, hi, it=4):
    import trimesh
    v, f = _box(lo, hi)
    for _ in range(it):
        v, f = trimesh.remesh.subdivide(v, f)
    return np.asarray(v, np.float64), np.asarray(f, np.int64)


def selftest():
    """Known answers on box pairs; mm units given directly by LONGEST via mm_per_unit=1."""
    ok = True

    def obj(pieces, name):
        return dict(name=name, path="-", group="-", tag="-", keys=["0", "1"], names=["0", "1"],
                    pieces=pieces, mm_per_unit=1.0, scale_from="selftest")

    def check(label, cond):
        nonlocal ok
        print(("  PASS " if cond else "  FAIL ") + label)
        ok &= bool(cond)

    # 1. two 20x10x2 slabs facing across x, 0.10 apart: gap 0.10 everywhere, nothing inside
    a = _subdivided_box([-20, -5, -1], [0, 5, 1])
    b = _subdivided_box([0.10, -5, -1], [20.10, 5, 1])
    r, _, _ = measure(obj([a, b], "apart"))
    p = r["all"]["pooled"]
    print("  apart 0.10:", json.dumps(dict(gap=p["gap_mm"], kept=p["kept_pct"],
                                           inside=p["inside_pct"])))
    check("apart: gap p10..p90 within 0.09-0.11 mm", p["gap_mm"][0] > 0.09 and p["gap_mm"][2] < 0.11)
    check("apart: nothing inside, all kept", p["inside_pct"] == 0 and p["kept_pct"] > 99)
    check("apart: sign control trusted", r["control"]["trusted"])
    check("apart: skins beside the join are not join dots (face is 10x2 mm, 2 sides)",
          p["join_dots"] < 2.2 * 10 * 2 / r["spacing_target_mm"] ** 2)

    # 2. pushed 0.10 INTO each other: every join dot inside, nothing kept
    b2 = _subdivided_box([-0.10, -5, -1], [19.90, 5, 1])
    r, _, _ = measure(obj([a, b2], "into"))
    p = r["all"]["pooled"]
    print("  into 0.10:", json.dumps(dict(join=p["join_dots"], kept=p["kept_pct"],
                                          inside=p["inside_pct"],
                                          control=r["control"])))
    check("into: >= 95% of join dots inside", p["inside_pct"] >= 95)
    check("into: under 5% kept", p["kept_pct"] < 5)
    check("into: sign control trusted", r["control"]["trusted"])

    # 2b. coincident faces (a clean CSC copy): touching, never inside
    b3 = _subdivided_box([0.0, -5, -1], [20.0, 5, 1])
    r, _, _ = measure(obj([a, b3], "coincident"))
    p = r["all"]["pooled"]
    print("  coincident:", json.dumps(dict(inside=p["inside_pct"], touching=p["touching_pct"])))
    check("coincident: under 5% inside, over 95% touching",
          p["inside_pct"] < 5 and p["touching_pct"] > 95)

    # 3. tilted: b turned about z so the gap runs 0.05 -> 0.45 mm along y (10 mm)
    v, f = _subdivided_box([0.0, -5, -1], [20.0, 5, 1])
    th = np.arctan(0.4 / 10.0)
    R = np.array([[np.cos(th), -np.sin(th), 0], [np.sin(th), np.cos(th), 0], [0, 0, 1]])
    v = v @ R.T           # the face at x = 0 now runs x = -y sin(th): -0.2 .. +0.2
    v[:, 0] += 0.25
    r, _, _ = measure(obj([a, (v, f)], "tilt"))
    p = r["all"]["pooled"]
    c = r["all"]["joins"][0]["corr"] if r["all"]["joins"] else {}
    print("  tilt:", json.dumps(dict(gap=p["gap_mm"], touching=p["touching_pct"], corr=c)))
    check("tilt: median gap 0.22-0.28 mm", 0.22 <= p["gap_mm"][1] <= 0.28)
    check("tilt: p10 0.05-0.15 and p90 0.35-0.45 mm",
          0.05 <= p["gap_mm"][0] <= 0.15 and 0.35 <= p["gap_mm"][2] <= 0.45)
    # a straight ramp over a join of length L reaches 1/e at about L / 3 (1 - r^2 / (2 var))
    check("tilt: correlation length 2-4 mm on a 10 mm join (a ramp reads about a third of L)",
          c.get("mm") is not None and 2.0 <= c["mm"] <= 4.0)

    # 4. ribbed: gap 0.2 + 0.15 sin(2 pi y / 2 mm) -> correlation length well under the join
    v, f = _subdivided_box([0.0, -5, -1], [20.0, 5, 1], it=6)
    face = v[:, 0] < 1e-6
    v[face, 0] = 0.2 + 0.15 * np.sin(2 * np.pi * v[face, 1] / 2.0)
    r, _, _ = measure(obj([a, (v, f)], "ribbed"))
    c = r["all"]["joins"][0]["corr"] if r["all"]["joins"] else {}
    print("  ribbed:", json.dumps(dict(gap=r["all"]["pooled"]["gap_mm"], corr=c)))
    check("ribbed: correlation length 0.2-0.6 mm (a quarter wave is 0.5 mm)",
          c.get("mm") is not None and 0.2 <= c["mm"] <= 0.6)
    print("SELFTEST " + ("PASS" if ok else "FAIL"))
    return ok


# ---------------------------------------------------------------- driver

def table(res, key="all"):
    s = res[key]
    p = s["pooled"]
    f = lambda v, n=3: "-" if v is None else format(v, f".{n}f")   # noqa: E731
    print(f"  pooled: join dots {p['join_dots']}, inside {f(p['inside_pct'], 1)}%, kept "
          f"{p['kept']} ({f(p['kept_pct'], 1)}%)" + ("  WEAK: under a third kept" if p["weak"]
                                                     else ""))
    print("    gap mm p10/p50/p90 " + "/".join(f(v) for v in p["gap_mm"]) +
          "   % diag " + "/".join(f(v) for v in p["gap_pct_diag"]) +
          f"   p90/p10 {f(p['p90_over_p10'], 1)}   touching {f(p['touching_pct'], 1)}%"
          f"   corr. length median {f(p['corr_mm_median_over_joins'], 2)} mm "
          f"({p['joins_with_corr']} joins)")
    print(f"    per sherd median gap: p90/p10 {f(p['sherd_median_p90_over_p10'], 2)}, "
          f"cv {f(p['sherd_median_cv'], 2)}")
    print("    join     dots  in%   kept%  length  gap p10/p50/p90 mm      touch%  corr mm")
    for r in s["joins"]:
        g = "/".join(f(v) for v in r["gap_mm"]) if "gap_mm" in r else "-"
        cl = r.get("corr", {}).get("mm") if "corr" in r else None
        note = r.get("corr", {}).get("note", "") if "corr" in r else ""
        print(f"    {r['join']:<7}{r['dots']:6d}{r['inside_pct']:6.1f}{r['kept_pct']:7.1f}"
              f"{r['length_mm']:8.1f}  {g:<22}{f(r.get('touching_pct'), 1):>7}  "
              f"{f(cl, 2)} {note}")
    print("    sherd  name        kept   median gap mm  touch%")
    for r in s["sherds"]:
        print(f"    {r['sherd']:5d}  {r['name']:<10}{r['kept']:6d}   {r['median_mm']:.3f}"
              f"          {r['touching_pct']:.1f}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--object", action="append", default=[],
                    help="NAME=FILE:GROUP:TAG[:LONGEST_MM]")
    ap.add_argument("--drop-sherds", default="", help="NAME:i,j -- also report without these "
                    "sherds' joins (e.g. juglet:2,7)")
    ap.add_argument("--out", default="artifacts/join_fingerprint")
    ap.add_argument("--no-render", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return 0 if selftest() else 1
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    drops = {}
    for d in filter(None, a.drop_sherds.split(";")):
        n, s = d.split(":")
        drops[n] = tuple(int(x) for x in s.split(","))
    allres = []
    for spec in a.object:
        obj = load_object(spec)
        print("=" * 90)
        print(f"{obj['name']}: {obj['path']}:{obj['group']}/{obj['tag']}, "
              f"{len(obj['pieces'])} sherds ({obj['scale_from']}, x{obj['mm_per_unit']:.4f})",
              flush=True)
        res, S, dots = measure(obj, drop=drops.get(obj["name"], ()))
        print(f"  longest {res['longest_mm']:.1f} mm, diagonal {res['diag_mm']:.1f} mm, wall "
              f"{res['wall_mm_median']:.2f} mm, spacing {res['spacing_mm']:.3f} mm (target "
              f"{res['spacing_target_mm']:.3f}), cut {res['cut_mm']:.2f} mm, {res['dots']} dots")
        c = res["control"]
        if c:
            print(f"  inside-test control on {c['checked']} join dots: pushed in reads inside "
                  f"{c['pushed_in_reads_inside_pct']:.1f}%, pushed out reads outside "
                  f"{c['pushed_out_reads_outside_pct']:.1f}% -> " +
                  ("TRUSTED" if c["trusted"] else "NOT TRUSTED -- do not read the overlap split")
                  + f"  (closest-face sign would agree on {c['face_sign_agrees_pct']:.1f}%)")
        table(res)
        if "without" in res:
            print(f"  --- without the joins of sherds {res['without']['drop_sherds']}")
            table(res, "without")
        if not a.no_render:
            res["render"] = render(obj, res, S, dots, out / f"{obj['name']}_joins.png")
        (out / f"{obj['name']}.json").write_text(json.dumps(res, indent=1))
        allres.append(res)
        sys.stdout.flush()
    (out / "fingerprint.json").write_text(json.dumps(allres, indent=1))
    print("wrote", out / "fingerprint.json")
    bad = [r["object"] for r in allres if r["control"] and not r["control"]["trusted"]]
    if bad:
        print("SIGN CONTROL FAILED on", bad)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
