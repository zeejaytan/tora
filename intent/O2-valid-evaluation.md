# O2 — Is there any valid way to score this work?

**Status:** open · **Blocked by:** none · **Blocks:** O6, and every corpus stage

## Why it matters

**There is currently no valid instrument.** The Juglet is one object and its reference
answer was wrong — it is the scattered scan/table layout, not an assembled vessel.
Until this closes, nothing built here can be shown to help or hurt, and any number
produced is unattributable to method, ruler or reference.

This is the failure mode that has already cost the most in this project: four probes
and two GPU training runs spent on a broken absolute-distance threshold.

## The two candidate routes

**RePAIR** (Zenodo 15800029, the 3 GB open-discovery subset) — about 1,000 real
fragments with archaeologist ground truth. The caveats are real and must be stated
wherever it is used: frescoes are **flat**, have **no vessel curvature**, and are
reassembled largely from the **painting**. It measures *worn fracture surfaces*, not
pottery reassembly.

**Real Rabati sherds**, scanned and physically reassembled by a conservator — the
honest instrument for this material, and the reason the fragment archive comes first.

## What the instrument is now known to do, 2026-09-07 (job 30185814)

**The ruler has a third axis nobody was watching: the size the model is *told* the pot
is.** `scales` is fed into the flow model at every step of the reconstruction, and every
run was being judged against a band derived on paper rather than measured. It is now
measured: **0.375 – 0.811**, from 400 objects of the corpus the baseline was trained on.

Two consequences for this question:

- **Every real pot we own is scored in the extreme bottom of that band, and two are
  below it.** `plate` 0.321 and `coxae` 0.332 sit under everything training showed;
  `vert9`, `galli_pot`, `limb3`, `blue_pot` (0.380–0.410) sit in its lowest 0.2–4.3%.
  So an absolute score on real material is measured on a handicapped model, and any
  route agreed under this question must state its `scales` alongside its numbers.
- **Paired comparisons are safe; absolute levels are not.** The wear sweep holds `scales`
  fixed to within 2% across the intervention, so its 0.843 → 0.645 fall stands. A
  bare "TORA seats 0.843 of real sherds" does not, and should not be quoted without the
  conditioning value beside it.

The earlier "normalised" route made this worse rather than better: `juglet_norm` was
rescaled about an origin the pot sits 0.48 away from, handing the model **0.041** —
eleven times below the floor. `juglet_gt` fixed it. `docs/notes/SCALE_CONDITIONING_MEASURED.md`,
ticket `.scratch/eval-readout/issues/04-what-does-the-scales-input-actually-mean.md`.

## Done when

- [ ] At least one evaluation route that is **not the Juglet** is agreed and written down,
- [ ] with its limits stated in the same place (what it can and cannot measure),
- [ ] and validated on a **known-answer case** before any conclusion is drawn from it.
- [ ] and reported with the model's size input (`scales`) beside every score, against
      the measured band 0.375–0.811

That last line is not optional. A metric that cannot distinguish a good model from a
bad one will happily report a stable, publishable-looking constant.

## Source

`../../CSC/docs/notes/PLAN.md` §R4, `EXTERNAL_DATA_PLAN.md` §4.
