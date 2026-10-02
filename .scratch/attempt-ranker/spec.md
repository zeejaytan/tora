# Spec — rank a method's attempts without the answer key

**Answers:** U17

**Status:** ready-for-agent

**Serves:** `intent/U17-finding-the-right-attempt-among-hundreds.md` (umbrella). Code lives
in tora because it reads both GARF's and TORA's saved attempts; it is method-neutral.

## Problem Statement

A reassembly method run 200–400 times on one pot produces the right answer once or twice.
On GARF's Juglet, 2 of 1,400 attempts put all 9 sherds in their own place and the right way
round. The conservator cannot look through 400 attempts, and nothing today picks the
right one: every best-of-N reported so far was found by checking each attempt against the
answer key, which real excavated material does not have.

Two facts from the conservator's own look make the job hard:

1. A genuine attempt has visible gaps and slight overlap at the joins and still needs
   only a little manual alignment. A scorer that rewards closed joins prefers tidy wrong
   attempts.
2. The hardest wrong attempts keep the pot's outline: a sherd spun 174° on its own face
   covers its home surface to within 1.2 mm. 19 of the Juglet's 21 own-place attempts are
   like this. Any judge of overall shape is blind to them.

## Solution

A ranker that orders one pot's attempts so the few the conservator looks at (**k = 5**)
contain a genuine reassembly, using only the sherds as placed. It works in a cascade:

- **Layer 1 — does it form a vessel?** Fit one axis of rotation to the placed sherds and
  measure how far the wall profile strays from a smooth curve, in mm (SfS++'s 7 mm bins);
  check no sherd is inside out. Attempts that fail are dropped to the bottom, not
  ranked further.
- **Layer 2 — is each sherd the right way round?** For each sherd, find the smallest
  rigid **nudge** (glossary) that makes its joins agree with the neighbours it sits
  against: break edges meet, and wall direction and curvature carry on across the join.
  A gap is allowed for. A sherd whose joins cannot be made to agree by any nudge within
  the allowance is **unfixable**. Attempts are ordered by number of unfixable sherds
  (fewer first), then by the largest nudge.
- **Layer 3 — agreement across attempts** (how often each pair of sherds sits side by
  side over all N). Computed and reported beside the ranking, never used in it.

Each attempt's output names the **least-sure sherd** (the one with the largest nudge, or
an unfixable one), so the conservator is told where to look.

The answer key is fenced into one piece: a **converter** turns a method's saved attempts
into **attempt bundles** (full-detail sherd scans at the attempt's placement, then the
whole attempt moved to a random position). The ranker reads bundles only. Labels are
joined only in the **report**, after ranking.

All computation runs on Spartan as CPU batch jobs, each with a laptop-side poll; only the
rankings and scores come back to the laptop.

## User Stories

1. As the conservator, I want to be shown 5 attempts per pot rather than 400, so that
   looking at a method's output takes minutes.
2. As the conservator, I want a genuine reassembly among those 5 whenever the method made
   one, so that the shortlist is worth trusting.
3. As the conservator, I want each shown attempt to name the sherd the ranker is least
   sure of, so that I check the place a blind look misses (attempt A was called perfect
   until sherd 7 was named).
4. As the conservator, I want an attempt with gaps and slight overlap not to be marked
   down for them, so that a right placement needing manual alignment is not hidden
   behind a tidy wrong one.
5. As the conservator, I want an attempt with one sherd spun or tilted to rank below the
   genuine attempts, even when the outline looks right.
6. As the conservator, I want each layer's contribution reported separately, so that I
   know which test does the work and whether a whole-shape model is worth building.
7. As the conservator, I want the result stated as "best of the 5 shown" beside the
   answer-key best-of-N, so that the gap between what is reported and what I would
   receive is visible.
8. As the conservator, I want the result on several pots and at least two methods, so
   that a striking Juglet number is not taken as general.
9. As the conservator, I want to look at the Juglet's top 5 in visual-qa twice, blind and
   then with the least-sure sherd named, so that both the ranker and the value of naming
   the sherd are tested.
10. As the researcher, I want the ranker to be provably blind to the answer key, so that
    a good ranking cannot come from leakage.
11. As the researcher, I want the score unchanged when the whole attempt is moved to a
    random position, so that it judges the arrangement, not where it sits.
12. As the researcher, I want the top 5 stable when the same attempts are re-drawn with
    a different point sample, so that the ranker is not ranking the sampling.
13. As the researcher, I want every cut-off fixed in mm and degrees and committed before
    labels are read, so that the result is not tuned on 2 positives.
14. As the researcher, I want the converter to handle both GARF's and TORA's saved
    attempts, so that one ranker serves every method that samples.
15. As the researcher, I want the converter checked on its own (a genuine attempt
    re-posed must come back with every sherd in its own place), so that a ranking
    failure is not a conversion failure in disguise.
16. As the researcher, I want synthetic near-misses (each sherd of a genuine attempt
    spun 180° in turn) reported separately from the method's real near-misses, so that
    clean test cases do not inflate the result.
17. As the researcher, I want the ranking also run on the coarse attempt cloud, so that
    I know whether the full-detail sherds are needed.
18. As the researcher, I want GARF's existing Fractura attempts labelled for right way
    round before any new GPU run, so that more pots come at CPU cost only.
19. As the researcher, I want pots where every attempt is right, or none is, set aside
    with the count stated, so that they do not dilute or flatter the result.
