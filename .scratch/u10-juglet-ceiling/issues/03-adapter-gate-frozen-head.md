# 03: Adapter gate with the pose head frozen

**What to build:** The adapter-training job checks that only the adapter's own weights
move, with the pose head frozen, and stops before any evaluation if anything else
changed. That keeps "adapter off" exactly equal to the untouched model. Wear v3's
"adapter off" arm was not the untouched model, because its head was trained.

Spec: the umbrella `.scratch/u10-juglet-ceiling/spec.md`, module 7.

**Answers:** U10

**Blocked by:** None (can start immediately). The smoke test uses an existing small
training file.

**Status:** ready-for-agent

- [ ] The U10 training configuration sets the head frozen explicitly, not by default.
      The default is still to train it.
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
