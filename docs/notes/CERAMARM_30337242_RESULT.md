# Wear v3 on eight real pots at five wear levels — job 30337242

**Run:** `scripts/hpc/eval_ceramics_arms.slurm`, Spartan job **30337242**,
2026-09-10 03:34–04:27 (52 min, gpu-a100-short, COMPLETED 0:0).
**Source:** `zeroshot/erosion_ceramics` — the eight real Fractura ceramics,
normalised once, then abraded at five levels (e000 fresh → e100 full).
40 objects × 20 draws × 3 arms = 2400 reassembly attempts.
**Arms:** `adapter_on` (wear v3 LoRA active) · `adapter_off` (same weights,
adapters disabled) · `baseline` (untouched `bbad_everyday_cka`).
**Answers:** [O7](../../intent/O7-wear-grounding.md), and reproduces part of
[O8](../../intent/O8-what-stops-the-juglet.md).

## Three lines of background

Wear v3 taught the model on 203 synthetic vessel shapes through switchable
adapters, to test whether shape variety plus simulated wear makes it better at
*worn* pottery. It had only ever been read out on synthetic objects and one
Juglet. This is the first test on real broken pots worn under controlled
conditions — and the first with a control arm, so a difference can be
attributed to the adapter rather than to the run.

## The answer, plainly

**Wear v3 does not help on real worn pottery. On this corpus it is slightly
worse than the untouched model, and the loss is not chance.** Across the 40
pot-and-wear-level combinations, the adapter placed *fewer* fragments than the
baseline on 14 and *more* on 4, with 22 level (sign test, p = 0.031).

**Which of the three: the method genuinely failed.** Not the ruler and not the
key. The measurement is sound here in a way it was not the last time — the
pots reassemble, the wear ladder moves monotonically, and the geometry was
rendered before this was written. The reference is the pots' own
scan-and-break record, not an inferred key.

The related and more useful finding is that **the instrument now works**: six
of the eight pots reassemble essentially completely when unworn, and simulated
abrasion takes them apart in a graded, visible way. That is the ladder ticket
11 was built to get, and it is the first time this workspace has had one on
real pottery with real fracture surfaces.

## 1. Does TORA assemble these pots at all? (the e000 control, read first)

Fragments seated at zero wear, median of 20 draws. This is the gate: a pot
that fails here cannot say anything about wear.

| pot | fragments | adapter_on | adapter_off | baseline |
|---|---|---|---|---|
| `blue_pot` | 5 | 5.0 | 5.0 | **5.0** |
| `narrow_bottle4` | 4 | 4.0 | 4.0 | **4.0** |
| `narrow_bottle2` | 3 | 3.0 | 3.0 | **3.0** |
| `pink_bowl` | 3 | 3.0 | 3.0 | **3.0** |
| `galli_pot` | 10 | 7.0 | 8.0 | **8.0** |
| `plate` | 6 | 4.0 | 5.0 | **4.0** |
| `narrow_bottle3` | 4 | 3.0 | 3.0 | **3.0** |
| `narrow_bottle1` | 12 | 4.0 | 5.0 | **3.5** |

Four pots reassemble completely. Two more get most of the way. Two — the
twelve-fragment `narrow_bottle1` and the four-fragment `narrow_bottle3` — are
already broken at zero wear, and their ladders carry no weight. (`narrow_bottle3`
reads 3 of 4 here but only 1 of 4 in the own-place audit in §4: two of its
fragments are exchanged, not seated.)

Ticket 11 set the floor at "fewer than three ceramics pass their own e000
control and this is still n ≈ 1". **Six pass. The floor is cleared.**

## 2. The three arms, paired per pot and per wear level

No pooled mean. Each of the 40 pot-rungs is one paired comparison, on
fragments **earned** (seated minus the one anchor fragment handed over free).

| comparison | adapter better | baseline better | level | p |
|---|---|---|---|---|
| `adapter_on` vs `baseline` | 4 | **14** | 22 | **0.031** |
| `adapter_off` vs `baseline` | 5 | 11 | 24 | 0.210 |
| `adapter_on` vs `adapter_off` | 6 | 13 | 21 | 0.167 |

