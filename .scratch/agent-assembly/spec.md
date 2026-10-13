# Agent assembly: does a general AI agent reassemble our sherds by looking?

Requested by the conservator, 2026-10-12 (project thread "general agent paper, fracture part").

**Prior work searched:** NOT searched before this spec was written (2026-10-12); the spec said
"code not released" from the PDF alone, and the environment was rebuilt. Searched 2026-10-13
after the conservator found it: GitHub "AssemblyWorld" -> https://github.com/AssemblyWorld/assembly-world-bench
(commit 22646c9, released 2026-10-02: harness, scorer, Claude Code runner); Hugging Face
AssemblyWorld/AssemblyWorldBench (episodes and answer clouds, commit f351f0f) and
AssemblyWorld/AssemblyWorldBench-Results (gated); project page https://assemblyworld.github.io/.
This miss is why check 8 of `scripts/check_intent_links.py` exists.

## What the paper claims (AssemblyWorld, arXiv 2609.40353v1; pr-papers `text/assemblyworld-2609.40353v1.md`)

An off-the-shelf agent (GPT-6 Astra via Codex; Claude Fable/Opus/Sonnet via Claude Code), with no
reassembly training, sees only rendered views and moves parts with tool calls.

1. **Two-fragment Fantastic Breaks**: 91.67% part accuracy on 150 objects (§4.3, Table 5), 90% success
   on the 20-object benchmark for Astra and Fable (§4.2). The anchor counts, so the floor is 50%:
   the second fragment is seated on about 83% of objects.
2. **GARF then agent** beats either alone: 83.67% -> 93.00% PA (Table 6, App. D).
3. Their own limits: two-fragment objects only; one run per object; no collision check;
   success varies by layout (App. E: 02/02007 and 18/18002 flip with a new scramble).

## What we test, on the Juglet (9 real sherds, the conservator's reassembly `juglet_gt`)

| task | why | paper's setting? |
|---|---|---|
| `pair_i_j` (4 touching pairs, most contact first) | claim 1 on real, worn pottery | yes, same task |
| `whole` (9 sherds, no picture) | does it scale past two pieces | no, never tried |
| GARF near-miss then agent (ticket 05) | claim 2 on our material | yes, order GARF -> agent |

Each task: one scramble (paper's App. A.1 initialisation, seed 0), **3 agent runs**, 60-minute
limit, the paper's task text verbatim. Agent: Claude (Opus) through Claude Code subagents in the
cloud thread, because each look-and-move step must return in seconds. The answer key never
leaves Spartan; Spartan prepares the tasks and scores.

## Rulers (both reported, never mixed)

- Ours: own place / right way round at 4.6 mm (7.07% of the 65 mm pot), turn in degrees,
  offset in mm; anchor-aligned and best-fit-aligned.
- Paper's: squared two-way chamfer <= 0.01 with the largest part's PCA-box diagonal = 1.

## Deviations from the paper, stated

- Environment rebuilt from Table A-2: `scripts/agent_assembly/aw_env.py`. ("Code not released" was written here unsearched; it had been released on 2026-10-02, see above. Calibrated against it 2026-10-13: 6 of 6 of their Fantastic Breaks objects solved in this rebuild, scored by their code.)
- A part's position is its centre; renders carry a colour legend and a world-axes triad.
- Sherds lightened to ~30k faces each for rendering; scoring uses the full meshes.
- The agent is a Claude Code subagent in a cloud container, not their harness build.
