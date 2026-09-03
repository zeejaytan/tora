# Intent — TORA

**What this folder is.** What we are trying to establish with TORA, and what would
count as establishing it. One file per open question.

- `AGENTS.md` — *how to work in this repo*
- `intent/` — *what we are trying to establish, and what would count* ← you are here
- `.scratch/<feature>/` — the tickets that get us there
- `docs/notes/` — the **log**: what happened, in the order it happened

**This folder is state, not a log.** Edit files in place. If a claim here is wrong,
fix the line — do not add a correction banner. Git holds the history. That is the
difference between `intent/` and `docs/notes/`, and it is the whole reason this
folder can stay readable.

**Numbering is permanent.** O3, O4 and O5 are retired; O8 is next. Never reuse a number — tickets
reference them.

**Last updated:** 2026-09-03.

---

## The question

Can a learned fracture-assembly method reassemble **real, worn, excavated pottery** —
and, given that excavated material almost never comes with a correct answer to score
against, **how would we know?**

TORA (`NahyukLEE/tora`) is the method under test, zero-shot and fine-tuned, on the
Fractura, Juglet and thin-walled sets.

The second half of that question is not a caveat. It is half the research. This
project has already produced a full finding that was an artefact of the ruler, and a
benchmark whose reference answer was not an assembled vessel.

## Who it is for

A conservator reassembling excavated ceramics, deciding whether a machine proposal is
worth acting on. Not a benchmark leaderboard. A result only counts if it can be stated
as "this many sherds seated correctly, this far out of place" and confirmed by looking
at the reconstruction.

---

## Open questions

| # | Question | Status | Blocked by |
|---|---|---|---|
| [O1](O1-wall-vs-sampling.md) | Can the network resolve a real pot wall at all? | open — **highest priority, ~1 day** | none |
| [O2](O2-valid-evaluation.md) | Is there any valid way to score this work? | open — **blocks O6 and all corpus work** | none |
| ~~O3~~ ~~O4~~ ~~O5~~ | *moved to the CSC project 2026-09-03 — see below. Numbers retired, not reused.* | — | — |
| [O6](O6-juglet-under-valid-reference.md) | Does the Juglet failure survive a valid reference? | open | **O2** |
| [O7](O7-wear-grounding.md) | Is the wear model grounded in real material? | open | none |

**Start with O1 and O2.** O1 is one day and can stop the corpus project outright;
until O2 closes, nothing built here can be shown to help or hurt.

---

## What is established

Load-bearing claims, with the weight each can bear.

| Claim | Weight | Source |
|---|---|---|
| TORA is **competent on real fresh fracture** — 0.861 avg / 0.928 best-of-N sherds correctly placed on 6 held-out real objects, matching its synthetic score (0.860). Assembles a 5-piece pot to 3.5° and a 10-piece ceramic at 0.8–0.9. | 6 objects, 1 checkpoint | `docs/notes/TORA_GOOD_VS_BAD_ANALYSIS.md` (jobs 27858648 / 27859890) |
| **TORA genuinely fails on the Juglet.** Anchor sherd with the other eight clustered against one side; no vessel. Stable across generations, which themselves vary noticeably run-to-run. | 1 object, visual verdict | `docs/notes/JUGLET_TORA_ROOTCAUSE.md`, `artifacts/juglet_viz/` |
| **The Juglet's reference answer is invalid** — it is the scattered scan/table layout, not an assembled pot. No *numerical* conclusion about Juglet reassembly can be drawn from this benchmark as shipped. | verified by rendering | same |
| **Wear-augmented training stops heavily worn pottery collapsing**, visibly; does nothing measurable on fresh material. | visual, small n | `docs/notes/WEAR_TEST_RESULTS.md` |
| **Real eroded archaeological fracture carries no fracture-like roughness** at any scale these scans resolve (texture rises as R^1.7; true fracture is R^0.4–0.8). Whether the ground removed it or the scanner never saw it **cannot be separated** with 0.4 mm data. | 20 RePAIR fragments | `docs/notes/GATE_A_RESULT.md` (job 29404479) |
| **Piece count is not piece balance.** 89% of Breaking Bad vessel instances behave as one piece; filtering on raw count would have selected 89% rubbish. The inverse Simpson index on fragment sizes is the filter that works. | whole corpus | `docs/notes/GATE_B_DECISION.md` |

