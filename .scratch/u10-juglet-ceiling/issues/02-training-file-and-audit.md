# 02: Training file and its audit, on the pre-check vessels

**What to build:** A writer that turns CSC's broken vessels into TORA's training-file
layout, and an audit that reads only the finished file. The audit fails a bad file and
names the reason. Both are proven on the two pre-check vessels from CSC ticket 02, and
on small, deliberately broken files.

Spec: the umbrella `.scratch/u10-juglet-ceiling/spec.md`, modules 5 and 6.

**Answers:** U10

**Blocked by:** CSC `u10-juglet-ceiling` 02 (the pre-check breakages).

**Status:** ready-for-agent

**Needs-eye:** the audit renders.

- [ ] The writer uses the layout TORA's existing training files use. Units match the
      Juglet's file, and the split is by vessel (training / choosing). There is no wear
      and there are no dropped pieces.
- [ ] Per breakage it stores:
      - the recipe id;
      - the sherd count;
      - the share of break-face vertices identical to a neighbour's.
- [ ] The anchor setting is stated, and chosen to match how the untouched model was
      trained, with the reason given.
- [ ] The audit fails, naming the reason, if:
      - any breakage falls outside 6–15 sherds;
      - any sherd is open or in more than one body;
      - any wall falls outside 1.6–2.5 mm;
      - any recipe value falls outside the frozen ranges, or the hash differs;
      - any vessel appears in both splits;
      - the arms' training counts differ;
      - the size label TORA will see falls outside the Juglet's.

      It reports the identical-face share without failing on it: every join is a perfect
      fit by design (spec, "Every join is a perfect fit").
- [ ] Fixtures: a 3-sherd breakage, a solid sherd, a 1.2 mm wall, a vessel in both
      splits, an out-of-range recipe, and unequal arm counts. Each one fails and names
      why. The pre-check file passes.
- [ ] TORA's own loader reads the pre-check file. One loaded sample is rendered with its
      sherds as the network will see them.
- [ ] Audit renders:
      - the outline beside the reassembly;
      - a 0.5 mm section of a sampled breakage, including the thinnest wall and a handle
        break.
- [ ] Written back: U10 gets a line saying the audit exists and the pre-checks pass, with
      the date.
