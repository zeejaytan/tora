# Skin spikes in the wear v2 datasets

**Prior work searched:** no paper or outside method is involved; this measures a fault in TORA's own
code, so no outside code or data can answer it. GitHub: not searched, for that reason. This repo's
`.scratch/`, `docs/` and `intent/` searched for "spike" and "max_ref": nothing found that names this
fault (the spikes in `docs/notes/WEAR_SIMULATION.md` and the u10 roughness tickets are other effects).

**The question:** sherd-worn found `blunt_asperities` can throw a skin vertex at a break-face rim far
past its cutoff. Do TORA's wear v2 datasets carry such vertices, and does it matter for what was
concluded from them? Serves O7. The one ticket is `issues/01-count-spikes-in-wear-v2.md`.

**Not in scope:** changing TORA's code. A fix exists in sherd-worn (`sherd_worn/wear.py`, ticket 07 of
its release spec); whether TORA takes it is decided after the count.
