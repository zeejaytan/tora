"""How much of the wall does each fragment wrap, and which vessels make bands?

WHY THIS EXISTS. check_break_realism.py asked the same question and got the
answer wrong. It called a fragment a ring only if it wrapped past 300 degrees,
reported 19% either way, and concluded the corpus was clean. Then the training
set was rendered and half the panels showed colour stacked in horizontal bands.
A fragment covering 250 degrees is a band to the eye and was not a ring to that
test. The threshold, not the geometry, produced the reassuring number.

So this script does not pick a threshold. It reports the whole distribution and
sweeps the cutoff, and it renders the measured quantity itself.

WHAT IS MEASURED, per fragment, in the assembled vessel:

  wrap        how far it reaches AROUND the axis of revolution, in degrees.
              Taken as 360 minus the largest empty run in a 1-degree occupancy
              histogram, so a wedge straddling the branch cut cannot read as a
              full circle. Uses every vertex -- subsampling inflates the gaps
              and would bias every wrap DOWNWARDS, which is the direction that
              flatters the corpus.

  arc         that wrap turned into a length: radians * the fragment's mean
              distance from the axis, as a fraction of vessel height. This is
              the honest version of wrap. A neck fragment wrapping 360 degrees
              on a 2cm neck is a short piece of wall; a body fragment wrapping
              120 degrees on a wide belly is a longer one.

  rise        how far it reaches ALONG the axis, same units.

  arc/rise    the fragment's shape. Above 1 it is wider than it is tall -- a
              band. Near 1 it is a patch. This is what "stacked slices" looks
              like as a number, and it does not depend on any cutoff.

AND PER VESSEL: slenderness = height / widest diameter. The hypothesis worth
refuting is that bands come from slender vessels -- tubes -- and not from the
selection filter. If that is true, band fraction rises with slenderness and the
decision is which shape classes to keep, not whether the builder is broken.

THE DECISION IT HAS TO SERVE. Dropping the narrow classes costs shape variety,
which is the entire reason this set was built. So the script reports, for each
candidate exclusion, what is left: examples, distinct shapes, and band fraction.
Cost and benefit in the same table, or the choice cannot be made.

Measured on the FRESH examples only. The three wear levels are the same break
geometry receded; counting all three would treble every fragment and make the
sample look three times stronger than it is.

Usage:
  python scripts/check_band_coverage.py \
      --src dataset/bbad_vessels.hdf5 --out artifacts/band_coverage.png
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path

import h5py
import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

COLOURS = ["#1f4e79", "#c1440e", "#4a7c59", "#7d5ba6", "#b8860b",
           "#2f6f7e", "#8b3a62", "#556b2f", "#a0522d", "#4682b4",
           "#8b0000", "#2e8b57", "#6a5acd", "#cd853f", "#708090",
           "#9932cc", "#008b8b", "#b22222", "#3cb371", "#daa520"]

SWEEP = [180.0, 220.0, 260.0, 300.0, 340.0]


def axis_frame(allv):
    """The vessel's axis of revolution and two directions across it."""
    P = allv - allv.mean(axis=0)
    U = np.linalg.svd(P.T @ P)[0]
    return U[:, 0], U[:, 1], U[:, 2]


def wrap_degrees(theta):
    """Angular reach, from 1-degree bin occupancy.

    360 minus the longest run of empty bins. Robust to where the branch cut
    falls, and -- unlike sorting gaps between sampled points -- it does not get
    smaller just because a fragment has fewer vertices.
    """
    occ = np.zeros(360, dtype=bool)
    occ[np.clip(((np.degrees(theta) + 180.0) % 360.0).astype(int), 0, 359)] = True
    if occ.all():
        return 360.0
    if not occ.any():
        return 0.0
    # longest empty run on the circle: rotate so a filled bin starts the array
    start = int(np.argmax(occ))
    r = np.roll(occ, -start)
    longest, run = 0, 0
    for v in r:
        run = 0 if v else run + 1
        longest = max(longest, run)
    return float(360 - longest)


def measure(parts):
    """Per-fragment wrap / arc / rise, plus the vessel's slenderness."""
    allv = np.concatenate(parts, axis=0)
    ctr = allv.mean(axis=0)
    ax, e1, e2 = axis_frame(allv)
    Q = allv - ctr
    height = float(np.ptp(Q @ ax)) + 1e-12
    max_r = float(np.hypot(Q @ e1, Q @ e2).max()) + 1e-12
    slender = height / (2.0 * max_r)

    rows = []
    for p in parts:
        q = p - ctr
        u, v, z = q @ e1, q @ e2, q @ ax
        w = wrap_degrees(np.arctan2(v, u))
        r = float(np.hypot(u, v).mean())
        arc = np.radians(w) * r / height
        rise = float(np.ptp(z)) / height
        rows.append((w, arc, rise, max(rise, 1e-9)))
    return slender, [(w, a, ri, a / d) for w, a, ri, d in rows]


