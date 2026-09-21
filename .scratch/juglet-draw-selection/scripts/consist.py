import numpy as np
d=np.load('artifacts/jugdraw/jugdraw_baseline_30130049/clouds/juglet_gt_sample00000.npz',allow_pickle=True)
gt=d['pts_gt']; G=d['generations_pred']; ppp=d['points_per_part']
ppp=[int(x) for x in ppp if x>0]; cuts=np.cumsum([0]+ppp)
ext=np.linalg.norm(gt.max(0)-gt.min(0)); print('sherds',len(ppp),'pot diag',ext)
TOL=0.071  # fraction of pot size, same bar as own-place scorer (approx, mean pt distance)
for s in range(len(ppp)):
    a,b=cuts[s],cuts[s+1]; P=G[:,a:b]  # 20 x n x 3
    D=np.array([[np.linalg.norm(P[i]-P[j],axis=1).mean() for j in range(20)] for i in range(20)])/ext
    nb=(D<TOL).sum(1)            # neighbours incl. self
    m=nb.argmax()                # modal draw
    gtd=np.linalg.norm(P[m]-gt[a:b],axis=1).mean()/ext
    home=(np.linalg.norm(P-gt[a:b],axis=2).mean(1)/ext<TOL).sum()
    print(f'sherd {s}: agree {nb[m]:2d}/20  modal-draw off-home {gtd*100:5.1f}%  draws home(meanpt) {home:2d}')