On how far misplaced fragments are turned, nothing separates the arms
(17–23, p = 0.43; 20–20, p = 1.00; 15–24, p = 0.20). The cost is in seating,
which is where wear's effect was already known to show.

**Read the middle row carefully.** `adapter_off` should *be* the baseline —
same weights, adapters switched off — and it is not: it loses 11 to 5. That is
the `train_head=true` contamination recorded in
[O7](../../intent/O7-wear-grounding.md): five pose-head tensors were moved
during v3 training, and switching the adapter off does not switch those back.
So the honest split is that `adapter_on` vs `adapter_off` (6–13, p = 0.167)
isolates the adapter, and the significant 4–14 against baseline is the adapter
**plus** the moved head. The training run damaged the model in a way the
adapter switch cannot undo.

The sharpest single case: **`pink_bowl` at full abrasion holds 3 of 3 on the
untouched baseline (worst fragment 3.6% of bowl width) and collapses to 1 of 3
on `adapter_off` (21.1%)** — with the adapter *disabled*. A bowl the original
model handles perfectly at every wear level, broken by weights that were
supposed to be inert.

## 3. What wear does, and what shape the failure takes

`blue_pot`, baseline arm, own-place seating of 5 fragments:
e000 **5** → e025 3 → e050 3 → e075 3 → e100 **2**.
Rendered: `artifacts/ceramarm_30337242/ladder_blue_pot_baseline.png`.

`pink_bowl`, baseline: holds 3 of 3 at every rung, worst free fragment moving
1.7% → 3.6% of bowl width. On `adapter_off` the same bowl slides apart along
the join, the two free sherds drifting to ~20%.
Rendered: `ladder_pink_bowl_baseline.png`, `ladder_pink_bowl_adapter_off.png`.

**This reproduces ticket 11's job 30293058 from an independently submitted
run** — same pots, same rungs. `blue_pot` exchanging at light wear and
scattering by e075 comes out the same way. The instrument repeats.

**A prediction of mine that the data refuted.** The ladder job's header
predicted exchange — fragments swapping places — would be the common pattern at
light and moderate wear. §4 shows it is not: on the pots that work, the
relabelling audit gains nothing, meaning nothing is being swapped. Those pots
fail by **scattering** — the right piece drifting out of place. Exchange
appears only on the pots already broken unworn. Recorded here rather than
quietly dropped.

## 4. How much of the published seating figure is relabelling

The number the job prints comes from the Hungarian assignment, which is free
to **relabel** fragments to whatever pairing passes most of them — so a sherd
standing in another sherd's place is credited. `own` is the conservator's
question: is *this* piece in *this* place. Both include the free anchor.

| pot / rung | frags | on (own/hung) | off (own/hung) | base (own/hung) |
|---|---|---|---|---|
| `blue_pot` e000 | 5 | 5.0 / 5.0 | 5.0 / 5.0 | 5.0 / 5.0 |
| `blue_pot` e100 | 5 | 3.0 / 3.0 | 4.0 / 4.0 | 2.0 / 2.0 |
| `galli_pot` e000 | 10 | 7.0 / 7.0 | 8.0 / 8.0 | 7.5 / 8.0 |
| `galli_pot` e100 | 10 | 4.0 / 5.0 | 5.0 / 6.0 | 3.0 / 4.0 |
| `narrow_bottle2` e100 | 3 | 2.0 / 2.0 | 2.0 / 2.0 | 3.0 / 3.0 |
| `narrow_bottle4` e100 | 4 | 4.0 / 4.0 | 4.0 / 4.0 | 4.0 / 4.0 |
| `pink_bowl` e100 | 3 | 3.0 / 3.0 | 1.0 / 1.0 | 3.0 / 3.0 |
| `plate` e100 | 6 | 1.0 / 3.0 | 2.0 / 3.0 | 2.0 / 4.0 |
| `narrow_bottle1` e000 | 12 | 2.0 / 4.0 | 3.0 / 5.0 | 2.0 / 3.5 |
| `narrow_bottle3` e100 | 4 | 1.0 / 1.0 | 1.0 / 3.0 | 1.0 / 3.0 |

