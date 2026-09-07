"""What does telling the model the wrong size actually cost, in sherds seated?

TICKET .scratch/eval-readout/issues/05-does-the-out-of-band-size-cost-anything.md

WHY THIS EXISTS AND WHY IT IS NOT THE LADDER SUMMARISER. `summarise_scale_ladder.py`
already reports a scale sweep, and it reports it in ROTATION. That is the metric this
project has been burned by twice: wear moves turn by about 3 degrees against a 27.7
degree between-pot spread, so a flat curve in turn was guaranteed before the job ran and
carried no information. The wear finding lives in SEATING. So this script reports seating
first and turn only as context, and it never pools the two.

WHAT IT COMPARES. Four arms, run in one job with one settings set:

    A  fresh pots, size as stored (0.319-0.383)   <- reproduces WEAR_TEST_RESULTS s4
    B  fresh pots, size restated at 0.550
    C  worn sweep, size as stored (0.319-0.321)   <- reproduces WEAR_TEST_RESULTS s4
    D  worn sweep, size restated at 0.550

A and C are controls, not spare arms. If they do not land on 0.843 and 0.645 then the
settings do not match the table this is meant to defend, and B and D mean nothing.

THE NUMBER TO READ is not any single arm. It is whether the wear gap survives the move
into the trained band:

    gap as stored      = A - C
    gap renormalised   = B - D

and those two are what the ticket predicts will agree. Arms are PAIRED BY OBJECT -- the
same pot, the same pieces, the same correct answer, differing only in the one number the
model is told -- so the per-object difference is the estimate and the spread of those
differences is its error bar. Averaging the arms separately and subtracting throws away
the pairing and inflates the noise.

HOW THE ERROR BAR IS MADE. Two spreads, and they answer different questions:

  draw scatter   sd across the draws of one object, pooled over objects. This is how
                 much the sampler alone moves the answer. A difference smaller than
                 this is not a result whatever its mean says.
  object spread  a bootstrap over OBJECTS of the paired per-object difference. Objects
                 are the independent unit here (draws of one pot are not), so this is
                 the honest interval on the arm-level claim. Six objects is few; the
                 interval will be wide, and that is the truth rather than a defect.

Seating is the non-anchor rate: (seated - anchors) / (fragments - anchors). The raw
part_accuracy has a floor of 1/k from the clamped anchor and is not comparable across
objects with different piece counts.

Everything is read through scripts/readout.py, the one admissible reader.

Usage:
  python scripts/summarise_scale_cost.py \
      --arm "A=fresh as-stored:/path/scalecost_A_fresh_stored_<jobid>" \
      --arm "B=fresh at-0.550:/path/scalecost_B_fresh_norm_<jobid>" \
      --arm "C=worn as-stored:/path/scalecost_C_worn_stored_<jobid>" \
      --arm "D=worn at-0.550:/path/scalecost_D_worn_norm_<jobid>" \
      --pair AB --pair CD --gap A-C --gap B-D
"""

import argparse
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from readout import TRAINED_SCALE_BAND, format_flags, read_run  # noqa: E402

BOOTSTRAP = 10000
RNG_SEED = 0


def seat_rate(rec) -> float:
    """Fraction of the LOOSE fragments seated. 0.0 = none beyond the free anchor."""
    loose = rec.n_fragments - rec.n_anchors
    if loose <= 0 or rec.seated < 0:
        return float("nan")
    return (rec.seated - rec.n_anchors) / loose


def base_and_wear(name: str) -> tuple[str, str]:
    """Split `blue_pot_e075` into ("blue_pot", "e075"). Fresh sets have no suffix."""
    m = re.match(r"^(.*)_(e\d{3})$", name)
    return (m.group(1), m.group(2)) if m else (name, "")


