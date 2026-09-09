# What wear v3 changed from wear v2

**Written 2026-09-10, from the source files rather than from memory.** Wear v3 ran
as job **29880370** (2026-09-02, `COMPLETED|0:0`); its results are read out in
[`LORAV3_29880370_RESULT.md`](LORAV3_29880370_RESULT.md). This note is the change
record only — what is different, and why each difference was made. It does not say
whether v3 worked; that is the other note, and the short answer there is no.

## In one paragraph, for someone who has not been following

**v2 and v3 are not two versions of the same thing.** v2 asked *how do we make a
sherd look worn?* and answered it on our own eight ceramic vessels. v3 accepted
that answer and asked a different question the conservator raised: *the model has
never seen the shape of the pot we want it to rebuild.* So v3 changed the **source
material** (from 8 real ceramic vessels to 203 synthetic vessel shapes), changed
**how the wear is applied** (because the new meshes are too coarse for v2's recipe
to do anything), and changed **how the model is trained** (from rewriting the whole
network to a small removable attachment). Each of those is a separate decision with
its own evidence, and the third is the one that could have been worth having on its
own.

---

## 1. The gap each version was built to close

|  | **wear v2** | **wear v3** |
|---|---|---|
| the gap | break faces in training were **too crisp** — real worn sherds have rounded, information-poor fracture surfaces | training had almost **no vessel shapes** — 8 ceramic pots in total, and the Juglet is not one of them |
| whose words | "Smoothness is where the information of how sherds lock into each other is diminished" | "the dataset provides more variety as to the shapes that get trained… we don't have the shape/object in training. That's the gap" |
| plan / build | `scripts/build_wear_trainset_v2.py`, rebuilt 2026-08-14 | `docs/notes/WEAR_V3_PLAN.md` (2026-08-18) → `scripts/build_bbad_vessel_trainset.py`, rebuilt 2026-08-31 |
| dataset written | `wear_trainset_v2.hdf5` | `bbad_vessels_v3.hdf5` |

## 2. Source material — the change everything else follows from

| | **v2** | **v3** |
|---|---|---|
| source file | `real_finetune.hdf5` — real scanned objects | `breaking_bad_vol.hdf5` — the Breaking Bad synthetic corpus |
| what is in it | **8 ceramic vessels** (plus bone and other), 27 objects, 3 excluded | **203 distinct vessel shapes**, 1,169 train / 117 val / 117 test |
| how fine the mesh is | **0.057–0.068%** of object between vertices (fine scans) | **0.25–0.47%** of object — four to eight times coarser |
| split | by instance | **by object**, so no shape appears on both sides |
| honesty note carried in the file | thin-walled objects may have wear applied to sound pot | **`test` is a verbatim copy of `val`** — there is no independent held-out set |

**This one change forces the next two.** The Breaking Bad meshes do not record
fracture detail at the scale v2's wear operates on, so v2's recipe applied to them
would be a no-op, and v2's training recipe applied to them would overwrite what the
model already knows about real pots.

## 3. How wear is applied — v2's recipe was reversed on measured evidence

