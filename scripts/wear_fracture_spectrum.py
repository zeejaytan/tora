"""Does our simulated wear produce the surface REAL eroded fracture has? (O7)

Gate A measured real eroded archaeological fracture on 20 RePAIR fresco
fragments and got a number: with each fragment's own curvature removed by a
fitted quadric, texture rises as R^1.71 from 0.4 to 6.4 mm. A real FRACTURE
surface is self-affine with a roughness exponent of 0.4-0.8 across metals,
ceramics and rocks; R^1.7 is what a smooth surface with mild residual shape
gives. So there is a dimensionless fingerprint separating fresh fracture from
worn archaeological fracture, and it had low scatter -- consistent across all
20 fragments, one straight log-log line with no kink.

That number has never been put beside our own output. This does that.

WHY THIS IS ANSWERABLE WHEN THE PAIRED COMPARISON IS NOT. `intent/O7` strikes
both captures: you cannot get a pot's break face as it was BEFORE burial, so
"is the wear on this face simulated correctly" is dead. This asks a different
question -- an ENDPOINT question. Do the surfaces our operator produces land
where real worn archaeological surfaces land, and away from where fresh
fracture lands? No before-state, no pairing, no second pot.

  CAN establish: whether simulated wear moves a real ceramic break face's
       roughness-scaling exponent off the fresh-fracture value and toward the
       value real eroded archaeological fracture actually shows.

  CANNOT establish: that the wear on any particular sherd is right. And it
       inherits Gate A's own limit -- whether the ground removed the texture
       from the frescoes or photogrammetry never recorded it is not separable.
       So the claim this supports is "our simulated wear matches real SCANNED
       worn fracture", which is the honest target for training data anyway,
       because the file is what a model sees.

PREDICTION, RECORDED BEFORE THE NUMBERS (this workspace's habit; the last two
predictions written into wear jobs were both refuted and had to be reported as
such -- see EROSION_LADDER_CERAMICS.md and CERAMARM_30337242_RESULT.md).

  1. Our fresh (e000) ceramic break faces should read 0.4-0.8 -- real fracture.
     If they already read >= 1.5 this test has a CEILING: fresh and worn would
     be indistinguishable on our material too. That is a negative result but a
     real one, and it would say the fingerprint cannot be used here.
  2. Simulated wear should RAISE the exponent, toward 1.7.
  3. It probably does NOT reach 1.7 on most pots. `erode_fracture_band`
     saturates from e075 on for every pot in this corpus (the knn=48 kernel
     stops widening), and achieved wear plateaus above the Juglet's roughness
     on half of them (`narrow_bottle4` 0.244 vs Juglet 0.171).

A CONFOUND TO STATE UP FRONT. The wear operator acts at a fixed FRACTION of
object size, but this axis is absolute millimetres. So the same rung is a
different physical abrasion per pot: roughly 0.40-0.67 mm on `blue_pot` and
1.0-1.67 mm on `plate`. Pots are therefore never pooled here -- each pot is
read up its own ladder, which is also this corpus's standing rule (agreement
between attempts correlates with fragment count at r = -0.87).

TWO THINGS ARE DELIBERATELY NOT GATE A'S, and both are corrections, not
shortcuts.

  FINDING THE FRACTURE. Gate A fits ONE global plane per fragment and calls a
  vertex fracture if its normal faces sideways. A fresco plaque is a thin flat
  slab, so that works; even so Gate A found about one fragment in four
  contaminated on merely LUMPY fragments. A pot sherd is a CURVED shell -- its
  "thinnest direction" is not defined, and on a bowl or a bottle neck the
  vessel's own inner and outer surfaces sweep through every orientation and
  would be labelled fracture. So the fracture is taken from the CONTACT BAND
  instead: vertices of one sherd lying within 2% of object size of another
  sherd. That is the extractor `compare_wear_to_juglet.py` already uses, it
  assumes nothing about shape, and it is the surface the wear operator acted
  on. It is RENDERED here before any number is trusted.

  ABSOLUTE MILLIMETRES. The ladder geometry is normalised to max|v| = 0.5, and
  erosion is a physical process, so each pot is rescaled back to real scan
  units before measuring: scale = raw_max|v| / 0.5, taken from
  `fractura_real.hdf5` in-script rather than hand-copied. That is exact because
  the normalisation was one uniform factor applied once, before erosion. It is
  verified per pot by checking the rescaled bounding-box diagonal against the
  raw one, and the drift is printed. Measured break-face spacing on this
  corpus is 0.088-0.329 mm against diagonals of 134-333 mm, so the units are
  millimetres and Gate A's radii are reachable.

THE FITTING BAND. Gate A's rule is that the finest readable scale is about
three times the point spacing. Our coarsest pot (`plate`, 0.329 mm) is valid
only from ~1.0 mm, so the band every pot AND RePAIR both support is 1.6-6.4 mm.
This costs nothing in comparability: refitting Gate A's own published texture
values over just 1.6-6.4 gives ln(0.2091/0.0197)/ln(4) = 1.704, against 1.71
over the full range. Per-pot exponents over each pot's own valid radii are
reported alongside, and a disagreement between the two is flagged rather than
averaged away.

Usage:
  python scripts/wear_fracture_spectrum.py \
      --erosion dataset/erosion_ceramics.hdf5 \
      --raw     dataset/fractura_real.hdf5 \
      --out-dir artifacts/wear_spectrum
"""

