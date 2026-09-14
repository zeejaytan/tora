# 13: Why does TORA put some sherds down as their own mirror image, and does it matter?

**Type:** `wayfinder:research` (AFK)

**What to build:**
- An explanation of where TORA's mirror-image sherds come from.
- Whether a mirrored sherd is one that also lands in the wrong place.
- Whether counting mirrored sherds tells a good attempt from a bad one without the
  answer key.

It comes with a render of one mirrored sherd beside its true self.

**Answers:** O8, U1

**Blocked by:** None. The first four boxes need no GPU, no fetch and no Slurm: every
input is already under `artifacts/`. Only the optional last box needs new sampling.

**Status:** ready-for-agent

**Needs-eye:** the render in the fourth box. A mirror image is easy to mis-measure and
easy to see.

## Why it exists

Ticket 12 (2026-09-12) found that the "warped" sherds the conservator saw in TORA's
intermediate output are not bent. They come out as the **mirror image** of the real
sherd: a left hand where a right hand should be.

- **On the Juglet:** 64 of 160 free sherd placements, and none bent out of shape.
- **On all three model variants and the 2026-08-10 run:** the same.
- **On control pots:**

  | pot | mirrored sherd placements |
  |---|---|
  | `galli_pot` | 13 of 90 |
  | `plate` | 13 of 50 |
  | `narrow_bottle1` | 39 of 110 |
  | `narrow_bottle3` | 6 of 30 |
  | `blue_pot` | 12 of 40, all on its two smallest rim chips, which still seat |

  None on `narrow_bottle2`, `narrow_bottle4` or `pink_bowl`.

Two things make this worth a ticket:

1. **It should not happen.** TORA is trained on sherds turned at random, never
   reflected: `tora/data/transform.py:46`, `Rotation.random()`, `dataset.py:433-447`.
   Its last step makes each sherd solid with a fit that can turn but never flip
   (`tora/procrustes.py:30-33`, det forced to +1). A mirrored sherd therefore cannot
   survive into the final assembly. The solid step turns the real sherd as close as it
   can, and it sticks out by up to about 4 mm, 6 mm in the worst attempt.
2. **It may mark the sherds that fail.** On the Juglet it does not: mirrored sherds sit
   13.5% of pot size from home, solid ones 19.2%. But on two control pots the mirrored
   sherds are the misplaced ones:

   | pot | mirrored sherds from home | solid sherds from home |
   |---|---|---|
   | `galli_pot` | 20.0% | 2.4% |
   | `plate` | 32.3% | 1.4% |

   If that holds, the number of mirrored sherds is a warning light that needs **no
   answer key**. The mirror test compares TORA's free output with the sherd's own shape,
   and the scanned fragment supplies that shape, so the true assembly is never used. That
   is the excavated case (workspace `U1`).

## What is already known, and what is not

- **Known.** The classification: bent = more than 1% of pot size left over after the
  best solid fit. Mirror = bent, and a fit that may also reflect leaves less than 3× the
  arm's own jitter. The code is in `scripts/measure_nonrigid_cheating.py`
  (`fit_leftover`, `mirror_flags`), and the numbers are in `artifacts/shape12/*.json`.
- **Known.** It is not simply the sherd turned inside out through its own wall. The
  reflection plane sits a median 51° off the wall-thickness direction (IQR 33–70°), and
  the extra turn is a median 64°.
- **Not known.** Why a model that never saw a reflection outputs one. Whether the
  mirrored sherd sits at its own home or somewhere else. Whether the test mistakes a
  nearly symmetric sherd for a mirrored one.

## Candidate explanations, to be tested rather than assumed

