# 05: Three arms on the Juglet, the decision, and the write-back

**What to build:** The untouched model, the generic adapter and the ceiling adapter are
each run 20 times on the Juglet, and on the eight Fractura pots. Each is scored with the
own-place count. U10's stage-1 decision rule is applied straight from the scorer's output,
and the reading is written into U10.

Spec: the umbrella `.scratch/u10-juglet-ceiling/spec.md`, modules 8 and 9.

**Answers:** U10

**Blocked by:** 01 (the scorer), 04 (both adapters).

**Status:** ready-for-agent

**Needs-eye:** the per-arm Juglet renders. The pictures decide; the table ranks.

- [ ] Evaluation settings are the ones every earlier Juglet arm used, stated here.
- [ ] 20 Juglet draws per arm. For each arm the ticket reports:
      - the own-place median and spread;
      - the swap-allowed count beside it;
      - how far off the unseated sherds land (% of pot height).
- [ ] The decision rule is applied by the scorer on the **solid sherds**, with the raw
      output's reading reported beside it (conservator, 2026-09-14). If the two differ,
      the solid one stands, and the ticket says what the difference is. The reading is
      quoted verbatim:
      - the ceiling fails to beat generic by ≥1 sherd (median) → close U10 and skip
        stage 2;
      - the ceiling wins → stage 2;
      - generic helps as much as the ceiling → the gain came from the fine-tune (a C4
        answer).
- [ ] Fractura: each of the eight pots is scored per pot for every arm, never pooled.
      Any pot where an adapter loses a sherd or more (median) is named. A ceiling that
      loses there is recorded but does not change the reading.
- [ ] Renders: the Juglet's median and worst draws per arm, full vessel, in the pot's
      own frame.
- [ ] The ticket states the weight: one pot, 20 draws, one training run per arm, and the
      label "ceiling: shown the answer's shape". It also names which of the three
      failure types it found.
- [ ] Every `sbatch` has a laptop-side poll, and the final `sacct` State/ExitCode is
      recorded here.
- [ ] Written back:
      - U10's boxes are ticked or struck, with the date;
      - on a loss, `tora/intent/O8` and `GARF/intent/G1` record that the break edges are
        what is left;
      - if generic matches the ceiling, `CSC/intent/C4` gets a line;
      - the umbrella intent README's U10 row is updated.