class Arm:
    def __init__(self, key: str, label: str, run_dir: Path):
        self.key, self.label, self.run_dir = key, label, Path(run_dir)
        self.records = read_run(self.run_dir)
        if not self.records:
            raise SystemExit(f"{run_dir}: no records")
        self.by_object: dict[str, list] = defaultdict(list)
        for r in self.records:
            self.by_object[r.object_name].append(r)

    # ---- per-object -------------------------------------------------------
    def object_rate(self, name: str) -> float:
        v = [seat_rate(r) for r in self.by_object[name]]
        v = [x for x in v if not math.isnan(x)]
        return float(np.mean(v)) if v else float("nan")

    def object_turn(self, name: str) -> float:
        v = [r.turn_deg for r in self.by_object[name] if not math.isnan(r.turn_deg)]
        return float(np.mean(v)) if v else float("nan")

    def object_draw_sd(self, name: str) -> float:
        v = [seat_rate(r) for r in self.by_object[name]]
        v = [x for x in v if not math.isnan(x)]
        return float(np.std(v, ddof=1)) if len(v) > 1 else float("nan")

    # ---- arm level --------------------------------------------------------
    @property
    def objects(self) -> list[str]:
        return sorted(self.by_object)

    @property
    def rate(self) -> float:
        v = [self.object_rate(o) for o in self.objects]
        v = [x for x in v if not math.isnan(x)]
        return float(np.mean(v)) if v else float("nan")

    @property
    def turn(self) -> float:
        v = [self.object_turn(o) for o in self.objects]
        v = [x for x in v if not math.isnan(x)]
        return float(np.mean(v)) if v else float("nan")

    @property
    def draw_scatter(self) -> float:
        """Sampler-only noise on one object's rate, pooled across objects (rms)."""
        v = [self.object_draw_sd(o) for o in self.objects]
        v = [x for x in v if not math.isnan(x)]
        return float(np.sqrt(np.mean(np.square(v)))) if v else float("nan")

    @property
    def draws(self) -> int:
        return max(len(v) for v in self.by_object.values())

    @property
    def scale_range(self) -> tuple[float, float]:
        s = [r.model_scale for r in self.records if not math.isnan(r.model_scale)]
        return (min(s), max(s)) if s else (float("nan"), float("nan"))


def boot_ci(values: np.ndarray, seed: int = RNG_SEED) -> tuple[float, float]:
    """Percentile bootstrap over the OBJECT axis. Few objects -> wide, honestly."""
    values = np.asarray([v for v in values if not math.isnan(v)], dtype=float)
    if values.size < 2:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, values.size, size=(BOOTSTRAP, values.size))
    means = values[idx].mean(axis=1)
    return (float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)))


def pct(x: float) -> str:
    return "  n/a " if math.isnan(x) else f"{100 * x:5.1f}"


def report_arm(a: Arm) -> None:
    lo, hi = a.scale_range
    band_lo, band_hi = TRAINED_SCALE_BAND
    inb = "in band" if band_lo <= lo and hi <= band_hi else "OUT OF BAND"
    print(f"\n--- arm {a.key}: {a.label}")
    print(f"    run          {a.run_dir.name}")
    print(f"    objects      {len(a.objects)}   draws {a.draws}")
    print(f"    size told    {lo:.4f} to {hi:.4f}   ({inb}; trained {band_lo}-{band_hi})")
    print(f"    seated       {pct(a.rate)}% of loose sherds")
    print(f"    draw scatter +-{pct(a.draw_scatter)} points (sampler alone, one object)")
    print(f"    turned       {a.turn:.1f} deg   [context only -- wear moves turn ~3 deg]")
    for line in format_flags(a.records):
        print(f"    flag: {line}")