**On the six pots that work, the published figure is honest** — own and
relabelled agree. Relabelling only inflates the two pots already broken unworn
(`narrow_bottle1`, `narrow_bottle3`) and `plate` at full abrasion, where half
the credit is relabelling. Unlike the Juglet, where 70% of the adapter arm's
credit was relabelling.

Full per-draw record: `artifacts/ceramarm_30337242/seating_audit.json`.

## 5. What was measured badly, recorded rather than buried

**Four of the eight pots were fed a size value 9–28% below the band the model
was trained on.** Normalising the source sets the extent from the file origin
(max|v| = 0.5 for every pot), but the value actually fed to the model is
measured *after* the cloud is re-centred — and a squat or off-centre pot loses
more in that step than a tall one. Estimated conditioning values: `blue_pot`
0.405, `galli_pot` 0.432, `narrow_bottle3` 0.388, `narrow_bottle4` 0.561
(in band); `narrow_bottle1` 0.336, `narrow_bottle2` 0.305, `plate` 0.342,
`pink_bowl` 0.269 (below the 0.375 floor). The job's own summariser flagged
1200 of 2400 draws.

Why this does not sink the run: the value is **constant across all five rungs
of every ladder** and identical across all three arms, so neither the wear
comparison nor the arm comparison has a second variable in it. And the four
below-band pots include two that reassemble perfectly (`pink_bowl` 3/3,
`narrow_bottle2` 3/3), so a 9–28% shortfall is a mild extrapolation, not the
100× catastrophe of job 30336653. It is still worth fixing:
`normalize_real_hdf5.py` should centre before it scales.

**Job 30336653 must not be quoted.** Its three arms ran on the raw millimetre
file at `scales ≈ 77` and every arm floored at the free anchor on seven of
eight pots. That is out-of-domain input, not a result. See `docs/lessons.md`,
*"I marked a warning fixed by matching it to the wrong fix"*.

## 6. How much weight this carries

Eight pots, five wear levels, twenty draws each, three arms, one training run
of wear v3. The pots are real, really broken, and really scanned — the
strongest material this question has been asked on. Against that: it is **one**
adapter training run, so "wear v3 as trained on 2026-09-09 does not help" is
supported while "adapters cannot help" is not. Two of the eight pots contribute
nothing. And p = 0.031 comes from 40 paired comparisons that are not fully
independent — five rungs of the same pot share a pot.

Treat it as: **strong enough to stop spending on this adapter, not strong
enough to close the question of whether wear training can work.**

## 7. What it means for the work

1. **Stop extending wear v3.** Two tests now, on different material, both
   negative: 107 synthetic vessels (job 29880370) and eight real pots here.
2. **The `train_head=true` damage is the concrete lesson.** Training moved five
   pose-head tensors the adapter switch cannot restore, so the "off" arm is not
   a control and the trained model is worse than baseline even with the adapter
   disabled. Any future adapter run should set `train_head=false`, or its
   control arm means nothing.
3. **The ladder is the asset, not the adapter.** Six real pots that assemble
   unworn and come apart gradually under controlled abrasion is a working
   instrument for [O8](../../intent/O8-what-stops-the-juglet.md). Use it
   against the Juglet's measured roughness.
4. **Fix `normalize_real_hdf5.py` to centre before scaling**, so the value fed
   to the model lands in band rather than the stored extent.

## Reproduce

```bash
ssh spartan 'cd /data/gpfs/projects/punim2657/TORA/repo && DRAWS=20 sbatch scripts/hpc/eval_ceramics_arms.slurm'
./scripts/slurm_poll.sh <JOBID>            # from C:\PR
# then, on the laptop:
scp -r spartan:.../eval_runs/ceramarm_<arm>_<JOBID>/clouds artifacts/ceramarm_<JOBID>/<arm>/
python scripts/audit_ceramarm_seating.py  --runs artifacts/ceramarm_<JOBID>
python scripts/render_ceramarm_ladder.py  --pot blue_pot  --arm baseline
python scripts/render_ceramarm_ladder.py  --pot pink_bowl --arm adapter_off
```
