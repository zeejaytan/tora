# 05: Three arms on the Juglet, the decision, and the write-back

**What to build:** The untouched model, the generic adapter and the ceiling adapter are
each run 20 times on the Juglet, and on the eight Fractura pots. Each is scored with the
own-place count. U10's stage-1 decision rule is applied straight from the scorer's output,
and the reading is written into U10.

Spec: the umbrella `.scratch/u10-juglet-ceiling/spec.md`, modules 8 and 9.

**Answers:** U10

**Blocked by:** 01 (the scorer), 04 (both adapters).

**Status:** done 2026-09-25 except the Needs-eye witness (viewer pairs staged, conservator look pending)

**Needs-eye:** the per-arm Juglet renders. The pictures decide; the table ranks.

- [x] Evaluation settings are the ones every earlier Juglet arm used, stated here.
- [x] 20 Juglet draws per arm. For each arm the ticket reports:
      - the own-place median and spread;
      - the swap-allowed count beside it;
      - how far off the unseated sherds land (% of pot height).
- [x] The decision rule is applied by the scorer on the **solid sherds**, with the raw
      output's reading reported beside it (conservator, 2026-09-14). If the two differ,
      the solid one stands, and the ticket says what the difference is. The reading is
      quoted verbatim:
      - the ceiling fails to beat generic by ≥1 sherd (median) → close U10 and skip
        stage 2;
      - the ceiling wins → stage 2;
      - generic helps as much as the ceiling → the gain came from the fine-tune (a C4
        answer).
- [x] Fractura: each of the eight pots is scored per pot for every arm, never pooled.
      Any pot where an adapter loses a sherd or more (median) is named. A ceiling that
      loses there is recorded but does not change the reading.
- [x] Renders: the Juglet's median and worst draws per arm, full vessel, in the pot's
      own frame.
- [x] The ticket states the weight: one pot, 20 draws, one training run per arm, and the
      label "ceiling: shown the answer's shape". It also names which of the three
      failure types it found.
- [x] Every `sbatch` has a laptop-side poll, and the final `sacct` State/ExitCode is
      recorded here.
- [x] Written back:
      - U10's boxes are ticked or struck, with the date;
      - on a loss, `tora/intent/O8` and `GARF/intent/G1` record that the break edges are
        what is left;
      - if generic matches the ceiling, `CSC/intent/C4` gets a line;
      - the umbrella intent README's U10 row is updated.

## How it runs on Spartan (amended 2026-09-24)

- **Three jobs, one per arm** (untouched, generic, ceiling), each on `gpu-a100-short`.
  Each holds the arm's 20 Juglet draws with renders (under 5 min, job 30130049) and the
  eight Fractura pots.
- The two adapter arms are submitted `afterok` on their ticket-04 training job. The
  untouched arm needs nothing and can run first. It re-runs the baseline under the same
  code as the other two, so all three are scored alike.
- **Scoring is CPU work and happens after**: `own_place.py --decide` on the fetched
  per-draw results, on the laptop or a CPU job. It never holds a GPU.
- If a render or evaluation step breaks on first contact, the fix is debugged in a held
  allocation, not by resubmitting.
- Each job carries the `job_status.log` exit trap, and each gets its own laptop-side
  poll.

## Arms, fixed before any Juglet draw (conservator, 2026-09-24)

Ticket 04 found neither adapter beat the untouched model on its choosing vessels at any
pass. Choosing on them picked the least-changed pass, a near-copy of the untouched model.
So each adapter arm is its **last pass** (`last.ckpt`, pass 19), not the kept one:
- **untouched:** `checkpoints/bbad_everyday_cka.ckpt`, `lora.enabled=false`;
- **generic:** `output/u10_train_generic_31200602_171624/last.ckpt`;
- **ceiling:** `output/u10_train_ceiling_31200602_163555/last.ckpt`.

Adapter arms: `lora.train_head=false lora.active=true`, strict diff before the draws.
Settings are job 30130049's: `zeroshot/juglet_gt`, batch 1, 20 generations, mitsuba 512.
Job script: `scripts/hpc/u10_juglet_arm.slurm` (tora `6dc1554`).

Submitted 2026-09-24 on `gpu-a100-short`: **31215861** untouched, **31215862** generic,
**31215863** ceiling. Each has its own laptop poll.

Fractura: the eight pots at erosion strength 0 (the `_e000` rung of `erosion_ceramics`),
copied into `dataset/fractura_fresh.hdf5` by `scripts/make_fractura_fresh.py`, config
`zeroshot/fractura_fresh`, batch 4, same arms and 20 draws. The job is the same script with
`SET=fractura` (tora `a408494`). Submitted 2026-09-24: **31216108** untouched, **31216109**
generic, **31216110** ceiling, each polled.

| Job | Arm | sacct State | ExitCode | Elapsed |
|---|---|---|---|---|
| 31215861 | Juglet untouched | COMPLETED | 0:0 | 2 min 42 s |
| 31215862 | Juglet generic | COMPLETED | 0:0 | 1 min 24 s |
| 31215863 | Juglet ceiling | COMPLETED | 0:0 | 1 min 9 s |

The untouched rerun reproduces ticket 01 (job 30130049): median 3 of 9 in own place on
both clouds. The code, settings and scorer are the same as before.

### Juglet result (2026-09-24), 20 draws per arm, solid sherds (raw beside)

