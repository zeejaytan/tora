"""Audit every eval run on Spartan for the two things that invalidate a comparison:
the stored size fed to the model (`scales`) and the anchor mode it was run in.

Reads data.anchor_free, NOT model.anchor_free -- the two keys are different and
tora/data/dataset.py is driven by the data one. Both are printed so the mismatch
is visible.

One level of glob over eval_runs/*/ only. No recursive find, no du.

Runs on Spartan (the eval runs are not on the laptop):

    scp scripts/audit_run_provenance.py spartan:/tmp/
    ssh spartan 'python3 /tmp/audit_run_provenance.py'

Output feeds .scratch/juglet-cause/issues/03-low-side-out-of-band-scale.md.
"""
import glob
import json
import os

ROOT = "/data/gpfs/projects/punim2657/TORA/eval_runs"
LO, HI = 0.375, 0.625


def yaml_block_value(path, block, key):
    """Read `key` from the top-level `block` of a hydra config, without pyyaml."""
    try:
        lines = open(path).read().splitlines()
    except OSError:
        return None
    inblock = False
    for ln in lines:
        if ln and not ln[0].isspace():
            inblock = ln.split(":")[0].strip() == block
            continue
        if inblock and ln.startswith("  ") and not ln.startswith("   "):
            k = ln.strip().split(":")[0]
            if k == key:
                return ln.split(":", 1)[1].strip()
    return None


rows = []
for d in sorted(glob.glob(os.path.join(ROOT, "*"))):
    if not os.path.isdir(d):
        continue
    name = os.path.basename(d)
    cfg = os.path.join(d, ".hydra", "config.yaml")
    data_af = yaml_block_value(cfg, "data", "anchor_free")
    model_af = yaml_block_value(cfg, "model", "anchor_free")
    ngen = yaml_block_value(cfg, "model", "n_generations")

    scales, objs = {}, 0
    for f in sorted(glob.glob(os.path.join(d, "results", "*.json")))[:400]:
        try:
            x = json.load(open(f))
        except Exception:
            continue
        objs += 1
        s = x.get("scales")
        if s is not None:
            scales.setdefault(x.get("name", "?"), float(s))
    if not scales:
        continue
    vals = sorted(scales.values())
    oob = [v for v in vals if not (LO <= v <= HI)]
    rows.append((name, data_af, model_af, ngen, len(scales), vals[0], vals[-1], len(oob)))

print("%-46s %-6s %-6s %-4s %4s %9s %9s %5s" % (
    "run", "dataAF", "modAF", "gen", "objs", "min_scale", "max_scale", "oob"))
for r in rows:
    print("%-46s %-6s %-6s %-4s %4d %9.4f %9.4f %5d" % r)
print("\n%d runs with results" % len(rows))