def report_pair(x: Arm, y: Arm) -> np.ndarray:
    """Paired per-object difference y - x. Returns the per-object differences."""
    shared = [o for o in x.objects if o in y.by_object]
    missing = set(x.objects) ^ set(y.objects)
    print(f"\n=== {y.key} - {x.key}   ({y.label}  minus  {x.label})")
    if missing:
        print(f"    WARNING: {len(missing)} object(s) in one arm only, excluded: "
              f"{sorted(missing)[:6]}")
    if not shared:
        print("    no shared objects -- arms are not paired, nothing to report")
        return np.array([])

    print(f"    {'object':<22} {'wear':<6} {x.key:>7} {y.key:>7} {'diff':>8}")
    diffs, keys = [], []
    for o in shared:
        dx, dy = x.object_rate(o), y.object_rate(o)
        d = dy - dx
        diffs.append(d)
        keys.append(base_and_wear(o)[0])
        base, wear = base_and_wear(o)
        print(f"    {base:<22} {wear:<6} {pct(dx)} {pct(dy)} {100 * d:+8.1f}")

    diffs = np.array(diffs, dtype=float)
    # Bootstrap over the base object, not over the wear rungs of one pot: the five
    # erosion levels of a pot are not five independent objects.
    uniq = sorted(set(keys))
    by_base = np.array([np.mean([d for d, k in zip(diffs, keys) if k == b])
                        for b in uniq])
    lo, hi = boot_ci(by_base)
    scatter = math.sqrt((x.draw_scatter ** 2 + y.draw_scatter ** 2) / 2)
    mean = float(np.nanmean(diffs))

    print(f"\n    mean paired difference   {100 * mean:+.1f} points of seating")
    print(f"    95% CI over {len(uniq)} pots     [{100 * lo:+.1f}, {100 * hi:+.1f}]")
    print(f"    draw scatter for scale   +-{100 * scatter:.1f} points")
    if math.isnan(lo):
        verdict = "too few objects to bound"
    elif lo <= 0.0 <= hi:
        verdict = ("NOT DISTINGUISHABLE FROM ZERO -- the interval covers no change; "
                   "the size input costs nothing readable here")
    else:
        verdict = ("moved: the interval excludes zero, so restating the size changed "
                   "seating")
    print(f"    verdict                  {verdict}")
    return by_base


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arm", action="append", required=True,
                    metavar="KEY=LABEL:PATH",
                    help="e.g. A=fresh as-stored:/path/to/run")
    ap.add_argument("--pair", action="append", default=[], metavar="XY",
                    help="report the paired difference Y-X, e.g. AB")
    ap.add_argument("--gap", action="append", default=[], metavar="X-Y",
                    help="report the wear gap X minus Y, e.g. A-C")
    args = ap.parse_args()

    arms: dict[str, Arm] = {}
    for spec in args.arm:
        key, rest = spec.split("=", 1)
        label, path = rest.rsplit(":", 1)
        try:
            arms[key.strip()] = Arm(key.strip(), label.strip(), path.strip())
        except SystemExit as e:
            print(f"arm {key}: {e}")

    print("=" * 78)
    print("WHAT DOES THE OUT-OF-BAND SIZE INPUT COST? -- read seating, not turn")
    print("=" * 78)
    for a in arms.values():
        report_arm(a)

    for spec in args.pair:
        x, y = spec[0], spec[1]
        if x in arms and y in arms:
            report_pair(arms[x], arms[y])

    gaps = {}
    for spec in args.gap:
        x, y = [s.strip() for s in spec.split("-")]
        if x in arms and y in arms:
            gaps[spec] = arms[x].rate - arms[y].rate
            print(f"\n=== wear gap {spec}: {arms[x].label} minus {arms[y].label}")
            print(f"    {100 * arms[x].rate:.1f} - {100 * arms[y].rate:.1f} = "
                  f"{100 * gaps[spec]:+.1f} points of seating lost to wear")

    if len(gaps) == 2:
        (k1, g1), (k2, g2) = gaps.items()
        print("\n" + "=" * 78)
        print("THE QUESTION THE TICKET ASKED")
        print("=" * 78)
        print(f"    wear gap {k1:<6} {100 * g1:+.1f} points")
        print(f"    wear gap {k2:<6} {100 * g2:+.1f} points")
        print(f"    change            {100 * (g2 - g1):+.1f} points")
        print("\n    The ticket predicted these two agree. If they do, the out-of-band")
        print("    conditioning costs the wear comparison nothing and the section 4")
        print("    numbers stand as levels, not only as a difference. If the gap")
        print("    CLOSES when the size is corrected, part of the twenty points was")
        print("    an artefact of scoring a handicapped model -- report that.")

    print("\nRENDER arm C against arm D at individual-sherd placement before writing")
    print("any claim from this table. The whole-pot outline survives even in the")
    print("worst draw on these objects and will not show you the difference.")


if __name__ == "__main__":
    main()