| | explanation | how to tell |
|---|---|---|
| **1** | **The ruler is wrong.** A sherd that is nearly its own mirror image (a flat, symmetric chip) reads as "mirrored" by accident. | Box 1: known turns and known reflections of the true sherds, and each sherd's own *handedness margin*. |
| **2** | **A reflection hides in the data pipeline.** For example, a principal-axis alignment or normalisation whose matrix has determinant −1, so TORA *is* shown mirrored sherds after all. | Box 2: read every transform on the path from file to network, and compute the determinant on real samples. |
| **3** | **The model cannot tell left from right.** Its sherd encoder only sees quantities a reflection leaves unchanged (distances, angles, dot products), so it is blind to handedness. | Box 2: name the encoder and the symmetry group it respects, from the code. |
| **4** | **The vessel invites it.** On a pot turned on a wheel, a sherd reflected across a vertical plane through the axis (or a horizontal plane on a straight wall) still lies on the vessel surface, just with its outline flipped. A model that has learned "points belong on this vessel's wall" is rewarded for it. | Box 3: express each mirrored sherd's reflection plane in the vessel's own frame (up the axis, around it, through the wall). |

These are not exclusive. 3 and 4 together would say that the model is blind to
handedness and that wheel-made vessels give it room to be wrong.

## Acceptance criteria

- [ ] **The instrument is checked first, and could refute ticket 12.**
      - On `juglet_gt` and the eight control pots, apply to every sherd a known random
        turn, then a known reflection, each with added point noise at the measured
        jitter. The turns must read "solid" and the reflections "mirror".
      - Report each sherd's **handedness margin**: how far its best solid fit to its own
        mirror image is left over, in % of pot size.
      - A sherd whose margin is under 3× the jitter cannot have its handedness measured.
        Remove it from every count below, and say how many of ticket 12's mirrors that
        removes.
      - If the check fails, stop. Ticket 12's mirror finding is then *the measurement
        was broken*, and O8 is corrected.
- [ ] **Every transform between the file on disk and the network is read**, and so is
      the sherd encoder.
      - Cover the dataset loader, augmentation, any centring or principal-axis
        alignment, and the evaluation path.
      - For each transform, record whether it can produce a determinant of −1. Measure it
        on at least 1,000 real training samples, not from reading alone.
      - Name the encoder, and the symmetry group it respects (turns only, or turns and
        reflections), with file and line.
- [ ] **What kind of reflection.**
      - For every mirrored sherd on the Juglet, `galli_pot` and `plate`, give the
        reflection plane in the vessel's own frame: up the axis, around it, and through
        the wall.
      - Also give where the mirrored points land, in one of three categories: at the
        sherd's own home reflected across that plane ("right place, wrong hand"), on the
        vessel wall somewhere else, or off the wall.
- [ ] **Render.**
      - Show one mirrored Juglet sherd and one mirrored `galli_pot` sherd, each four ways:
        its true home, TORA's free points, TORA's solid placement, and the true home
        reflected across the measured plane.
      - Use side and top views in the true pot's frame, with nothing re-centred, at a
        view resolving 1% of pot size.
      - The picture must show the flipped outline, not just report it.
- [ ] **Does it matter?**
      - On every object with mirrors, compare mirrored against solid sherds: from home,
        seated, and before and after the solid step.
      - Per attempt, check whether the number of mirrored sherds predicts how many sherds
        seat. Use rank correlation within each object, never pooled across objects, and
        report it with its spread over draws.
      - If it predicts, write down the reference-free warning light as a rule someone
        could apply to an excavated vessel, and say how often it would have been wrong
        here.
- [ ] *Optional, only if boxes 1–3 leave the source open:* sampling with the flow's
      intermediate steps saved, to see at which step a sherd flips. This needs a GPU job
      and a decision first. Do not submit it from this ticket.
- [ ] The ticket names which of the three it found:
      - **ruler broken:** explanation 1;
      - **method genuinely failed:** explanations 2, 3 or 4;
      - **reference wrong:** not expected, because `juglet_gt` and the Fractura controls
        are valid.
- [ ] **Written back:**
      - O8: the mirror bullet under "What is still open" is either struck (if it is the
        ruler) or given its cause.
      - U1: a line only if the warning light holds on more than one object.

## Weight this can bear

Mirrors appear on six objects, but only the Juglet has 20 attempts. The controls have 10
each, and the two where mirroring and misplacement coincide (`galli_pot`, `plate`) have
13 mirrored placements each. A cause found in the code (explanations 2 and 3) holds for
every object at once. A cause read off the geometry (explanation 4) holds only for
wheel-made vessels. A warning light fitted on eight pots is a lead until it is tried on
pots it was not fitted on.
