# 05: Agent tidies GARF's Juglet near-misses

**What to build:** start the agent from GARF attempts that seat 6-8 of 9 sherds (rough/worn
adapters, GARF rough-worn-dose), paper's GARF -> agent order; count sherds gained and lost.

**Answers:** U16

**Blocked by:** 04 (only if the whole-Juglet runs show the agent can handle 9 sherds at all)

**Status:** results-in

## Comments

2026-10-13: not run yet. Ticket 04 found the agent cannot seat a body sherd from scratch (0 of 9 body-pair runs), and correcting GARF's near-misses needs exactly that. Waiting on the conservator: run it anyway, or close it.

2026-10-13: closed by the conservator ("no, close it"). Not run.

2026-10-13: reopened by the conservator ("for completion sake, do the agent-correct garf-test as well"). Built as the paper's GARF -> agent order (App. D: GARF's poses on the original meshes, the original no-reference prompt, no history). `scripts/agent_assembly/prep_from_garf.py` takes GARF's saved Juglet attempts from ticket 02's rough 1x and worn 4x runs (jobs 31835635-36, 400 attempts), scores each on the solid cloud with `own_place.score_draw`, and keeps the attempt with the most sherds right way round at 8, 7 and 6 of 9 own place (`garf_a`, `garf_b`, `garf_c`). The frame fit from GARF's normalised cloud to the conservator's reassembly is printed in mm and refused above 0.5 mm. Each untouched scene is scored as GARF's own baseline (`runs_garf_base`), which must equal the count it was picked on. Three agent attempts per scene, scored by `score_tasks.py`; read as sherds gained and lost against that baseline. `score_tasks.py` right way round now also requires a turn under 90 degrees, as own_place has since 2026-10-12; no earlier run here changes (the one right-way-round pair was turned 18 degrees).

2026-10-13, result (Spartan job 32892267, TORA a2dc564; `agentasm_garf_table.txt`, baselines `agentasm_garfbase_table.txt`): **no sherd gained in 9 runs; one run lost ground.** Right way round, by the anchor fit, against GARF's own attempt:

| scene (GARF) | r1 | r2 | r3 | what the agent moved |
|---|---|---|---|---|
| garf_a (7/9) | 7 | 7 | 7 | d and q every time: GARF's two wrong sherds |
| garf_b (7/9) | 7 | 7 | 7 | o only: one of GARF's two wrong sherds |
| garf_c (6/9) | 6 | 6 | 1 (5 by best fit) | t (r1), t+p+h+y (r2), whole body shifted ~6 mm off the neck (r3) |

The agent found the misplaced sherds reliably (in a, b and c the sherds it moved were GARF's wrong ones, never a right one on its own), but never turned one the right way round: d stayed flipped (156-175 deg), q went from 64 deg to 45-168 deg. The paper's ruler scores garf_a r3 as a full success (all 9 under chamfer 0.01): q is 45 deg out and d upside down, both counted correct. That is the same leniency ticket 04 found, not a solved pot. Pictures checked (`agentasm_garf_garf_a_r3_look.png`, `..._c_r3_look.png`). Weight: one pot, three GARF attempts, three agent runs each, one model.
