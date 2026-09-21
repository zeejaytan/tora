# 02: Training file and its audit

**What to build:** A writer that turns CSC's broken vessels into TORA's training-file
layout, and an audit that reads only the finished file. The audit fails a bad file and
names the reason. Both are proven on the two pre-check vessels from CSC ticket 02, and
on small, deliberately broken files.

*Amended 2026-09-21.* The pre-check vessels were only a stand-in while the corpus did
not exist. CSC ticket 04 has now built it, so the writer and the audit run on the real
corpus: both arms, 20 training and 5 choosing vessels each. The sherd rule is the one in
force since ticket 06, 3–64 and never exactly 9. The wall rule is judged per vessel (see
the box), because judged per sherd the thickness measure itself fails. Every vessel was
built at 1.6–2.5 mm, yet 432 of 9,715 kept sherds (4%) measure 1.44–4.21 mm. The
measure is twice the volume over the outer skin, and it is thrown off at a small sherd's
edges and by the solid handle and the rounded lip. Per vessel, the median sherd lands
within 0.07 mm of the wall the vessel was built with (1.62–2.44 mm).

Spec: the umbrella `.scratch/u10-juglet-ceiling/spec.md`, modules 5 and 6.

**Answers:** U10

**Blocked by:** CSC `u10-juglet-ceiling` 04 (the corpus), done 2026-09-21.

**Status:** done except the witnessed look at the audit renders (2026-09-21)

**Needs-eye:** the audit renders.

- [x] The writer uses the layout TORA's existing training files use. Units match the
      Juglet's file, and the split is by vessel (training / choosing). There is no wear
      and there are no dropped pieces.
- [x] Per breakage it stores:
      - the recipe id;
      - the sherd count;
      - the share of break-face vertices identical to a neighbour's.
- [x] The anchor setting is stated, and chosen to match how the untouched model was
      trained, with the reason given.
- [x] The audit fails, naming the reason, if:
      - any breakage falls outside 3–64 sherds, or has exactly 9;
      - any sherd is open or in more than one body;
      - any vessel's median sherd wall falls outside 1.6–2.5 mm, or any single sherd is
        more than 2.5 times its vessel's median (a solid lump; the corpus's thickest,
        a handle rod, is 2.0 times);
      - any recipe value falls outside the frozen ranges, or the hash differs;
      - any vessel appears in both splits;
      - the arms' training counts differ;
      - the size label TORA will see falls outside the Juglet's.

      It reports the identical-face share without failing on it: every join is a perfect
      fit by design (spec, "Every join is a perfect fit").
- [x] Fixtures: a 2-sherd breakage, a 9-sherd breakage, an open sherd, a two-body
      sherd, a solid sherd, a 1.2 mm wall, a vessel in both
      splits, an out-of-range recipe, and unequal arm counts. Each one fails and names
      why. The real corpus file passes.
- [x] TORA's own loader reads the file and admits every breakage in it (none silently
      dropped by its part-count limits). One loaded sample is rendered with its
      sherds as the network will see them.
- [ ] Audit renders:
      - the outline beside the reassembly;
      - a 0.5 mm section of a sampled breakage, including the thinnest wall and a handle
        break.
- [x] Written back: U10 gets a line saying the audit exists and the corpus passes, with
      the date.

## Result (2026-09-21)

**Jobs.** 30919195 (the full run) ended **FAILED 1:0**. Writer, audit, fixtures and loader
all passed; the render step crashed because the thickest-walled vessel is a choosing
vessel and the render only indexed training ones (fixed in tora `0935405`). The renders
were then rerun alone as **30921251, COMPLETED 0:0**. Outputs are in
`TORA/work/u10_trainset_30919195/` on Spartan, and the files are `TORA/dataset/u10_ceiling.hdf5`
and `u10_generic.hdf5` (1.2 GB each). Small copies are in `tora/artifacts/u10_02/`.

