# Wear v3: switchable adapters, external shapes, real worn fracture

**Status:** plan, 2026-08-18. Supersedes the data half of
`EXTERNAL_DATA_PLAN.md`, which it absorbs. Gated — see §5.

Built on what the wear tests actually established
(`WEAR_TEST_RESULTS.md`): wear-augmented training **stops heavily worn pottery
collapsing**, visibly, and does nothing measurable on fresh material. The Juglet
is still unsolved. v3 is aimed at the Juglet.

---

## 1. What we are NOT going to assume

Two things were checked before planning around them, and one came back against
the hypothesis that prompted it.

### The Juglet's shape is not unusual

The conservator's hypothesis was that the Juglet is asymmetric — one handle —
and that the model has only ever seen surfaces of revolution. Measured
(`measure_vessel_symmetry.py`) by spinning each object about its own axis and
asking how far the surface travels:

| object | surface movement | surface outside the wall |
|---|---|---|
| **Juglet** | **1.31%** | **3.6%** |
| narrow_bottle1–4 | 0.8–1.4% | 0.1–0.3% |
| blue_pot | 2.88% | 1.9% |
| galli_pot | 5.13% | 19.7% |
| pink_bowl | 5.84% | 13.9% |
| **training mean (27 objects)** | **3.16%** | **7.9%** |

The Juglet is **more** axially symmetric than the average training object and
sits in the same class as the narrow bottles. Its handle is 3.6% of the surface.
**The shape hypothesis is not supported and v3 should not be built on it.**

(The measure misreads flat objects — the plate's 27% is flatness, not an
attachment — so it is trustworthy for vessels and not for dishes.)

### What does distinguish the Juglet

Ranked by how much they differ from anything in training:

1. **Its scan is coarse.** 0.243% point spacing against blue_pot's 0.068% —
   three and a half times. Nothing finer than ~0.5% of object size is recorded
   at all.
2. **Its wear is real**, not simulated, and we cannot check whether ours
   resembles it (§2 of `WEAR_TEST_RESULTS.md`).
3. **A piece is genuinely missing**, so a correct reconstruction leaves a gap.

v3 should target 1 and 2. 3 is already addressed by the missing-piece variants.

---

## 2. Switchable adapters (LoRA)

The conservator's proposal, and it has direct precedent in the sibling method.

**GARF already does this.** Adapters in the self-attention and global-attention
layers of the **final transformer block**, rank 128, alpha 256, dropout 0.1,
with only the adapters and the pose-prediction MLP heads unfrozen. It reports
**5–10 domain-specific objects** sufficient for substantial gains, specifically
on thin-shell material — which is our case.

Why it fits here better than more fine-tuning:

- **Domains stay separate.** Fresco fracture, ShapeNet vessels and real
  archaeological pottery are different material. One set of weights forced to
  serve all three is how wear_v1 bought worn-material gains by losing fresh
  ones.
- **It is reversible.** An adapter can be switched off, which means a negative
  result costs nothing and a per-domain comparison is possible at all.
- **It is cheap enough to run per domain**, so RePAIR and GB do not compete for
  the same weights.

**Not currently present.** Neither `peft` nor any LoRA code exists in TORA or
the Spartan environment. Adding it is the first implementation task.

**Plan:** one base checkpoint, then adapters — `lora_gb` (synthetic vessel
shapes), `lora_repair` (real worn fracture), `lora_pottery` (our own
archaeological material). Evaluate each on and off, on the same objects.

---

## 3. Geometric Breaks — shapes to train on

1,125 vessel-shaped objects: 500 jars, 447 bottles, 178 mugs, against the **8
ceramic vessels** in our training source.

**Use `model_c.ply`**, the waterproofed complete vessels — not GB's own
fractures, which are 97.3% single-fragment because it is a repair dataset, with
break faces that are boolean cuts from a jittered icosphere. We fracture and
wear them ourselves.

