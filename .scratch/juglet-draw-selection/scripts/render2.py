import sys,numpy as np,matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
sys.path.insert(0,'scripts'); from readout import part_slices; from own_place import score_object, SEAT_PCT
from pathlib import Path
npz=Path('artifacts/jugdraw/jugdraw_baseline_30130049/clouds/juglet_gt_sample00000.npz')
d=np.load(npz,allow_pickle=True); gt=d['pts_gt']; G=d['generations_pred']; sl=list(part_slices(d['points_per_part']))
_,sc=score_object(npz); raw=sc['raw']
cases=[(9,[0,7],'attempt 9: check keeps {0,7}'),(14,[0,3,4,5,6,7],'attempt 14: check keeps {0,3,4,5,6,7}')]
fig=plt.figure(figsize=(13,12))
for r,(t,keep,title) in enumerate(cases):
    for c,(el,az) in enumerate([(15,0),(15,90),(80,0)]):
        ax=fig.add_subplot(2,3,3*r+c+1,projection='3d')
        for s,(a,b) in enumerate(sl):
            P=G[t,a:b]
            if s not in keep: ax.scatter(*P.T,s=0.5,c='0.8',alpha=0.4); continue
            home=raw[t].home_pct[s]<SEAT_PCT
            col='tab:blue' if s==0 else ('tab:green' if home else 'tab:red')
            ax.scatter(*P.T,s=2,c=col)
            if not home: ax.scatter(*gt[a:b].T,s=1,c='k',alpha=0.5)
            ax.text(*P.mean(0),str(s),fontsize=9,weight='bold')
        ax.view_init(el,az); ax.set_box_aspect(np.ptp(gt,0)); ax.set_axis_off()
        if c==0: ax.set_title(title+'\nblue=fixed sherd, green=kept & right, red=kept & wrong (black=its true home), grey=not kept',fontsize=8,loc='left')
plt.tight_layout(); plt.savefig('artifacts/u10/verify_kept_groups.png',dpi=100)
