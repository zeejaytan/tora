# Handoff — attempt ranker (live file; overwrite, don't pile up)

- Now (2026-10-05): held-out test done (job 32317912, pre-registration @ 2d07202).
  narrow_bottle3 passes: Layers 1+2 top 20 all genuine (random top 5 13.2%); galli_pot
  top 5 all genuine, 0 of 257 near-misses above the best genuine. Layer 1 alone misses
  the top 5 on both: the ranking is Layer 2's. Results in ticket 05.
- Done: the 31 rejected genuine galli_pot attempts all fail on the flat base (sherd 0),
  at the floor-to-wall corner; renders show it seated. Broken measurement (inferred).
  Ranking unaffected. Revision 4 only if it bites, and never re-tested on these two pots.
- Now: ticket 06 (second method, TORA), ticket 07 (conservator's witnessed look at the
  Juglet top 5), ticket 08 (write back to U17, refute-finding offered first).
- Open faults, stated not fixed: inside-out misfires (narrow_bottle4, plate, galli_pot
  sherd 7; not gating); small-move control (ticket 02) still fails; `l2_top_look.py`
  titles hardcode "Juglet" and 9 sherds.
- Spartan requests from cloud threads go through the Connect Spartan workspace thread
  (via the coordinator); renders come back through the project's shared folder.
- Synthetic check: `scripts/l1_synthetic.py` (Spartan only).
