# 04: Label GARF's Fractura attempts as right way round or not

**What to build:** for every pot in GARF's existing Fractura evaluation runs on Spartan,
how many attempts are genuine full reassemblies (every sherd in its own place and the
right way round), and which pots qualify for ranking. CPU only; no new GPU run.

**Answers:** U17

**Blocked by:** None (can start immediately)

**Status:** resolved

- [x] Confirm which pots the Fractura file holds: 8, not 3 — blue_pot, galli_pot, narrow_bottle1–4,
      pink_bowl, plate (one clouds npz per pot per run)
- [x] `own_place.py` (with `oriented`) run over every GARF `rwlora_eval_*_fractura_fresh_*`
      run as a Spartan CPU batch job; polled; sacct State/ExitCode recorded here
- [x] Per pot and training variant: attempts, own place, full reassembly
- [x] Pots qualify where the right answer is rare but present; pots where all or none are
      right are set aside with the count stated

## Result (2026-10-02)

Job **32111374** (`scripts/hpc/label_u17_fractura.slurm`, `scripts/label_attempts.py`):
sacct **COMPLETED 0:0**, 35 s. 70 runs (the Juglet's 7 variants × ds1..10), 11,200 attempts.
Labels: `TORA/rank_u17/fractura_labels_32111374.json` (copy in `artifacts/rank_u17/`).

| pot | sherds | attempts | near-miss | genuine | random top 5 | verdict |
|---|---|---|---|---|---|---|
| blue_pot | 5 | 1400 | 16 | 1377 | 100% | set aside: right too often |
| galli_pot | 10 | 1400 | 257 | 305 | 70.8% | set aside: right too often (22%) |
| narrow_bottle1 | 12 | 1400 | 0 | 0 | 0% | set aside: none right |
| narrow_bottle2 | 3 | 1400 | 0 | 1400 | 100% | set aside: right too often |
| **narrow_bottle3** | **4** | 1400 | 21 | **39** | 13.2% | **qualifies** |
| narrow_bottle4 | 4 | 1400 | 0 | 1394 | 100% | set aside: right too often |
| pink_bowl | 3 | 1400 | 271 | 1128 | 100% | set aside: right too often |
| plate | 6 | 1400 | 446 | 741 | 97.7% | set aside: right too often |

narrow_bottle3 by variant (attempts / near-miss / genuine): fresh 200/0/3, fresh_s7 200/0/3,
noise_d100 200/7/10, noise_d100_s7 200/6/8, untouched 200/0/0, worn_d400 200/5/6,
worn_d400_s7 200/3/9.

**Reading.** One qualifying pot, and a small one (4 sherds): a weak second test. A 4-sherd
pot gives Layer 2 few joins to judge, and random top 5 already finds a genuine attempt 13% of
the time. galli_pot (10 sherds, 22% genuine) misses RARE = 0.10 but is the richest pot in
near-misses (257); ticket 05 should decide, before ranking, whether to rank it as a
"right often" side case — a decision, not a re-threshold after seeing scores.
