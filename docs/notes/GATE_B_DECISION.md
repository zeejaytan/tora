# Gate B: don't build a fracturing pipeline — filter the one we have

**Decided 2026-08-19.** Gate B of `WEAR_V3_PLAN.md` asked how to fracture
Geometric Breaks' 1,125 vessels, since nothing in this repo can break a whole
object into pieces. The answer is that we do not need to.

## The decision

Use the **375 vessel-shaped objects already in `breaking_bad_vol.hdf5`**,
filtered by **effective piece count ≥ 4**. That yields **2,946 genuinely
multi-piece breaks across 371 distinct vessel shapes**, against the **8 ceramic
vessels** in the current fine-tuning source.

No tetgen. No Mosek academic licence. No Python 3.9 environment. No fracturing
of 1,125 objects. The data is on disk and was fractured with fracture modes by
the people who wrote it.

## Why it nearly did not work: piece count is not piece balance

The corpus looks better than it is if counted naively. Nearly a tenth of
fracture instances have five or more pieces — but rendering them shows one
dominant piece with slivers at the rim, and the measurement agrees:

| | |
|---|---|
| mean largest-piece share | **88.4%** |
| mean effective piece count | **1.43** |
| instances behaving as one piece | **89.2%** |

A break that is 97% one remnant plus three chips is a chip-detection problem,
not a reassembly. **Filtering on raw piece count would have selected 89%
rubbish.**

The filter is the **inverse Simpson index**, `1 / Σ share²`, on fragment sizes:
four equal quarters gives 4.0, one remnant with three slivers gives ~1.0. It is
the number to compare against the Juglet, which is nine sherds of broadly
comparable size.

Scanning every object and every instance:

| threshold | objects | instances |
|---|---|---|
| effective ≥ 3 | 375 of 375 | 4,036 |
| **effective ≥ 4** | **371 of 375** | **2,946** |
| effective ≥ 5 | 352 of 375 | 2,098 |

The good breaks are spread across essentially every object rather than
concentrated in a few, which is what makes this fill the shape gap rather than
just adding instances.

## They are hollow, and that was worth checking

The conservator's warning: some Breaking Bad meshes are solid rather than
thin-walled. Plausible rather than paranoid — fracture modes tetrahedralises the
interior through a cage, so a non-watertight input comes out solid whatever it
looked like as a surface. And it would matter: a sherd's fracture is a ribbon
through a wall, a solid's is a broad face through the body.

Checked two ways. `wear_ops._wall_estimate` found a wall in **72 of 72** sampled
objects, median **0.95–3.10% of object** — our real pottery sits at 0.22–2.90%.
And slices cut through each object show thin outlines with empty interiors, not
filled sections.

**CORRECTED 2026-08-31 (jobs 29765705, 29768556).** That 72-of-72 is wrong, and
the instrument that produced it was already known to be broken: `_wall_estimate`
has a search reach of about 2% of object, so it reports a wall of roughly its own
reach on anything — including a solid. Both `validate_wall_estimator.py` and
`check_wall_estimator_noise.py` flagged it and neither conclusion was written
back here. On **1053** objects screened with an even-odd scanline fill (checked
against a solid sphere at 1.000 and two shells at 0.097/0.277, and confirmed
object-by-object in `artifacts/fill_ladder.png`, where each scanline's measured
interior is shaded):

| fill | what it is | n | wall by 2V/A | mean cells |
|---|---|---|---|---|
| <0.25 | thin shell | 394 | 2.75% | 0.61 |
| 0.25–0.5 | thick shell | 212 | 5.41% | 1.19 |
| 0.5–0.8 | mostly filled | 59 | 6.39% | 1.46 |
| ≥0.8 | **SOLID — not a vessel** | **388** | **17.14%** | 3.95 |

2V/A shares no code with the scanline and agrees with it, so the label is not an
artefact of one routine. **37% of the corpus is a solid lump.** The conservator's
warning was right and this section was wrong.

Worse, the two defects coincide. Cross-tabulating fill against cells through the
wall: **solid & ≥2 cells 370, hollow & <2 cells 648, hollow & ≥2 cells 17,
solid & <2 cells 18** — 97% on one diagonal. Where TORA can resolve the break
face the object is not a vessel; where it is a vessel TORA cannot see the break.
A `cells>=1 & fill<0.5` screen keeps **207 of 1053 (19.7%)**.

One caveat on the figure: the **Plate** panel looks filled, but that is the slice
direction. A plate's thin axis is its third principal axis, so a slab there
captures the whole disc face-on rather than sectioning it. Not evidence of
solidity — the same viewpoint trap that made the plate look asymmetric in
`measure_vessel_symmetry.py`.

## What this corpus can and cannot carry — CORRECTED 2026-08-19

An earlier version of this section said these objects "cannot carry much
simulated wear". That was half right and the important half was wrong, and the
conservator caught it: *"I don't understand how a coarse model stops you making
it worn. Wear is blunting of its fracture surface and reducing the contact
surface between the break."*

Wear does two things and they have different requirements. Measured
(`test_wear_on_coarse.py`):

| | spacing | available to blunt | blunting → gap | recession → gap |
|---|---|---|---|---|
| bbad Vase | 0.252% | 0.0053% | +0.7% | **+9.0%** |
| bbad Vase | 0.467% | **0.0001%** | +0.0% | **+9.7%** |
| bbad Vase | 0.357% | **0.0002%** | +0.0% | **+6.2%** |
| blue_pot | 0.057% | 0.0131% | +0.7% | +1.1% |
| plate | 0.061% | 0.0080% | +1.8% | +1.9% |

**BLUNTING is genuinely inert here.** On the coarsest meshes 0.0001% of the
surface stands proud at the cutoff, a hundredth of blue_pot's, and blunting moves
the joins by 0.0%. There are no teeth in the file to remove — not a failure of
the tool, the geometry was never recorded.

**OPENING THE JOINS works better here than on our fine scans.** The same 0.05%
retreat opens these joins by 6–10% against 1.1–1.9% on blue_pot and the plate,
because these fragments were cut from one mesh and mate exactly, so a retreat has
nowhere to hide.

That is the half that matters. Gate A found real archaeological scans carry no
fracture texture either, so the contact reduction is the effect that survives
digitisation — and it is what makes a worn pot hard to reassemble.

**Consequence: recession must be un-retired for this corpus.** It was retired on
a dose table measured entirely on fine meshes, where blunting opened joins more
cheaply; on a mesh where blunting is inert that comparison does not apply, and
generalising it was a mistake.

**Not yet measured:** what recession costs the CURVE on these coarse meshes. On
fine meshes the same dose cost 2.5–5.3%. That must be checked before any of this
reaches a training set.

## Geometric Breaks is not dead, only deferred

GB's `model_c.ply` are far finer (20k–150k vertices per fragment, ~0.1% of
object) and could carry wear properly. If the wear axis ever needs shape variety
too, that is the route — and it would then need the fracturing pipeline this
gate was originally about.

One thing to check first if we go there: GB's meshes are **waterproofed**, and
waterproofing a hollow pot may close its mouth and make it solid. The same
hollowness test should be run on GB before committing, not after.

## Next

Build a vessel-variety training set from the filtered corpus and fine-tune a
`lora_bbad_vessels` adapter on it, evaluated on and off against the Juglet and
the worn sweep. The adapter machinery passed Gate C on 2026-08-19.
