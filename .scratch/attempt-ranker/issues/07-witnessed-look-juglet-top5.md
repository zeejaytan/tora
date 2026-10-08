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
