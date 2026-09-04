# O6 — Does the Juglet failure survive a valid reference?

**Status:** first half answered 2026-09-05 · **Blocked by:** [O2](O2-valid-evaluation.md)

## Why it matters

The Juglet failure is currently a **visual verdict on one pot**: anchor sherd with the
other eight clustered against one side, no vessel. That is a **lead, not a conclusion**,
and it is the single result this project leans on hardest.

Two distinct faults are both real and must not blur together:

1. **The method** fails to rebuild this vessel — genuine, confirmed by looking.
2. **The reference** was an invalid scan layout, so the scores were meaningless.
   **Fixed 2026-08-10.**

The broken scores *concealed* the genuine failure rather than excusing it. But one
object, judged by eye, cannot carry a thesis claim on its own.

## What is already ruled out

- Not a **shape** problem: the Juglet is *more* axially symmetric than the average
  training object; its handle is 3.6% of the surface.
- Not a **real-vs-synthetic** problem: that gap does not exist.
- Not a **scoring-units** artefact. The `juglet_gt` runs sit at `scales` = 0.511,
  inside the band the model was trained on, so neither of the two units bugs that
  invalidated the Fractura ceramics touches them.
- The model **never sees the target**. In anchor-free mode every part is centred and
  non-anchor parts randomly rotated, so the input is nine loose sherds. The reference
  is a yardstick, never an instruction. The proposed assembly is TORA's own unaided
  reconstruction.

## Done when

**Either**

- [x] a correct assembled reference exists for the Juglet, and it is re-scored against it
      — `juglet_gt.hdf5`, hand-reassembled by the conservator in Blender 2026-08-10 and
      fitted back to the source fragments as a rigid transform with 0.0000% residual.
      Three runs scored against it: 31.4°, 33.5°, 58.2° mean non-anchor rotation, with
      3–4 of 9 fragments seated against an anchor floor of 1 of 9. **The failure
      survives a valid reference.** Whether those three numbers differ from each other
      by more than run-to-run noise is the first ticket of
      [O8](O8-what-stops-the-juglet.md),

**or**

- [ ] the same qualitative failure is reproduced on **at least 3 worn multi-sherd
      vessels**, with the verdicts rendered side by side and the run-to-run variation
      shown (generations vary noticeably — that instability is itself a documented
      warning sign).

The **first** condition now holds, so the failure is no longer a scoring artefact.
The second is still open and still worth doing: one pot cannot carry the claim, and
the Juglet is not only worn but **incomplete**, which no other object here is.

*Why does it fail* is a separate question and does not belong in this one — it is
[O8](O8-what-stops-the-juglet.md), charted at `.scratch/juglet-cause/map.md`. The
standing answer of "worn fracture surfaces" is exactly what O8 tests rather than
assumes; the diagnosis in `JUGLET_TORA_ROOTCAUSE.md` was computed before the units
fixes and two of its findings are void.

## Source

`docs/notes/JUGLET_TORA_ROOTCAUSE.md`, `JUGLET_TORA_TEST_PLAN.md`, `artifacts/juglet_viz/`,
`scripts/build_juglet_ground_truth.py`.
