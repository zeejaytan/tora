"""Paired presentations (pr-workspace wear-beyond-juglet 19): with presentation_seed set, the
same seed hands identical inputs whatever the global numpy state and call order; another seed
differs; numpy's global state is left alone; anchor-fixed keeps the anchor at its true pose.
Builds a two-pot HDF5 in a temporary folder; no GPU. torch is stubbed when it is not installed.

    python scripts/test_presentation_seed.py      (exit 1 on a failure)
"""
import os, tempfile
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(tempfile.mkdtemp())
import sys, types, importlib.util, numpy as np, h5py, trimesh
try:
    import torch  # noqa: F401
except ImportError:
    pass
if "torch" not in sys.modules:
    torch=types.ModuleType("torch"); u=types.ModuleType("torch.utils"); d=types.ModuleType("torch.utils.data")
    class Dataset: pass
    torch.Tensor=type("Tensor",(),{})
    d.Dataset=Dataset; sys.modules.update({"torch":torch,"torch.utils":u,"torch.utils.data":d})
pkg=types.ModuleType("tdata"); pkg.__path__=[os.path.join(REPO, "tora", "data")]; sys.modules["tdata"]=pkg
spec=importlib.util.spec_from_file_location("tdata.dataset",os.path.join(REPO, "tora", "data", "dataset.py")); m=importlib.util.module_from_spec(spec); sys.modules["tdata.dataset"]=m; spec.loader.exec_module(m)
# small h5: two pots, each a sphere cut into 4 parts
with h5py.File("t.hdf5","w") as f:
    for k,pot in enumerate(["potA","potB"]):
        s=trimesh.creation.icosphere(3, radius=1+k)
        c=s.triangles_center; lab=(c[:,0]>0)*2+(c[:,2]>0)
        g=f.create_group(f"set/{pot}/pieces")
        for i in range(4):
            sub=s.submesh([np.where(lab==i)[0]],append=True)
            gg=g.create_group(f"piece_{i}"); gg["vertices"]=sub.vertices; gg["faces"]=sub.faces
    f["data_split/set/val"]=np.array([b"set/potA",b"set/potB"])
def make(ps, af=True):
    ds=m.PointCloudDataset.__new__(m.PointCloudDataset)
    m.PointCloudDataset.__init__(ds, split="val", data_path="t.hdf5", dataset_name="set", max_parts=20, anchor_free=af, presentation_seed=ps)
    return ds
def keys(x): return (x["pointclouds_gt"].tobytes(), x["pointclouds"].tobytes(), x["points_per_part"].tobytes())
ok=True
for af in (True, False):
    a=make(3,af); b=make(3,af)
    np.random.seed(1); xa=[keys(a[i]) for i in range(len(a))]
    np.random.seed(999); [np.random.rand() for _ in range(7)]; xb=[keys(b[i]) for i in reversed(range(len(b)))][::-1]
    same = xa==xb; ok&=same
    c=make(4,af); xc=[keys(c[i]) for i in range(len(c))]
    diff = all(p!=q for p,q in zip(xa,xc)); ok&=diff
    st=np.random.get_state()[1].copy(); a[0]; kept=(np.random.get_state()[1]==st).all(); ok&=kept
    if not af:
        x=a[0]; anc=x["anchor_parts"]; i=int(np.argmax(anc)); ppp=x["points_per_part"]; o=np.concatenate([[0],np.cumsum(ppp)]); 
        fixed=np.allclose(x["pointclouds"][o[i]:o[i+1]], x["pointclouds_gt"][o[i]:o[i+1]]); print("  anchor-fixed: anchor input == truth", fixed); ok&=fixed
    print(f"anchor_free={af}: seed 3 twice identical {same}; seed 4 differs {diff}; global state restored {kept}; pots {len(a)}")
off1=make(None); off2=make(None)
np.random.seed(5); o1=keys(off1[0]); np.random.seed(5); o2=keys(off2[0])
print("flag off: draws come from the global state (two same-seed calls equal only by luck of threads):", o1==o2)
print("ALL OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
