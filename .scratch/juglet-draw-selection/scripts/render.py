import sys, json, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
sys.path.insert(0,'scripts'); from readout import part_slices
d=np.load('artifacts/jugdraw/jugdraw_baseline_30130049/clouds/juglet_gt_sample00000.npz',allow_pickle=True)
gt=d['pts_gt']; G=d['generations_pred']; sl=list(part_slices(d['points_per_part']))
res=json.load(open('artifacts/u10/consistency_baseline_30130049.json'))
show=[1,7,6,4]; views=[(15,0),(15,90)]
fig=plt.figure(figsize=(12,11))
for r,s in enumerate(show):
    a,b=sl[s]; m=res[str(s)]['modal']; P=G[m,a:b]
    for c,(el,az) in enumerate(views):
        ax=fig.add_subplot(4,2,2*r+c+1,projection='3d')
        ax.scatter(*gt.T,s=0.3,c='0.8',alpha=0.4)
        ax.scatter(*gt[a:b].T,s=2,c='k',label='true home')
        ax.scatter(*P.T,s=2,c='tab:red' if s in (4,6) else 'tab:green',label=f'attempt {m} (agrees {res[str(s)]["agree"]}/20)')
        ax.view_init(el,az); ax.set_box_aspect(np.ptp(gt,0)); ax.set_axis_off()
        if c==0: ax.set_title(f'sherd {s}: most-agreed placement, {res[str(s)]["modal_off"]:.1f}% of pot size from home',fontsize=9); ax.legend(fontsize=7,loc='lower left')
plt.tight_layout(); plt.savefig('artifacts/u10/consistency_modal_placements.png',dpi=110)
