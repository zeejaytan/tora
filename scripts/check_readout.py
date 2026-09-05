"""Gate: the anchor correction is applied once, correctly, and cannot be quietly lost.

WHY THIS EXISTS. Three separate units-or-convention faults have produced false findings
in this project in a month, and each survived because the wrong number looked reasonable
in the one place anyone checked it. The most recent: `tora/eval/metrics.py` sums rotation
error over non-anchor fragments but divides by all of them, so every stored
`rotation_error` and `translation_error` carries a free zero, and four of our five
reading scripts pass that dilution straight into a published table. The dilution factor
n/(n-1) is per-object, so a cross-object comparison built from it is wrong by a
different amount in every row.

Prose rules did not stop the last one. This is the check.

WHAT THIS ASSERTS.
  1.  Nine fragments, eight of them turned exactly 40 deg, anchor 0: the stored mean is
      35.56 and the corrected read-out is 40.00. The arithmetic is written out in the
      assertion so it can be checked without reading readout.py.
  2.  The same fixture at 2, 3 and 9 fragments: the correction scales with fragment
      count (x2.000, x1.500, x1.125). It is not a constant that cancels.
  3.  Translation is diluted by the identical divisor and is corrected too.
  4.  Seating reads as a count with its free anchor named; no formatter emits a bare
      fraction.
  5.  Pooling records made with different settings raises; identical settings pool.
  6.  A settings field the run never saved reads "unrecoverable", and that word reaches
      the printed view.
  7.  Model size 0.041 and 61.0 raise the out-of-band flag; 0.511 does not. A run
      evaluated before the unit-box fix raises its own flag.
  8.  A subset of 8 of 9 fragments divides by 8, not 9.
  9.  The unit-box derivation moved out of rescore_part_acc.py unchanged, and the
      chamfer matches pytorch3d 0.7.8 -- both directions SUMMED, no 0.5;
      `anchor_free` does not change the anchor count and `multi_anchor` warns instead
      of silently correcting by the wrong number.
  10. A warning is printed once however many draws or rungs raise it, and a size sweep
      collapses to one line naming its range. A warning repeated fourteen times is a
      warning nobody reads.
  11. An offset is only ever reported as a fraction of the object, and the read-out
      states which size it divided by -- the unit box on a run scored after the fix,
      the stored scale on an older one. They are not the same denominator.

NO SNAPSHOT TESTS. A golden-output test written any time in the last month would have
frozen the diluted figure and certified the bug.

Run:  python scripts/check_readout.py     (0 = the ruler is sound)
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from readout import (  # noqa: E402
    FLAG_PRE_UNIT_BOX,
    FLAG_SCALE_OUT_OF_BAND,
    ProvenanceMismatch,
    chamfer,
    unit_box_threshold,
    format_flags,
    format_seated,
    format_turn,
    pool,
    read_run,
    unit_box_scale,
    weight,
)

FAILURES: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  ok    {label}")
    else:
        print(f"  FAIL  {label}" + (f"\n          {detail}" if detail else ""))
        FAILURES.append(label)


def make_run(
    tmp: Path,
    name: str,
    *,
    n_fragments: int,
    stored_rotation: float,
    stored_translation: float = 0.0,
    part_accuracy: float = 0.0,
    scale: float = 0.5,
    post_fix: bool = True,
    unit_translation: bool = True,
    hydra: dict | None = None,
    draws: int = 1,
    object_name: str = "juglet",
) -> Path:
    """A minimal run directory: results/ plus optionally .hydra/config.yaml."""
    run = tmp / name
    (run / "results").mkdir(parents=True)
    for g in range(draws):
        entry = {
            "name": object_name,
            "dataset": "zeroshot/juglet_gt",
            "num_parts": n_fragments,
            "generation_idx": g,
            "scales": scale,
            "part_accuracy": part_accuracy,
            "rotation_error": stored_rotation,
            "translation_error": stored_translation,
            "object_chamfer": 0.0,
        }
        if unit_translation:
            entry["translation_error_unit"] = stored_translation
        if post_fix:
            entry["part_accuracy_absolute"] = part_accuracy
        (run / "results" / f"juglet_sample00000_generation{g:02d}.json").write_text(
            json.dumps(entry))
    if hydra is not None:
        (run / ".hydra").mkdir()
        lines = []
        for key, val in hydra.items():
            if key in ("model", "data"):
                lines.append(f"{key}:")
                for k2, v2 in val.items():
                    lines.append(f"  {k2}: {v2}")
            else:
                lines.append(f"{key}: {val}")
        (run / ".hydra" / "config.yaml").write_text("\n".join(lines) + "\n")
    return run


FULL_HYDRA = {
    "ckpt_path": "/data/gpfs/projects/punim2657/TORA/ckpt/bbad_everyday_cka.ckpt",
    "seed": 42,
    "model": {"n_generations": 5},
    "data": {
        "anchor_free": "true",
        "multi_anchor": "false",
        "_target_": "tora.data.zeroshot.JugletGT",
        "num_points_to_sample": 5000,
    },
}


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="check_readout_"))
    try:
        # ------------------------------------------------------------------
        print("\n1. Nine fragments, eight turned 40 deg, the anchor free.")
        # Eight fragments at 40 deg, the anchor skipped by the sum but counted by the
        # divisor:  (8 x 40 + 0) / 9  =  320 / 9  =  35.5555...
        stored = (8 * 40.0 + 0.0) / 9
        check("the fixture reproduces the stored dilution: 320/9 = 35.56",
              abs(stored - 35.5556) < 1e-3, f"got {stored}")

        run = make_run(tmp, "fix9", n_fragments=9, stored_rotation=stored,
                       part_accuracy=4 / 9, hydra=FULL_HYDRA)
        (rec,) = read_run(run)
        # The correction: multiply back by 9/8, recovering the mean over the eight
        # fragments the model actually had to place.
        check("corrected turn_deg is 40.00, not 35.56",
              abs(rec.turn_deg - 40.0) < 1e-6, f"got {rec.turn_deg}")
        check("the diluted value is still reachable, under its long name",
              abs(rec.turn_deg_diluted_by_free_anchor - stored) < 1e-9)
        check("placed = 8, floor = 1",
              rec.placed == 8 and rec.floor == 1)

        # ------------------------------------------------------------------
        print("\n2. The correction scales with fragment count; it is not a constant.")
        expected = {2: 2.0, 3: 1.5, 9: 1.125}
        for n, factor in expected.items():
            r = make_run(tmp, f"fix{n}b", n_fragments=n, stored_rotation=40.0,
                         hydra=FULL_HYDRA)
            (rc,) = read_run(r)
            check(f"{n} fragments -> x{factor:.3f} (40.0 -> {40.0 * factor:.2f})",
                  abs(rc.turn_deg - 40.0 * factor) < 1e-9,
                  f"got {rc.turn_deg}")
        check("a two-fragment object is corrected twice as hard as a nine-fragment one",
              abs(expected[2] / expected[9] - 16 / 9) < 1e-9)

        # ------------------------------------------------------------------
        print("\n3. Translation is diluted by the same divisor, and corrected too.")
        r = make_run(tmp, "trans", n_fragments=9, stored_rotation=stored,
                     stored_translation=0.0888888888888889, hydra=FULL_HYDRA)
        (rc,) = read_run(r)
        check("gap 0.08889 (=0.8/9) reads as 0.1000 over the eight placed",
              abs(rc.gap - 0.1) < 1e-9, f"got {rc.gap}")

        # ------------------------------------------------------------------
        print("\n4. Seating is a count, with the free anchor named.")
        line = format_seated(rec)
        check("reads '4 of 9 sherds seated (1 free)'",
              line == "4 of 9 sherds seated (1 free)", f"got {line!r}")
        check("no formatter emits a bare fraction",
              "0.44" not in line and "0.444" not in format_turn(rec))
        check("format_turn names the fragments it is a mean over",
              "8 sherds it had to place" in format_turn(rec), format_turn(rec))
        # Quantisation: a 9-fragment object can only score multiples of 1/9.
        check("seated is an integer count, so quantisation is visible",
              isinstance(rec.seated, int) and rec.seated == 4)

        # ------------------------------------------------------------------
        print("\n5. Pooling checks that the records were made the same way.")
        same = read_run(make_run(tmp, "poolA", n_fragments=9, stored_rotation=stored,
                                 hydra=FULL_HYDRA, draws=2))
        try:
            pool(same)
            check("identical settings pool", True)
        except ProvenanceMismatch as exc:
            check("identical settings pool", False, str(exc))

        other = dict(FULL_HYDRA, seed=7)
        diff = read_run(make_run(tmp, "poolB", n_fragments=9, stored_rotation=stored,
                                 hydra=other))
        try:
            pool(same + diff)
            check("different seeds raise", False, "pooled silently")
        except ProvenanceMismatch:
            check("different seeds raise", True)
        try:
            pooled = pool(same + diff, across="deliberate: seed sweep")
            check("an explicit reason pools, and travels with the records",
                  any("pooled across settings" in f for f in pooled[0].flags))
        except ProvenanceMismatch as exc:
            check("an explicit reason pools", False, str(exc))

        # ------------------------------------------------------------------
        print("\n6. A field the run never saved is stamped, not guessed.")
        bare = read_run(make_run(tmp, "nohydra", n_fragments=9,
                                 stored_rotation=stored))
        check("absent settings read 'unrecoverable'",
              bare[0].provenance.checkpoint == "unrecoverable")
        check("the word reaches the printed view",
              any("unrecoverable" in f for f in format_flags(bare)),
              str(format_flags(bare)))
        try:
            pool(bare)
            check("unrecoverable provenance blocks pooling", False)
        except ProvenanceMismatch:
            check("unrecoverable provenance blocks pooling", True)

        # ------------------------------------------------------------------
        print("\n7. Health flags fire where they should.")
        for scale, should in ((0.041, True), (61.0, True), (0.511, False)):
            rr = read_run(make_run(tmp, f"scale{scale}", n_fragments=9,
                                   stored_rotation=stored, scale=scale,
                                   hydra=FULL_HYDRA))
            fired = any(f.startswith(FLAG_SCALE_OUT_OF_BAND) for f in rr[0].flags)
            check(f"model size {scale} -> flag {'raised' if should else 'silent'}",
                  fired == should, str(rr[0].flags))
        pre = read_run(make_run(tmp, "prefix", n_fragments=9, stored_rotation=stored,
                                post_fix=False, hydra=FULL_HYDRA))
        check("a run scored before the unit-box fix is flagged",
              FLAG_PRE_UNIT_BOX in pre[0].flags, str(pre[0].flags))
        check("a run scored after it is not",
              FLAG_PRE_UNIT_BOX not in rec.flags)

        # ------------------------------------------------------------------
        print("\n8. A subset divides by the subset.")
        sub = read_run(run, subset={"juglet": 8})
        check("8 of 9 fragments -> denominator 8, floor 1, placed 7",
              sub[0].n_fragments == 8 and sub[0].floor == 1 and sub[0].placed == 7)
        check("the subset correction is 8/7, not 9/8",
              abs(sub[0].turn_deg - stored * 8 / 7) < 1e-9,
              f"got {sub[0].turn_deg}")

        # ------------------------------------------------------------------
        print("\n9. The rescoring derivation, and the ruler it thresholds.")
        pts = np.array([[0.0, 0, 0], [2.0, 0, 0], [0, 1.0, 0]])
        check("unit_box_scale is the longest bounding-box side (2.0)",
              abs(unit_box_scale(pts) - 2.0) < 1e-12)
        a = np.array([[0.0, 0, 0]])
        b = np.array([[3.0, 0, 0]])
        # pytorch3d 0.7.8 chamfer_distance(point_reduction="mean") returns
        # cham_x + cham_y, with no 0.5 -- so two points 3 apart give 9 + 9 = 18.
        # This assertion exists because the halved version shipped here on
        # 2026-09-05 and made every cloud rescoring twice as forgiving as the
        # evaluator it was being compared against.
        check("chamfer sums both directions, as pytorch3d does (3 apart -> 18.0)",
              abs(chamfer(a, b) - 18.0) < 1e-12, f"got {chamfer(a, b)}")
        # The tolerance is compared against a SQUARED distance, so translating it
        # into the stored frame squares the size. A unit box of 2.0 puts TAU at
        # 0.01 * 4 = 0.04. Two scripts here divided by the scale instead of its
        # square, and by the stored scale rather than the box, which is the
        # withdrawn absolute metric.
        check("unit-box tolerance squares the size (box 2.0 -> 0.04)",
              abs(unit_box_threshold(pts) - 0.04) < 1e-12,
              f"got {unit_box_threshold(pts)}")

        # dataset.py:324 flags exactly one anchor -- the largest part -- whatever
        # anchor_free says; only multi_anchor adds more. So multi_anchor settles it,
        # and anchor_free must NOT be read as if it did.
        cfg_free = {**FULL_HYDRA, "data": {**FULL_HYDRA["data"], "anchor_free": "true"}}
        (rf,) = read_run(make_run(tmp, "afree", n_fragments=9,
                                  stored_rotation=stored, hydra=cfg_free))
        check("anchor_free: true still means one free fragment, from config",
              rf.n_anchors == 1 and rf.n_anchors_source == "config",
              rf.n_anchors_source)

        cfg_multi = {**FULL_HYDRA,
                     "data": {**FULL_HYDRA["data"], "multi_anchor": "true"}}
        (rm,) = read_run(make_run(tmp, "amulti", n_fragments=9,
                                  stored_rotation=stored, hydra=cfg_multi))
        check("multi_anchor: true warns that the turn column cannot be trusted",
              any("multi_anchor was on" in f for f in format_flags([rm])),
              str(format_flags([rm])))

        # A sweep that walks the size input on purpose must not print the same
        # sentence once per rung. It printed fourteen identical lines before this.
        spread = []
        for i, sc in enumerate((1.0, 5.0, 15.0, 50.0, 100.0)):
            spread += read_run(make_run(tmp, f"rung{i}", n_fragments=9,
                                        stored_rotation=stored, scale=sc,
                                        hydra=FULL_HYDRA))
        band_lines = [f for f in format_flags(spread)
                      if f.startswith(FLAG_SCALE_OUT_OF_BAND)]
        check("a size sweep raises the band warning once, with its range",
              len(band_lines) == 1 and "1 to 100" in band_lines[0],
              str(band_lines))

        # An offset in an object's own units is unreadable: the ceramics are
        # millimetres. Which size it is divided by must be stated, not assumed.
        (post,) = read_run(make_run(tmp, "gapnew", n_fragments=9,
                                    stored_rotation=stored, stored_translation=0.08,
                                    scale=0.5, hydra=FULL_HYDRA))
        (old_run,) = read_run(make_run(tmp, "gapold", n_fragments=9,
                                       stored_rotation=stored, stored_translation=8.0,
                                       scale=61.0, unit_translation=False,
                                       post_fix=False, hydra=FULL_HYDRA))
        check("a run with translation_error_unit is already a fraction",
              post.gap_denominator == "unit box (GT longest side)"
              and abs(post.gap_object_fraction - post.gap) < 1e-12,
              post.gap_denominator)
        check("an older run is divided by its stored scale, and says so",
              old_run.gap_denominator == "stored scale"
              and abs(old_run.gap_object_fraction - old_run.gap / 61.0) < 1e-12,
              old_run.gap_denominator)

        # A repeated warning printed once per draw is a warning nobody reads;
        # this fired five times on a five-draw run before it was fixed.
        many = read_run(make_run(tmp, "dedup", n_fragments=9,
                                 stored_rotation=stored, draws=5))
        check("a warning that applies to every draw is printed once",
              len(format_flags(many)) == len(set(format_flags(many)))
              and sum("anchor count assumed" in f for f in format_flags(many)) <= 1,
              str(format_flags(many)))

        # ------------------------------------------------------------------
        print("\n10. A view states the weight it can bear.")
        w = weight(same)
        check("weight names objects, draws and trained models",
              "1 object(s)" in w and "2 draw(s)" in w, w)

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} assertion(s)")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("The read-out corrects the free anchor once, and says when it cannot be trusted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
