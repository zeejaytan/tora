"""Turn an AssemblyWorldBench Fantastic Breaks episode into an aw_env task (calibration)."""
import json, sys, zipfile, tempfile
from pathlib import Path
import numpy as np, trimesh, mujoco as mj
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation as Rot
sys.path.insert(0, str(Path(__file__).resolve().parent))
from prep_tasks import lighten

ep, ev, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
with zipfile.ZipFile(ep) as z, tempfile.TemporaryDirectory() as d:
    z.extract('world/model.mjb', d)
    m = mj.MjModel.from_binary_path(str(Path(d) / 'world/model.mjb'))
data = mj.MjData(m); mj.mj_forward(m, data)
e = json.loads(ev.read_text())
ids = e['part_ids']
(out / 'pieces').mkdir(parents=True, exist_ok=True)
names = []
for g in range(m.ngeom):
    if m.geom_type[g] != mj.mjtGeom.mjGEOM_MESH: continue
    k = m.geom_dataid[g]
    a, n = m.mesh_vertadr[k], m.mesh_vertnum[k]
    fa, fn = m.mesh_faceadr[k], m.mesh_facenum[k]
    V = m.mesh_vert[a:a + n].astype(float); F = m.mesh_face[fa:fa + fn]
    R = data.geom_xmat[g].reshape(3, 3); t = data.geom_xpos[g]
    W = V @ R.T + t
    body = mj.mj_id2name(m, mj.mjtObj.mjOBJ_BODY, m.geom_bodyid[g])
    mesh = trimesh.Trimesh(W, F, process=False)
    lm, how = lighten(mesh, 30000)
    names.append((body, mesh))
    lm.export(out / 'pieces' / f'{body}.ply')
# check: GT clouds (initial frame) lie on some mesh
for pid in ids:
    P = np.asarray(e['points'][pid])
    best = min(np.median(cKDTree(mesh.vertices).query(P)[0]) for _, mesh in names)
    print(pid, 'median dist to nearest mesh verts', round(float(best), 5))
(out / 'task.json').write_text(json.dumps({'task': out.name, 'parts': sorted(b for b, _ in names),
    'conventions': 'scene units; world up +Z; parts start scattered on the floor z=0'}, indent=1))
