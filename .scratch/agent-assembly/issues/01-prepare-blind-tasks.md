# 01: Prepare blind Juglet tasks on Spartan

**What to build:** `scripts/agent_assembly/prep_tasks.py` scrambles the Juglet sherds into
pair and whole-pot tasks the way AssemblyWorld does; public meshes go to the cloud thread,
the answer stays on Spartan.

**Answers:** U16

**Blocked by:** None (can start immediately)

**Status:** in-progress
**Working in:** project thread "general agent paper, fracture part" (2026-10-12)

- [x] Checked on a made-up three-piece pot (cloud): perfect poses score 3/3, unmoved 1/3
- [ ] Run on `TORA/dataset/juglet_gt.hdf5`; touching pairs listed with contact area
- [ ] Public task folders copied to project files `agent-assembly/tasks_v1/`
