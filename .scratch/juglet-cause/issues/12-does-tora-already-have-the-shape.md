# 12: Does TORA already have the Juglet's shape, and lose it only when the sherds are made rigid?

**Type:** `wayfinder:research` (AFK)
**What to build:** A measurement of what TORA's raw output gets right about the Juglet
*before* each sherd is forced back to its real shape. It covers three things: the
vessel's outline, where each sherd's points land, and how much each sherd was bent to
get there. It runs against pots TORA does rebuild, and it comes with a render.

**Answers:** O8, U10

**Blocked by:** None. No GPU, no fetch, no Slurm: every input is already under `artifacts/`.

**Status:** done (2026-09-12). Reading C; the recorded prediction (A) was wrong. See
**Result** at the end.

**Needs-eye:** the render from the fourth box below. The question started as the
conservator's look and closes on it.

- `artifacts/shape12/shape_before_rigid.png`: the true juglet, the raw output and the
  rigid assembly, then the raw output coloured by bending, with a blue `M` on each
  mirrored sherd. The rows are the baseline's median and worst draws, the 2026-08-10
  attempt, and `blue_pot`.

  ```
  J=artifacts/jugdraw/jugdraw_baseline_30130049/clouds/juglet_gt_sample00000.npz
  python scripts/render_shape_before_rigid.py --case "Juglet baseline=$J:median" \
      --case "Juglet baseline=$J:worst" \
      --case "Juglet wear_v2, 2026-08-10 picture 05=artifacts/juglet_runs/jugletgt_render_wear_v2_29330980/clouds/juglet_gt_sample00000.npz:4" \
      --case "blue_pot (control)=artifacts/nb3/whole/ceramics_sample00001.npz:median" \
      --out artifacts/shape12/shape_before_rigid.png
  ```

- `artifacts/shape12/juglet_gap_map.png`: `juglet_gt` unrolled around its upright
  axis, showing where the missing piece is and which sherds border it.

  ```
  python scripts/render_juglet_gap_map.py \
      --npz artifacts/jugdraw/jugdraw_baseline_30130049/clouds/juglet_gt_sample00000.npz \
      --out artifacts/shape12/juglet_gap_map.png
  ```

## Why it exists

Conservator's observation, 2026-08-10, raised again 2026-09-12: in TORA's intermediate
output the Juglet looks like a good juglet, but its sherds are warped. The reading is
that TORA knows what the vessel looks like and does not know how each sherd fits.

How TORA works makes that possible:

- **The flow moves each of the ~5,000 points on its own** (`tora/modeling/tora.py:335`:
  one position per point). Nothing keeps a sherd rigid. The raw output
  (`generations_pred`) can therefore bend and stretch sherds into a convincing outline.
- **Each sherd is given one rigid position only at the very end:** the best fit to
  wherever its points ended up (`fit_transformations`, `tora.py:520`). That is the
  proposed assembly (`generations_proposed`, `tora/visualizer.py:202-212`). Every score
  in this map is read off it.

`scripts/measure_nonrigid_cheating.py` was written on 2026-08-10 to measure exactly this.
Nothing records it having been run.

Two things already point the same way, and neither was measured:

- ticket 02's render: the proposed Juglet "still reads as a juglet in outline, handle and
  neck included, with its sherds shuffled";
- O8's note that the outline survives even in the worst draw, "so on this object a
  silhouette is not evidence".

