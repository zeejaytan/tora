# 01: The own-place scorer, first used on draws we already have

**What to build:** A count of sherds landed in **their own** place, reported beside the
existing count (which lets look-alike sherds swap). It is proven on made-up results, then
run on ticket 12's 20 existing draws from the untouched model. That gives the untouched
model's true own-place count on the Juglet before anything is built.

Spec: the umbrella `.scratch/u10-juglet-ceiling/spec.md`, module 8.

**Answers:** U10

**Blocked by:** None (can start immediately).

**Status:** resolved

- [x] It reads the per-draw results the existing readout reads. In each draw, sherd *i*
      counts only if its distance to ground-truth sherd *i* is under the existing count's
      threshold, on the same unit-box ruler. The anchor is handled as the existing
      readout handles it, and the output says how.
- [x] Per draw it reports:
      - the own-place count;
      - the swap-allowed count;
      - how far off the unseated sherds land, as % of pot height.

      Per arm it reports the distribution and median over draws.
- [x] A test script on constructed draws exits non-zero on failure:
      - a perfect draw reads 9/9 on both counts;
      - two swapped sherds read 9/9 swap-allowed and 7/9 own-place;
      - everything displaced reads 0.
- [x] Its swap-allowed count agrees exactly with the existing readout on an old Juglet
      run.
- [x] It is callable per epoch on a validation set, because ticket 04 chooses on it.
      (`score_batch` takes a validation batch's tensors; wiring it into training is 04.)
- [x] It applies U10's stage-1 decision rule to three arms' outputs and prints which
      reading holds.
- [x] Run on ticket 12's 20 untouched-model draws. The ticket reports the untouched
      model's own-place median against its swap-allowed median.
- [x] Render: one untouched-model draw, full vessel in the pot's own frame. Sherds are
      coloured by own place, swapped, or off.
- [x] Written back: U10's scoring box records the untouched baseline's own-place count
      and the date.

## Result (2026-09-14)

**The untouched model puts 3 of the Juglet's 9 sherds in their own place (median over 20
draws). The evaluator's count says 5.5.** One of the 3 is the anchor, sherd 0, which sits
at its true place in every draw. So about 2 of the 8 loose sherds land home.

| Untouched model, 20 draws (job 30130049) | own place | swap-allowed | sherds not in own place, from home |
|---|---|---|---|
| raw output (what the evaluator scores) | median 3, range 1–6 | 5.5, range 3–7 | median 20.2% of pot size (13.1 mm), middle half 14.4–26.3% |
| solid sherds (each true sherd rigidly placed; what could be glued) | median 3, range 1–6 | 5, range 3–6 | 19.8% (12.9 mm), middle half 14.5–26.7% |

Ruler:
- A sherd is seated when its unit-box chamfer is under 0.01, which means within 7.1% of
  pot size: 4.6 mm on the 65 mm Juglet.
- The Juglet's longest side is its height, so % of pot size is % of height.

- **Reconcile.** The swap-allowed count equals two existing counts exactly, on every draw
  and on both clouds: the evaluator's `results/*.json` and `readout.rescore_from_clouds`.
  That holds on the untouched model and on ticket 12's two wear v3 arms: 60 draws.
- **Anchor.** Sherd 0 is the largest (1927 points). It is pinned exactly at home in every
  draw, and is counted among the 9, as the evaluator counts it. The scorer flags it if it
  ever leaves home.
- **Which sherds land home.** Own-place count per sherd over the 20 raw draws:
  [20, 15, 3, 4, 2, 2, 0, 14, 0]. Sherds 0, 1 and 7 are usually home; sherds 6 and 8
  never are.
- **Where the evaluator's extra seats come from.** Sherds slid one place along into a
  neighbour's spot, not look-alike pairs exchanged:
  - the slides: 5→6 ×11, 4→5 ×9, 8→3 ×5, 2→7 ×3, 7→8 ×3, and others;
  - only 2 of the 43 swapped sherd-draws are mutual exchanges.
- **Wear v3 arms (ticket 12), for context:**
  - adapter on: own place 2 / swap-allowed 4, on both clouds;
  - adapter off: 2 / 5 on the raw output, 2 / 4 on the solid sherds.
- **Render, looked at:** `artifacts/u10/own_place_baseline_median.png`, attempt 19, the
  middle draw (raw: own place 3, swap-allowed 5; solid: the same).
  - Sherds 4 and 5 have slid down and round into sherd 5's and sherd 6's places.
  - The base sherd 6 is displaced up the side.
  - Sherd 8 stands out beyond the handle.
  - The raw and solid pictures are nearly identical.
- **Per-draw scores:** `artifacts/u10/own_place_baseline_30130049.json`.
- **Decision rule.** `--decide` was run with ticket 12's arms as stand-ins, and printed
  "ceiling loses" (+0 on both clouds). That checks the wiring only; it is not a U10
  reading.
- **Tests:** `scripts/test_own_place.py`, all 25 checks pass.

**A correction the scorer turned up.** The evaluator scores the raw output
(`tora/modeling/tora.py`, `validation_step` and `test_step` both pass `trajs[-1]`), not
the solid sherds. So a sherd output as its own mirror image (ticket 13) can count as
seated. Ticket 12 has one mirrored in 10 of 10 draws that still seats.
- It does not block U10: every arm shares it.
- But an arm that mirrors more could gain seats nobody could glue.
- The scorer reports both clouds, and `--decide` flags a reading that differs between
  them.
- **Decided (conservator, 2026-09-14): U10 is decided on the solid sherds, with the raw
  output reported beside it.** `--decide` now prints the solid reading first, marked as
  deciding.

**Weight.**
- One pot, 20 draws, the untouched model only.
- No failure is claimed; this is a baseline. The existing count was not broken: it
  answers a looser question, one that credits a sherd in its neighbour's place. On the
  Juglet that looser question reads about 2.5 sherds higher.

Written back 2026-09-14: U10's scoring box and its "Why it matters" line.