import argparse
import json
import sys
from pathlib import Path

import h5py
import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from repair_fracture_spectrum import RADII_MM, spectrum_mm  # noqa: E402

import matplotlib                                            # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt                              # noqa: E402

# Gate A, docs/notes/GATE_A_RESULT.md -- 20 Pompeii fresco fragments, real
# archaeological fracture eroded for two thousand years.
REPAIR_EXPONENT = 1.71
REPAIR_TEXTURE = {0.40: 0.0018, 0.80: 0.0049, 1.60: 0.0197,
                  3.20: 0.0685, 6.40: 0.2091}
# self-affine roughness exponent of a real fracture surface, across metals,
# ceramics and rocks -- the fresh end of the axis.
FRESH_FRACTURE_BAND = (0.4, 0.8)
# the band every pot's sampling supports, and RePAIR's too. See docstring.
COMMON_BAND = (1.60, 6.40)
SPACING_RULE = 3.0        # finest readable scale ~ 3x point spacing (Gate A)
BAND_FRAC = 0.02          # contact band width, fraction of object diagonal
RUNGS = ["e000", "e025", "e050", "e075", "e100"]


def load_pieces(h5, group, tag, max_pts, seed=0):
    rng = np.random.default_rng(seed)
    g = h5[group][tag]["pieces"]
    out = []
    for k in sorted(g.keys()):
        v = np.asarray(g[k]["vertices"][:], dtype=np.float64)
        if len(v) > max_pts:
            v = v[rng.choice(len(v), max_pts, replace=False)]
        out.append(v)
    return out


def contact_bands(pieces, diag, band_frac=BAND_FRAC, min_pts=400):
    """Break-face points: vertices of one sherd close to any other sherd.

    No assumption about the sherd's shape, unlike a slab plane fit. This is
    the surface the wear operator acted on.
    """
    bands = []
    for i, a in enumerate(pieces):
        best = None
        for j, b in enumerate(pieces):
            if i == j:
                continue
            d, _ = cKDTree(b).query(a, workers=-1)
            best = d if best is None else np.minimum(best, d)
        if best is None:
            continue
        band = a[best < band_frac * diag]
        if len(band) >= min_pts:
            bands.append(band)
    return bands


def fit_exponent(radii, texture, lo, hi):
    """log-log slope of texture against patch radius over [lo, hi]."""
    pairs = [(r, t) for r, t in zip(radii, texture)
             if lo - 1e-9 <= r <= hi + 1e-9 and np.isfinite(t) and t > 0]
    if len(pairs) < 2:
        return float("nan"), len(pairs)
    r = np.array([p[0] for p in pairs])
    t = np.array([p[1] for p in pairs])
    return float(np.polyfit(np.log(r), np.log(t), 1)[0]), len(pairs)


def raw_scales(raw_path, raw_group):
    """max|v| / 0.5 per pot, and the raw diagonal to verify the rescale."""
    scale_of, diag_of = {}, {}
    with h5py.File(raw_path, "r") as fr:
        if raw_group not in fr:
            raise SystemExit("no group '" + raw_group + "' in " + raw_path +
                             "; top level: " + str(list(fr.keys())))
        for pot in sorted(fr[raw_group].keys()):
            g = fr[raw_group][pot]["pieces"]
            allv = np.concatenate(
                [np.asarray(g[k]["vertices"][:], dtype=np.float64)
                 for k in sorted(g.keys())], axis=0)
            scale_of[pot] = float(np.abs(allv).max()) / 0.5
            diag_of[pot] = float(np.linalg.norm(allv.max(0) - allv.min(0)))
            del allv
    return scale_of, diag_of


