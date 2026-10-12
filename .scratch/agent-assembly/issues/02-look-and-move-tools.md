# 02: Rebuild the AssemblyWorld look-and-move tools

**What to build:** `scripts/agent_assembly/aw_env.py`, a command-line copy of the paper's
Table A-2 tools (render, camera, translate, rotate, set pose, groups), logging every call.

**Answers:** U16

**Blocked by:** None (can start immediately)

**Status:** in-progress
**Working in:** project thread "general agent paper, fracture part" (2026-10-12)

- [x] Renders 1024x768 at 38 deg in the cloud container (pyrender + OSMesa), ~2 s a view
- [ ] Pilot agent run completes and writes final.json
