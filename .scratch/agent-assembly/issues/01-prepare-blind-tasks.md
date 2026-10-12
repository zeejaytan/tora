# 01: Prepare blind Juglet tasks on Spartan

**What to build:** `scripts/agent_assembly/prep_tasks.py` scrambles the Juglet sherds into
pair and whole-pot tasks the way AssemblyWorld does; public meshes go to the cloud thread,
the answer stays on Spartan.

**Answers:** U16

**Blocked by:** None (can start immediately)

**Status:** resolved

- [x] Checked on a made-up three-piece pot (cloud): perfect poses score 3/3, unmoved 1/3
- [x] Run on `TORA/dataset/juglet_gt.hdf5`; touching pairs listed with contact area (job 32804650, COMPLETED 0:0): 20 touching pairs, most contact 4-6 (130 mm²), 5-6, 0-7, 3-6 -> the four pair tasks
- [x] Public tasks in project files `agent-assembly/agentasm_tasks_v1_public.tar.gz` (2.1 MB); secret/ stays on Spartan
