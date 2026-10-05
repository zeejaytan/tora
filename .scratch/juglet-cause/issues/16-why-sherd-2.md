# 16: Why does neither method seat Juglet sherd 2?

**What to build:** an answer to "what is it about sherd 2?", stated as something measurable.

TORA's three best Juglet attempts (ticket `u10-juglet-ceiling/10`: rough 1x (08) s42,
presentations 18 and 2, 7 of 9 the right way round) all fail on sherd 2. It is turned over
166-176 degrees and sticks out past the pot's left side. Sherd 2 is also one of the turned
sherds in the near-miss looked at the same day (noise_d100 t10s7, presentation 22,
attempt 19: sherd 2 at 162 degrees, outline up to 9 mm out). On GARF, sherd 2 is the sherd
that wanders most: it sits in another sherd's home 770 times in 1,400 attempts, against
526 for the next sherd (`GARF/.scratch/rough-worn-dose/issues/04`). Pictures:
`/mnt/project-files/best_look_noise_t10_*.png` and `flip_look_d19.png` (debug aids, not the
look). So far this is four TORA attempts picked for being the best, plus one GARF count. It
is a lead, not a finding.

Three explanations, each pointing to a different one of the three answers, and the work
must keep them apart:
1. **The reference is wrong for sherd 2.** Both methods "fail" the same sherd because the
   answer key places it wrongly. The conservator's `juglet_gt` already has known faults
   (sherd 7 off by 5-11 degrees; joins overlapping 0.2-0.5 mm, G1). This is checked first,
   because it would void the other two.
   **Conservator, 2026-10-05: "the sherd I placed is correct in gt."** The placement of
   sherd 2 in `juglet_gt` stands on the conservator's word. The join gap/overlap
   measurement below still runs, as a check on the joins and not on the placement.
2. **The measurement is hard on sherd 2.** For example, sherd 2 could be nearly symmetric,
   so a half turn barely changes its outline, and the scoring call depends on fine
   detail.
3. **The method genuinely cannot place it.** Sherd 2's break faces carry too little to
   match on (worn, short, or facing the missing sherd), or no neighbour's break face fits
   it.

**Answers:** O8 (also feeds `GARF/intent/G1`: a named, measurable property of one sherd is
the kind of mechanism G1's "Done when" asks for)
**Blocked by:** None (can start immediately). All inputs are saved; no new sampling runs.
**Status:** ready-for-agent. **Re-scoped 2026-10-05 (conservator's choice):** the question is
now why sherds 2, 4, 5, 6 and 8 almost never go home the right way round while 1, 3 and 7
sometimes do, on both methods. The break-face step below is measured for all nine sherds
and compared across the two groups (`t16_break.py`, read-only on `juglet_gt.hdf5`).
**Needs-eye:** sherd 2 at home in `juglet_gt`, with its joins to its neighbours, staged
in visual-qa as a single look (`single:`) with sherd 2 coloured. The conservator says
whether it sits where they put it and whether its break edges meet. A visual-qa desc
under `visual-qa/viewer/pairs/` is written when the laptop is on.

- [x] **Is it really sherd 2?** For every sherd, count how often it is wrong (not the
      right way round) across all 3,120 ticket-10 attempts (six jobs 32274395-400, solid
      cloud, `own_place.json`), and across GARF's 1,400 saved attempts with GARF's
      right-way-round scoring. Report per sherd and per model. Stop if sherd 2 is not
      clearly the worst on both methods, and say which sherd is. Also check that "sherd 2"
      is the same physical sherd in both: compare the point counts per part and the
      `juglet_gt.hdf5` part order that both loaders read.
- [ ] **Reference first.** The conservator's look at sherd 2 at home (Needs-eye above).
      Alongside it, measure the gap and the overlap between sherd 2's break faces and each
      neighbour's in `juglet_gt`, in mm, against the same figures for the other joins. If
      sherd 2's joins are the worst in the reference, that is answer 3 (reference wrong),
      and the remaining items wait.
- [ ] **Symmetry.** For each sherd, the best fit of the sherd onto its own home after a
      half turn about its outward normal, in mm. A sherd that fits itself well when spun
      can't be told apart from its spun self by outline alone. Report sherd 2's figure beside
      the others'.
- [ ] **Break faces.** For each sherd: break-face area, longest break edge in mm, and
      which neighbour (or the missing sherd) each break edge faces. Report whether sherd 2
      is the sherd with the least break face that meets a real neighbour.
- [ ] One line in O8, and in G1 if the mechanism holds for GARF too, naming which of the
      three answers it is and the weight (one pot; both methods).

All computation runs on Spartan, in the held CPU allocation if one is up (workspace rule
6). The laptop only stages the look.

## Result so far (2026-10-05)

**Step 1 stopped the ticket as written: sherd 2 is not the worst sherd.** Counted over every
saved attempt, it is one of five sherds that almost never go home the right way round, on
both methods. Sherd 0 is the anchor and never fails.

| sherd | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| TORA, % of 3,120 attempts not right way round | 56 | 99 | 82 | 99 | 99 | 98 | 68 | 96 |
| GARF, % of 2,140 attempts not right way round | 81 | 92 | 85 | 96 | 94 | 92 | 81 | 88 |

Worst first: TORA 4, 5, 2, 6, 8, 3, 7, 1; GARF 4, 5, 6, 2, 8, 3, 7, 1. GARF's count
covers 2,140 saved attempts, not the 1,400 named above: the script took every `rwlora_eval`
run on `juglet_gt` except the `_ns`/`_rs` arms (107 rescored from saved clouds because
their `own_place.json` predates `point_pct`). The split is the same on both methods:
sherds 1, 7 and 3 sometimes go home; sherds 2, 4, 5, 6 and 8 almost never do. Sherd 2
stood out in the four best TORA attempts because, in those few attempts, the other four
happened to land. That was selection from a handful, which is why the ticket called it a lead.

**Numbering matches.** Each sherd's share of the points is identical in both methods to
three places, its longest extent agrees within 1.1% of the pot, and the distances between
sherd centres agree within 1.1% of the pot. "Sherd 2" is the same physical sherd in both.

**Symmetry (done early, same run).** Spun a half turn about its own outward direction and
nudged to fit, every sherd except the large sherd 0 sits back on its own surface within
0.7-1.2 mm on average. That is at or under the spacing between sampled points (about
1.1 mm) and far under the 4.6 mm seating threshold. At this sampling, the outline of a
small Juglet sherd barely tells it apart from itself turned round. That holds for sherds
that seat (1: 0.74 mm, 7: 0.78 mm) as well as those that do not (2: 0.85 mm, 4: 0.95 mm),
so it does not explain the split by itself. Scoring is not fooled by it: the score compares
each point with its own home point, not with the nearest surface.

**Reference.** Conservator, 2026-10-05: sherd 2's placement in `juglet_gt` is correct.
Nothing in step 1 points at the reference: the same five sherds fail on both methods.

Output: `/mnt/project-files/t16_sherd2_step1_output.txt` (script run read-only on Spartan).
