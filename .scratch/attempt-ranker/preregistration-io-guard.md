# Pre-registration: U17, the inside-out rule as a gate again, with a sherd-size guard (ticket 11)

Committed **before** any guarded flag is counted on any pot. `scripts/u17_io_guard.py`
prints this file's commit.

## Why

The inside-out rule (`check_inside_out.rule_flag`, juglet-cause 14: the sherd's hollow
side must face into the pot) agreed with the key on 212 of 212 Juglet sherds, and on TORA's
narrow_bottle3 top 5 it flagged exactly the green sherd in picks 3 and 4, which the
conservator saw inside out, and nothing in picks 1, 2, 5 (ticket 09). Revision 3 does not
gate on it because it misfires on correct attempts: narrow_bottle4 sherds 1 (46% of the
pot) and 3 (28%), plate floor sherd 5 (54.5% of genuine), small chips on galli_pot and
narrow_bottle1 (3%). Ticket 14 proposed a size guard.

## The rule (fixed)

- The flag counts only on a sherd whose share of the pot's total surface area is inside a
  band [lo, hi]; outside it the sherd is not judged for inside-out.
- The band is chosen on GARF's five calibration pots only (Revision 3 ranks
  `calib_32274553`, labels with the turn limit from ticket 10): from lo in {0, 2, 5, 10}%
  and hi in {20, 25, 30, 40, 50, 100}%, the bands where on **every** calibration pot at most
  **1%** of genuine attempts carry a guarded flag; of those, the one judging the most
  calibration sherds (ties: the wider band). If none qualifies, no gate: said so.
- Order: Layer 1 pass AND no guarded flag, then worst-sherd gap, then profile (Revision 3
  otherwise unchanged).

## Read-outs

Per calibration pot: each sherd's size and its flag rate on genuine attempts. The grid.
Per pot (calibration, GARF test, TORA seen): Revision 3 against the guarded gate, kept,
best genuine rank, top-5 classes, genuine and near-miss attempts the gate removes.

## Decision rule

- Useful if, on the pots it is applied to, it removes near-misses from the top 5 without
  losing any pot's top-5 genuine, and rejects at most 1% of genuine attempts on any pot.
- Every rejected genuine attempt on a non-calibration pot is a misfire to be looked at
  before reporting (which sherd, its size).
- Every failure is named: method failed, measurement broken, or reference wrong.

## Prediction, written before the run

The band excludes the largest sherds (narrow_bottle4's 46%) and the chips, so hi lands
near 25-40% and lo near 2-5%. **Risk, stated:** plate floor sherd 5's misfire comes from
flatness, not size; if it is mid-sized, no band clears plate at 1% except a narrow one,
and the gate then judges few sherds. On TORA narrow_bottle3 (4 sherds of roughly a quarter
each) the green sherd may fall outside a band set by narrow_bottle4, in which case the
gate would not catch the case that prompted it; that would be reported plainly.

## Weight

All pots here have been seen; the calibration pots shaped the band. A help on TORA
narrow_bottle3 is a design check, not a test. The next fresh pot that qualifies is the test.
