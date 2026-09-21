import sys,glob,numpy as np; sys.path.insert(0,'scripts')
from scipy.spatial import cKDTree
from own_place import score_object, SEAT_PCT
from readout import part_slices, unit_box_scale
from pathlib import Path
rows=[]
FILES=sorted(glob.glob(sys.argv[1]+"/clouds/*.npz"))
for f in FILES:
    d=np.load(f,allow_pickle=True); gt=d['pts_gt']; sl=list(part_slices(d['points_per_part']))
    L=unit_box_scale(gt); TOL=0.01*L   # 1% of pot size as contact tolerance
    _,sc=score_object(Path(f)); raw=sc['raw']; n=len(raw)
    anc=raw[0].anchor; ta=cKDTree(gt[sl[anc][0]:sl[anc][1]])
    for s,(a,b) in enumerate(sl):
        if s==anc: continue
        near=ta.query(gt[a:b])[0]<TOL
        # its whole edge: points near ANY other sherd
        allo=np.vstack([gt[c:e] for j,(c,e) in enumerate(sl) if j!=s]); edge=cKDTree(allo).query(gt[a:b])[0]<TOL
        rows.append((Path(f).stem, s, near.sum()/max(edge.sum(),1), near.any(), (b-a)/len(gt), np.mean([r.home_pct[s]<SEAT_PCT for r in raw])))
R=np.array([(r[2],r[3],r[4],r[5]) for r in rows],float); np.save("artifacts/u10/anchorcontact_ceramarm.npy",R); np.save("artifacts/u10/anchorcontact_ceramarm_names.npy",np.array([(r[0],r[1]) for r in rows]))
print('objects',len(set(r[0] for r in rows)),'non-anchor sherds',len(R))
t=R[:,1]>0
print(f'touch anchor: {t.sum()} sherds, home rate {R[t,3].mean():.2f} | no touch: {(~t).sum()} sherds, home rate {R[~t,3].mean():.2f}')
from scipy.stats import spearmanr
print('spearman home vs share-of-edge-on-anchor: rho=%.2f p=%.3g'%spearmanr(R[:,0],R[:,3]))
print('spearman home vs size: rho=%.2f p=%.3g'%spearmanr(R[:,2],R[:,3]))
for lo,hi in [(0,0.001),(0.001,0.25),(0.25,0.5),(0.5,1.01)]:
    m=(R[:,0]>=lo)&(R[:,0]<hi); print(f'  share on anchor {lo:.2f}-{hi:.2f}: {m.sum():3d} sherds, home rate {R[m,3].mean() if m.any() else float("nan"):.2f}')
sz=R[:,2]; q=np.quantile(sz,[0,1/3,2/3,1]); q[-1]+=1
print('\nsize tercile x touches anchor -> home rate (n)')
for k in range(3):
    m=(sz>=q[k])&(sz<q[k+1])
    print(f'  size {q[k]*100:4.1f}-{q[k+1]*100:4.1f}% of pot: touch {R[m&t,3].mean():.2f} ({(m&t).sum()})   no touch {R[m&~t,3].mean() if (m&~t).any() else float("nan"):.2f} ({(m&~t).sum()})')
pots={}
for r in rows:
    pot=int(r[0][-5:])//5 if False else None
