# 01: Count skin spikes in the wear v2 datasets

**What to build:** a measurement, no code change: on the wear v2 datasets, count the vertices moved
by more than R between fresh and worn, per object, with the largest move in mm. R is the blunting
cutoff, `cut_frac` x the object's diagonal. Do not change TORA code from this ticket.

**Answers:** O7
**Blocked by:** None - can start immediately
**Status:** needs-triage

**Why (2026-10-30, found in sherd-worn ticket 07).** `scripts/wear_ops.py` at 1db3453: `_proud_height`
(line 199) fits a plane in a frame whose up is the outward direction, and `blunt_asperities` (line 385)
removes all of what it reports. At a corner where skin meets a finer break face, the fit can extrapolate
far past the cutoff. On a sherd-worn example jar (0.2 mm break faces, 1 mm skin, seed 0), one skin vertex
moved 5.5 mm through a 6 mm wall with R = 0.74 mm. So wear v2 meshes may carry skin spikes at break-face
rims.

**Where to look first.** On a synthetic corner the spike needs the thinning in `_proud_height`: it
appeared above `max_ref` = 60,000 reference points (3.66 mm, 21 vertices past R) and not below them
or with thinning switched off (at most 0.39 mm). That is one synthetic corner, so count every piece, but
report each piece's band vertex count beside its result.

**Count first: any piece over 60,000 vertices (2026-10-30, sherd-worn ticket 07).** TORA v2 spikes are
expected on these. The thinning tests the piece's whole vertex count, not the band. On the sherd-worn
jar (coordinator's cloud run, one jar, seed 0), TORA's code moved a vertex 5.525 mm thinned against at
most 0.582 mm with thinning off, on pieces of 74,000-88,000 vertices.

**A move past R is a suspect, not a proof.** A vertex that moved more than R is what to look at; render
the worst few before saying what they mean for any training result.

- [ ] Wear v2 datasets and their fresh counterparts listed, with the commit that built them
- [ ] Per object: vertices moved more than R, largest move in mm, vertex and band vertex count per piece, pieces over 60,000 vertices first (job on Spartan)
- [ ] The worst few rendered before and after
- [ ] What it means for the wear v2 training results said plainly, or the next ticket opened
