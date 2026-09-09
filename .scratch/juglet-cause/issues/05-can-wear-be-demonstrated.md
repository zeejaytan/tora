# 05: Can the Juglet's wear be demonstrated at all, at any resolution we have?

**Type:** `wayfinder:grilling` (HITL)
**What to build:** A decision on whether "the fracture surfaces are worn" is a claim this
project can currently support with data — and if not, whether the honest next step is a
capture (a finer scan) rather than an algorithm.

**Answers:** O8

**Blocked by:** 02, 04 (its framing depends on what they leave unexplained)

**Status:** resolved 2026-09-07 — **(a) wear is demonstrably a cause**, with the bridge
to the Juglet's own real wear recorded as **(c)**. Decision taken with the conservator.
See Answer.

## Why it is last and why it is framed this way

The opening proposal for this whole effort was to teach TORA how worn fracture surfaces
align. That is set aside as a destination, not dismissed — but three things have to be
faced before spending a curriculum on it.

**The wear cannot be seen in this scan.** Break faces are sampled at 0.243% of object
size; the blunting acts at 0.3–0.5%. Every scale a comparison can reach lies *above*
where the wear lives. The dimensionless fine-over-coarse ratio was tried and withdrawn:
the worn Juglet reads **0.169**, fresh `blue_pot` reads **0.167**, and between-pot
variation spans 0.167–0.386 (`WEAR_TEST_RESULTS.md` §2).

**Real eroded fracture carries no fracture-like roughness at any scale these scans
resolve**, and whether the ground removed it or the scanner never recorded it cannot be
separated at 0.4 mm (`GATE_A_RESULT.md`, job 29404479).

**It has already been trained twice.** Jobs 29027773 and 29308186: Juglet rotation
51.5° → 49.2° → 52.9°, recall@10° flat at 0.000. Note that 29027773 ran at `scales`
0.041 — ticket 03 decides whether that comparison was fair.

## Acceptance criteria

- [x] Whatever residual tickets 02 and 04 leave unexplained is stated as a number, with
      01's threshold, so it is clear how much there is for wear to account for
- [x] A decision, taken with the conservator: is wear (a) demonstrably the residual,
      (b) demonstrably not, or (c) unmeasurable with current data
- [x] If (c): what capture would settle it — resolution, and on what material — written
      down, and whether it is reachable. `WEAR_TEST_RESULTS.md` names the two options:
      a scan finer than 0.1% of object size, or fresh *and* worn scans of the same pot
      so between-pot variation cancels
- [x] If (a): the wear curriculum is specified enough to hand to `/to-spec`, and this map
      closes
- [x] Names which of the three this is


---

## Answer (2026-09-07)

**Decision, taken with the conservator: (a) — wear is demonstrably a cause of reassembly
failure. The bridge from our simulated wear to the Juglet's own real wear is (c),
unmeasurable at this scan resolution.** Those are two different claims and this ticket
kept confusing them; separating them is the finding.

### The causal test already exists, and it is the load-bearing evidence

Everything else on this map is correlational — worn objects score worse than fresh ones,
which is consistent with wear causing the failure and also consistent with a dozen other
things. The erosion sweep is the one **intervention**: `scripts/build_erosion_sweep.py`
takes pots TORA already reassembles cleanly, abrades **only the break surfaces**, and
leaves the faces and the ground-truth poses untouched. Same pots, same pieces, same
correct answer. The only thing that varies is surface wear.

Baseline model, `readout.py`-corrected (`WEAR_TEST_RESULTS.md` §4, job 29308186):

| set | sherds seated (loose) | turned |
|---|---|---|
| fresh held-out | **0.843** | 46.4° |
| the same pots, worn | **0.645** | 49.3° |

**Seating falls by twenty points when wear is the only thing that changed.** The pictures
(§6) agree and are the arbiter: the baseline `blue_pot` **splits open** at the heaviest
wear (50.5° corrected), the baseline `plate` has **collapsed by heavy** (83.8° corrected).
Wear training then repairs exactly those two cases — `blue_pot` 16.3°, `plate` holding a
clean plate to the second-heaviest at 19.9°.

**And that repair is not the simulator marking its own homework.** Verified 2026-09-07 by
reading the builders: the worn *test* sweep is made by `build_erosion_sweep.py` using
GARF's mollifier `erode_fracture_band`; **wear_v2's training set is made by
`build_wear_trainset_v2.py` using `wear_ops.apply_wear`** — one-sided peak truncation,
recession removed, half the variants blurred to scan resolution. Different operators,
different source objects (`real_finetune` vs `real_heldout_norm`). wear_v2's sweep win is
a genuine **cross-simulator transfer** result.

**wear_v1's is not, and must not be quoted as one.** Its training set was built by
`build_erosion_sweep.py --dataset-name wear_trainset`
(`scripts/hpc/finetune_wear_augmented.slurm:57`) — different pots, **the same operator as
the test sweep**. Object-level held out, operator-level circular.