**The corpus is the one the conservator was shown.** CSC's `assemble_u10_corpus.py`
rebuilt `corpus.json` on Spartan. Its sha256 differs from the laptop copy (7195223c… vs
d10dac4b…), but a structural diff finds the content identical. The difference is line
endings only.

**Writer.** Ceiling: 349 training + 103 choosing breakages. Generic: 349 + 84. That is
885 breakages and 8,547 sherds in all. Training maps to TORA's `train`, choosing to `val`,
and `test` is left empty (the Juglet is its own file). Each breakage is centred and scaled
so its farthest point sits at 0.5 (the Juglet's file uses the same convention). Each one
stores `vessel`, `arm`, `role`, `form`, the full recipe, `sherds`, `mm_per_unit` (so a
wall can be read back in millimetres) and `coincident_share`. There is no wear and no
dropped piece.

**Anchor: `anchor_free: false`, the largest sherd held in place.** This matches how the
untouched model's training data was set up (bbad_everyday) and how wear v3 was trained.
The Juglet's eval config (`juglet_gt.yaml`) uses `anchor_free: true`, but job 28228263
showed the anchor-mode difference on the Juglet is below the draw-to-draw noise. Training
needs its own data config with `max_parts: 64` (the Juglet's config says 20, which would
silently drop every breakage above 20 sherds), `anchor_free: false` and `up_axis: z`.

**Audit: PASS, 0 failures**, reading only the two finished files and the Juglet's.
- Every breakage has 3–36 sherds and none has exactly 9. Every sherd is closed and in one
  body.
- Wall per vessel: across 50 vessels the median sherd reads 1.62 mm (ceiling_train_16)
  to 2.44 mm (ceiling_choose_04). Each is within 0.07 mm of the wall it was built with.
  Single sherds range 1.45–4.21 mm (99% under 3.12 mm). The largest ratio to its vessel's
  median is 2.06, on ceiling_train_15's 3.62 mm handle rod; the lump limit is 2.5.
- Recipes are inside the frozen ranges and the hash is 422081368edc…f424. No vessel is in
  both splits, and both arms train on 349.
- Size label: after TORA's own centring, the farthest point sits at 0.462–0.526, against
  the Juglet's 0.510 (0.91–1.03×).
- Reported, not failed on: the share of break-face vertices identical to a neighbour's is
  1.0 everywhere (min and median). Every join is a perfect fit, by design. The median
  sherd's break faces are 19% of its surface.

**Fixtures** (`scripts/test_u10_audit.py`). The clean mini pair passes. Each of the 11
broken copies fails with its named reason: 2 sherds, 9 sherds, open, two bodies, a solid
ball of the sherd's width, a 1.2 mm wall, in both splits, a 2.8 mm recipe wall, an
edited hash, unequal arms, and a halved size. Output: "ALL FIXTURES BEHAVE".

**Loader** (`scripts/check_u10_loader.py`, TORA's `PointCloudDataset` with training
settings). All four splits were loaded in full, with nothing dropped (ceiling 3–30 / 3–36
sherds, generic 3–36 / 3–28). The sample size labels are 1.022× (ceiling) and 0.990×
(generic) the Juglet's 0.5108 through the same loader. `u10_look_loader.png`: the
assembled sample and the network's view (each sherd centred and turned, the largest held
in place) both look right.

**Audit renders** (`tora/artifacts/u10_02/`), looked at by the agent. **Still to be
witnessed by the conservator:**
- `u10_look_juglet.png`: a ceiling training breakage beside the Juglet, on the same axes.
  Same size and the same family of form.
- `u10_look_forms.png`: three ceiling vessels, plus one of each generic form (cup, bowl,
  jar, bottle). The cup is generic_spare_00, which stood in under the spare-swap rule.
- `u10_look_sections.png`: axis cuts through the thinnest-walled (1.6 mm) and
  thickest-walled (2.4 mm) vessels, in 7 mm windows with a 0.5 mm bar. Both walls are
  resolved, and the joins meet with no visible gap or overlap. The third panel is the sherd
  that reads thickest against its vessel. It is the solid handle rod, cut lengthwise:
  real clay, not a lump.

