# O8 — What actually stops TORA reassembling the Juglet?

**Status:** open · **Blocked by:** none · **Supersedes the diagnosis half of** [O6](O6-juglet-under-valid-reference.md)

## Why it matters

Two things changed the ground under the Juglet, and the old diagnosis has not been
re-derived since either of them.

1. **A correct reference now exists.** `juglet_gt.hdf5`, hand-reassembled by the
   conservator 2026-08-10, fitted rigidly to the source fragments with a residual of
   0.0000% of the object. The rotations needed to correct the old scan-table layout ran
   **26° to 177°** — that is how wrong the previous answer key was.
2. **Both units bugs are fixed.** The scoring threshold, and then the object's stored
   size being fed to the network as a conditioning input it had never seen out of band.

`docs/notes/JUGLET_TORA_ROOTCAUSE.md` diagnosed the Juglet as a synthetic-to-real
domain gap compounded by piece count. **Two of its three load-bearing findings were
computed on the corrupted run** and are dead: the four fresh control ceramics it said
TORA scored at chance on now seat every fragment, and the flat 3-to-12-piece curve it
used to rule out piece count *was* the units bug.

So the failure is real — the render shows no vessel — but its cause is unattributed,
and the obvious next move (train on worn fracture) rests on a premise the data does not
currently support.

## What the premise runs into

**The Juglet's rotation error sits inside the fresh-break range.** On `juglet_gt`, at
scale 0.511 — inside the trained band, so unaffected by either bug — baseline runs read
**35–66°** non-anchor. Fresh, unworn, normalised pots span **1.6° to 61.3°**
(`narrow_bottle3` has 4 fragments and reads 61°). There is no wear-shaped gap left over.

**And the wear cannot be measured in this scan.** Break faces are sampled at 0.243% of
object size; the blunting acts at 0.3–0.5%. The dimensionless roughness ratio was tried
and withdrawn: the worn Juglet reads 0.169, fresh `blue_pot` reads 0.167. Between-pot
variation swamps the effect (`WEAR_TEST_RESULTS.md` §2, `GATE_A_RESULT.md`).

**Wear training has already been run twice.** Jobs 29027773 and 29308186: rotation
51.5° → 49.2° → 52.9°. The "recall@10° flat at 0.000" once quoted alongside those is not
evidence: that field is a per-object 0/1 on the whole-pot mean, not a fraction of
fragments, so on a nine-sherd pot averaging 35–60° a flat zero is what the metric must
produce whatever the model does.

**The read-out is now one instrument.** `scripts/readout.py` (gated by
`scripts/check_readout.py`) is the single place a run is read: it undoes the free-anchor
dilution once, reports seating as a count with its floor, refuses to pool runs made
differently, and flags a run whose stored size fell outside the trained band. Five
scripts previously disagreed about the same run. Every candidate below is read through
it, or the number is not admissible.

## The candidates

| | candidate | cost | why it is live |
|---|---|---|---|
| 1 | Run-to-run spread | free | The three baseline runs have effectively identical `.hydra` settings, so they *are* repeats; the 31.4° / 58.2° pair quoted from them appears to be generation 0 rather than run means, and draws within one run span ~31–69°. Confirm the spread before reading any difference below |
| 2 | Fragment count (9) | free | Normalised, error tracks fragment count; the old "ruled out" was the units bug |
| 3 | A missing sherd | cheap GPU | The Juglet is **incomplete** and none of the eight pots TORA reassembles are. Never tested. [U4](../../intent/U4-missing-fragments.md) names the failure mode |
| 4 | Low-side out-of-band scale | cheap | `juglet_norm` runs report `scales = 0.041`, 9× below the trained floor of 0.375. The scale ladder only tested *above* 0.5 |
| 5 | Wear | expensive | Cannot currently be shown to differ from fresh pots at the resolution available |

## Done when

- [ ] Each of the five is ruled in or ruled out, each with a **render** at a view that
      resolves what it claims to test
- [ ] Whichever survives is specified precisely enough to hand to `/to-spec`
- [ ] Every reading states which of the three it is — method failed, ruler broken,
      reference wrong

Stopping at the first candidate that looks sufficient is what produced "piece count is
ruled out" in the first place. Rule all five.

## What would refute the whole framing

The five together leaving the gap unexplained — then the cause is something not on this
list, and saying so is the result.

## Source

`docs/notes/JUGLET_TORA_ROOTCAUSE.md`, `WEAR_TEST_RESULTS.md`, `GATE_A_RESULT.md`,
`scripts/build_juglet_ground_truth.py`, job 29891327. Map: `.scratch/juglet-cause/map.md`.
Instrument: `scripts/readout.py`, `.scratch/eval-readout/`.