### The residual this ticket was asked to state, and why it does not carry the weight

Tickets 02 and 04 leave this. Fit the eight fresh normalised ceramics — turn against
fragment count — and a fresh nine-piece pot is predicted at **46.6°**. The Juglet reads
**60.9°**. The residual for wear to claim is **+14.3°**, against a between-pot scatter of
**±27.7° (1 sd)** about that line, with a 95% prediction interval of −29.1 to +122.4°.
Half a standard deviation. Separating it would need roughly **n = 15** comparable pots.

**Ticket 01's 9.1° rule does not apply here** and applying it would manufacture a finding:
9.1° is run-to-run noise for **one object run twice at twenty draws**. Between *different*
pots the spread is 27.7°, three times wider. The two rulers must not be mixed.

**But that null is uninformative about wear, and reporting it as evidence was an error.**
Look at the causal table again: wear moves **seating** by twenty points and **turn** by
about **3°**. An effect worth 3° in turn cannot show against a 27.7° between-pot spread.
The residual was measured in the metric wear barely registers on.
**Which of the three: the measurement was broken** — the ruler chosen for the test, not
the code. The lesson generalises: *pick the metric the intervention is known to move, and
check the intervention's own effect size against the comparison's noise floor before
reporting a null.*

The corollary is a standing rule for every later wear test: **score wear on seating, not
on turn.** Turn is the wrong instrument for this effect and always was.

### TORA can see the wear — the earlier "it cannot" was proved for the gap only

The encoder is fed **six** numbers per point, not three: coordinates and the face normal
of the triangle the point landed on (`tora/modeling/encoder/point_cloud_encoder.py:113`).
That is a sub-spacing cue, at triangle scale — roughly thirty times finer than the spacing
between the sampled points themselves. Measured on the exact points the network receives
(`scripts/measure_faces_as_network_sees.py`, `LORA_VESSELS_29623885_RESULT.md`), break-face
roughness on the six real objects falls **monotonically** as wear rises:

| erosion | e000 | e025 | e050 | e075 | e100 |
|---|---|---|---|---|---|
| roughness | 29.7° | 27.2° | 26.6° | 24.3° | **22.2°** |

So "TORA's sampling is too coarse to resolve the wear" is true of the **join gap** and
false of the **orientation channel**. There is a signal, the network is fed it, and the
intervention moves it.

### What is (c), and it is a capture question rather than an algorithm one

What the sweep demonstrates is *"removing fine break-face detail causes collapse."* What
it cannot demonstrate is that **the Juglet's real wear removed that same detail**, because
these scans never recorded it either way:

- the Juglet's break faces are sampled at **0.243%** of object size; the blunting acts at
  **0.3–0.5%** — every scale a comparison can reach lies *above* where the wear lives;
- the dimensionless fine-over-coarse ratio was tried and withdrawn — worn Juglet **0.169**,
  fresh `blue_pot` **0.167**, fresh range 0.167–0.386 (§2);
- Gate A (job 29404479, 20 RePAIR fresco fragments): **real eroded archaeological fracture
  carries no fracture-like roughness at any resolvable scale**, and whether the ground
  removed it or the scanner never recorded it cannot be separated at 0.4 mm.

**What would settle it**, unchanged from `WEAR_TEST_RESULTS.md` §2 and now the standing
requirement on `O7`:

1. **a scan of real worn material finer than 0.1% of object size** — for a 100 mm juglet
   that is a point spacing under 0.1 mm, roughly 2.5× finer than the current capture; or,
   better,
2. **fresh *and* worn scans of the same pot**, so between-pot variation cancels and the
   wear is the only difference. This is reachable in principle on excavated material where
   a fresh break has been made during conservation, or on a modern replica broken, scanned,
   abraded, and scanned again.

Until one of those exists, "the Juglet fails *because* its fractures are worn" stays an
inference from a simulator, not a measurement of the object.

> **Superseded 2026-09-09 — read `intent/O7` for the current wording of both captures.**
> Two things above are now known wrong. The **modern replica** half of (2) is **struck**:
> burial cannot be simulated, so abrading a fresh replica calibrates one simulator against
> another and moves the guess rather than removing it — and after two millennia the fabric
> is not the same material a replica offers. The *excavated* half survives and is the strong
> version: one sherd bearing both an ancient buried break face and a fresh modern one is a
> real paired control with nothing simulated. And (1) is incomplete: a finer scan grounds
> the wear model but does not by itself reach the reassembly question, because
> `num_points_to_sample: 5000` leaves ~1.2 mm between the points the network is shown. The
> "100 mm juglet" is also a different size convention — ticket 10 measures this vessel at
> 65 mm; the requirement is the ratio.

### Which of the three