**Why it decides something.** Workspace `U10` proposes training a juglet-shaped prior,
on the premise that TORA lacks the Juglet's shape. U10 is paused on this ticket
(conservator's decision, 2026-09-12). Of the three possible readings below, two retire
that premise.

## Three readings, with the prediction recorded before running

| | raw outline vs `juglet_gt` | raw sherds vs their own place | what it means | next move |
|---|---|---|---|---|
| **A** | about as close as on pots TORA solves | far from home | **it has the shape, not the fit** (the conservator's reading) | U10 targets what TORA already has. The lever is matching each sherd to its place: break surfaces, O8 and G1 |
| **B** | as close | near home, but bent | it has the shape *and* roughly the fit; the rigid step loses it | the lever is sampling that keeps sherds rigid, not a prior. U10's premise retires |
| **C** | no closer than the rigid assembly | — | it does not have the shape | U10's premise stands; resume its grilling |

**Prediction (2026-09-12, before any number): A.** Recorded so it can be wrong.

## What to measure: per draw, per object, never pooled

**Ruler:** % of pot size, where pot size is the longest side of the **true** object's
box (`readout.unit_box_scale(pts_gt)`). This is the ruler every other ticket here uses.
Work with the free sherds; the anchor is reported separately. The Juglet runs
anchor-free and the ceramics anchor-fixed, and a pinned anchor would read as "not bent".

1. **Outline.** How close the raw output sits to the true vessel as a whole cloud,
   ignoring which sherd each point belongs to: `readout.chamfer` →
   `100 * sqrt(chamfer / 2)`, as in `check_identity_swap.py`. Measure the rigid assembly
   the same way. If the raw output is close and the rigid one far, the shape was there
   and the rigid step lost it.
2. **Each sherd in its own place.** For each free sherd, how far its raw-output points sit
   from its home in `pts_gt`, and how far after the rigid step. Match sherds by
   `part_ids` identity; no relabelling.
3. **Bending.** For each free sherd, how far its raw points sit from the rigid placement
   of that same sherd (`generations_pred` vs `generations_proposed`, which is the
   best-fit residual). Report it both as % of pot size and against the sherd's own size,
   so a small sherd bent badly is not hidden by a large one placed well.

## Inputs (already on disk)

- **The Juglet, job 30130049:**
  `artifacts/jugdraw/jugdraw_{baseline,adapter_on,adapter_off}_30130049/clouds/juglet_gt_sample00000.npz`,
  20 draws each. The **baseline** (the untouched model) carries the verdict. The adapter
  arms are secondary.
- **The original observation:**
  `artifacts/juglet_runs/jugletgt_render_wear_v2_29330980/clouds/juglet_gt_sample00000.npz`,
  attempt 05. Check whether "05" counts from 0 or 1 against the 2026-08-10 render before
  reading it.
- **Control, job 30167044 `whole` arm:** `artifacts/nb3/whole/ceramics_sample0000{0..7}.npz`,
  eight fresh pots, 10 draws each. The pots this model rebuilds (`blue_pot`,
  `narrow_bottle2`, `narrow_bottle4`, `pink_bowl`) give the floor: how much bending a
  *correct* assembly carries. Without that floor, "bent" has no scale.

Check that `generations_pred` and `generations_proposed` both exist in each file before
trusting it. `visualizer.py` writes the second only when rotations were passed.

## Fix the instrument before reading it

Reading `measure_nonrigid_cheating.py` (2026-09-12) found three faults:

- **Its ruler is the box of the prediction** (lines 64-65:
  `norm(prop.max - prop.min)`). `readout.unit_box_scale` exists to forbid this: a
  splayed assembly has a bigger box, so the Juglet's bending would read *smaller* the
  worse it is placed. Use the true object's longest side instead.
- **Its verdict is a fixed 2% cut-off** chosen without a control. That is the
  absolute-threshold fault that once faked a whole finding here. Remove it; read against
  the control instead.
- **It includes the anchor**, and its docstring promises a `spread` (bending against
  sherd size) that the code never computes.

Extend the script, or add a sibling that imports `chamfer` and `unit_box_scale` from
`readout`. Do not copy the arithmetic.

**The check that could refute the instrument:** on a pot the model rebuilds, bending
should be small and the raw and rigid outlines should nearly agree. If the control shows
large bending, suspect the ruler before reading the Juglet.

## Acceptance criteria

- [x] The three faults are fixed. The control's floor (bending and outline, per pot, on
      the four pots with a valid unworn control) is printed first.
- [x] The 2026-08-10 attempt reproduces (raw a closed vessel, rigid splayed) in numbers
      and in a render. If it does not, stop and say so.
- [x] Measurements 1-3 are run on all 20 baseline Juglet draws: median and range, plus
      per sherd on the median draw. The adapter arms are reported as secondary.
- [x] **Render.** For the median and the worst baseline draw, three columns: the true
      juglet, the raw output, and the rigid assembly. Use one colour per sherd and
      re-centre nothing. Add the raw output coloured by per-point bending, and the same
      set for one control pot. The view must resolve a few % of pot size. Points on these
      clouds sit ~1.8% of pot size apart, so bending below that is reported as "not
      resolvable", not as "rigid". `render_juglet_vs_fresh.py` and
      `render_juglet_spread.py` already draw `generations_pred`; reuse them.
- [x] Reading A, B or C is stated against the recorded prediction.
- [x] Secondary, suggestive only (one object): whether the most-bent or furthest-placed
      sherds are the ones bordering the gaps, read off the `juglet_gt` render. The Juglet
      is missing one very visible piece **and a few small ones** (conservator,
      2026-08-10, `scripts/build_wear_trainset_v2.py:174-207`).
      - **If they cluster at the gaps,** that ties the missing pieces to the shape: TORA
        is stretching the neighbours to cover the hole.
      - **That triggers a targeted follow-up.** On `galli_pot`, remove one large piece
        plus two small ones, then score the pieces that remain against `galli_pot`'s own
        complete run.
      - **Why `galli_pot`, with its caveat.** It is the only control with enough pieces
        (10). The four clean pots have 3-5 fragments, so losing three would leave
        almost nothing. TORA only partly rebuilds it complete: 7 of 9 free sherds
        seated in ticket 04, already broken at zero wear in ticket 11. So the question
        is whether the sherds that seat when it is complete still seat, not whether
        the pot comes out whole.
      - **Why the follow-up is new.** Ticket 04 removed one piece at a time from other
        pots and never tried a loss shaped like the Juglet's. `omit_rank` removes exactly
        one piece, so the follow-up needs a code change.
- [x] The ticket names which of the three it found: method failed, ruler broken, or
      reference wrong.
- [x] Written back: a line in O8 under "What is still open", and U10's premise marked
      confirmed, retired or narrowed.

## Weight this can bear

This is one object: 20 draws of one model, against eight control pots. Reading A or B
would say *what* TORA does with the Juglet, not *why*. It says nothing about GARF or
PF++, which move sherds as solid pieces throughout.

## Result (2026-09-12)

**Reading C. The recorded prediction, A, was wrong.** Before its sherds are made solid,
TORA's output is no closer to the true Juglet than its solid assembly, and both sit
where TORA's failed pots sit. The good-looking juglet the conservator saw is an outline,
but it is a failed pot's outline. Its sherds are already about 12 mm from their own
places before anything is made solid.

All figures below are % of pot size, as medians over draws. Pot size is the longest side
of the true box, about 65 mm for the Juglet, so 1% is about 0.65 mm. "Free" is
`generations_pred` and "solid" is `generations_proposed`.

### Floor: job 30167044, `whole` arm, 10 draws per pot

| pot | outline free / solid | own place free / solid | bent mean / worst sherd |
|---|---|---|---|
| narrow_bottle4 | 1.25 / 1.25 | 1.36 / 1.36 | 0.10 / 0.15 |
| blue_pot | 1.31 / 1.33 | 2.31 / 2.33 | 1.12 / 4.16 |
| pink_bowl | 1.32 / 1.32 | 1.35 / 1.35 | 0.12 / 0.13 |
| narrow_bottle2 | 1.10 / 1.09 | 1.13 / 1.12 | 0.09 / 0.10 |

**The check that could refute the instrument passed.** On pots TORA rebuilds, the free
and solid figures agree to 0.02%, and bending stays at or below 0.15%. There is one
exception: `blue_pot`'s worst sherd reads 4.2%. That is its smallest rim chip (sherd
3, 131 points), which comes out mirrored in 10 of 10 draws and still seats.

