# A general AI agent reassembling the Juglet by sight (AssemblyWorld test), 2026-10-13

Spec and tickets: `.scratch/agent-assembly/`. Paper: AssemblyWorld, arXiv 2609.40353v1
(pr-papers `text/assemblyworld-2609.40353v1.md`). Scored by job 32842542 (COMPLETED 0:0);
pilot by 32819965; tasks prepared by 32804650. Pictures and per-run JSON: project files
`agent-assembly/agentasm_full_*`.

## What was claimed and what was run

The paper reports that a general agent, seeing only rendered views and moving parts by tool
call, seats the second fragment of a two-fragment Fantastic Breaks object about 83% of the time
(its 91.67% part accuracy includes the pinned anchor). We rebuilt its tools, scrambled Juglet
sherds its way, gave Claude (Opus, through Claude Code) its task text verbatim, and ran each
task three times: the four sherd pairs with most contact in the conservator's reassembly, and
the whole 9-sherd pot. Answer key on Spartan only.

## Result

| task | what the pair is | right way round (ours, 4.6 mm) | paper's "correct" | runs |
|---|---|---|---|---|
| pair 0-7 | neck/handle sherd + body strip | 1 (turn 18 deg, 3.3 mm) | 2 | 3 |
| pair 3-6 | two body sherds | 0 | 1 (sherd upside down, 166 deg) | 3 |
| pair 4-6 | two body sherds | 0 | 0 | 3 |
| pair 5-6 | two body sherds | 0 | 0 | 3 |
| **pairs** | | **1 of 12** | **3 of 12** | |
| whole pot | 9 sherds, no picture | 0 of 8 movable sherds, every run | 1-3 of 9 incl. anchor | 3 |

- **Against the paper's ~83%: 3 of 12 (25%) on its own ruler, 1 of 12 (8%) the right way
  round.** Kind of failure: the method genuinely fails on this material; the pictures agree
  with the numbers (`*_look.png`).
- **The paper's ruler is blind to a sherd flipped in its own place.** Of its 3 successes, 2 are
  a sherd lying in its gap turned 166-173 deg (points 16-18 mm from home). One more run
  (4-6 r2) had the sherd in its own place but turned 169 deg; neither ruler counts it.
- **The one success leans on a distinctive sherd.** Pair 0-7 contains the neck and handle,
  which the agent recognised every time; the three body-only pairs never succeeded (0 of 9).
- **Whole pot:** every run stood the neck sherd upright and called the rest a jug. Run 3's
  silhouette reads as the right vessel, but no sherd other than the pinned one is in its place
  the right way round. The agents said so themselves ("placed in rings without matching any
  break edges").

## Weight and caveats

One pot, four pairs, three runs each, one model (Opus; the paper's best agent, GPT-6 Astra, was
not run). Deviations: tools rebuilt from the paper's Table A-2, not its code; part position is
the centre; agents could see project instructions naming the work as pottery (the paper
disabled them); some agents wrote small helper scripts; wall time was 4-11 min for round 2 but
~4.5 h for rounds 1 and 3 (the container slowed, 87-341 calls; the paper's Astra averaged 94),
so time was not what limited them.

## What it means

On real, worn pottery a general agent recognises what the pieces are (neck, handle, base,
throwing rings, inside versus outside) but does not fit break faces. It is not a route to a
reassembled pot (U16) on its own. The paper's GARF-then-agent step (ticket 05) is not run:
the agent cannot place a sherd from scratch, and a correction step needs exactly that.
