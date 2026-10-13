"""Score aw_env runs on AssemblyWorldBench Fantastic Breaks tasks with the benchmark's own mathematics.

Calibration for ticket 04: imports assembly_world_bench (github.com/AssemblyWorld/assembly-world-bench,
commit 22646c9) from AWB_ROOT, default /tmp/ab_chk/awb. Usage: score_fb.py <block snapshot dir> <runs dir>"""
import json, sys
from pathlib import Path
import numpy as np
import os
sys.path.insert(0, os.environ.get('AWB_ROOT', '/tmp/ab_chk/awb'))
from assembly_world_bench.geometry import rotation_matrix, score_parts
from assembly_world_bench.registration import align, transform

def score(run, ev, T=None):
    e = json.loads(Path(ev).read_text())
    ids = e['part_ids']; div = float(e['scale_divisor'])
    groups = [[ids.index(p) for p in g] for g in e['equivalence']['groups']]
    if T is None:
        T = json.loads((Path(run) / 'final.json').read_text())['T']
    pred, targ, seeds = [], [], []
    for i, pid in enumerate(ids):
        M = np.asarray(T[f'part-{i + 1:04d}']); R, t = M[:3, :3], M[:3, 3]
        cloud = np.asarray(e['points'][pid]); pose = np.asarray(e['gt_poses'][pid])
        Rg = rotation_matrix(pose[3:])
        pred.append(transform(cloud, R, t) / div)
        targ.append((cloud @ Rg.T + pose[:3]) / div)
        r = Rg @ R.T
        seeds.append((r, (pose[:3] - r @ t) / div))
    r, t, al = align(np.concatenate(pred), np.concatenate(targ), seeds)
    pred = [transform(p, r, t) for p in pred]
    s, rec = score_parts(pred, targ, groups, ids, al['chamfer'])
    return s, rec, pred, targ

if __name__ == '__main__':
    S = Path(sys.argv[1]); runs = Path(sys.argv[2])
    for run in sorted(runs.iterdir()):
        ev = S / 'cache' / run.name / 'evaluation.json'
        if not (run / 'final.json').exists():
            print(run.name, 'no final.json'); continue
        s, rec, pred, targ = score(run, ev)
        print(run.name, 'PA', s['PA'], 'SR', s['SR'], 'SCD', round(s['SCD'], 3),
              [round(r['chamfer'], 4) for r in rec])
        (run / 'official_score.json').write_text(json.dumps({'scores': s, 'parts': rec}, indent=1))