Failing controls, for scale (outline free / solid, own place free):

| pot | outline free / solid | own place free |
|---|---|---|
| `narrow_bottle1` | 4.17 / 4.40 | 24.4 |
| `narrow_bottle3` | 4.92 / 5.11 | 16.6 |
| `plate` | 2.00 / 2.02 | 11.9 |
| `galli_pot` | 1.98 / 1.98 | 11.3 |

### The Juglet: job 30130049, baseline (the untouched model), 20 draws

Points sit 1.62% apart (about 1.05 mm).

- **Outline.** Free **4.42%** [3.03–8.39], about 2.9 mm. Solid **4.91%**
  [3.38–8.58], about 3.2 mm. The 0.3 mm between them is below the point spacing. Every
  draw is at least twice the worst rebuilt pot.
- **Own place.** Free **17.95%** [10.2–25.7], solid **18.30%** [10.9–26.3]. That is
  about 12 mm either way.
- **Bending.** The mean is 2.27%, and the worst sherd is 5.75% (about 1.5 mm and
  3.7 mm). The anchor reads 0.01%, as a pinned sherd should.

Per sherd, median draw (draw 1). Own place is free / solid; the last column is how many
of the 20 draws that sherd came out mirrored:

| sherd | own place | bent | mirrored |
|---|---|---|---|
| 1 | 13.46 / 14.08 | 4.37 | 8/20 |
| 2 | 21.69 / 24.22 | 5.74 | 10/20 |
| 3 | 5.79 / 5.36 | 3.60 | 10/20 |
| 4 | 11.86 / 11.82 | 0.15 | 4/20 |
| 5 | 16.65 / 16.47 | 5.54 | 9/20 |
| 6 | 24.50 / 24.51 | 0.18 | 7/20 |
| 7 | 34.49 / 34.56 | 0.13 | 9/20 |
| 8 | 15.73 / 15.69 | 0.13 | 7/20 |

