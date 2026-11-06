"""Identity check for own_place's whole-pot ruler (pr-workspace wear-beyond-juglet 13).

On a run of COMPLETE pots (round 2, nothing missing) the answer key must say what it said
before the change:
  1. without a pot size, every draw's own / swap / right-way-round count equals the
     own_place.json the run wrote with the earlier key;
  2. with --pot-size copies.csv (the whole pot = the same sherds, measured on the mesh rather
     than on the sampled points), the counts are reported side by side and every draw that
     differs is listed with the two rulers' sizes; swap_box (what --reconcile checks) must
     equal the stored swap on every draw.

    python scripts/check_pot_size_identity.py RUN_DIR copies.csv     (exit 1 on a mismatch in 1)
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from own_place import read_pot_sizes, score_object  # noqa: E402
from readout import clouds_by_object  # noqa: E402

KEYS = ("own", "swap", "oriented")


def main() -> int:
    run, csvp = Path(sys.argv[1]), Path(sys.argv[2])
    stored = json.loads((run / "own_place.json").read_text())
    sizes = read_pot_sizes(csvp)
    table = clouds_by_object(run)
    same_bad, pot_diff, box_bad, draws = [], [], [], 0
    for name in sorted(table):
        _, plain = score_object(table[name])
        _, whole = score_object(table[name], sizes)
        for cloud in plain:
            for k, (old, p, w) in enumerate(zip(stored[name][cloud], plain[cloud], whole[cloud])):
                draws += 1
                a = tuple(old[x] for x in KEYS)
                if a != tuple(getattr(p, x) for x in KEYS):
                    same_bad.append(f"{name} {cloud} {k}: stored {a}, now {tuple(getattr(p, x) for x in KEYS)}")
                if w.swap_box != old["swap"]:
                    box_bad.append(f"{name} {cloud} {k}: stored swap {old['swap']}, swap_box {w.swap_box}")
                b = tuple(getattr(w, x) for x in KEYS)
                if a != b:
                    pot_diff.append(f"{name} {cloud} {k}: box {a}, whole pot {b}")
        w0, p0 = whole["raw"][0], plain["raw"][0]
        print(f"{name}: box {p0.unit:.4f}, whole pot {w0.unit:.4f} units "
              f"(whole/box {w0.unit / p0.unit:.4f})")
    print(f"\n{draws} draws (both clouds).")
    print(f"1. no pot size vs the stored own_place.json: {len(same_bad)} draw(s) differ")
    for x in same_bad:
        print("   ", x)
    print(f"2. whole-pot size vs the box: {len(pot_diff)} draw(s) differ on own/swap/right way round")
    for x in pot_diff:
        print("   ", x)
    print(f"   swap_box vs the stored swap: {len(box_bad)} draw(s) differ")
    for x in box_bad:
        print("   ", x)
    return 1 if (same_bad or box_bad) else 0


if __name__ == "__main__":
    raise SystemExit(main())
