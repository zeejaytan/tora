"""How much do repeat attempts at the same Juglet job disagree?

Ticket .scratch/juglet-cause/issues/01. Every later ticket on that map compares two
conditions on this one pot; none of those comparisons mean anything until we know how
far apart two runs of the SAME condition land.

Reads only saved results through scripts/readout.py, so the free-anchor correction
(x9/8 on this nine-sherd pot) is applied once, in one place. No GPU.

Three quantities, deliberately separated, because conflating them is what produced the
"31.4 / 33.5 / 58.2 deg" reading this ticket was opened to check:

  within-run   the spread across the draws of ONE run. The sampler is stochastic;
               this is what a single attempt is worth.
  between-run  the spread of run MEDIANS across runs of the same condition. This is
               what a repeat of the whole job is worth.
  draw 0       what you get if you quote generation 0 and call it the run.
"""
from __future__ import annotations

import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from readout import ProvenanceMismatch, format_flags, pool, read_run  # noqa: E402

RUNS = Path("artifacts/juglet_runs")

BASELINE = [
    "lorav_juglet_baseline_29527496",
    "lorav_juglet_baseline_29623885",
    "lorav3_juglet_baseline_29880370",
    "wearft2_jugletgt_baseline_29308186",
]
OTHER = [
    "lorav_juglet_adapter_off_29527496",
    "lorav_juglet_adapter_off_29623885",
    "lorav3_juglet_adapter_off_29880370",
    "lorav_juglet_adapter_on_29623885",
    "lorav3_juglet_adapter_on_29880370",
    "wearft2_jugletgt_wear_v1_29308186",
    "wearft2_jugletgt_wear_v2_29308186",
    "jugletgt_render_wear_v2_29330980",
]


def rows(name):
    return sorted(read_run(RUNS / name), key=lambda r: r.draw)


def line(name, rs):
    t = [r.turn_deg for r in rs]
    return ("%-38s n=%d  draw0 %5.1f | median %5.1f  min %5.1f  max %5.1f  "
            "spread %5.1f | seated %s" % (
                name, len(t), t[0], st.median(t), min(t), max(t), max(t) - min(t),
                "/".join(str(r.seated) for r in rs)))


print("=" * 100)
print("EVERY juglet_gt RUN, non-anchor turn in degrees, one row per run")
print("=" * 100)
allruns = BASELINE + OTHER
data = {}
for name in allruns:
    rs = rows(name)
    data[name] = rs
    tag = "BASE " if name in BASELINE else "     "
    print(tag + line(name, rs))

print()
for f in format_flags([r for rs in data.values() for r in rs]):
    print("  ! " + f)

print()
print("=" * 100)
print("1. WITHIN ONE RUN: how far apart are the five draws of a single attempt?")
print("=" * 100)
for name in allruns:
    t = [r.turn_deg for r in data[name]]
    print("%-38s %s   spread %5.1f" % (
        name, " ".join("%5.1f" % x for x in t), max(t) - min(t)))
w = [max(r.turn_deg for r in data[n]) - min(r.turn_deg for r in data[n]) for n in allruns]
print("\nwithin-run spread across %d runs: median %.1f deg, range %.1f-%.1f deg"
      % (len(w), st.median(w), min(w), max(w)))

print()
print("=" * 100)
print("2. BETWEEN RUNS OF THE SAME CONDITION: the four baselines")
print("=" * 100)
try:
    pool([r for n in BASELINE for r in data[n]])
    print("provenance: identical across all four -- these are true repeats")
except ProvenanceMismatch as e:
    print("provenance differs:\n  " + str(e).replace("\n", "\n  "))
print()
for name in BASELINE:
    print("  %-38s %s" % (name, data[name][0].provenance.describe()))

meds = [st.median([r.turn_deg for r in data[n]]) for n in BASELINE]
d0 = [data[n][0].turn_deg for n in BASELINE]
pooled = sorted(r.turn_deg for n in BASELINE for r in data[n])
print()
print("run medians   : %s  -> spread %.1f deg" % (
    " ".join("%5.1f" % x for x in meds), max(meds) - min(meds)))
print("draw 0 only   : %s  -> spread %.1f deg" % (
    " ".join("%5.1f" % x for x in d0), max(d0) - min(d0)))
print("all %d draws  : median %.1f, min %.1f, max %.1f, spread %.1f deg"
      % (len(pooled), st.median(pooled), pooled[0], pooled[-1], pooled[-1] - pooled[0]))
print("               10th-90th percentile band %.1f-%.1f deg"
      % (pooled[max(0, round(0.1 * (len(pooled) - 1)))],
         pooled[round(0.9 * (len(pooled) - 1))]))
print("seated, all draws: %s of 9 sherds (1 free)"
      % "/".join(str(r.seated) for n in BASELINE for r in data[n]))

print()
print("=" * 100)
print("3. THE DECISION RULE")
print("=" * 100)
sd = st.stdev(pooled)
print("baseline draws: mean %.1f, sd %.1f deg over n=%d" % (st.mean(pooled), sd, len(pooled)))
for k in (1, 5):
    print("  a %d-draw run's median carries a standard error of about %.1f deg"
          % (k, sd / (k ** 0.5)))
print("  two %d-draw runs differ by chance alone up to about %.0f deg (2 sd of the "
      "difference)" % (5, 2 * sd * (2 / 5) ** 0.5))