**Secondary arms give the same reading.**
- `adapter_on`: outline 4.98 / 5.48, own place 22.1 / 22.5.
- `adapter_off`: outline 6.07 / 6.64, own place 17.6 / 18.6.

**The 2026-08-10 attempt reproduces.** This is wear_v2, job 29330980, 5 draws. Picture
"05" is draw index 4: `visualizations/` counts from 1 and `results/` from 0. In that
attempt the free output is a closed vessel and the solid one splays: outline 2.5 / 3.7,
own place 15.5 / 16.2. The median over its 5 draws is 2.45 / 4.47 for outline and
14.2 / 15.3 for own place. This is the flattering end of TORA's range. The free outline
beats the solid by more than the point spacing here. It is still twice the floor, and
the sherds are still about 9–10 mm from home.

### What the "warping" is: mirror images

A sherd counts as *bent* when its free points sit more than 1% from its best solid
placement. A bent sherd counts as a *mirror* when a placement that is allowed to reflect
fits it to within 3× that arm's own jitter. The jitter is the median leftover of the
unbent sherds in the same arm. The solid step cannot reflect, because
`tora/procrustes.py:30-33` forces det = +1. Training uses turns only
(`tora/data/transform.py:46`, `dataset.py:433-447`).

| object | free sherd-draws | mirror | bent out of shape | solid |
|---|---|---|---|---|
| Juglet baseline | 160 | 64 | 0 | 96 |
| Juglet adapter_on | 160 | 73 | 0 | 87 |
| Juglet adapter_off | 160 | 89 | 0 | 71 |
| Juglet wear_v2 | 40 | 26 | 0 | 14 |
| narrow_bottle4 / pink_bowl / narrow_bottle2 | 30 / 20 / 20 | 0 | 0 | all |
| blue_pot | 40 | 12, all on its two smallest chips (sherd 3 10/10, sherd 0 2/10) | 0 | 28 |
| narrow_bottle3 | 30 | 6 | 4 | 20 |
| narrow_bottle1 | 110 | 39 | 2 | 69 |
| plate | 50 | 13 | 2 | 35 |
| galli_pot | 90 | 13 | 0 | 77 |

**No Juglet sherd is bent out of shape in any arm. Every one that looks warped is a
mirror image.** The solid step cannot reproduce a mirror image. It turns the real sherd
as close as it can, and the result sticks out from where the free output had it: up to
about 4 mm on a typical draw, and 6 mm on the worst.

**Mirroring is not why the Juglet fails.** On the baseline, mirrored sherds sit
**13.5%** from home (25% seated), and solid ones **19.2%** (21% seated). On wear_v2 it
runs the other way, 14.8% against 7.3%, on only 40 sherd-draws.

On the control pots, mirroring and misplacement coincide on two of them:

| pot | mirrored sherds from home | solid sherds from home |
|---|---|---|
| `galli_pot` | 20.0% | 2.4% |
| `plate` | 32.3% | 1.4% |

**Not established.** Two things are open: why a model never shown a reflection outputs
one, and what the reflection is. It is not simply a flip through the wall: the
reflection plane is a median 51° off the wall-thickness direction (IQR 33–70°). This is
a lead, and it is worth its own ticket if pursued.

### Secondary: do the worst-placed sherds border the missing piece?

`juglet_gap_map.png` unrolls `juglet_gt` around its upright axis. The cells are 10°
around by 3.8% tall, about 2.7 × 2.5 mm, so a chip smaller than one cell does not show.

