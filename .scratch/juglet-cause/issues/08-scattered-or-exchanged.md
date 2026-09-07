# 08: Is the Juglet scattered, or are its sherds merely mixed up?

**Type:** `wayfinder:research` (AFK)
**What to build:** The answer to the question ticket 07's instrument was built to ask,
pointed for the first time at the object this map is actually about.

**Answers:** O8

**Blocked by:** None. Everything needed is already on the laptop.

**Status:** resolved 2026-09-07 — **scattered.** Twelve runs, four model arms, one answer.

## Why it exists

Ticket 07 found that a reassembly can fail in two ways that every metric we report
scores identically:

- **exchange** — the pieces are in roughly the right places wearing the wrong names;
- **scattering** — the pieces are genuinely nowhere near where they belong.

They call for opposite responses. More or better training is the lever for a scattering
and cannot be for an exchange. `scripts/check_identity_swap.py` separates them for free
from clouds already on disk — and it had been run on eight fresh pots and never on the
Juglet.

It matters here beyond bookkeeping. The most conservator-plausible reason a machine
would fail on excavated pottery is that plain body sherds look alike, so it puts the
right pieces in the wrong slots. If that were the Juglet's failure, the whole wear
story would be beside the point.

## Acceptance criteria

- [x] Run on every Juglet cloud on disk, not one arm — a single run cannot tell two
      things apart on this object (ticket 01)
- [x] Report whether the winning renaming **repeats** across draws; an exchange repeats,
      a scattering does not
- [x] A render at individual-sherd placement
- [x] States which of the three: method failed, ruler broken, reference wrong

---

## Answer (2026-09-07)

**The Juglet is scattered. It is not a mix-up, and no renaming of its sherds rescues
it.** The best renaming the assignment can find still leaves the worst loose sherd
**19% of the pot's size from home** — about 12 mm on a 65 mm juglet — against **2–3%**
for the pots this model assembles correctly. And the renaming that wins is a different
one almost every attempt.

| run | draws | worst loose sherd | best renaming | different renamings | identity wins |
|---|---|---|---|---|---|
| baseline, job 30130049 | 20 | 35.5% | 19.2% | 17 of 20 | 0 of 20 |
| adapter_on, job 30130049 | 20 | 47.9% | 22.9% | 17 of 20 | 0 of 20 |
| adapter_off, job 30130049 | 20 | 39.8% | 24.6% | 16 of 20 | 0 of 20 |
| nine earlier runs (29330980, 29527496, 29623885, 29880370) | 5 each | 33–56% | 12–24% | 4–5 of 5 | 0 |

Compare the two things this instrument has already told apart:

- `narrow_bottle3` — **exchange**: 26.2% → 8.1%, and **the same** renaming in 10 of 10.
- `narrow_bottle4`, `narrow_bottle2`, `pink_bowl`, `blue_pot` — **correct**: the identity
  naming wins outright, so a non-identity match is not handed out for free.
- the Juglet — **scattering**: a different renaming nearly every draw, and it does not
  rescue the assembly when it wins.

**"Identity never wins" is a symptom of the scattering, not evidence of a mix-up.** Once
pieces are flung about, each ground-truth sherd's neighbourhood is occupied by whatever
happened to land nearest it, so *some* permutation always scores a little better than
the true one. The tell is that it is a different permutation each time and it stays
seven times worse than a correct assembly.

**Which of the three: the method genuinely failed** — and this ticket narrows *how*.
Not the ruler: the same instrument reads 2.4–3.3% on pots that are right and 8.1% on a
pot that is merely mis-named. Not the reference: the reference is the conservator's own
reassembly, and nothing here scores it.

### Render

`artifacts/juglet_scatter_vs_swap.png` — three rows: the Juglet as it really is; the
model's answer coloured by the name the model gave each piece; the same points
recoloured by the place each piece actually landed in. **The third row moves no
geometry.** On `narrow_bottle3` that row snaps back to the reference. Here it does not:
pieces sit outside the vessel outline in both rows, and the juglet does not reappear.

`scripts/render_identity_swap.py` grew a `--hilite all` option for this, because a
scattered pot has no pair to point at — the eye needs to follow every sherd.

### What it means for the work

**One plausible cause of the Juglet's failure is now off the table**: it is not
confusing look-alike sherds for one another. That was worth checking precisely because
it is the failure a conservator would predict first on plain body sherds, and because
it is the one failure mode that no amount of extra training would fix.

What is left standing is a genuine placement failure — the model does not know where
the pieces go — which is what makes wear still a live candidate rather than a settled
one, and is why the map stays open.

It also hands the umbrella's `U2` (perception or placement?) a second, independent
probe. U2's only evidence so far is a feature-separability number that did not move
beside a seating number that did. This is a different instrument on a different object
and it points the same way: the pieces are not being confused with each other, they are
being put in the wrong places.