| operation | **v2** (fine real scans) | **v3** (coarse synthetic vessels) | why the reversal |
|---|---|---|---|
| **blunting / abrasion** | the main mechanism. One-sided **peak truncation**: removes only material standing proud of the local envelope, so material can never be added | **not used** | measured on these meshes (`test_wear_on_coarse.py`): only **0.0001–0.0053%** of the surface stands proud at the cutoff, and blunting moves the joins **0.0–0.7%**. There are no teeth in the file to remove |
| **recession** (uniform retreat from the break face) | **retired** — at every safe dose it opened joins *less* than blunting already did, while *adding* the fine relief abrasion is supposed to remove | **un-retired, and is the main mechanism** | the same 0.05% retreat opens these joins by **6–10%** against 1.1–1.9% on fine scans, because these fragments were cut from one mesh and mate exactly |
| **dose** | severity rides on the blunting cutoff (0.30–0.50% of object) | **0.15% and 0.30%** of object retreated (`WEAR_LEVELS`) | 0.30% lands the contact-band gap on a real worn pot at **all three percentiles** (p10/p50/p90 = 0.181 / 0.588 / 1.771 against the real pot's 0.182 / 0.615 / 1.692) |
| **chipping** | sampled per variant from the conservator's size distribution | **2–3 chips at 0.22–0.25% of object**, restrained | uniform retreat makes a *tall narrow* gap peak where the real contact band is a *broad hump*; localised loss supplies the spread. Job 28742114 showed 6 chips at 0.40% make "heavy wear" read **rougher** than untouched |
| **scan-resolution blur** | **half the variants blurred** to 0.25% of object | **none** | the v3 meshes are *already* at 0.25–0.47%; blurring again would remove the shape, not the fracture texture |
| **fragment loss** | `sample_missing` — complete / lost one / lost two / lost three, by attrition or by a major absent piece | **imported unchanged** from v2 | "a real assemblage is missing pieces" applies identically; the code was deliberately not forked |

⚠ **A stale line in the config.** `config/data/main/bbad_vessels_v3.yaml` still says
*"Two wear doses per break (0.05% and 0.10% recession); 0.20% was dropped."* That is
pre-rebuild text. The file that was actually built and trained on uses **0.15% and
0.30%**, and the 0.20% exclusion was explicitly overturned once the metric it was
measured against turned out to be an artefact. **Corrected in the yaml 2026-09-10**; the comment now carries the built doses and says what it used to say.

## 4. Two data defects v3 found and fixed — the part that is unambiguously worth having

Neither of these is about wear. Both were in the vessel corpus, and either alone
would have made any result read off it meaningless.

- **49.22% of fragment vertices sat exactly on a neighbouring fragment's vertex.**
  The break faces were congruent copies, so a sherd could be seated by matching a
  surface to **its own mirror image** — something no real sherd offers. v3 rebuilds
  those faces to **0.00% coincident**, and adds a gate that **drops any worn example
  still holding a coincident vertex**, loudly, rather than writing it out with a worn
  label on it. The old figure had been hidden by `joint_gap`, a 10th percentile over
  5000 points that bottoms out at the sampling floor: it read a healthy 0.277 on a
  corpus whose true join gap was zero.
- **37% of the corpus was a solid lump, not a vessel** — sectioned through, not a
  hollow pot. Those are **removed** from train/val/test by
  `scripts/filter_lumps_from_splits.py`, with the untouched membership kept beside
  them as `train_all` / `val_all` / `test_all`. Checked by eye at the threshold, not
  only in aggregate (`artifacts/lump_cut_boundary.png`).
- **`fresh` is no longer trainable.** In v2 the unworn variant was training data. In
  v3 it *is* the defect — the coincident-vertex build — so it is kept, still
  measurable, under split `"control"` where nothing can train on it by accident.

Deliberately **not** applied: the cells-through-wall corpus screen. It would raise
the median wall thickness of the kept set from 2.10% to 5.86% of object — keeping the
vessels TORA finds easy and dropping the thin-walled ones, which are the closest thing
here to real archaeological sherds. Rings are also not filtered: 13.9% of these
fragments close into a hoop, and so do 2 of the Juglet's 9 pieces.

## 5. How the model is trained — the largest change, and the best-engineered one

| | **v2** — `finetune_wear_augmented_v2.slurm` | **v3** — `finetune_lora_vessels_v3.slurm` |
|---|---|---|
| what is changed in the model | **everything.** A full fine-tune of the whole network | **a removable attachment.** LoRA adapters, rank 128 / alpha 256 / dropout 0.1, on all 6 transformer blocks, plus the pose head. **1,181,184 of 43,867,136 parameters — 2.69%** |
| datasets mixed in | `wear_trainset_v2` **+ `pig` + `rib`** (synthetic replay) | `bbad_vessels_v3` **alone. No replay.** |
| why replay, or why not | a full fine-tune overwrites what it is trying to keep. wear_v1 bought **+0.235** seating on worn material by **losing 0.115** on fresh, with no way to undo it | an adapter cannot do that: switching it off restores the base model **bit-for-bit**, so the do-no-harm arm is guaranteed by construction rather than bought with replay data. GARF's own fine-tune config does the same — one domain, no replay |
| learning rate | 2e-5 | **2e-5.** GARF uses 2e-4; on this data 2e-4 stopped improving at epoch 9 and then drifted for fifty more |
| epochs | 40 | **20** |
| checkpoint selection | newest file by modification time — which is `last.ckpt`, the **final** epoch | **best epoch on `val/overall/part_accuracy`**, validated **every** epoch, saved at validation end. The default config validates every 10 epochs and saves on train-epoch end, so `save_top_k=1` did not mean what it says |
| gates before any result was read | none | **five**, in order: freeze-is-really-a-freeze; the adapter's identity / effect / exact off-switch / file round-trip (Gate C); a train-and-reload smoke test; **then** a weight-level diff of what actually moved; only then the evaluation arms |

### What the v3 gates returned

- **Gate C, all five parts PASS, exactly.** The adapter is the identity at
  initialisation (max difference 0.000e+00), it does something when enabled
  (1.616e+00), it switches off to **0.000e+00**, and it survives a save/reload to
  **0.000e+00**. An adapter that cannot be switched off exactly is not switchable,
  and every cross-domain comparison built on one would carry an unknown offset.
- **The freeze held.** `0` encoder weights changed (492 identical), `0` flow-backbone
  weights changed (171 identical). This is a real fix: job 29527496 had been a full
  fine-tune *wearing* a LoRA, because `_freeze_encoder()` re-enables `requires_grad`
  at every epoch unless `frozen_encoder` is set.
- **"Reversible" turned out to be only three-quarters true.** `train_head=true` left
  the pose head trainable and **5 of its tensors moved** (largest 1.943e-03,
  median 1.121e-03). The switch does not cover them. So **"adapter off" means
  "adapter off, retrained pose head still in"** — a real arm, but not the untouched
  baseline. The job knew this and ran the untouched base checkpoint as a third arm,
  which is why the read-out has three arms and not two.

## 6. What is NOT comparable between them

- **The datasets are not comparable to each other**, and v2 is not comparable to
  anything built before 2026-08-14. Different source material, different wear
  mechanism, different mesh resolution.
- **The trained models are not comparable head to head either.** v2 changed all the
  weights; v3 changed 2.69% of them plus a pose head. A difference between the two is
  a difference of two things at once.
- **The evaluation ruler changed underneath both.** Commit `0d6a85f` (2026-09-02
  14:58) moved the seating threshold into the unit-length box the benchmark states it
  in. Job 29880370 is the one wear-family run whose stored results are all post-fix —
  every arm carries `part_accuracy_absolute`, the marker. Anything quoted from the v2
  runs is on the old ruler unless it says otherwise.

## 7. What each version has actually shown

- **v2** established the wear model itself: one-sided truncation that cannot add
  material, recession retired on a measured dose response, half the variants blurred
  to scan resolution — and a measured list of its own limits (a per-object smoothness
  floor; 93–99% of relief removed well inside a break face against only 7–9% within
  one cutoff of its edge, so every fracture in that set carries a slightly under-worn
  rim).
- **v3** fixed two corpus defects that had made the vessel data a lookup table, and
  built a genuinely switchable adapter with the freeze verified at weight level.
  **On the reassembly result it was bought for, it did not earn its place.** See
  [`LORAV3_29880370_RESULT.md`](LORAV3_29880370_RESULT.md).

## Files

```
v2  scripts/build_wear_trainset_v2.py          config/data/main/wear_finetune_v2.yaml
    scripts/hpc/build_wear_trainset_v2.slurm   scripts/hpc/finetune_wear_augmented_v2.slurm
v3  scripts/build_bbad_vessel_trainset.py      config/data/main/bbad_vessels_v3.yaml
    scripts/hpc/build_bbad_vessel_trainset_v3.slurm
    scripts/hpc/finetune_lora_vessels_v3.slurm
    scripts/filter_lumps_from_splits.py        docs/notes/WEAR_V3_PLAN.md
```
