import sys,numpy as np,matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
sys.path.insert(0,'scripts'); from readout import part_slices; from own_place import score_object, SEAT_PCT
from pathlib import Path
J=sys.argv[1]; arm='held0_6'; a=[0,6]
npz=Path(f'artifacts/twoheld/twoheld_{arm}_{J}/clouds/juglet_gt_sample00000.npz')
d=np.load(npz,allow_pickle=True); gt=d['pts_gt']; G=d['generations_pred']; sl=list(part_slices(d['points_per_part']))
_,sc=score_object(npz); raw=sc['raw']
n=[sum(x.home_pct[s]<SEAT_PCT for s in range(9)) for x in raw]
t=int(np.argmax(n)); print('best attempt',t,'home',n[t],'/9')
print('per-sherd offset %  :', ' '.join(f'{s}:{raw[t].home_pct[s]:.1f}' for s in range(9)))
fig=plt.figure(figsize=(16,6))
for c,(el,az) in enumerate([(10,0),(10,90),(10,180),(80,0)]):
    ax=fig.add_subplot(1,4,c+1,projection='3d')
    for s,(p,q) in enumerate(sl):
        P=G[t,p:q]; home=raw[t].home_pct[s]<SEAT_PCT
        col='tab:blue' if s in a else ('tab:green' if home else 'tab:red')
        if not home: ax.scatter(*gt[p:q].T,s=0.4,c='0.75',alpha=0.35)
        ax.scatter(*P.T,s=1.5,c=col)
        ax.text(*P.mean(0),str(s),fontsize=9,weight='bold')
    ax.view_init(el,az); ax.set_box_aspect(np.ptp(gt,0)); ax.set_axis_off()
    lo=gt.min(0);hi=gt.max(0);m=(hi-lo)*0.5
    ax.set_xlim(lo[0]-m[0],hi[0]+m[0]);ax.set_ylim(lo[1]-m[1],hi[1]+m[1]);ax.set_zlim(lo[2]-m[2],hi[2]+m[2])
    if c==0: ax.set_title(f'{arm} best attempt {t}: {n[t]}/9 home. blue = held (0 neck, 6 base), green = at home',fontsize=9,loc='left')
plt.tight_layout(); plt.savefig(f'artifacts/twoheld/two_held_best_{J}.png',dpi=95); print('saved')