Resolution checked and adequate: 20k–150k vertices per fragment, ~0.1% of object
size, against our 0.30–0.50% blunting cutoff.

**Mugs are the handled subset** — 178 objects, every one with a handle. Worth
keeping as a labelled group even though the symmetry measurement says the handle
is unlikely to be the Juglet's problem: it is a cheap way to test that
conclusion rather than trust it.

**Still gated on the fracturing method** (§5).

---

## 4. RePAIR — real worn fracture, geometry only

~1,000 Pompeii fresco fragments reassembled by archaeologists, ground-truth
poses shipped with the data, scanned at 110k–193k vertices per fragment
(~0.05–0.2 mm).

**The conservator's constraint, which narrows this usefully:** these are fresco
plaques, not ceramic sherds, and **the painted surface does much of the matching
work**. We are interested only in **how the worn fracture joins**.

That rules out using RePAIR as a reassembly benchmark for our purposes — a
geometry-only method will do badly there for reasons that say nothing about
pottery, and reporting that would be misleading. What it rules *in* is narrower
and more valuable:

**Use RePAIR to measure real worn fracture surfaces.** A thousand of them, with
a known correct answer, against our one Juglet. Specifically:

- Run the break-face relief spectrum on RePAIR's fracture ribbons and ask
  whether real erosion leaves a signature at scales these scans resolve.
- If it does, **calibrate the wear model against it** — the calibration the
  Juglet could not provide, because its scan is too coarse.
- Compare the *shape* of that signature with what our blunting produces.

**Ignore the painted surface entirely.** Use geometry only, and take the
fracture ribbon around each plaque's perimeter — which is the thin-slab case,
the same geometry as an eggshell sherd, and the case where our own blunting is
weakest at the edges.

A `lora_repair` adapter is worth trying afterwards, but the measurement is the
point and comes first.

---

## 5. GATES, in order

**A. Does real erosion leave a measurable signature?** Pull RePAIR's 3 GB
open-discovery subset, merge duplicate vertices (the OBJs store one per face
corner — a naive spacing measurement reads 0.000%), extract the fracture
ribbons, run the spectrum. If yes, the wear model finally has something real to
aim at. If no, we learn the signature is below what archaeological scanning
delivers, which settles the question rather than leaving it open.
**Cost: a few hours. Highest value of anything here.**

**B. How to fracture GB's vessels.** Nothing in this repo can break a whole
object into pieces. The choice matters more than anything else in the chain
because the break surface *is* the signal: fracture modes (Sellán et al., what
Breaking Bad used, physically motivated) versus Voronoi cells cut with booleans
(a day's work, near-planar faces carrying almost no curve, which would defeat
the purpose). **Read fracture modes at its pinned version first, for thin-walled
vessels specifically — a pot is a shell.**

**C. LoRA into TORA.** Add `peft`, insert adapters per the GARF recipe, verify
that switching an adapter off reproduces the base model exactly. That check
matters: an adapter that cannot be turned off cleanly is not switchable.

---

## 6. Order of work

1. **Gate A** — measure real worn fracture in RePAIR. Cheap, and it either
   unblocks the wear model or closes the question.
2. **Gate C** — LoRA plumbing, verified reversible on the existing checkpoint.
3. **Gate B** — decide the fracturing method, then build GB vessels.
4. Train `lora_gb`, evaluate on and off against the Juglet and the worn sweep.
5. If Gate A produced a signature, retune the wear model against it and rebuild.

---

## 7. How results will be judged

Not on part accuracy. It over-credits — it read 0.80 on a Juglet assembly the
render shows is scattered — and rotation error over-penalises, because a
symmetric fragment turned about its own axis gives a different matrix and the
same assembly.

**Render every assembly beside its correct answer, and read rotation error with
~40° as the collapse threshold rather than 10°.** Both stated in
`WEAR_TEST_RESULTS.md` §5, both learned the hard way.
