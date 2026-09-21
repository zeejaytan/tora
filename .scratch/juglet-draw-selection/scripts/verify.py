"""SARe-style geometric verification on saved Juglet draws (no training, no GPU).
Arm A: break-face labels from the answer key (best case for SARe's learned detector).
Arm B: no labels at all (plain proximity) - what we could run on an unknown pot today.
Both: overlap (interpenetration) filter on voxels."""
import sys, json, numpy as np
sys.path.insert(0,'scripts')
from scipy.spatial import cKDTree
from own_place import score_object, SEAT_PCT
from readout import part_slices, unit_box_scale
from pathlib import Path
npz=Path('artifacts/jugdraw/jugdraw_baseline_30130049/clouds/juglet_gt_sample00000.npz')
d=np.load(npz,allow_pickle=True); gt=d['pts_gt']; G=d['generations_pred']
sl=list(part_slices(d['points_per_part'])); K=len(sl)
MM=unit_box_scale(gt)/65.0          # data units per mm (65 mm pot)
TOL=float(sys.argv[1])*MM if len(sys.argv)>1 else 2.0*MM   # contact tolerance
VOX=2.0*MM; TAU_O=0.3; MINPTS=int(sys.argv[2]) if len(sys.argv)>2 else 10
_,sc=score_object(npz); raw=sc['raw']
# oracle break labels: points of sherd i within TOL of another sherd in the TRUE assembly
trees=[cKDTree(gt[a:b]) for a,b in sl]
F=[]
for i,(a,b) in enumerate(sl):
    m=np.zeros(b-a,bool)
    for j,(c,e) in enumerate(sl):
        if i!=j: m|=trees[j].query(gt[a:b])[0]<TOL
    F.append(m)
def vox(p): return set(map(tuple,np.floor(p/VOX).astype(int)))
def edges(P,labels):
    V=[vox(P[a:b]) for a,b in sl]; E=[]; info={}
    for i in range(K):
        for j in range(i+1,K):
            r=len(V[i]&V[j])/min(len(V[i]),len(V[j]))
            Pi=P[sl[i][0]:sl[i][1]]; Pj=P[sl[j][0]:sl[j][1]]
            if labels: Pi=Pi[F[i]]; Pj=Pj[F[j]]
            nij=(cKDTree(Pj).query(Pi)[0]<TOL).sum(); nji=(cKDTree(Pi).query(Pj)[0]<TOL).sum()
            n=min(nij,nji); info[(i,j)]=(round(r,2),int(n))
            if r<=TAU_O and n>=MINPTS: E.append((i,j))
    return E,info
def comps(E):
    par=list(range(K))
    def f(x):
        while par[x]!=x: x=par[x]
        return x
    for i,j in E: par[f(i)]=f(j)
    g={}
    for i in range(K): g.setdefault(f(i),[]).append(i)
    return [c for c in g.values() if len(c)>=2]
truth,_=edges(gt,True); truthB,_=edges(gt,False)
print(f'tol {TOL/MM:.1f} mm, vox {VOX/MM:.1f} mm, overlap max {TAU_O}, min pts {MINPTS}')
print('answer key, arm A edges:',len(truth),'| arm B edges:',len(truthB))
out={}
for arm,lab in (('A_oracle_break_labels',True),('B_no_labels',False)):
    kept_n=np.zeros(K,int); kept_home=np.zeros(K,int); rows=[]
    for t in range(20):
        E,_=edges(G[t],lab); C=comps(E); ks=sorted({s for c in C for s in c})
        home=[raw[t].home_pct[s]<SEAT_PCT for s in range(K)]
        for s in ks: kept_n[s]+=1; kept_home[s]+=home[s]
        te=[e for e in E if e in truth]
        rows.append(dict(draw=t,edges=E,true_edges=len(te),kept=ks,kept_home=[s for s in ks if home[s]],home=[s for s in range(K) if home[s]]))
    print(f'\n{arm}')
    for s in range(K): print(f'  sherd {s}: kept in {kept_n[s]:2d}/20 draws, home in {kept_home[s]:2d} of those')
    tot=kept_n[1:].sum(); good=kept_home[1:].sum()
    print(f'  non-anchor sherds kept: {tot}, of which home {good} ({100*good/max(tot,1):.0f}%)')
    out[arm]=rows
json.dump(out,open(f'artifacts/u10/verify_{sys.argv[1] if len(sys.argv)>1 else "2.0"}mm.json','w'),indent=1,default=int)

# diagnostics: score distributions, answer key vs draws
_,ig=edges(gt,True)
tn=[v[1] for k,v in ig.items() if k in truth]; fr=[v[0] for k,v in ig.items() if k in truth]
print('\nANSWER KEY true joins: contact pts min/median',min(tn),int(np.median(tn)),' overlap max',max(fr))
print('ANSWER KEY non-joins contact pts max',max(v[1] for k,v in ig.items() if k not in truth))
en=[];ov=[];ne=[]
for t in range(20):
    E,info=edges(G[t],True); ne.append(len(E))
    en+= [v[1] for v in info.values()]; ov+=[v[0] for v in info.values()]
print('DRAWS: edges passing per draw',ne)
print('DRAWS: overlap ratio pcts 50/90/max',np.percentile(ov,[50,90,100]).round(2))
print('DRAWS: contact pts pcts 50/90',np.percentile(en,[50,90]).round(0))
print('break pts per sherd',[int(f.sum()) for f in F],' pts per sherd',[b-a for a,b in sl])
