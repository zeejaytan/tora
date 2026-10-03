# 02: Per-sherd nudge test (Layer 2) on the Juglet

**What to build:** each attempt that passes Layer 1 ordered by whether every sherd's joins
can be made to agree with a small nudge, with the least-sure sherd named. Delivers the
Juglet's real top-5 result and the near-miss table. See `../spec.md` (glossary: *nudge*).

**Answers:** U17

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] Neighbours found from the attempt itself (surfaces within 5 mm), never from the key
- [ ] Per sherd: the smallest rigid nudge (no point moved more than 5 mm, rotation at most
      20°) making break edges meet and wall direction and curvature carry on across the
      join; unfixable flag when no allowed nudge reaches the pre-registered agreement
      (1.5 mm, 15°)
- [ ] Cascade order: Layer 1 pass, then fewest unfixable sherds, then smallest largest
      nudge; least-sure sherd written per attempt
- [ ] Broken-on-purpose tests, stated in mm and degrees: a genuine attempt with one sherd
      spun 180° ranks below it; the same attempt with every sherd moved 1–3 mm apart or
      into slight overlap keeps its rank
- [ ] Near-miss table: the 2 genuine attempts against the 19 real own-place near-misses,
      and separately against 18 synthetic ones (each sherd of each genuine attempt spun
      180° in turn); attempt A (`garf_juglet_spun_t06`) must rank below B
      (`garf_juglet_genuine_t06`)
- [ ] Rank of each genuine attempt among 1,400 and top-5 hit, Layer 1 alone vs Layers 1+2
- [ ] Spartan job polled; sacct State/ExitCode recorded here

## Log

Groundwork, before the score is chosen (gaps in % of pot size, longest box side;
Juglet 1% = 0.65 mm). Scripts: `scripts/l2_measure.py`, `l2_truth.py`, `l2_summary.py`,
`l2_truth_render.py`.

- 32144323 `l2_measure_u17.slurm` — FAILED 1:0. Converter self-check used an absolute
  0.2 mm tolerance; blue_pot rebuild residual ~0.3 mm on a nominal 100 mm pot, all labels
  agreed. Tolerance made relative (`CHECK_PCT` 0.5% of pot).
- 32147567 `l2_measure_u17.slurm` — OUT_OF_MEMORY 0:125, but all 9 outputs complete
  (1,400 attempts each); 3 of 32 workers killed at init loading dense Fractura sherds.
  Next run: raise `--mem` or cut workers. Outputs: `artifacts/rank_u17/l2_32147567/`.
- Open: on Fractura the TRUE assembly reads a larger gap (1.0–1.9% of pot) than most
  GARF attempts after the nudge (0.56–0.78% on the easy pots); Juglet is the reverse
  (true 0.61%, attempts 1.48%). Debug render 32149018 to find out why before any cut-off.
- 32149018 `l2_truth_render.slurm` COMPLETED 0:0; 32149051 `l2_join_section.slurm`
  COMPLETED 0:0; 32149123 `l2_contact.slurm` COMPLETED 0:0. Renders in
  `artifacts/rank_u17/{look,cut,touch}_*/`.
- **Anomaly explained (two parts).** (1) Not like for like: attempts were measured after
  the nudge, the truth before. Truth after the same nudge: pink_bowl 0.54–0.74%,
  narrow_bottle4 0.54–1.04%, plate 0.66–1.58%, i.e. the same as the easy pots' attempts
  (0.56–0.78%). (2) Fractura ceramics are real, separately scanned fragments (GARF paper
  §2/A.1: Artec Spider; no simulated ceramics); their stored correct poses leave the
  mating faces ~1% of pot apart and slightly crossed (pink_bowl, narrow_bottle4 cuts), and
  the nudge moves the TRUE sherds 2–4% / 2–6°. The Juglet's faces coincide exactly (nudge
  moves the truth <1%, 0.1–1.7°). Consequence: a Layer 2 cut-off tuned on the Juglet
  (floor 0.6%) would fail correct joins between real scanned sherds; any cut-off must be
  set on real-scan data.
