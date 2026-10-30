# TORA uses sherd-worn

**Answers:** none (routine; the code move belongs to sherd-worn's release effort)
**Status:** agreed as ticket 05 of that effort; the plan and the decision are there, `sherd-worn/.scratch/release/issues/05-tora-csc-use-the-package.md`

**Prior work searched:** no new search for this effort, because it moves code already released. Copied from
`sherd-worn/.scratch/release/spec.md` (2026-10-29): GitHub "mesh erosion fragments", "fracture surface abrasion";
web "simulate erosion wear fracture surfaces 3D fragments", "PRESIOUS erosion simulation"; PyPI. Found:
https://arxiv.org/abs/1901.05726, https://pypi.org/project/age3d, https://www.ntnu.edu/presious/software.
None wears the break faces of a fragment set while keeping the assembled poses.

## Intention

TORA stops holding its own copy of the wear code and imports `sherd-worn` v0.1.0, so the two cannot drift.
Ticket `issues/01-tora-uses-the-package.md` holds the work and the comparison that decides whether it merges.
