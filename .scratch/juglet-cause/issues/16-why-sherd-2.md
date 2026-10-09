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
**Status:** resolved (2026-10-05; see Result). **Re-scoped 2026-10-05 (conservator's choice):** the question is
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

## Break faces and joins (2026-10-05, Spartan job 32319267, `t16_break.py` on `juglet_gt.hdf5`)

Output: `/mnt/project-files/t16_break_output.txt`. Mesh area shares match step 1's point
shares sherd for sherd, so the numbering is confirmed a second way.

**The reference joins are tight, sherd 2's included.** Across the 21 places where two sherds
meet, the typical gap is 0.04-0.5 mm, with local overlaps up to 0.6 mm (the 0.2-0.5 mm of G1).
Sherd 2's joins sit at 0.12-0.21 mm, like the rest. Only two near-touches stand apart:
5-7 (0.84 mm over 2 mm) and 2-3 (0.50 mm over 4 mm). Both are corner contacts, not joins.
This agrees with the conservator: nothing here points at the reference.

**Break-face size does not split the groups.** The share of break face that meets a
neighbour is 94-98% for sherds 1, 7, 5 and 8, and 68-70% for sherds 2 and 3. Sherds 5 and 8
are in the rarely-seated group, and sherd 3 (sometimes seated) reads like sherd 2.
The skin/break split by facing direction is rough near rim and base, so only the
neighbour-contact figures are relied on.

**What does split them, so far: the join with the anchor (sherd 0).**

| sherd | % right way round (TORA) | joins sherd 0? | length of that join |
|---|---|---|---|
| 7 | 32 | yes | 29 mm |
| 1 | 44 | yes | 25 mm |
| 3 | 18 | yes | 19 mm |
| 2 | 1 | yes | 16 mm |
| 8 | 4 | yes | 16 mm |
| 4, 5, 6 | 1-2 | no | none (they meet only each other, 2, 7, 1, 3 and 8) |

All three sometimes-seated sherds share a long join with the anchor. Sherds 4, 5 and 6 do
not touch it at all, and 2 and 8 touch it along a shorter edge. This is eight sherds on one
pot, so the 16-vs-19 mm cut could be chance. It is a hypothesis, not a finding. It would
make this answer 3 (the method's placement, not the break faces or the reference),
in line with U2's "placement, not perception".

**Test that could refute it:** `t16_rel.py` asks whether sherds 4, 5 and 6 come
out right *relative to each other* while wrong relative to the anchor. If they do, the
method assembles the body correctly and only misplaces it as a block against the anchor.
If they are wrong among themselves too, the anchor-join story is not enough.

## Are the rarely-seated sherds right among themselves? (TORA, `t16_rel.py`)

Output: `/mnt/project-files/t16_rel_output.txt`, covering all 3,120 TORA ticket-10 attempts
(solid cloud). "Right" uses the same 4.6 mm test, applied once the whole attempt is moved so
one chosen sherd sits at home. Measured against the anchor, it reproduces step 1 to within
a point (sherd 1: 44.3%, 7: 31.6%, 3: 17.6%, 2: 1.4%, 4: 0.5%).

| pair (joined in the reference) | right relative to each other | either one at home |
|---|---|---|
| 4-6 | 18.1% | 0.5% / 1.7% |
| 5-6 | 11.0% | 1.4% / 1.7% |
| 3-6 | 8.9% | 17.6% / 1.7% |
| 4-5 | 5.7% | 0.5% / 1.4% |
| all of 4, 5, 6 together | 5.5% | 0.1% all three |
| any pair with sherd 2 (0-2, 2-4, 2-7) | 0.1-1.8% | |
| any pair with sherd 8 (0-8, 5-8, 6-8) | 0.4-1.8% | |

Two different failures, not one:
- **Sherds 4, 5 and 6 (the body block) are often fitted to each other and then misplaced
  as a block.** Sherds 4 and 6 come out correctly joined 18% of the time but sit at home
  under 2%. The method finds those joins, so their break faces carry enough. What fails is
  connecting the block to the anchor side, which none of them touches. This part of the
  anchor-join hypothesis survives the test.
- **Sherds 2 and 8 are wrong against everything**, including their neighbours. The block
  story does not cover them. Both touch the anchor along a shorter join (16 mm) than the
  sherds that seat (19-29 mm). That remains the only difference found, and it is untested.

Caveat on the ruler: a pair test moves the whole attempt by the smaller sherd's placement,
which magnifies small turning errors onto the larger sherd. So pair figures read low next
to at-home figures (0-1: 36.4% as a pair against 44.3% for sherd 1 at home). That cuts
against the block finding, not for it.

Weight: one pot. The 3,120 attempts come from a few dozen presentations of the same nine
sherds, so they are not 3,120 independent trials.

## Same test on GARF (`/mnt/project-files/t16_rel_garf_output.txt`, 2,140 attempts)

| | 4-6 | 5-6 | 4-5 | 3-6 | 4, 5, 6 together | 4, 5, 6 all at home |
|---|---|---|---|---|---|---|
| TORA | 18.1% | 11.0% | 5.7% | 8.9% | 5.5% | 0.1% |
| GARF | 54.3% | 21.0% | 18.5% | 21.5% | 17.1% | 1.3% |

GARF shows the same pattern, more strongly: it fits the body sherds to each other far more
often than it puts them home. Against the anchor, GARF seats 2 and 8 more than TORA does
(8.4% and 11.8% vs 1.4% and 4.1%), but pairs with sherd 2 are still the weakest of any
(0.7-6.8%).

## Result

**This was mostly already known, and should have been read first.** O8's anchor-choice
entries (`.scratch/anchor-choice/issues/01`, `02`) already showed by experiment what the
anchor-join table above only suggests: the region of the pot near the held sherd comes
right, holding the base seats 3, 4 and 5 about half the time, and 2, 7 and 8 are never seated
by any single held sherd. Those were held-sherd experiments; this ticket is observation on
saved attempts, and carries less weight on that point.

What this ticket adds:
1. **Sherd 2 is not singled out.** Over every saved attempt on both methods, 2, 4, 5, 6 and 8
   almost never go home the right way round; 1, 3 and 7 sometimes do (TORA, rough adapters).
2. **The reference is not the cause.** The conservator confirms sherd 2's placement, and every
   real join in `juglet_gt` closes to 0.04-0.5 mm, sherd 2's at 0.12-0.21 mm.
3. **The body block is often assembled correctly and then misplaced.** Sherds 4 and 6 are
   correctly joined to each other in 54% of GARF attempts and 18% of TORA's, against under
   4% at home. This refines anchor-choice 01's "not a correct block put in the wrong place":
   that was the whole far region on raw output; on solid sherds the body pairs often do hold
   together, although all three together still only reach 17% (GARF) and 5.5% (TORA).
4. **Sherds 2 and 8 stay a separate problem**, wrong even against their own neighbours. The
   only difference found is a shorter join with the anchor (16 mm against 19-29 mm), which is
   untested and could be chance on eight sherds.

**Which of the three:** the method genuinely failed: placement across the pot, not break-face
matching (the body joins are found) and not the reference. **Weight:** one pot, two methods,
many attempts from a few dozen presentations each.


## Follow-up: which sherds does rough or worn training help? (2026-10-05, from step 1's per-run counts)

Percentage of attempts with each sherd home the right way round. GARF arms are compared
on the same presentations (ds1-10, ds123), for each seed separately. Neck-side sherds are
1, 3 and 7; the body is 4, 5 and 6.

| arm | 1 | 3 | 7 | 4 | 5 | 6 | 8 | 2 |
|---|---|---|---|---|---|---|---|---|
| TORA fresh (1,040) | 27 | 9 | 19 | 0.2 | 0.1 | 0.4 | 4 | 1 |
| TORA rough 08 (1,040) | 54 | 23 | 39 | 1 | 2 | 3 | 4 | 2 |
| TORA rough 09 d100 (1,040) | 52 | 20 | 37 | 0.2 | 2 | 2 | 5 | 1 |
| GARF fresh s42 / s7 | 11 / 21 | 8 / 13 | 19 / 24 | 2 / 3 | 2 / 2 | 2 / 2 | 5 / 6 | 4 / 3 |
| GARF rough d100 s42 / s7 | 36 / 40 | 21 / 25 | 36 / 33 | 7 / 7 | 12 / 12 | 13 / 14 | 13 / 10 | 6 / 6 |
| GARF worn d400 s42 / s7 | 24 / 36 | 17 / 28 | 21 / 29 | 4 / 6 | 10 / 19 | 9 / 17 | 19 / 24 | 2 / 2 |

- Both methods: rough or worn training about doubles the neck-side sherds (1, 3, 7).
- GARF only: it also lifts the body (5, 6: about 2% to 10-19%) and sherd 8 (worn most,
  to 19-24%). On TORA the body stays at 0-3%.
- Neither helps sherd 2. But in GARF's single original presentation (the runs without
  `_ds`, 20-60 attempts each) sherd 2 comes home in 50-57% of rough/worn attempts (14%
  fresh) while sherd 7 drops to 0%. Which sherds succeed depends on the presentation
  as much as on the training.
- Weight: one pot; training-run counts per GARF arm not re-checked here. The figures are
  sherds at home, not join-by-join fits.

**Not run (conservator, 2026-10-05: "Not now"):** the held-sherd tests (neck, base,
neck + base; anchor-choice 01-02) on fresh TORA at ticket-10 scale, 26 presentations × 20
attempts per arm, with the fitted-together check. They currently rest on one presentation
and 20 attempts per arm. This is the next step if the question of why fresh fails is reopened.
