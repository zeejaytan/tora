# 11: The erosion ladder, run on pots TORA can actually rebuild

**Type:** `wayfinder:research`
**What to build:** Ticket 09's experiment with the object-selection step that was
written into the design and never executed.

**Answers:** O8, O7

**Blocked by:** Nothing technical. One GPU evaluation pass on `gpu-a100-short`
(job 30190268 did 30 variants in 16 minutes; this is 40) plus a CPU build step.
**Needs the conservator's go-ahead to submit** — no `sbatch` without it, and the
submit gets a laptop-side `scripts/slurm_poll.sh`, per `AGENTS.md`.

**Status:** open

## Why it exists

Ticket 09 asked whether wear breaks a pot the way the Juglet is broken. It answered
on **one object**, and said so. The limitation was not in the method or the
instrument — both held. It was in the object list.

`scripts/build_erosion_sweep.py` opens by stating its own design:

> *"the causal wear test: progressively wear pots TORA **CAN currently rebuild**"*

The job that ran it (`scripts/hpc/eval_erosion_sweep.slurm:51-52`) passed **no
`--objects` filter**, and pointed at `real_heldout_norm.hdf5`. The script's default
for `--objects` is every object in the source. That source is fixed at six objects,
and three of them are **bones** — `limb3`, `coxae`, `vert9` — not pottery at all.

So exactly three ceramics have ever been worn and re-measured: `blue_pot`,
`galli_pot`, `plate`. Of those three, one assembles correctly unworn. That is where
ticket 09's n = 1 came from. The filter existed in the script and was never used, and
the pots that would have passed it were sitting in a different file.

## What is actually available (verified on Spartan, 2026-09-09)

`dataset/ceramics.hdf5` is a **symlink** to `fractura_real.hdf5`, whose top-level
groups are `bones`, `ceramics`, `egg`. The `ceramics` group holds **eight** real
pots, not three:

| object | fragments | ever worn? |
|---|---|---|
| `blue_pot` | 5 | yes — the one informative ladder in ticket 09 |
| `galli_pot` | 10 | yes — already broken at zero wear |
| `plate` | 6 | yes — already broken at zero wear |
| `narrow_bottle1` | 12 | **never** |
| `narrow_bottle2` | 3 | **never** |
| `narrow_bottle3` | 4 | **never** |
| `narrow_bottle4` | 4 | **never** |
| `pink_bowl` | 3 | **never** |

Five real pots have never been put on the erosion ladder. Two of them are the ones
TORA does best on — `narrow_bottle2` seats 2 of 2 loose fragments at about **4°** of
turn, `narrow_bottle4` seats 3 of 3 at about **8°**
(`docs/notes/FRACTURA_WHY_IT_FAILS.md:226-231`). Those are near-perfect unworn
reassemblies: precisely the controls this ladder needs and has never had.

**There is no training leakage, and that is what makes all eight usable.** The
baseline arm is `bbad_everyday_cka`, trained on synthetic Breaking Bad data only
(`docs/notes/TORA_GOOD_VS_BAD_ANALYSIS.md:978-982`). No real pot was ever in its
training set. "Held out" was never the binding constraint for this arm — the
six-object file was. Ticket 09 already fixed the baseline as the clean instrument
here, because `wear_v1` / `wear_v2` carry their own finetuning regression.

## The scale trap — checked before anything is submitted, not after

Measured on Spartan, `max|v|` per object:

| file | scale |
|---|---|
| `fractura_real.hdf5` → `ceramics` | **54.9 to 187.3**, raw scan units, varying 3.4× between pots |
| `real_heldout_norm.hdf5` | 0.5000 on every object |

The ceramics group is **not normalised**. Feeding it to the sweep as-is would repeat
the exact failure that faked a finding in this project — `blue_pot` read 0% until it
was rescored — and it is worse than a metric problem: `scales` is a **conditioning
input** to the flow model, not just bookkeeping (`scripts/normalize_real_hdf5.py`,
header). The model has only ever been shown roughly 0.375–0.625. Raw ceramics arrive
100–190× outside that band.

**So the source is normalised once, before erosion, and never again.**

Do **not** use `build_erosion_sweep.py --normalize` for this. That flag computes the
factor **per variant, after erosion** (`scripts/build_erosion_sweep.py:124-129`),
which lets the scale drift from rung to rung and puts a second changing thing into an
experiment whose entire logic is that only the wear changes. Normalising the source
once reproduces how `real_heldout_norm` was handled and holds the factor fixed across
the ladder by construction.

## The prediction, written before the result

Ticket 09 found an **exchange** on `blue_pot` — the pot stays built and two shoulder
chips trade names — where the Juglet **scatters**, its sherds genuinely in the wrong
places. My prediction there was wrong, so this one is written with that on the record.

**Prediction: exchange will be the common pattern at light and moderate wear**, on
the reasoning that abrasion removes the distinguishing detail from break faces and a
discrimination failure is an exchange. If instead the added pots scatter as they are
worn, the Juglet's failure has the shape wear produces, and route (b) has carried
something across the bridge with no finer scan.