def render_bands(shown, out):
    """LOOK AT THE BAND BEFORE BELIEVING THE NUMBERS (mandatory here).

    The contact band is the whole basis of the measurement. If it has picked
    up the vessel wall instead of the break, every exponent below is a
    statement about pot shape.
    """
    fig, axes = plt.subplots(1, len(shown), figsize=(3.3 * len(shown), 3.6))
    axes = np.atleast_1d(axes)
    for ax, (tag, allv, band) in zip(axes, shown):
        rng = np.random.default_rng(0)
        sub = allv[rng.choice(len(allv), min(25000, len(allv)), False)]
        bsub = band[rng.choice(len(band), min(9000, len(band)), False)]
        ax.scatter(sub[:, 0], sub[:, 1], s=0.3, c="0.82", linewidths=0)
        ax.scatter(bsub[:, 0], bsub[:, 1], s=0.5, c="crimson", linewidths=0)
        ax.set_title(tag + "\nred = the surface measured", fontsize=8)
        ax.set_aspect("equal")
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    plt.close(fig)
    print("wrote " + str(out))


def render_spectrum(rows, out):
    fig, ax = plt.subplots(figsize=(6.6, 5.2))
    rr = sorted(REPAIR_TEXTURE)
    ax.axvspan(COMMON_BAND[0], COMMON_BAND[1], color="0.91", zorder=0,
               label="fitting band 1.6-6.4 mm")
    for r in rows:
        if r["rung"] == "e000":
            ax.plot(RADII_MM, r["texture"], "-", color="#2980b9", alpha=0.5,
                    lw=1.1)
        elif r["rung"] == "e100":
            ax.plot(RADII_MM, r["texture"], "-", color="#c0392b", alpha=0.5,
                    lw=1.1)
    ax.plot(rr, [REPAIR_TEXTURE[x] for x in rr], "k-o", lw=2.6, ms=5,
            label="RePAIR real eroded fracture  R^" + str(REPAIR_EXPONENT))
    ax.plot([], [], color="#2980b9", label="ours, fresh (e000)")
    ax.plot([], [], color="#c0392b", label="ours, fully abraded (e100)")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("patch radius (mm)")
    ax.set_ylabel("texture, deviation from fitted quadric (mm)")
    ax.set_title("Break-face texture spectrum, absolute scale")
    ax.legend(fontsize=7.5, loc="upper left")
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    plt.close(fig)
    print("wrote " + str(out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--erosion", required=True)
    ap.add_argument("--raw", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--group", default="erosion_ceramics")
    ap.add_argument("--raw-group", default="ceramics")
    ap.add_argument("--max-piece-pts", type=int, default=200000)
    ap.add_argument("--max-band-pts", type=int, default=60000)
    ap.add_argument("--max-probe", type=int, default=8000)
    ap.add_argument("--pots", default="", help="comma list; default all")
    a = ap.parse_args()

    outd = Path(a.out_dir)
    outd.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(0)

    scale_of, rawdiag_of = raw_scales(a.raw, a.raw_group)
    print("raw scales from " + a.raw + ": " +
          ", ".join(p + " x" + format(s, ".2f") for p, s in scale_of.items()))

    want = [p for p in a.pots.split(",") if p] or None
    rows, shown = [], []

    with h5py.File(a.erosion, "r") as fe:
        for tag in sorted(fe[a.group].keys()):
            pot, rung = tag.rsplit("_", 1)
            if want and pot not in want:
                continue
            if pot not in scale_of:
                print("  " + tag + ": no raw counterpart, skipped")
                continue

            pieces = load_pieces(fe, a.group, tag, a.max_piece_pts)
            if len(pieces) < 2:
                print("  " + tag + ": fewer than two pieces, skipped")
                continue
            pieces = [v * scale_of[pot] for v in pieces]      # -> millimetres
            allv = np.concatenate(pieces, axis=0)
            diag = float(np.linalg.norm(allv.max(0) - allv.min(0)))
            drift = 100.0 * abs(diag - rawdiag_of[pot]) / rawdiag_of[pot]

            bands = contact_bands(pieces, diag)
            if not bands:
                print("  " + tag + ": no contact band, skipped")
                continue
            band = np.concatenate(bands, axis=0)
            if len(band) > a.max_band_pts:
                band = band[rng.choice(len(band), a.max_band_pts, False)]

            d, _ = cKDTree(band).query(band, k=2, workers=-1)
            spacing = float(np.median(d[:, 1]))
            finest = SPACING_RULE * spacing

            tex = spectrum_mm(band, RADII_MM, max_probe=a.max_probe)
            tex = [float(x) for x in tex]
            e_common, n_common = fit_exponent(RADII_MM, tex, *COMMON_BAND)
            e_own, n_own = fit_exponent(RADII_MM, tex, finest, RADII_MM[-1])

            rows.append(dict(tag=tag, pot=pot, rung=rung, diag_mm=diag,
                             scale_drift_pct=drift, band_pts=int(len(band)),
                             spacing_mm=spacing, finest_valid_mm=finest,
                             texture=tex, exponent_common=e_common,
                             n_common=n_common, exponent_own=e_own,
                             n_own=n_own))
            print("  " + tag.ljust(22) + " diag " + format(diag, "6.1f") +
                  " mm (drift " + format(drift, ".2f") + "%)  spacing " +
                  format(spacing, ".3f") + "  valid>=" +
                  format(finest, ".2f") + "  exp[1.6-6.4] " +
                  format(e_common, "5.2f") + "  exp[own] " +
                  format(e_own, "5.2f"), flush=True)

            if rung in ("e000", "e100") and len(shown) < 6:
                shown.append((tag, allv, band))
            del pieces, allv

    if not rows:
        print("nothing measured")
        return

    if shown:
        render_bands(shown, outd / "band_classification.png")
    render_spectrum(rows, outd / "spectrum.png")

    (outd / "wear_spectrum.json").write_text(json.dumps(
        dict(repair_exponent=REPAIR_EXPONENT,
             fresh_fracture_band=list(FRESH_FRACTURE_BAND),
             common_band=list(COMMON_BAND), radii_mm=RADII_MM,
             spacing_rule=SPACING_RULE, band_frac=BAND_FRAC, rows=rows),
        indent=2), encoding="utf-8")

    # ---- the table that answers the question -----------------------------
    pots = sorted({r["pot"] for r in rows})
    print("")
    print("=" * 78)
    print("ROUGHNESS-SCALING EXPONENT over 1.6-6.4 mm, per pot up its own "
          "ladder")
    print("  real eroded archaeological fracture (RePAIR, n=20) = " +
          format(REPAIR_EXPONENT, ".2f"))
    print("  fresh fracture, literature                          = 0.4 - 0.8")
    print("=" * 78)
    print("pot".ljust(16) + "".join(x.rjust(8) for x in RUNGS) +
          "   spacing   own-band exp (e000 -> e100)")
    for pot in pots:
        line = pot.ljust(16)
        for rg in RUNGS:
            m = [r for r in rows if r["pot"] == pot and r["rung"] == rg]
            line += (format(m[0]["exponent_common"], "8.2f") if m
                     else "-".rjust(8))
        sp = [r["spacing_mm"] for r in rows if r["pot"] == pot]
        ends = []
        for rg in ("e000", "e100"):
            m = [r for r in rows if r["pot"] == pot and r["rung"] == rg]
            ends.append(format(m[0]["exponent_own"], ".2f") if m else "-")
        line += "   " + format(float(np.median(sp)), ".3f") + " mm"
        line += "   " + ends[0] + " -> " + ends[1]
        print(line)

    # ---- the checks that decide whether the table can be read ------------
    print("")
    worst_drift = max(r["scale_drift_pct"] for r in rows)
    print("scale-rescale drift, worst of all rungs: " +
          format(worst_drift, ".2f") + "%  " +
          ("(OK)" if worst_drift < 1.0 else "(SUSPECT - the mm axis is not "
           "trustworthy above 1%)"))
    e0 = [r["exponent_common"] for r in rows if r["rung"] == "e000"]
    if e0:
        print("fresh (e000) exponents: " + format(float(np.min(e0)), ".2f") +
              " - " + format(float(np.max(e0)), ".2f") + ", median " +
              format(float(np.median(e0)), ".2f"))
        if float(np.median(e0)) >= 1.5:
            print("  CEILING: our fresh fracture already reads like RePAIR's "
                  "worn fracture,")
            print("  so this fingerprint cannot separate fresh from worn on "
                  "this material.")
    dis = [r for r in rows if np.isfinite(r["exponent_own"]) and
           np.isfinite(r["exponent_common"]) and
           abs(r["exponent_own"] - r["exponent_common"]) > 0.3]
    print("rungs where the own-band and common-band fits disagree by >0.3: " +
          str(len(dis)) + " of " + str(len(rows)) +
          ("" if not dis else "  -> " +
           ", ".join(r["tag"] for r in dis[:8])))
    print("")
    print("wrote " + str(outd) + "/wear_spectrum.json, spectrum.png, "
          "band_classification.png")
    print("LOOK AT band_classification.png BEFORE QUOTING ANY NUMBER ABOVE.")


if __name__ == "__main__":
    main()
