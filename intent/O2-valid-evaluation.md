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

## Done when

- [ ] At least one evaluation route that is **not the Juglet** is agreed and written down,
- [ ] with its limits stated in the same place (what it can and cannot measure),
- [ ] and validated on a **known-answer case** before any conclusion is drawn from it.

That last line is not optional. A metric that cannot distinguish a good model from a
bad one will happily report a stable, publishable-looking constant.

## Source

`../../CSC/docs/notes/PLAN.md` §R4, `EXTERNAL_DATA_PLAN.md` §4.