**Both outcomes are results and they point opposite ways.** A third outcome — the
signature does not separate at all — is also a real answer and must be reported as
one, not buried.

## The rules, fixed in advance (inherited from ticket 09, unchanged)

- **The `e000` control comes first.** On each pot, at zero abrasion, the instrument
  must pick the true naming outright. Pots that fail their own unworn control are
  **reported and excluded from the reading** — they cannot show a wear-induced
  transition because they are already broken. That exclusion list is the result of
  the selection step this ticket exists to perform, and it is stated before the
  ladder is read, not after.
- **Read the low and middle rungs, not `e100`.** At the heaviest wear everything
  collapses and "scattering" is trivially what the instrument must report.
- **Read per object, up its own ladder.** Never pooled. Ticket 09 measured the
  confound directly: agreement across draws correlates with fragment count at
  **r = −0.81**, so a cross-pot reading is partly just counting pieces. And a pooled
  six-pot mean already scored a model that cut the ladder drop by two thirds as
  indistinguishable from the untouched baseline (`intent/O2`).
- **Baseline arm only.**

## What to do

1. **Normalise the source once.**
   `python scripts/normalize_real_hdf5.py --src fractura_real.hdf5 --dst ceramics_norm_src.hdf5 --dataset-names ceramics`
   Confirm every ceramic reads `max|v| = 0.5000` before continuing. (The script
   copies the whole 3 GB file, which also carries `bones` and `egg`; that is fine —
   1.1 TB free, and the extra groups are simply not read.)
2. **Build the ladder on all eight ceramics**, five rungs, no `--normalize`:
   `--src ceramics_norm_src.hdf5 --src-dataset ceramics --strengths 0,0.25,0.5,0.75,1.0`
   → `erosion_ceramics.hdf5`, with the relief calibration JSON written alongside.
   Add `config/data/zeroshot/erosion_ceramics.yaml` (copy `erosion_sweep.yaml`;
   `min_parts: 3`, `max_parts: 12`).
3. **Verify the scale held across the ladder** — report `max|v|` at every rung. It
   should be 0.5 throughout by construction; if it is not, stop, because the
   experiment then has two variables.
4. **Evaluate**: baseline checkpoint, **10 draws**, clouds saved and renderer off —
   the pattern from `scripts/hpc/eval_wear_table_corrected.slurm:126-140`, which is
   what produced ticket 09's inputs. Keep its
   `git merge-base --is-ancestor 0d6a85f HEAD` gate: scoring on a pre-fix checkout
   would silently reproduce the retired ruler.
5. **Read the `e000` control and publish the exclusion list** before anything else.
6. **Run `scripts/check_wear_failure_shape.py`** per pot per rung: worst loose sherd
   under the evaluator's naming, worst under the best renaming, how many *distinct*
   renamings win across ten draws, and whether the true naming ever wins.
7. **Render individual sherd placement** for the clearest case at both ends of every
   informative ladder. Whole-pot outline is not admissible on this material — four
   successive views of the same wear were each too coarse to resolve it
   (`docs/lessons.md`). The measured quantity, per sherd, unbinned.
8. **Compare the signature with the Juglet's** and say which it is, per pot.
9. **Check the wear actually reached the Juglet's level.** The calibration JSON
   records achieved `relief_p90` at every rung. A flat result is uninterpretable if
   the simulated wear plateaued below the real thing — GARF's Exp 7 failed exactly
   here.

## Acceptance criteria

- [ ] Every ceramic's `e000` control reported, and the exclusion list stated
      **before** the ladder is read
- [ ] `max|v|` reported at every rung, confirming the scale did not move
- [ ] Every pot × rung reported, including the ones with no signal
- [ ] Distinct-renaming counts reported, not just the median draw — that is the
      number that separates an exchange from a scattering
- [ ] Read per object up its own ladder; **no pooled mean anywhere in the read-out**
- [ ] Renders at individual-sherd placement, both ends of each informative ladder
- [ ] Achieved wear compared against the Juglet's measured roughness
- [ ] States which of the three: the method genuinely failed / the measurement was
      broken / the reference answer was wrong
- [ ] States how much weight it bears — how many pots survived the `e000` bar, how
      many draws, and whether a Fractura ceramic sweep can carry a claim about one
      excavated juglet
- [ ] Written back to **`O8`** (does this attribute the Juglet's failure to wear?)
      and to **`O7`** (does the wear augmentation earn its place behaviourally?),
      either way — including "the signature does not separate", which is a real answer
- [ ] `python scripts/check_intent_links.py` exits 0 from `C:\PR`

## What would make this not worth pursuing

**If fewer than three ceramics pass their own `e000` control**, this is still n ≈ 1,
and the honest report is that TORA does not assemble enough real pottery unworn to
support a ladder at all — which is itself a finding about the model, and one that
should be written back rather than buried. Step 5 checks that before any analysis is
built on top of it.

**It does not rescue route (a).** A powered ladder says what wear does to pots we
control. It still does not measure the Juglet's own wear, which no scan we have can
resolve (`intent/O7`). What it can do is make ticket 09's n = 1 bear weight, and give
`O7`'s behavioural criterion a second erosion operator to test transfer against.
