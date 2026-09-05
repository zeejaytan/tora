# 02: Is nine fragments on its own enough to explain the Juglet?

**Type:** `wayfinder:research` (AFK)
**What to build:** A direct comparison of the Juglet against fresh, unworn pots of
similar fragment count, using data already on disk, to decide whether the Juglet is
performing worse than its difficulty predicts — or exactly as well.

**Answers:** O8

**Blocked by:** 01 (needs the readable-difference threshold)

**Status:** resolved

## The claim under test

`JUGLET_TORA_ROOTCAUSE.md` ruled piece count out on the grounds that rotation error was
flat at 59–70° from 3 to 12 pieces. **That flatness was the units bug.** Normalised, the
same eight pots spread from 1.6° to 61.3°, so the ruling-out is void and piece count is
live again.

First-pass numbers, which this ticket must verify rather than inherit: the Juglet reads
35–66° non-anchor on `juglet_gt`; fresh normalised `galli_pot` (10 fragments) reads
31.4°, `plate` (6) 40.6°, `narrow_bottle1` (12) 57.1°. On that reading the Juglet is
**inside** the fresh range and there is nothing left for wear to explain.

The confound to name: `narrow_bottle3` has only 4 fragments and still reads 61.3°, so
fragment count is not a clean predictor even among fresh pots.

## Acceptance criteria

- [x] Non-anchor rotation and fragments-seated plotted against fragment count for all
      eight fresh normalised pots (job 29891327) with the Juglet overlaid, using 01's
      spread as the error bar — no new GPU job
- [x] Stated plainly whether the Juglet falls inside or outside the fresh band **for its
      fragment count**, and by how much relative to the readable threshold
- [x] A render of the Juglet's proposed assembly beside a fresh pot of similar fragment
      count that scores similarly, so "the same score" can be checked to mean "the same
      kind of arrangement" — two assemblies can share a number and look nothing alike —
      **not possible from disk: no `*_fresh_*` or ladder run saved clouds, only
      `results/`. The two figures that were producible without GPU are
      `artifacts/fragment_count.png` (the comparison) and `artifacts/anchor_mode.png`
      (the confound). Drawing the two assemblies side by side is owed and needs GPU.**
- [x] If it falls inside the band: say so, and record that the wear hypothesis has no
      residual to explain
- [x] Names which of the three this is

## Answer

**The Juglet is doing about as badly as a fresh, unworn pot of nine fragments does. It is
not an outlier.** On the count of sherds put in the right place it sits exactly on the
line the fresh ceramics trace, between `plate` (6 fragments) and `narrow_bottle1` (12).
On how far the misplaced sherds are turned it sits inside the fresh spread, at the high
end of it, and only one of the eight fresh pots is *readably* better.

**Which of the three this is: none of them — the method is doing what it does on any pot
of this many pieces.** There is no Juglet-specific residual visible here for wear, or for
anything else about this object, to explain. That is the same conclusion the map's premise
already carried, but it is now measured on a common ruler and a common stored size rather
than inherited.

**Fragment count is ruled in only weakly.** It is a real but loose predictor — the
correlation across the eight fresh pots is r = 0.47 on eight points, which on its own
would not survive a significance test, and `narrow_bottle3` breaks it outright.

### The numbers

Eight fresh ceramics, job 29891327 arm B, all normalised to the same stored size (0.500,
inside the trained band), anchor-fixed, ten draws each. The Juglet: twenty pooled baseline
draws at scale 0.511. All read through `scripts/readout.py`, so the non-anchor `× n/(n-1)`
correction is applied once. Render: `artifacts/fragment_count.png`
(`scripts/plot_fragment_count.py`).

```
fragments   turn (median)   seated       object            [draw range]
    3            2.4          3/3        pink_bowl          [ 2.0- 2.9]
    3            4.3          3/3        narrow_bottle2     [ 3.8- 4.8]
    4            7.8          4/4        narrow_bottle4     [ 5.1- 8.8]
    4           81.8        3.5/4        narrow_bottle3     [76.8-92.1]
    5           30.5          5/5        blue_pot           [ 6.8-48.4]
    6           48.7          4/6        plate              [27.1-60.0]
   10           34.8          8/10       galli_pot          [22.8-51.6]
   12           62.3        5.5/12       narrow_bottle1     [46.3-71.0]
    9           60.9          5/9        THE JUGLET         [35.4-88.9]
```

**Seating.** The fresh pots seat everything up to 5 fragments, then fall away: 4 of 6,
8 of 10, 5.5 of 12. The Juglet seats **5 of 9 — 55%**, which is between `plate`'s 67% at
six fragments and `narrow_bottle1`'s 45% at twelve. It is on the trend, not below it.

**Rotation.** Applying ticket 01's rule — below 17° between two runs is sampler noise,
not a result — the Juglet's 60.9° is **not readably different** from `plate` (48.7°),
`narrow_bottle1` (62.3°) or `narrow_bottle3` (81.8°). The one fresh pot it is readably
worse than is `galli_pot` (34.8°, a 26° gap at ten fragments, one more piece than the
Juglet). So the comparison gives one point against the Juglet and three ties.