def load_parts(grp):
    pg = grp["pieces"]
    keys = sorted(pg.keys(), key=lambda s: int(s) if s.isdigit() else s)
    return [np.asarray(pg[k]["vertices"][:], dtype=np.float64) for k in keys]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", required=True)
    ap.add_argument("--dataset", default="bbad_vessels")
    ap.add_argument("--manifest", default="")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    man_path = args.manifest or (str(args.src) + ".manifest.json")
    manifest = json.loads(Path(man_path).read_text())

    h = h5py.File(args.src, "r")
    dg = h[args.dataset]

    frag = []          # (category, object, wrap, arc, rise, ratio, slender)
    per_vessel = []    # (category, object, tag, slender, wrap list)
    tags = [t for t in dg.keys() if t.endswith("__fresh")]
    print(f"measuring {len(tags)} fresh breaks "
          f"(of {len(dg.keys())} examples; the worn copies are the same "
          f"geometry receded)\n", flush=True)

    for n, tag in enumerate(sorted(tags)):
        m = manifest.get(tag, {})
        c, o = m.get("category", "?"), m.get("object", "?")
        parts = load_parts(dg[tag])
        if len(parts) < 3:
            continue
        slender, rows = measure(parts)
        for w, a, ri, ratio in rows:
            frag.append((c, o, w, a, ri, ratio, slender))
        per_vessel.append((c, o, tag, slender, [r[0] for r in rows]))
        if (n + 1) % 100 == 0:
            print(f"  {n + 1}/{len(tags)}", flush=True)

    W = np.array([f[2] for f in frag])
    RATIO = np.array([f[5] for f in frag])
    SL = np.array([f[6] for f in frag])
    cats = np.array([f[0] for f in frag])

    print(f"\n{len(frag)} fragments over {len(per_vessel)} breaks\n")

    print("HOW FAR FRAGMENTS WRAP (no threshold -- the whole distribution)")
    for q in (10, 25, 50, 75, 90, 99):
        print(f"  {q:>3d}th percentile   {np.percentile(W, q):>6.0f} deg")
    print(f"\n  wider than tall (arc/rise > 1): "
          f"{100 * float((RATIO > 1).mean()):.1f}% of fragments")
    print(f"  more than twice as wide as tall: "
          f"{100 * float((RATIO > 2).mean()):.1f}%")

    print("\nWHAT THE CUTOFF DECIDES -- the last test picked 300 and got 19%")
    for t in SWEEP:
        print(f"  wrap >= {t:>5.0f} deg   {100 * float((W >= t).mean()):>5.1f}% "
              f"of fragments")

    # Does slenderness explain it? The claim that could be refuted here.
    print("\nDO BANDS COME FROM SLENDER VESSELS?")
    med = float(np.median(SL))
    for lab, sel in (("squat  (below median)", SL <= med),
                     ("slender (above median)", SL > med)):
        print(f"  {lab:<24s} slenderness<= {med:.2f}   "
              f"mean wrap {W[sel].mean():>5.0f} deg   "
              f"wide-than-tall {100 * float((RATIO[sel] > 1).mean()):>5.1f}%")
    if len(set(np.round(SL, 3))) > 2:
        r = float(np.corrcoef(SL, RATIO)[0, 1])
        print(f"  correlation slenderness vs arc/rise: {r:+.2f}")

    # Per class, with the cost of dropping it in the same table.
    print("\nPER VESSEL CLASS  (band = wider than tall)")
    print(f"  {'class':<18s} {'shapes':>7s} {'breaks':>7s} {'frags':>7s} "
          f"{'slender':>8s} {'mean wrap':>10s} {'band %':>8s}")
    print("  " + "-" * 74)
    stats = {}
    for c in sorted(set(cats)):
        s = cats == c
        shapes = len({f[1] for f in frag if f[0] == c})
        breaks = len([v for v in per_vessel if v[0] == c])
        stats[c] = (shapes, breaks, int(s.sum()), float(SL[s].mean()),
                    float(W[s].mean()), 100 * float((RATIO[s] > 1).mean()))
    for c in sorted(stats, key=lambda k: -stats[k][5]):
        a, b, n, sl, mw, bp = stats[c]
        print(f"  {c:<18s} {a:>7d} {b:>7d} {n:>7d} {sl:>8.2f} "
              f"{mw:>9.0f}d {bp:>7.1f}%")

    # The decision. Drop worst-first, and show what is left each time.
    print("\nWHAT DROPPING CLASSES COSTS AND BUYS")
    print("  Classes removed worst-band-first. 'shapes' is the variety this")
    print("  set was built for -- that is the cost side of the trade.")
    print(f"\n  {'dropped':<20s} {'shapes left':>12s} {'breaks left':>12s} "
          f"{'band % left':>12s}")
    print("  " + "-" * 60)
    order = sorted(stats, key=lambda k: -stats[k][5])
    dropped = []
    keep = np.ones(len(frag), dtype=bool)
    tot_shapes = len({(f[0], f[1]) for f in frag})
    print(f"  {'(nothing)':<20s} {tot_shapes:>12d} "
          f"{len(per_vessel):>12d} {100 * float((RATIO > 1).mean()):>11.1f}%")
    for c in order:
        keep &= cats != c
        dropped.append(c)
        if not keep.any():
            break
        sh = len({(f[0], f[1]) for f, k in zip(frag, keep) if k})
        br = len([v for v in per_vessel if v[0] not in dropped])
        print(f"  {('+' + c):<20s} {sh:>12d} {br:>12d} "
              f"{100 * float((RATIO[keep] > 1).mean()):>11.1f}%")

    if not args.out:
        return

    # RENDER THE MEASURED QUANTITY ITSELF, unbinned, plus vessels at both ends
    # so the picture can disagree with the table the way it did last time.
    fig = plt.figure(figsize=(19, 12))
    gs = fig.add_gridspec(3, 6, height_ratios=[1.0, 1.0, 1.25], hspace=0.42,
                          wspace=0.28)

    a0 = fig.add_subplot(gs[0, 0:2])
    step = max(1, len(SL) // 9000)
    a0.scatter(SL[::step], RATIO[::step], s=3.5, alpha=0.28, linewidths=0,
               color="#1f4e79")
    a0.axhline(1.0, color="#c1440e", lw=1.2)
    a0.set_yscale("log")
    a0.set_xlabel("vessel slenderness  (height / widest diameter)")
    a0.set_ylabel("fragment arc / rise")
    a0.set_title("Every fragment. Above the red line it is\n"
                 "wider than it is tall -- a band.", fontsize=10)

    a1 = fig.add_subplot(gs[0, 2:4])
    a1.hist(W[SL <= med], bins=60, range=(0, 360), alpha=0.62,
            color="#4a7c59", label=f"squat (slenderness <= {med:.2f})")
    a1.hist(W[SL > med], bins=60, range=(0, 360), alpha=0.62,
            color="#c1440e", label=f"slender (> {med:.2f})")
    for t in SWEEP:
        a1.axvline(t, color="#708090", lw=0.7, ls=":")
    a1.set_xlabel("wrap around the axis (degrees)")
    a1.set_ylabel("fragments")
    a1.legend(fontsize=8)
    a1.set_title("Dotted lines are candidate cutoffs.\n"
                 "300 deg was the one that missed this.", fontsize=10)

    a2 = fig.add_subplot(gs[0, 4:6])
    names = sorted(stats, key=lambda k: stats[k][5])
    a2.barh(range(len(names)), [stats[k][5] for k in names], color="#7d5ba6")
    a2.set_yticks(range(len(names)))
    a2.set_yticklabels(names, fontsize=8)
    a2.set_xlabel("% of fragments wider than tall")
    a2.set_title("Band fraction by vessel class", fontsize=10)

    # Worst and best vessels, side-on, at the same scale.
    def band_frac(v):
        _, _, tag, _, _ = v
        return None

    scored = []
    for c, o, tag, sl, wl in per_vessel:
        scored.append((float(np.mean([w >= 260 for w in wl])), c, o, tag, sl))
    scored.sort(key=lambda r: -r[0])
    gallery = scored[:6] + scored[-6:]

    for k, (bf, c, o, tag, sl) in enumerate(gallery):
        ax_ = fig.add_subplot(gs[1 + k // 6, k % 6])
        parts = load_parts(dg[tag])
        allv = np.concatenate(parts, axis=0)
        ctr = allv.mean(axis=0)
        s = float(np.abs(allv - ctr).max()) + 1e-12
        axv, e1, _ = axis_frame(allv)
        for i, p in enumerate(parts):
            q = (p - ctr) / s
            if len(q) > 4000:
                q = q[::max(1, len(q) // 4000)]
            ax_.scatter(q @ e1, q @ axv, s=1.3, alpha=0.75, linewidths=0,
                        color=COLOURS[i % len(COLOURS)])
        ax_.set_aspect("equal")
        ax_.set_xlim(-1.12, 1.12); ax_.set_ylim(-1.12, 1.12)
        ax_.set_xticks([]); ax_.set_yticks([])
        ax_.set_title(f"{c}/{o[:8]}\nslender {sl:.2f}, "
                      f"{100 * bf:.0f}% wrap>260", fontsize=8)

    fig.suptitle(
        "Band coverage in bbad_vessels. Top row is the measurement; "
        "below it the six most banded breaks, then the six least.\n"
        "The last test of this question used one 300-degree cutoff and "
        "called the corpus clean. The render disagreed.", fontsize=12)
    fig.savefig(args.out, dpi=120, bbox_inches="tight")
    print(f"\n  wrote {args.out}")


if __name__ == "__main__":
    main()