**The method genuinely failed** — wear degrades reassembly on real pots under a
controlled intervention, visibly, and wear-augmented training repairs it across a
different simulator. **Plus the measurement was broken**, in this ticket's own first
analysis: the residual was tested in turn, a metric the intervention moves by ~3°, against
a ~28° noise floor.

### Consequence for the map

Candidate 5 is **ruled in**, and it is the one that survives. The map's destination is
reached and it closes: the surviving cause is specified for `/to-spec` below.

Two things are explicitly **not** claimed:

- **The Juglet's specific +14.3° gap is not attributed to wear.** It cannot be, at n = 8
  with a 27.7° spread. The Juglet fails the way a nine-fragment pot fails *and* is worn;
  those add, and this data cannot apportion them.
- **`narrow_bottle3` is not explained by this and is not evidence against it.** Fresh,
  unworn, four fragments, **+55.3° (2.0 sd)** — the largest deviation in the corpus, four
  times the Juglet's. Rendered 2026-09-06 (`artifacts/nb3/narrow_bottle3_vs_working.png`):
  genuinely **torn into two flaps**, two free sherds 23.7% and 27.0% of pot size from home
  (about 24 mm and 27 mm on a 100 mm bottle), not a small-sherd symmetry artefact. That is
  a **separate failure** and gets its own ticket, `07`.

---

## The wear curriculum, specified for `/to-spec`

Wear v3 continues. What follows is what the evidence above constrains; it is a
specification, not a plan of runs.

**Operator.** `wear_ops.apply_wear` (the wear_v2 model) — one-sided peak truncation,
recession removed on a measured dose response, half the variants blurred to scan
resolution. **Not** `erode_fracture_band`. That mollifier stays as the *test* operator and
must never be the training operator, or the transfer result becomes circular the way
wear_v1's did.

**Corpus.** bbad vessels v3: filtered by inverse Simpson effective piece count ≥ 4, and by
the solidity screen `cells >= 1 & fill < 0.5` that keeps 207 of 1053 — 37% of the raw
corpus is a solid lump and `_wall_estimate` was broken (its search reach was approximately
its own answer). v3's rebuild took coincident break-face vertices from **49.22% to 0.00%**.
Blunting is inert on coarse meshes (0.0001% available to blunt), so the screen is
load-bearing, not tidying.

**Adapter recipe**, read off GARF's `configs/experiment/finetune.yaml` at the pinned
version: rank **128**, alpha **256**, dropout **0.1**, pose head unfrozen, lr **2e-4**,
adapters in **all six** transformer blocks (`WEAR_V3_PLAN.md`'s "final block only" claim is
wrong). **`frozen_encoder` must be set explicitly to `true`** — it defaults False and
`_freeze_encoder()` re-enables `requires_grad` every epoch, which is how job 29527496
became an accidental full fine-tune of the 403M model.

**Success criterion — seating, not turn.** The intervention moves seating twenty points
and turn three. State the target as recovery of the worn-sweep seating gap
(baseline 0.645 against fresh 0.843) and report turn alongside as context only.

**Evaluation protocol, all four mandatory:**
- **twenty draws per arm** — the readable bar is 9.1°; at five draws it is 17° and no wear
  effect of this size is visible through it;
- **stored object size inside the trained band (≥ 0.375)** — the §4 fresh and sweep rows
  were scored at 0.319–0.383, at or below the trained floor, a handicap at source that is
  still untested;
- read through `scripts/readout.py`, which is the only admissible reader;
- **a render at individual-sherd placement**, never whole-pot outline — on this object the
  outline survives even in the worst draw.

**What this curriculum cannot deliver, stated up front.** It will show whether wear
training transfers across simulators and repairs collapse on worn material. It will **not**
show that it fixes the Juglet, and a Juglet result must not be the success criterion —
three attempts have produced no readable movement (baseline 57.9° / v1 55.3° / v2 59.6°;
v3 adapter at twenty draws: baseline 66.2°, on 61.2°, off 69.8°, largest gap 8.6° against a
9.4° bar, all ties). Closing that last step needs the capture in (c), not more training.

## Jobs and sources

Retrain and sweep: **29308186** (read through `readout.py` 2026-09-05). Gate A: **29404479**.
Gate C / LoRA plumbing: passed 2026-08-19; accidental full fine-tune **29527496**.
v3 adapter at twenty draws: **30130049** (ticket 06). Fragment-count trend and the
`narrow_bottle3` render: **30167044**.
Notes: `WEAR_TEST_RESULTS.md` §2 §4 §6, `GATE_A_RESULT.md`, `GATE_B_DECISION.md`,
`WEAR_V3_PLAN.md`, `LORA_VESSELS_29623885_RESULT.md`.
Builders: `scripts/build_erosion_sweep.py`, `scripts/build_wear_trainset_v2.py`,
`scripts/wear_ops.py`.
