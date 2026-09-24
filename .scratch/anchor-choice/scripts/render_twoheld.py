import sys,numpy as np,matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
sys.path.insert(0,'scripts'); from readout import part_slices; from own_place import score_object, SEAT_PCT
from pathlib import Path
J=sys.argv[1]; fig=plt.figure(figsize=(14,16))
for r,(arm,a) in enumerate([('held0',[0]),('held0_6',[0,6]),('held0_4',[0,4])]):
    npz=Path(f'artifacts/twoheld/twoheld_{arm}_{J}/clouds/juglet_gt_sample00000.npz')
    d=np.load(npz,allow_pickle=True); gt=d['pts_gt']; G=d['generations_pred']; sl=list(part_slices(d['points_per_part']))
    _,sc=score_object(npz); raw=sc['raw']
    n=[sum(x.home_pct[s]<SEAT_PCT for s in range(9)) for x in raw]; med=np.median(n)
    t=int(np.argmin([abs(v-med) for v in n]))
    for c,(el,az) in enumerate([(10,0),(10,90),(10,180)]):
        ax=fig.add_subplot(3,3,3*r+c+1,projection='3d')
        for s,(p,q) in enumerate(sl):
            P=G[t,p:q]; home=raw[t].home_pct[s]<SEAT_PCT
            col='tab:blue' if s in a else ('tab:green' if home else 'tab:red')
            if not home: ax.scatter(*gt[p:q].T,s=0.4,c='0.75',alpha=0.35)
            ax.scatter(*P.T,s=1.5,c=col)
            ax.text(*P.mean(0),str(s),fontsize=10,weight='bold')
        ax.view_init(el,az); ax.set_box_aspect(np.ptp(gt,0)); ax.set_axis_off()
        lo=gt.min(0);hi=gt.max(0);m=(hi-lo)*0.6
        ax.set_xlim(lo[0]-m[0],hi[0]+m[0]);ax.set_ylim(lo[1]-m[1],hi[1]+m[1]);ax.set_zlim(lo[2]-m[2],hi[2]+m[2])
        if c==0: ax.set_title(f'{arm}: sherd {a} held (blue). Attempt {t}, {n[t]}/9 home (median of 20 = {med:.0f})\ngreen = at home, red = misplaced, grey = where red sherds belong',fontsize=9,loc='left')
plt.tight_layout(); plt.savefig('artifacts/twoheld/two_held_'+J+'.png',dpi=90); print('ok')
