# Handoff — attempt ranker (live file; overwrite, don't pile up)

- Now (2026-10-05): held-out test done (job 32317912, pre-registration @ 2d07202).
  narrow_bottle3 passes: Layers 1+2 top 20 all genuine (random top 5 13.2%); galli_pot
  top 5 all genuine, 0 of 257 near-misses above the best genuine. Layer 1 alone misses
  the top 5 on both: the ranking is Layer 2's. Results in ticket 05.
- Done: the 31 rejected genuine galli_pot attempts all fail on the flat base (sherd 0),
  at the floor-to-wall corner; renders show it seated. Broken measurement (inferred).
  Ranking unaffected. Revision 4 only if it bites, and never re-tested on these two pots.
- Done: ticket 06 (TORA, job 32330575 after the converter scale fix 0dce053; 32329999
  void). narrow_bottle3 passes (top 5: 4 genuine); plate misses (best genuine 84, AUC
  0.41): small floor sherds put in the wrong place still read as snug. Ruler checks
  pass on both.
- Done: Revision 4 overlap gate (job 32345673): failed by its ruler. Share of a sherd's
  surface inside another is inflated on tiny sherds by GARF's slightly pressed-in joins,
  so the cut-off came out at 37.8% and TORA plate stayed at rank 81. The drawing shows
  the overlap itself is seen (17% vs 1.6%).
- Done (2026-10-06): Revision 5 (area away from a one-wall join strip, job 32352965):
  no fresh TORA pot qualified (0 genuine in 200 on bottle3 and plate), so no test. On
  seen attempts it catches the plate's sherd-on-sherd leader (74 vs cut-off 71), plate
  best genuine 84 -> 53, but rejects 40/305 correct galli_pot attempts; drawn (32376045),
  all are long pressed GARF seams, not overlap. Measurement broken; not adopted. Revision
  3 stands. Details: preregistration-overlap5.md.
- Done (2026-10-08): ticket 07, conservator's blind look at the Juglet top 5 matched the
  key (pick 1 genuine, sherd 7 flipped in 2-5); the key's sherd-4 mark was its threshold.
  Ticket 08: U17 written back after refute-finding (0 refuted, 5 weakened), status open,
  partly answered; hard-negative and loosening controls failed.
- Next, cheapest first: ticket 03 re-draw on the Juglet; turn angles for the
  narrow_bottle3/galli_pot top 5s; a Layer 2 that scores the nudge, not the gap.
- Open faults, stated not fixed: overlap (a sherd on another) is not gated, two rulers
  failed (Revisions 4, 5); small featureless sherds misplaced but snug fool both
  layers (TORA plate, ticket 06); inside-out misfires (narrow_bottle4, plate, galli_pot
  sherd 7; not gating); small-move control (ticket 02) still fails; `l2_top_look.py`
  titles hardcode "Juglet" and 9 sherds.
- Spartan requests from cloud threads go through the Connect Spartan workspace thread
  (via the coordinator); renders come back through the project's shared folder.
- Synthetic check: `scripts/l1_synthetic.py` (Spartan only).
