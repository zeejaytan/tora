"""O1: Juglet wall thickness against the 5000-point sampling spacing (TORA and GARF).

Runs screen_vessel_corpus.py's own wall functions on artifacts/juglet_gt.hdf5 (the
conservator's reassembly). load_meshes is stubbed because its home module imports the
tora package, which needs lightning; the stub is the same loader, verbatim in effect.
Laptop: python scripts/o1_juglet_wall.py from tora/scripts. Result: tora/intent/O1.
"""
import sys, numpy as np, h5py, trimesh
sys.path.insert(0, r"C:\PR\tora\scripts")
import types
def _load(grp):
    pg = grp["pieces"]; out=[]
    for k in sorted(pg.keys(), key=lambda s: int(s) if s.isdigit() else s):
        out.append(trimesh.Trimesh(vertices=np.asarray(pg[k]["vertices"][:],dtype=np.float64), faces=np.asarray(pg[k]["faces"][:]), process=False))
    return out
_m=types.ModuleType("measure_gap_as_network_sees"); _m.load_meshes=_load; sys.modules[_m.__name__]=_m
from compare_wear_severity import object_size
from measure_gap_as_network_sees import load_meshes
from measure_wall_vs_sampling import NUM_POINTS, break_faces, wall_thickness
from screen_vessel_corpus import shell_thickness, fill_fraction
h = h5py.File(r"C:\PR\tora\artifacts\juglet_gt.hdf5", "r")
meshes = load_meshes(h["juglet_gt/Juglet-000"])
rng = np.random.default_rng(0)
allv = np.concatenate([np.asarray(m.vertices) for m in meshes])
print("pieces", len(meshes), "bbox extent", allv.max(0) - allv.min(0))
size = object_size([np.asarray(m.vertices) for m in meshes])
area = sum(m.area for m in meshes)
spacing = float(np.sqrt(2 * area / NUM_POINTS + 1e-4))
masks = break_faces(meshes, spacing)
walls = [wall_thickness(m, rng, ~b) for m, b in zip(meshes, masks)]
shell = shell_thickness(meshes, masks)
print("size(diag)", size, "area", area, "spacing", spacing)
print("per-piece wall (ray)", [None if w is None else round(w, 3) for w in walls])
w = float(np.median([x for x in walls if x is not None]))
print("wall ray", w, "wall 2V/A", shell)
print("wall ray %", 100*w/size, " 2V/A %", 100*shell/size, " spacing %", 100*spacing/size)
print("CELLS ray", w/spacing, " CELLS 2V/A", shell/spacing)
print("break faces %", 100*np.mean([m.mean() for m in masks]), "fill", fill_fraction(trimesh.util.concatenate(meshes)))