| Arm | own place, median (range) | swap-allowed | sherds not in own place, from home |
|---|---|---|---|
| untouched | 3 of 9 (2–5); raw 3 (3–5) | 4.5; raw 5 | 18.5% of pot size (12.1 mm) |
| generic, pass 19 | 2 of 9 (1–4); raw 2 (1–4) | 4; raw 4 | 21.5% (14.0 mm) |
| ceiling, pass 19 | 1 of 9 (1–3); raw 1 (1–3) | 3; raw 4 | 23.6% (15.3 mm) |

The anchor (sherd 0) is pinned at home and counts as one, so the ceiling's median of 1
means that apart from the anchor, no sherd is in its own place.

The scorer's reading (`own_place.py --decide`) is the same on both clouds, quoted verbatim:
> own-place medians: untouched 3, generic 2, ceiling 1. Ceiling minus generic = -1
> sherd(s); the rule needs +1.
> CEILING LOSES: shape is not what the Juglet is missing, even when handed over. Close
> U10 (the method genuinely failed, for this lever), skip stage 2, and write back to
> tora/intent/O8 and GARF/intent/G1 that the break edges are what is left.

Renders, looked at (lead, debugging view): `artifacts/u10/j05_{untouched,generic,ceiling}_{median,worst}.png`.
Each shows a whole pot at the right size in the pot's own frame. Nothing has collapsed or
been rescaled, so the ruler is fine. In the ceiling's middle attempt, sherd 8 sits inside
the neck and the lower body is scrambled among itself. The untouched model's middle
attempt keeps 1 and 7 at home.

### Fractura result (2026-09-24), per pot, never pooled

| Job | Arm | sacct State | ExitCode | Elapsed |
|---|---|---|---|---|
| 31216108 | Fractura untouched | COMPLETED | 0:0 | 3 min 47 s |
| 31216109 | Fractura generic | COMPLETED | 0:0 | 4 min 7 s |
| 31216110 | Fractura ceiling | COMPLETED | 0:0 | 4 min 11 s |

Own place, solid sherds, median over 20 draws (range). The raw medians are identical
except generic on narrow_bottle4 (raw 4).

| Pot | sherds | untouched | generic | ceiling |
|---|---|---|---|---|
| blue_pot | 5 | 5 (3–5) | 5 (2–5) | 5 (3–5) |
| galli_pot | 10 | 8 (7–9) | **4.5 (1–7)** | **2 (1–4)** |
| narrow_bottle1 | 12 | 2 (1–4) | **1 (1–3)** | 2 (1–4) |
| narrow_bottle2 | 3 | 3 | 3 | 3 |
| narrow_bottle3 | 4 | 1 (1–2) | 1 (1–2) | 1 (1–4) |
| narrow_bottle4 | 4 | 4 | 3.5 (3–4) | **3 (3–4)** |
| pink_bowl | 3 | 3 | 3 (2–3) | 3 (2–3) |
| plate | 6 | 4 (4–5) | 4 (1–5) | 4 (1–5) |

Pots where an adapter loses one sherd or more (median):
- galli_pot: generic −3.5, ceiling −6;
- narrow_bottle1: generic −1;
- narrow_bottle4: ceiling −1.

No adapter gains a sherd on any pot. Render looked at (lead, debugging view):
`artifacts/u10/j05_fractura_galli_{untouched,ceiling}_median.png`. It is a genuine
scramble at the right scale, with anchor sherd 3 at home. Sherd 2 has swung into the
middle and 1/6/7/9 sit outside the vessel. Per the ticket this is recorded and does not
change the reading. It is independent evidence that the last-pass adapters damage
placement on pots unlike their training shapes too.

**Caveat on the verdict's wording (lead).** Ticket 04 found both adapters got *worse* with
training even on their own choosing vessels (ceiling .897 → .815). So the last-pass
adapters are worse placers in general, not better placers of the Juglet shape. The ceiling
was supposed to show what handing over the shape can do. Instead it measured a fine-tune
that damages placement. By the pre-registered rule "ceiling loses" stands. The claim that
"shape is not what is missing" is stronger than this run can carry. To be settled before
the write-back (refute-finding offered).

**Settled 2026-09-25 (refute-finding, 5 skeptics: 0 refuted, 2 weakened, 3 stand).** The
narrower reading stands, at a smaller weight than first worded. The fine-tune damaged
placement on the Juglet (sherds 1 and 7), on galli_pot, and on its own choosing vessels.
"In general" is not established: one training run per arm, and on real pots the harm is
mainly galli_pot, because four pots were already full and one is anchor-only. Generic's
Fractura figures were re-checked from its fetched `own_place.json` and match. Weight: one
pot, 20 draws, one training run per arm, one sampling seed. Label: "ceiling: shown the
answer's shape". Which of the three: the method genuinely failed, meaning *this fine-tune*.
The ruler and the reference were checked and are sound.

Written back: U10 (status, *Stage 1 result*, two boxes ticked, gate line), the umbrella
README row, `tora/intent/O8` candidate 7 and `GARF/intent/G1` ("shape not ruled out"; the
pre-registered "break edges are what is left" is **not** written, because its premise, a
harmless fine-tune, failed). CSC C4 is not written, because generic did not match the ceiling;
it trailed the untouched model.

Viewer pairs for the Needs-eye look: `visual-qa/viewer/pairs/u10_juglet_{untouched,generic,ceiling}.json`,
staged 2026-09-25. The untouched pair shows attempt 0 (3 of 9, the solid median). The
`j05_untouched_median.png` debugging picture was picked on the raw count and shows 2.
