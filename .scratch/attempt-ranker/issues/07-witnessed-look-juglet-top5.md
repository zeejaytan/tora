# 07: Witnessed look at the Juglet's top 5

**What to build:** the conservator's own verdict on the 5 attempts the ranker would show,
looked at blind and then with the least-sure sherd named.

**Answers:** U17

**Needs-eye:** the Juglet top 5, staged as five singles from pair descs this ticket
writes — closes on a witnessed look plus a conservator note, never on numbers alone.

**Blocked by:** 02

**Status:** ready-for-agent (started 2026-10-06; conservator chose to move on from overlap)

- [ ] Lead writes five `single:` descs (full-detail sherds as placed); the
      visual-qa-helper stages them; gates pass
- [ ] Pass 1, blind: the conservator's verdict per attempt recorded before any sherd is
      named
- [ ] Pass 2: the least-sure sherd named per attempt; second verdict recorded
- [ ] Each verdict recorded beside its rank; every note gets a same-round agent reply

## Log

- 2026-10-06: `scripts/u17_top5_export.py` writes the Revision 3 top 5 (Layer 1
  jug_v2_32274553, Layer 2 l2_32147567, bundles juglet_32107634) as posed full sherd
  meshes, one fixed colour per sherd, no labels, to Spartan `TORA/rank_u17/jug_top5/`.
  Five blind `single:` descs in `visual-qa/viewer/pairs/u17_juglet_top{1..5}.json`
  (visual-qa d5a2274); staging dry-run on a synthetic mesh passed. Labels are read from
  the key only after the blind verdicts are recorded. Ticket 02 (small-move control) is
  still open; this look goes ahead regardless, at the conservator's call.
- 2026-10-08, **pass 1 verdicts (blind, conservator, shared viewer on phone), recorded
  before the key is opened:** pick 1 correct; picks 2, 3, 4 and 5 each have the yellow
  sherd flipped (yellow-green = sherd 7, "olive" in `top.json`; no other sherd is
  yellow). Verbatim: "1 seem to be the correct assembly, all others have yellow piece
  flipped". Viewer panel covered the model on a phone; Hide panel added (visual-qa 10daed1).
- 2026-10-08, **unblinded** (`l2_top_look.py`, Spartan, at 09d526e; picture
  `/mnt/project-files/u17_jug_top5_unblind.png`):
  ```
  rank12 rank1 own/right-way worst  per-sherd gap (% of pot; * = turned, ! = not own)
   1  589  9/9  1.17  0.96 0.99 0.97 1.08 0.86 0.91 1.13 1.17 1.13   worn_d400_s7_ds4 #11
   2  396  9/8  1.21  0.96 0.80 0.91 1.20 0.76 0.64 0.77 1.21* 0.78  noise_d100_s7_ds1 #15
   3  539  9/7  1.22  0.94 1.00 0.92 0.89 0.80* 0.83 0.93 1.22* 0.59 worn_d400_ds1 #18
   4  397  9/7  1.28  0.95 1.15 1.16 0.90 0.90* 1.15 1.01 1.28* 0.67 worn_d400_s7_ds1 #18
   5  410  9/8  1.31  0.90 0.67 0.83 1.21 0.91 0.64 0.72 1.31* 0.78  noise_d100_ds1 #15
  ```
  **Eye and key agree on every pick's verdict:** pick 1 is the genuine attempt; 2-5 are
  near-misses (every sherd home) and in each the turned sherd includes sherd 7, the one the
  conservator named. Not seen blind: sherd 4 (purple) is also turned in picks 3 and 4.
  Pass 2 names sherd 4 in picks 3 and 4 (the sherd the eye did not flag).
  Weight: one pot, one method (GARF, 1,400 attempts, 2 genuine), one look.