**One hole.** It spans 19–42% of the height and 60° around, about 16 × 15 mm, and it is
the "one very visible piece". Its border, counted in edge cells shared with the hole:
- sherd 4: 8;
- sherd 2: 8;
- sherd 3: 7;
- sherd 6: 1.

The small missing pieces are below this map's resolution.

| sherd | edge cells on the hole | from home (median, 20 draws, solid) | seated | mirrored |
|---|---|---|---|---|
| 1 | 0 | 3.5% | 75% | 40% |
| 2 | 8 | 22.5% | 10% | 50% |
| 3 | 7 | 15.8% | 20% | 50% |
| 4 | 8 | 12.6% | 5% | 20% |
| 5 | 0 | 19.2% | 5% | 45% |
| 6 | 1 | 20.1% | 0% | 35% |
| 7 | 0 | 4.2% | 65% | 45% |
| 8 | 0 | 31.4% | 0% | 35% |

The sherds bordering the hole sit a median 17.9% from home with 9% seated. The others
sit 11.7% from home with 36% seated. That difference comes entirely from sherds 1 and 7,
the two TORA usually seats, which are both away from the hole. Sherds 5 and 8 are also
away from it, and they are among the worst placed. With four sherds on each side, the
two best land on the same side by chance about one time in five (6 of 28 ways).
Mirroring does not differ either: 39% against 41%.

**No clear clustering, so the `galli_pot` follow-up is not triggered.** Nothing here
ties the missing piece to TORA stretching the neighbours: there is no stretching, and
the neighbours are not singled out.

### Which of the three

**The method genuinely failed**, by misplacement, and before the solid step as much as
after it.

- **The measurement was not broken.** It was checked. The floor passes. The three listed
  faults were fixed:
  - the ruler is now the true box;
  - there is no fixed cut; readings are against the control;
  - the anchor is reported apart, and the size-relative figure is computed.

  Two more changes were made during the ticket:
  - a KD-tree chamfer (`readout.chamfer_fast`), which agrees with `readout.chamfer` to
    1e-5;
  - the mirror test. "Bending" was first read as deformation. A fixed 0.5% cut for
    "mirror" then misread `adapter_off` (0 of 89), because that arm's jitter is 0.58%.
    It was replaced by the per-arm jitter rule.
- **The reference was not wrong.** `juglet_gt` is valid per O8.

### Weight

This is one object. It rests on 20 draws of the untouched model, plus two adapter arms
(20 draws each) and 5 draws of wear_v2, all giving the same reading, against eight
control pots, four of them rebuilt.

Within that, reading C is not borderline: every Juglet draw's outline is worse than
every rebuilt pot's. It says TORA does not have the Juglet's shape at the fidelity of a
solved pot. It does not say a shape prior would supply that shape.

The mirror finding covers the Juglet and five control pots. It is a lead.

### Written back

- `tora/intent/O8`: a bullet under "What is still open".
- Workspace `intent/U10`: the premise is confirmed and the status line updated. Grilling
  may resume, and C2 still blocks it.
- `intent/README.md`: the U10 row.
- `map.md`: this ticket moved to "Decisions so far".

### Commands

Laptop, no GPU. The inputs are already under `artifacts/`.

```
python scripts/measure_nonrigid_cheating.py --npz artifacts/nb3/whole/*.npz \
    --json artifacts/shape12/control_whole_30167044.json \
    > artifacts/shape12/control_whole_30167044.txt
for arm in baseline adapter_on adapter_off; do
  python scripts/measure_nonrigid_cheating.py \
      --npz artifacts/jugdraw/jugdraw_${arm}_30130049/clouds/juglet_gt_sample00000.npz \
      --label "Juglet $arm (job 30130049)" --json artifacts/shape12/juglet_${arm}_30130049.json \
      > artifacts/shape12/juglet_${arm}_30130049.txt
done
python scripts/measure_nonrigid_cheating.py \
    --npz artifacts/juglet_runs/jugletgt_render_wear_v2_29330980/clouds/juglet_gt_sample00000.npz \
    --label "Juglet wear_v2 (job 29330980, 2026-08-10)" \
    --json artifacts/shape12/juglet_wear_v2_29330980.json > artifacts/shape12/juglet_wear_v2_29330980.txt
```

The renders are under **Needs-eye**, at the top.
