# 03: Adapter gate with the pose head frozen

**What to build:** The adapter-training job checks that only the adapter's own weights
move, with the pose head frozen, and stops before any evaluation if anything else
changed. That keeps "adapter off" exactly equal to the untouched model. Wear v3's
"adapter off" arm was not the untouched model, because its head was trained.

Spec: the umbrella `.scratch/u10-juglet-ceiling/spec.md`, module 7.

**Answers:** U10

**Blocked by:** None (can start immediately). The smoke test uses an existing small
training file.

**Status:** in progress (2026-09-24): laptop pieces done, held node requested

- [x] The U10 training configuration sets the head frozen explicitly, not by default.
      The default is still to train it. (`scripts/hpc/u10_session.sh` passes
      `lora.train_head=false` on every U10 run; `config/train.yaml` still says true.)
- [ ] Before training, the existing freeze test and the reversibility check pass.
- [ ] A smoke train of a few steps, then a reload.
- [ ] The weight diff fails on any frozen change. It also enforces the stricter rule:
      every tensor outside the adapter is identical to the untouched model's.
- [ ] Proof that the gate catches a leak: a smoke run with the head deliberately left
      trainable must fail it.
- [ ] Inside the job, a failed gate stops everything after it.
- [ ] Every `sbatch` has a laptop-side poll, and the final `sacct` State/ExitCode is
      recorded here.
- [ ] Written back: U10's adapter-hygiene lines record that the gate works, with the
      date.

## How it runs on Spartan (amended 2026-09-24)

The conservator asked for no long queue waits, and a held allocation for the debugging at
the start. What the sizes are, measured rather than guessed:
- Wear v3's whole job took **1 h 14 min** on one A100 (job 29880370). That covers the
  smoke test, 20 passes over 1,169 examples with validation every pass, and 12
  evaluation runs.
- Each U10 arm trains on **349** examples, under a third as many.
- 20 Juglet draws took **under 5 min** (job 30130049).
- So no step here needs the 7-day `gpu-a100` partition. Everything fits
  `gpu-a100-short` (4 h wall, `docs/agents/slurm.md`).

**This ticket runs inside a held allocation, not through `sbatch`.** Every step is new
code meeting the GPU for the first time: the frozen-head config, the strict diff, the
deliberate leak, and ticket 04's own-place check on the choosing set. Each answer
decides the next command. Through `sbatch`, each one-line fix would cost a queue wait.

1. **Before asking for the node**, on the laptop:
   - write and push the U10 data config: `max_parts: 64`, `anchor_free: false`,
     `up_axis: z`, and `min_dataset_size` at or below 349 (see ticket 04);
   - write and push the training overrides, with `lora.train_head=false` explicit;
   - write and push the strict mode of `diff_adapter_checkpoint.py`;
   - write and push ticket 04's own-place validation hook;
   - smoke-test all of it on the login node on CPU with a tiny slice where the code
     allows. Then `git pull --ff-only` on Spartan.
2. `scripts/gpu_session.sh start 4` (default `gpu-a100-short`), launched in the
   background. The grant is the notice. Step 1 of the session is loaded before the
   request goes in.
3. Inside the session, back to back:
   - freeze test;
   - reversibility check;
   - smoke train (8 batches) on `u10_ceiling` with the head frozen, then reload through
     `sample.py`;
   - strict diff: pass;
   - the leak run (head trainable): strict diff must fail;
   - one full epoch of each arm, with the own-place score printed on its choosing set.
     That measures time per pass, and memory at 36 sherds × batch 8.
4. **If the session has time left**, ticket 04's two training runs go straight into it,
   one after the other, with no queue between them. Otherwise it is stopped
   (`gpu_session.sh stop`) as soon as step 3 is done. It must never sit idle.

The allocation's job ID and final `sacct` State/ExitCode are recorded here, like any
batch job's. The session job carries the `job_status.log` exit trap.

## Progress (2026-09-24)

**Step 1, laptop pieces: done**, tora `22647ed`, pulled on Spartan.
- `config/data/main/u10_ceiling.yaml` and `u10_generic.yaml`: 64 sherds max, largest
  sherd held, pots stand on z, `min_dataset_size: 0` (no repetition, so one pass is one
  pass over the 349). Hydra composes them with every U10 override (`--cfg job` on the
  login node).
- `diff_adapter_checkpoint.py --strict`: fails if anything outside the adapter differs at
  all, if a base tensor is missing, or if a new non-adapter tensor appears.
- The choosing score in `validation_step`, switched on by `model.extra_metrics=[own_place]`:
  the share of sherds in their own place per breakage, on the solid sherds
  (`val/overall/own_place_solid`, what the checkpoint is chosen on) and raw beside it.
  It calls `scripts/own_place.py`'s own scorer, so choosing and judging use one ruler.
- `scripts/hpc/u10_session.sh`: one call per step (freeze, gate, smoke, leak, epoch,
  train). Each step writes its own `job_status.log` line; the holder's sleep job does not
  carry the trap, the steps do.
- CPU check on the login node, synthetic sherds: a breakage with two sherds swapped reads
  2 of 4 in their own place on both clouds. The strict gate passes a clean adapter
  and fails a moved pose head, which `--fail-on-frozen` passes (exit 0). That is the gap
  the strict mode closes.

**Holder.** The first request (31200575) was moved by Spartan's submit filter to the long
`gpu-a100` queue: `gpu-a100-short` accepts at most 8 CPUs. It was cancelled before
starting. `gpu_session.sh` now defaults to 8 CPUs / 64G and refuses more on the short
partition (umbrella `a64a166`). Re-requested as **31200602** on `gpu-a100-short`, estimated
start 16:20.
