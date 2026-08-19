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

One caveat on the figure: the **Plate** panel looks filled, but that is the slice
direction. A plate's thin axis is its third principal axis, so a slab there
captures the whole disc face-on rather than sectioning it. Not evidence of
solidity — the same viewpoint trap that made the plate look asymmetric in
`measure_vessel_symmetry.py`.

## What this corpus cannot do

**Carry much simulated wear.** Its meshes are sampled at **0.232–0.283% of
object**, against blue_pot's 0.068% — three and a half times coarser — and the
blunting cutoff is 0.30–0.50%. The cutoff sits barely above the spacing, so wear
will act weakly on these objects.

That matters less than it sounds. Gate A found real archaeological scans carry no
fracture texture at these scales anyway, and the training set now blurs to 0.25%
of object by default; Breaking Bad's native sampling is already close to that.
So these objects contribute **shape variety**, and the 27 high-resolution
objects continue to carry the **wear axis**. Keeping those roles separate is
cleaner than pretending one corpus does both.

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