## Retracted — do not rebuild on these

- The **synthetic-to-real capability gap**. There is none. Every "total failure at
  exactly `1/n_parts`" was an absolute `CD < 0.01` threshold applied to raw scan
  units, judging real objects against a bar 125–216x stricter than synthetic.
- The **joint-solve wall**, and the architectural coarse-shape-bootstrap
  recommendation that rested on it.
- The **fine-tuning remedy**: it *harmed* the model (limb3 7.9° to 26.4–40.5°) to fix
  a problem that did not exist. Two GPU training runs spent on it.
- The **Juglet shape hypothesis**. Measured, the Juglet is *more* axially symmetric
  than the average training object; its handle is 3.6% of the surface.

Cost of not catching this earlier: **four probes and two training runs.** The tell was
a metric reading *exactly* `1/n_parts` across every checkpoint and piece count while
`rotation_error` on the same predictions said 29°. That constancy was an instrument
failure, not a finding.

---

## Constraints

- **8 ceramic vessels** in `real_finetune.hdf5`; **none is an excavated vessel type**.
- **One real worn object** (the Juglet) — and its reference answer was wrong.
- **No in-house route to break a hollow vessel.** Every dataset here arrived pre-fractured.
- **Wall thickness is the number everything turns on.** A fracture is a ribbon through
  a wall, not a face through a body. The median training vessel gets **0.78 sampling
  cells** through its wall and mates at 83–96°; objects above 4 cells mate at 152–177°.
- Laptop edits, GitHub push, Spartan pull-only; heavy data stays on GPFS. See `AGENTS.md`.

## How a result must be reported

Every finding names **which of these three it is**, because they lead to opposite decisions:

1. **The method failed** — TORA cannot do this on this material.
2. **The measurement was broken** — the ruler was wrong. *(Has happened. Faked a finding.)*
3. **The reference answer was wrong** — we scored against a non-reassembly. *(Has happened. The Juglet.)*

And it carries a **rendered** before/after, at a view that resolves the scale being
tested. A numeric check missed the wear bug through three rounds; drawing the join
caught it in seconds.

## Stop conditions

Written in advance so they are not renegotiated in the moment:

- **O1 fails and cannot be designed around** — the finding is about sampling density, and the corpus is premature.
- **O2 has no evaluation** — nothing built here could be shown to help or hurt.

## The corpus moved out

The synthetic Caucasus vessel corpus became its own project on **2026-09-03**:
**`../../CSC/`** (`zeejaytan/CSC`). It is training data for TORA *and* GARF, so keeping
it here made every result from it read as a TORA property — the confound the workspace
question `U3` exists to remove.

Moved: **O3** (generated interiors) → `CSC/intent/C1`, **O4** (hollow-shell fracture) →
`CSC/intent/C2`, **O5** (reachable shapes) → `CSC/intent/C3`. Those numbers stay retired.

**Three questions here still gate that project**, because they are about the network and
its scoring rather than about the corpus: **O1** (can the network resolve a pot wall),
**O2** (a valid way to score), **O7** (wear grounding). Answering them unblocks CSC.

`wear_ops.py` and `sdf_offset.py` stay in `scripts/` — TORA's own experiments are built
on them. CSC copies one in when a gate needs it.

## Plans this folder sits above

`WEAR_V3_PLAN.md` · `EXTERNAL_DATA_PLAN.md` · `JUGLET_TORA_TEST_PLAN.md`
(the corpus plan left with the project: `../../CSC/docs/notes/PLAN.md`)
