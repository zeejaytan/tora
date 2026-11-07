"""Whole-pot frame (pr-workspace wear-beyond-juglet 20): checks on a synthetic pot, no GPU.
  1. complete pot, whole_pot_path = its own file: inputs and `scales` byte-identical to off;
  2. a sherd removed: each kept sherd's extent in the input equals its true extent divided by
     the WHOLE pot's half-span (off: by the kept sherds' own, which is smaller);
  3. a pot the whole file does not hold, or no presentation_seed: refused.
torch is stubbed when it is not installed.
    python scripts/test_whole_pot_frame.py      (exit 1 on a failure)
"""
import importlib.util, os, sys, tempfile, types
import numpy as np, h5py, trimesh
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
try:
    import torch  # noqa: F401
except ImportError:
    torch = types.ModuleType("torch"); u = types.ModuleType("torch.utils"); d = types.ModuleType("torch.utils.data")
    class Dataset: pass
    torch.Tensor = type("Tensor", (), {}); d.Dataset = Dataset
    sys.modules.update({"torch": torch, "torch.utils": u, "torch.utils.data": d})
pkg = types.ModuleType("tdata"); pkg.__path__ = [os.path.join(REPO, "tora", "data")]; sys.modules["tdata"] = pkg
spec = importlib.util.spec_from_file_location("tdata.dataset", os.path.join(REPO, "tora", "data", "dataset.py"))
m = importlib.util.module_from_spec(spec); sys.modules["tdata.dataset"] = m; spec.loader.exec_module(m)
os.chdir(tempfile.mkdtemp())

def write(path, ds, drop):
    with h5py.File(path, "w") as f:
        names = []
        for k, pot in enumerate(["p1_d00", "p2_d00"]):
            s = trimesh.creation.capsule(height=2 + k, radius=1, count=[24, 24])
            c = s.triangles_center
            lab = (c[:, 0] > 0) * 2 + (c[:, 1] > 0) + 4 * (c[:, 2] > 0.5)
            g = f.create_group(f"{ds}/{pot}/pieces")
            for i in range(8):
                if i in drop:
                    continue
                sub = s.submesh([np.where(lab == i)[0]], append=True)
                gg = g.create_group(f"piece_{i}"); gg["vertices"] = sub.vertices; gg["faces"] = sub.faces
            names.append(f"{ds}/{pot}".encode())
        f[f"data_split/{ds}/val"] = np.array(names)

write("whole.hdf5", "whole", drop=())
write("miss.hdf5", "miss", drop=(4, 6))   # two of the four top sherds: the span shrinks

def make(path, ds, whole=None, seed=7, af=False):
    return m.PointCloudDataset(split="val", data_path=path, dataset_name=ds, max_parts=20, up_axis="z",
                               anchor_free=af, presentation_seed=seed, whole_pot_path=whole)

ok = True
for af in (False, True):
    off, on = make("whole.hdf5", "whole", af=af), make("whole.hdf5", "whole", "whole.hdf5", af=af)
    same = all(off[i][k].tobytes() == on[i][k].tobytes() for i in range(2)
               for k in ("pointclouds", "pointclouds_gt", "scales", "rotations", "translations"))
    print(f"1. complete pot, anchor_free={af}: on == off byte for byte: {same}"); ok &= same

off, on, whole = make("miss.hdf5", "miss"), make("miss.hdf5", "miss", "whole.hdf5"), make("whole.hdf5", "whole")
for i in range(2):
    xo, xn, xw = off[i], on[i], whole[i]
    ppp = xn["points_per_part"][:xn["num_parts"]]; o = np.concatenate([[0], np.cumsum(ppp)])
    with h5py.File("miss.hdf5") as f:
        grp = f[xn["name"]]["pieces"]; parts = sorted(grp)
        true_ext = [np.ptp(grp[p]["vertices"][()], axis=0).max() for p in parts]
    ext_on = [np.ptp(xn["pointclouds_gt"][o[j]:o[j+1]], axis=0).max() for j in range(len(ppp))]
    ext_off = [np.ptp(xo["pointclouds_gt"][o[j]:o[j+1]], axis=0).max() for j in range(len(ppp))]
    # sampled points sit inside the sherd, so their extent is a little under the mesh's
    r_on = np.array(ext_on) * float(xn["scales"]) / np.array(true_ext)
    r_off = np.array(ext_off) * float(xn["scales"]) / np.array(true_ext)
    sw, sn, so = float(xw["scales"]), float(xn["scales"]), float(xo["scales"])
    # on: the kept sherds sit in the whole pot's frame, so `scales` is the whole pot's half-span
    # (sampled alone under its own name, so a different draw: within 2%), and each kept sherd's
    # extent in the input is its true extent over that half-span (sampled points sit just inside
    # the mesh: ratio a little under 1). off: `scales` is the kept sherds' own half-span about their own mean, which differs (here larger, the mean having moved).
    good = (r_on > 0.9).all() and (r_on <= 1.0 + 1e-6).all() and abs(sn - sw) < 0.02 * sw and abs(so - sw) > 0.05 * sw
    print(f"2. {xn['name']}: scales on {float(xn['scales']):.4f} (whole pot sampled alone {float(xw['scales']):.4f}), off {float(xo['scales']):.4f}; "
          f"input extent x scale / true extent, per kept sherd: min {r_on.min():.3f} max {r_on.max():.3f}; good {good}")
    ok &= good

for what, kw in (("unknown pot", dict(path="miss.hdf5", ds="miss", whole="other.hdf5")),
                 ("no presentation_seed", dict(path="miss.hdf5", ds="miss", whole="whole.hdf5", seed=None))):
    try:
        if what == "unknown pot":
            write("other.hdf5", "other", drop=())
            with h5py.File("other.hdf5", "a") as f:
                f.move("other/p2_d00", "other/p9_d00")
            make(kw["path"], kw["ds"], kw["whole"])[1]
        else:
            make(kw["path"], kw["ds"], kw["whole"], seed=None)
        print(f"3. {what}: NOT refused"); ok = False
    except (KeyError, ValueError) as e:
        print(f"3. {what}: refused ({type(e).__name__}: {e})")
print("ALL OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
