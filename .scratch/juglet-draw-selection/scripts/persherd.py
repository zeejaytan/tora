import sys,runpy,io,contextlib,numpy as np
HERE=sys.path[0]
for tol,mp in [(2.0,30),(1.0,5)]:
    sys.argv=['v',str(tol),str(mp)]
    with contextlib.redirect_stdout(io.StringIO()): g=runpy.run_path(HERE+'/verify.py')
    raw,G,K,SEAT=g['raw'],g['G'],g['K'],g['SEAT_PCT']
    kept=np.zeros(K,int); good=np.zeros(K,int); groups=[]
    for t in range(20):
        E,_=g['edges'](G[t],True); C=g['comps'](E); c0=next((c for c in C if 0 in c),[0])
        groups.append(sorted(c0))
        for s in c0: kept[s]+=1; good[s]+=raw[t].home_pct[s]<SEAT
    print(f'tol {tol} mm, min {mp}:', ' '.join(f's{s}:{kept[s]}({good[s]} home)' for s in range(1,K)))
    print('   anchor group per draw:',groups)
