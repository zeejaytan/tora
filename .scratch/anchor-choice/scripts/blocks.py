# is the far block assembled correctly inside itself, just misplaced as a whole?
import sys; sys.path.insert(0,'scripts')
import numpy as np
from pathlib import Path
from own_place import SEAT_PCT
from readout import unit_box_scale
J='30917498'
def kabsch(P,Q):
    mp,mq=P.mean(0),Q.mean(0); H=(P-mp).T@(Q-mq); U,S,Vt=np.linalg.svd(H)
    d=np.sign(np.linalg.det(Vt.T@U.T)); D=np.diag([1,1,d]); R=Vt.T@D@U.T
    return (R@(P-mp).T).T+mq
for arm,block in [('anchor0',[0,1,7]),('anchor6',[4,5,6]),('anchor4',[4,5,6])]:
    d=np.load(f'artifacts/anchor/anchor_{arm}_{J}/clouds/juglet_gt_sample00000.npz',allow_pickle=True)
    gt=d['pts_gt']; G=d['generations_pred']; ppp=d['points_per_part']
    off=np.concatenate([[0],np.cumsum(ppp)]); k=unit_box_scale(gt) if callable(unit_box_scale) else 1
    idx=np.concatenate([np.arange(off[s],off[s+1]) for s in block])
    ok=[];res=[]
    for t in range(len(G)):
        A=kabsch(G[t][idx],gt[idx])
        per=[np.sqrt(((A[(idx>=off[s])&(idx<off[s+1])]-gt[off[s]:off[s+1]])**2).sum(1)).mean()/k*100 for s in block]
        ok.append(sum(p<SEAT_PCT for p in per)); res.append(np.median(per))
    print(f'{arm} block {block}: after moving the block as one piece, sherds home per draw {ok}; median offset {np.median(res):.1f}% of pot')
