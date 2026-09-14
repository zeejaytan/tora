# 01: The own-place scorer, first used on draws we already have

**What to build:** A count of sherds landed in **their own** place, reported beside the
existing count (which lets look-alike sherds swap). It is proven on made-up results, then
run on ticket 12's 20 existing draws from the untouched model. That gives the untouched
model's true own-place count on the Juglet before anything is built.

Spec: the umbrella `.scratch/u10-juglet-ceiling/spec.md`, module 8.

**Answers:** U10

**Blocked by:** None (can start immediately).

**Status:** ready-for-agent

- [ ] It reads the per-draw results the existing readout reads. In each draw, sherd *i*
      counts only if its distance to ground-truth sherd *i* is under the existing count's
      threshold, on the same unit-box ruler. The anchor is handled as the existing
      readout handles it, and the output says how.
- [ ] Per draw it reports:
      - the own-place count;
      - the swap-allowed count;
      - how far off the unseated sherds land, as % of pot height.

      Per arm it reports the distribution and median over draws.
- [ ] A test script on constructed draws exits non-zero on failure:
      - a perfect draw reads 9/9 on both counts;
      - two swapped sherds read 9/9 swap-allowed and 7/9 own-place;
      - everything displaced reads 0.
- [ ] Its swap-allowed count agrees exactly with the existing readout on an old Juglet
      run.
- [ ] It is callable per epoch on a validation set, because ticket 04 chooses on it.
- [ ] It applies U10's stage-1 decision rule to three arms' outputs and prints which
      reading holds.
- [ ] Run on ticket 12's 20 untouched-model draws. The ticket reports the untouched
      model's own-place median against its swap-allowed median.
- [ ] Render: one untouched-model draw, full vessel in the pot's own frame. Sherds are
      coloured by own place, swapped, or off.
- [ ] Written back: U10's scoring box records the untouched baseline's own-place count
      and the date.
