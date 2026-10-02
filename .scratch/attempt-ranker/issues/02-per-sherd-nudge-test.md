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
