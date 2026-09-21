import sys, json, numpy as np
sys.path.insert(0,'scripts')
from scipy.spatial import cKDTree
from own_place import SEAT_PCT, pct, score_object, part_slices
from readout import unit_box_scale
from pathlib import Path
npz=Path('artifacts/jugdraw/jugdraw_baseline_30130049/clouds/juglet_gt_sample00000.npz')
d=np.load(npz,allow_pickle=True); gt=d['pts_gt']; G=d['generations_pred']
sl=list(part_slices(d['points_per_part']))
k=unit_box_scale(gt); print("box",k)
gt=gt/k; G=G/k
_,sc=score_object(npz); raw=sc['raw']
def cd(x,y):
    a,_=cKDTree(y).query(x); b,_=cKDTree(x).query(y); return (a**2).mean()+(b**2).mean()
res={}
for s,(a,b) in enumerate(sl):
    P=G[:,a:b]
    D=np.array([[pct(cd(P[i],P[j])) for j in range(20)] for i in range(20)])
    nb=(D<SEAT_PCT).sum(1); m=int(nb.argmax())
    home=[raw[t].home_pct[s] for t in range(20)]
    print(f'sherd {s}: agree {nb[m]:2d}/20 | modal draw {raw[m].home_pct[s]:5.1f}% from home | home in {sum(h<SEAT_PCT for h in home):2d}/20 draws')
    res[s]=dict(agree=int(nb[m]),modal=m,modal_off=raw[m].home_pct[s])
json.dump(res,open('artifacts/u10/consistency_baseline_30130049.json','w'),indent=1)