20. As the researcher, I want the random-choice baseline stated per pot (chance a
    genuine attempt is in a random 5), so that every rank has its comparison.
21. As the researcher, I want each Spartan job polled from the laptop and its final
    State/ExitCode recorded in the ticket.

## Implementation Decisions

- **Three modules, one hand-over format.**
  - *Converter* (method adapter + re-poser): reads one evaluation run's saved attempts
    (GARF: the rigid "solid" cloud `generations_proposed`; TORA: its clouds/ npz) and the
    pot's full-detail sherd scans. Recovers each sherd's rigid placement from the solid
    cloud, applies it to the full-detail sherd, applies one random rigid move to the whole
    attempt, writes one bundle per attempt. Bundle content: per sherd, placed points and
    normals, sherd id, sherd size; per attempt, an opaque attempt id. Nothing else: no
    reference pose, no label, no pot frame.
  - *Ranker*: reads a folder of bundles for one pot. Writes, per attempt: Layer 1 values
    (profile deviation in mm, inside-out sherds), Layer 2 values (per-sherd nudge in mm
    and degrees, unfixable flag), cascade rank, least-sure sherd. Layer 3 written to a
    separate file.
  - *Report*: joins ranks to labels (`own_place.py`'s `oriented` / full reassembly) by
    attempt id; writes rank of every genuine attempt, top-5 hit, random baseline, per-layer
    results, hard-negative table, and the restated headline.
- **The converter's mapping from opaque attempt id to the run's attempt index** is a
  separate file only the report reads.
- **Nudge allowance:** accepted if no point of the sherd moves more than **5 mm** and the
  rotation is at most **20°**. Bounding the largest point displacement is what makes the
  allowance size-adjusted: a large sherd gets less rotation than a small one.
- **Neighbours** are found from the attempt itself (sherds whose surfaces come within
  5 mm), never from the answer key.
- **Starting cut-offs, pre-registered:** profile deviation 7 mm (SfS++); join agreement
  after the best nudge within 1.5 mm median break-edge distance and 15° wall-direction
  change. The first ranking ticket may change these **only before** the labelled run, in
  a committed pre-registration file whose commit hash the report prints.
- **No learned shape model in this spec.** TripoSG's frozen features were at chance on
  vessel parts (CRAG ticket 06); a thin-wall model on the CSC corpus is built only if
  Layer 1 proves the weak link.
- **Pots:** GARF Juglet (1,400 labelled attempts) first. Then GARF's Fractura attempts on
  Spartan, labelled for right way round; pots kept where the right answer is rare but
  present (expected: plate, narrow_bottle3, galli_pot). A TORA rerun of 200 attempts per
  pot only if those are too thin.
- **Where it runs:** Spartan CPU batch jobs submitted with `pull_and_sbatch.sh`, polled
  with `scripts/slurm_poll.sh`; reads data in place on Spartan.

## Testing Decisions

- A good test drives the ranker from the outside: hand it bundles, read its ranking. No
  test inspects its internals.
- **Main test seam: bundle → ranker.**
  - *Moved-attempt invariance:* the same bundle under two random rigid moves gives the
    same scores (to rounding).
  - *Answer-key fence:* the ranker runs with reference files made unreadable and must not
    fail or change output; any attempt to open one fails the test.
  - *Broken on purpose:* a genuine attempt with one sherd spun 180° ranks below it; the
    same attempt with every sherd moved 1–3 mm apart or into slight overlap keeps its rank.
    Stated in mm and degrees.
  - *Point-draw stability:* re-drawn points; the top 5 is reported for overlap.
- **Converter's own check:** re-posing a genuine attempt and scoring it with
  `own_place.py` returns every sherd in its own place and the right way round.
- **Prior art:** the `check_*.py` scripts in tora's `scripts/` (gates fed deliberately
  broken inputs), `own_place.py` (labels), `check_inside_out.py` (Layer 1 input).
- **The look:** the Juglet's top 5 staged as singles in visual-qa (`Needs-eye:`), blind
  then named; the conservator's verdict recorded beside each rank.

## Out of Scope

- Training or using a whole-shape generative model (TripoSG, a CSC-trained VAE).
- PF++'s trained pair verifier as a Layer 2 signal; a later ticket only if the geometric
  version fails.
- Acceptance verdicts on a single reassembly ([U1](../../../intent/U1-judging-without-answer-key.md)).
- Improving how often a method produces the right answer (G1, O9).
- Rabati material: no attempts exist yet.

## Further Notes

- Data on Spartan: Juglet full-detail sherds in `TORA/dataset/juglet_gt.hdf5`; GARF
  attempts in `GARF/logs/rwlora/rwlora_eval_*_{juglet_gt,fractura_fresh}_*`; Fractura
  sherds in `TORA/dataset/fractura_fresh.hdf5`; TORA Fractura attempts in
  `TORA/eval_runs/u10_fractura_*/clouds/`. Labels for the Juglet already exist on the
  laptop (`GARF/artifacts/rwlora/jug_t06_rescore.json`).
- The Juglet is handmade, outside SfS++'s wheel-thrown assumption, so the Layer 1 profile
  cut-off may be loose for it. Report it as found; do not tune it on the Juglet.
- Stop rules are U17's gate: if neither layer beats random on the Juglet, check the ruler
  before building more.
