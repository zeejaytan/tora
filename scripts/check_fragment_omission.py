"""Gate: what actually happens to the sherds we KEEP when one sherd is removed.

WHY THIS IS A MEASUREMENT AND NOT AN ASSERTION.

Ticket .scratch/juglet-cause/issues/04 asked for a gate that asserts the kept
fragments' point clouds and reference poses come back "bit-identical to the full
run". They cannot, and the reason is in the loader, not in this script:

  * The 5000-point budget is shared out by AREA over the TOTAL area
    (PointCloudDataset._sample_points). Remove a mesh and both `total_area` and
    `len(meshes)` change, so every surviving fragment is allotted a different
    number of points and is re-sampled from scratch.
  * The pot is then re-centred on the concatenation of what is left
    (`center_pcd`), so the origin moves to the new centre of mass.
  * And re-normalised by the new max|v|, so the whole object changes size.
  * `overlap_thr` moves with total_area too.

An assertion of bit-identity would therefore either fail on every object or --
far worse -- be written loosely enough to pass on the wrong thing. So this gate
does the honest version instead. It ASSERTS the things that must hold (the right
sherd is gone, the rest are all present, the anchor does not change identity),
and it MEASURES the disturbance that cannot be removed, alongside a control that
says how much of that disturbance is only re-sampling.

THE THREE ARMS, on the same object:

  whole      the pot as stored, sampler seed S
  reseed     the pot as stored, sampler seed S' -- CONTROL. Nothing was removed,
             so every difference here is the sampler drawing different points.
  dropped    the rank-k largest fragment removed, sampler seed S

Reading it: the "dropped" column has to be read against the "reseed" column, not
against zero. Shape figures near the reseed level mean the kept sherds are the
same sherds, just re-sampled. Frame figures well above it are the real cost of
absence -- the pot genuinely is a different size and centred somewhere else once
a piece is gone, exactly as a genuinely incomplete pot is -- and any effect the
experiment claims must be larger than that.

WHY RANK 1 IS REFUSED. `_transform` picks the anchor as `argmax(counts)`, and
counts rise with area, so rank 1 IS the anchor -- the fragment the model is
handed already seated. Dropping it hands the model a different starting sherd,
which is a different task, not a missing-piece test. The dataset raises on
`omit_rank < 2`; this gate checks that it does.

Run on Spartan (needs the tora env), from the TORA working area:
  python repo/scripts/check_fragment_omission.py \
      --data dataset/ceramics.hdf5 --dataset-name ceramics \
      --min-parts 3 --max-parts 12 --anchor-fixed --rank 2
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import h5py
import numpy as np

from tora.data.dataset import PointCloudDataset


def build(a, omit_rank):
    return PointCloudDataset(
        split=a.split,
        data_path=a.data,
        dataset_name=a.dataset_name,
        min_parts=a.min_parts,
        max_parts=a.max_parts,
        anchor_free=not a.anchor_fixed,
        num_points_to_sample=a.num_points,
        min_points_per_part=20,
        random_scale_range=None,
        disable_augmentation=True,
        num_threads=1,          # the pool interleaves RNG draws; 1 keeps it repeatable
        omit_rank=omit_rank,
    )


def get(ds, index, seed):
    np.random.seed(seed)
    return ds[index]


def part_keys(h5, name):
    """The fragment keys, in the order the loader uses them."""
    g = h5[name]
    if "pieces" in g:
        g = g["pieces"]
    return sorted(list(g.keys()))


def fragments_of(sample):
    """Split a sample's assembled cloud back into one array per fragment.

    Undoes the [-1, 1] normalisation by multiplying through by `scales`, so the
    numbers below are in the object's own units rather than in units that
    themselves changed when the sherd was removed.
    """
    pts = np.asarray(sample["pointclouds_gt"], dtype=np.float64)
    pts = pts * float(sample["scales"])
    counts = np.asarray(sample["points_per_part"])[: sample["num_parts"]]
    out, st = [], 0
    for c in counts:
        out.append(pts[st: st + int(c)])
        st += int(c)
    return out


def chamfer(a, b):
    """Symmetric mean nearest-neighbour distance between two point sets."""
    d = np.linalg.norm(a[:, None, :] - b[None, :, :], axis=2)
    return 0.5 * (d.min(1).mean() + d.min(0).mean())


def compare(ref, var, ref_keep, var_keep, span):
    """Per-fragment disturbance between two arms, as a percentage of pot size.

    `ref_keep` / `var_keep` are the indices into each arm's fragment list that
    refer to the same physical sherd.

    Returns (frame, shape): `frame` includes the re-centring and re-scaling and
    is the honest cost of absence; `shape` removes each fragment's own centroid
    first, so it reports only whether the sherd itself came back different.
    """
    frame, shape = [], []
    for i, j in zip(ref_keep, var_keep):
        x, y = ref[i], var[j]
        frame.append(100.0 * np.linalg.norm(x.mean(0) - y.mean(0)) / span)
        shape.append(100.0 * chamfer(x - x.mean(0), y - y.mean(0)) / span)
    return np.array(frame), np.array(shape)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--dataset-name", required=True)
    ap.add_argument("--split", default="val")
    ap.add_argument("--min-parts", type=int, default=3)
    ap.add_argument("--max-parts", type=int, default=12)
    ap.add_argument("--num-points", type=int, default=5000)
    ap.add_argument("--anchor-fixed", action="store_true",
                    help="anchor-fixed mode (config anchor_free: false), as the "
                         "fractura ceramics config uses")
    ap.add_argument("--rank", type=int, default=2,
                    help="which fragment to drop, by descending surface area; "
                         "1 is the anchor and is refused")
    ap.add_argument("--limit", type=int, default=8)
    ap.add_argument("--seed", type=int, default=100)
    a = ap.parse_args()

    ok = True

    # 1. The anchor must be un-droppable, and the loader must say so itself.
    try:
        build(a, omit_rank=1)
        print("FAIL: omit_rank=1 was accepted. Dropping the largest fragment "
              "changes which sherd the model is given pre-seated, so the run "
              "would answer a different question.")
        ok = False
    except ValueError as e:
        print(f"anchor guard: omit_rank=1 refused -- {e}\n")

    whole = build(a, omit_rank=None)
    drop = build(a, omit_rank=a.rank)

    h5 = h5py.File(a.data, "r", libver="latest", swmr=True)

    common = [n for n in drop.fragments if n in set(whole.fragments)]
    skipped = [n for n in whole.fragments if n not in set(drop.fragments)]
    print(f"{a.dataset_name}: {len(whole.fragments)} objects whole, "
          f"{len(drop.fragments)} can lose their rank-{a.rank} fragment, "
          f"{len(common)} comparable")
    if skipped:
        print("  too few fragments to drop one, excluded from BOTH arms in the "
              "analysis: " + ", ".join(s.split('/')[-1] for s in skipped))
    print()

    n = min(len(common), a.limit)
    print(f"{'object':22s} {'frags':>5s} {'dropped':>10s} {'pot size':>9s} "
          f"{'scale w':>8s} {'scale d':>8s} | "
          f"{'reseed frame':>12s} {'drop frame':>10s} | "
          f"{'reseed shape':>12s} {'drop shape':>10s}")
    print("-" * 128)

    rows = []
    for k in range(n):
        name = common[k]
        iw = whole.fragments.index(name)
        idd = drop.fragments.index(name)
        seed = a.seed + k

        s_whole = get(whole, iw, seed)
        s_reseed = get(whole, iw, seed + 9973)      # control: same pot, new draw
        s_drop = get(drop, idd, seed)

        keys = part_keys(h5, name)
        gone = str(s_drop["omitted_fragment"])
        if gone not in keys:
            print(f"FAIL {name}: reported dropping '{gone}', which is not one of "
                  f"this object's fragments")
            ok = False
            continue
        di = keys.index(gone)
        if s_drop["num_parts"] != s_whole["num_parts"] - 1:
            print(f"FAIL {name}: {s_whole['num_parts']} fragments whole but "
                  f"{s_drop['num_parts']} after dropping one")
            ok = False
            continue

        fw = fragments_of(s_whole)
        fr = fragments_of(s_reseed)
        fd = fragments_of(s_drop)
        keep = [i for i in range(len(fw)) if i != di]

        # The anchor is the largest fragment. Dropping rank >= 2 must leave it
        # alone -- if it moves, the two arms are not the same task.
        aw = int(np.argmax(np.asarray(s_whole["anchor_parts"])))
        ad = int(np.argmax(np.asarray(s_drop["anchor_parts"])))
        if aw == di:
            print(f"FAIL {name}: the dropped fragment '{gone}' WAS the anchor. "
                  f"Rank {a.rank} should never select it; check the area "
                  f"ranking for ties.")
            ok = False
        elif keep.index(aw) != ad:
            print(f"FAIL {name}: the anchor changed from fragment {aw} to "
                  f"fragment {keep[ad]} when the rank-{a.rank} sherd was "
                  f"dropped. This is a different task, not a missing piece.")
            ok = False

        allpts = np.concatenate(fw)
        span = float((allpts.max(0) - allpts.min(0)).max())

        rf, rs = compare(fw, fr, keep, keep, span)
        df, ds = compare(fw, fd, keep, list(range(len(fd))), span)

        cw = [len(x) for x in fw]
        print(f"{name.split('/')[-1]:22s} {len(fw):5d} {gone[:10]:>10s} "
              f"{span:9.3f} {float(s_whole['scales']):8.3f} "
              f"{float(s_drop['scales']):8.3f} | "
              f"{rf.mean():11.2f}% {df.mean():9.2f}% | "
              f"{rs.mean():11.2f}% {ds.mean():9.2f}%")
        rows.append((rf.mean(), df.mean(), rs.mean(), ds.mean(),
                     cw[di], sum(cw)))

    h5.close()

    if not rows:
        print("\nFAIL: no object could be compared.")
        return 1

    rf, df, rs, ds, _, _ = (np.array(x) for x in zip(*rows))
    print()
    print("What the numbers mean, in the pot's own terms")
    print("---------------------------------------------")
    print(f"Re-sampling alone (nothing removed) moves a kept sherd's centre by "
          f"{rf.mean():.2f}% of the pot's size")
    print(f"and changes its shape by {rs.mean():.2f}%. That is the floor: it is "
          f"what 'the same pot, drawn twice' looks like.")
    print(f"Removing the rank-{a.rank} sherd moves a kept sherd's centre by "
          f"{df.mean():.2f}% and changes its shape by {ds.mean():.2f}%.")
    print()

    # A kept sherd must still be the SAME sherd. Shape is the test for that,
    # because it is measured with each fragment's own centroid removed and so
    # cannot be inflated by the frame moving.
    floor = max(rs.mean(), 1e-6)
    if ds.mean() > 5.0 * floor and ds.mean() > 0.5:
        print("FAIL: the kept sherds come back a different SHAPE, well beyond "
              "what re-sampling explains. Something other than the point budget "
              "changed; do not run the experiment on this.")
        ok = False
    else:
        print(f"Kept sherds are the same sherds: shape disturbance {ds.mean():.2f}% "
              f"against a re-sampling floor of {rs.mean():.2f}%.")

    print()
    print(f"THE BAR THIS EXPERIMENT MUST CLEAR: {df.mean():.2f}% of pot size.")
    print("Absence necessarily re-centres and re-normalises the pot, so a result")
    print("smaller than that is the loader moving the frame, not the model")
    print("failing. Report the effect against this number, not against zero.")
    print()
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