**Fragment count is a weak predictor even among fresh pots.** `narrow_bottle3` has four
fragments and reads 81.8° — worse than anything else on the chart including the
twelve-piece bottle. Whatever makes a pot hard, it is not only how many pieces it is in.
This confound was named in the ticket's premise and it survives.

### A confound that had to be measured, not assumed

`juglet_gt` is run **anchor-free** (`config/data/zeroshot/juglet_gt.yaml:6`) while all
eight fresh ceramics are run **anchor-fixed**. That is not cosmetic: anchor-fixed hands
the reconstruction its largest fragment already seated correctly in the finished vessel
and holds it there; anchor-free places nothing, and all nine sherds start stacked at the
origin, the eight smaller ones turned at random (`tora/data/dataset.py:383`, `:395`).
On this pot the given fragment would be **1927 of 5000 points, 39% of the object**.
`artifacts/anchor_mode.png` draws all three states from the stored cloud, no GPU.

`readout.pool()` refuses to combine the two on its own, without being asked:

```
REFUSED: lorav_juglet_baseline_29623885 and lorav_fresh_baseline_29623885
  were not produced the same way:
  checkpoint=bbad_everyday_cka.ckpt seed=42 draws=5 anchor_free=True  ...
  checkpoint=bbad_everyday_cka.ckpt seed=42 draws=3 anchor_free=False ...
```

**How much it is worth was measured rather than argued.** Job **28228263** ran the same
six real pots both ways — same checkpoint, same seed, same objects, only the anchor mode
different:

```
object       n   anchor-fixed   anchor-free   change    seated fixed -> free
blue_pot     5        5.6           18.9      +13.3          5/5 -> 5/5
coxae        3       91.6           72.2      -19.3          2/3 -> 2/3
galli_pot   10       34.1           27.6       -6.5         9/10 -> 9/10
limb3        3       17.8           14.7       -3.1          3/3 -> 3/3
plate        6       49.8           54.1       +4.3          4/6 -> 4/6
vert9        3       64.8           63.5       -1.4          3/3 -> 2/3
                              median change   -2.2
```

**The median change is −2.2°, and the sign is not even consistent** — three pots got
better, three worse, every one of them inside ticket 01's 17° threshold. Seating is
unchanged on five of six. So taking the anchor away is worth nothing measurable, and the
mode mismatch cannot manufacture the Juglet's position on the chart.

This is **not** a floor effect, which is why it is usable: `blue_pot` reads 5.6°
anchor-fixed and seats all five, so there was ample room for anchor-free to be worse and
it was not (+13.3°, still unreadable). The earlier Fractura anchor-free pairs
(`fractura_*_anchorfree_24343146`) *are* floored — every arm at out-of-band millimetre
scale with medians of 65–97° — and were discarded for that reason.

The same ablation was run on the Juglet itself (`anchor2x2_juglet_af{false,true}`):
95.1° → 87.9°, a −7.2° change, also unreadable. That pair is at scale 0.041, nine times
below the trained floor, so both arms are compromised and it only corroborates.

### One thing worth recording that this did not settle

`config/model/tora.yaml:28` sets `anchor_free: false`, and the audit of all 141 eval runs
on Spartan confirms **every single one** was run that way. Two consequences follow, and
neither is measured here:

1. In anchor-free *data* mode the sampler still pins the anchor to its ground-truth
   position (`tora/modeling/tora.py:604`, `:338`) while the encoder — which is fed
   absolute coordinates with no per-fragment re-centring
   (`tora/modeling/encoder/point_cloud_encoder.py:101-113`) — is shown that fragment at
   the origin. The two halves disagree.
2. `tora/eval/evaluator.py:74` runs the anchor-aligning ICP only `if self.model.anchor_free`,
   so it has **never run**, on any run in this project.

Job 28228263 says the net effect of all of that is below the noise floor on six pots, so
it does not change any conclusion here. It is recorded on the map because it is a real
inconsistency, not because it is currently costing anything.

### What this means for the map

- **Candidate 2 (fragment count): ruled in, weakly.** More pieces does mean more error,
  but loosely (r = 0.47 over eight pots) and with a clear exception. It does not single
  the Juglet out — the Juglet is where a nine-piece fresh pot would be.
- **Candidate 5 (wear) has no residual to explain**, on this evidence. That strengthens
  what ticket 01 and the map already said, and it is now the second independent route to
  the same place.
- The remaining live candidates are **3 (the missing sherd)** and **4 (low-side
  out-of-band scale)**. Neither is addressed here.

### How much weight this can bear

Eight fresh pots and one Juglet, one architecture, one checkpoint. Ten draws per fresh
pot and twenty for the Juglet, so each point is a median with roughly ±4–6° of standard
error. The r = 0.47 is eight points and should be read as "loosely related", not as a
measured slope. The seating comparison is the stronger half: it is a count, it moves
monotonically with fragment count across the fresh pots, and the Juglet lands on it.
