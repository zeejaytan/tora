# Calibration: U17 cut-offs set on the set-aside Fractura pots

Committed **before** any Layer 1 score of a Fractura attempt exists and before any Layer 2
gap is joined to a Fractura label. `scripts/u17_calibrate.py` prints this file's commit.

**Why.** The Juglet's breaks were simulated and fit perfectly (true join 0.6% of pot);
Fractura's sherds are real, separately scanned fragments (true join ~1%, ticket 02 log).
A cut-off meant to pass correct reassemblies must be set on real scans. Fractura pots have
no real size, so cut-offs are in **% of pot size** (longest box side; nominal 100 mm).
Conservator's permission to spend the set-aside pots on this: 2026-10-03.

## Pots

| Role | Pots | Why |
|---|---|---|
| Calibration | blue_pot, narrow_bottle2, narrow_bottle4, pink_bowl, plate | set aside in ticket 04 (right too often): many genuine attempts, which is what a pass cut-off is set from |
| Test (held out) | narrow_bottle3, galli_pot | narrow_bottle3 qualifies (genuine rare); galli_pot (10 sherds, 22% genuine, 257 near-misses) is the richest pot for telling turned sherds apart, scored as a "right often" side case |
| Unused | narrow_bottle1 | no attempt has every sherd in place |

Neither test pot is ranked by Layer 1 or joined to a label until the test pre-registration
is committed. (Their label-free Layer 2 gaps were already summarised in ticket 02's
groundwork, with no label.)

## Fixed before calibration (not tuned)

- Layer 1 bin: **10.77% of pot** (the Juglet's 7 mm on 65 mm). Inside-out rule unchanged.
- Layer 2 settings exactly as in `preregistration-l2.md` (ed7bd42).
- Layers 1+2 order unchanged: Layer 1 pass, then worst-sherd gap, then profile deviation.

## The rules

1. **Layer 1 profile cut-off** = the largest, over the 5 calibration pots, of the 99th
   percentile of genuine attempts' profile deviation. A cut-off must not reject correct
   reassemblies. For comparison, the Juglet's 7 mm is 10.77%.
2. **Layer 2 "unfixable" cut-off** (flag for the conservator only; not used in the order)
   = the largest, over the 5 calibration pots, of the 99th percentile of the per-sherd gap
   in genuine attempts.
3. Reported, not tuned: the share of genuine attempts the inside-out rule flags, per pot.
   Above 1% is a fault to be stated, not fixed on these pots before the test.

## Development read-outs (calibration pots; not evidence for U17)

Per pot and class (genuine, near-miss, other): profile deviation, inside-out share, worst
gap, share passing Layer 1 and share flagged unfixable under the new cut-offs; near-miss
vs genuine worst-gap AUC; best genuine rank, Layer 1 alone vs Layers 1+2. These pots are
easy (random top 5 already finds a genuine attempt 97.7–100% of the time), so ranks here
say nothing about U17.

## Revision 2 (after jobs 32157454 and 32159300) — committed before the rerun

Run 32157454 set a 23.42% profile cut-off from plate alone. Render 32159300 showed both
faults were **broken measurements, not wrong placements** (ticket 05 log): the height
bands fail on a flat floor, and the sphere-based inside-out rule misreads flat floor
sherds and S-shaped neck sherds. Conservator chose to repair Layer 1 and recalibrate on
the same 5 pots (2026-10-03). Changed, and fixed before the rerun:

- **Profile measure: `--profile outer`** (`rank_attempts.py` docstring). Only the outer
  surface; each sherd's offset at right angles to the other sherds' outer outline, as SfS++
  checks its profile curve (one surface, orthogonal distance to a local line; SfS++ supp.
  Alg. 3). Points beyond the others' reach (sideways > **2% of pot**) are not judged.
  Attempt deviation = worst judged sherd. The bins above no longer apply.
  Synthetic check before the run (plate and bottle, 6 mm wall): correct attempts 0.04–0.16
  mm; one sherd lifted 15 mm, upside down or inside out 7–20 mm; pushed out 5 mm 1.7–3.2
  mm. Blind to: a rim sherd stood on end (it then touches nobody's outline: reported as
  *unjudged*), a flat disc turned over (same shape), sliding along a straight wall.
- **Inside-out rule: reported, does not fail an attempt** (`--io-gate off`).
- Rules 1 and 2 unchanged (99th percentile of genuine, largest over the 5 pots). Rule 3
  now also reports the share of genuine attempts with an unjudged sherd; reported, not
  tuned, not used in the pass.
