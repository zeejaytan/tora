"""Size the anchor-mode handicap from the one paired ablation on disk (job 28228263).

Same job, same checkpoint, same seed, same objects -- only data.anchor_free differs.
Read through scripts/readout.py so the non-anchor x n/(n-1) correction is applied once.
"""
import sys
import statistics as st

sys.path.insert(0, "scripts")
import readout  # noqa: E402

BASE = "artifacts/anchor2x2"


def per_object(run):
    recs = readout.read_run("%s/%s" % (BASE, run))
    out = {}
    for r in recs:
        out.setdefault(r.object_name, []).append(r)
    return out


for label, fixed, free in (
    ("real held-out pots", "anchor2x2_heldout_affalse_28228263",
     "anchor2x2_heldout_aftrue_28228263"),
    ("the Juglet (juglet_norm, scale 0.041)", "anchor2x2_juglet_affalse_28228263",
     "anchor2x2_juglet_aftrue_28228263"),
):
    a, b = per_object(fixed), per_object(free)
    print("\n==== %s ====" % label)
    print("%-14s %4s %8s %8s %8s   %8s %8s" % (
        "object", "n", "fixed", "free", "change", "seatFix", "seatFree"))
    deltas = []
    for name in sorted(set(a) & set(b)):
        ra, rb = a[name], b[name]
        ma = st.median([r.turn_deg for r in ra])
        mb = st.median([r.turn_deg for r in rb])
        sa = st.median([r.seated for r in ra])
        sb = st.median([r.seated for r in rb])
        deltas.append(mb - ma)
        print("%-14s %4d %8.1f %8.1f %+8.1f   %5.1f/%-2d %5.1f/%-2d" % (
            name, ra[0].n_fragments, ma, mb, mb - ma, sa, ra[0].n_fragments, sb, rb[0].n_fragments))
    if deltas:
        print("median change anchor-fixed -> anchor-free: %+.1f deg over %d objects"
              % (st.median(deltas), len(deltas)))
