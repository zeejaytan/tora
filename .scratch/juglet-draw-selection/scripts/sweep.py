import sys,runpy,io,contextlib,numpy as np
HERE=sys.path[0]
for tol,mp in [(2.0,10),(1.0,5),(1.0,10),(2.0,20),(2.0,30),(3.0,30)]:
    sys.argv=['v',str(tol),str(mp)]
    with contextlib.redirect_stdout(io.StringIO()): g=runpy.run_path(HERE+'/verify.py')
    raw,G,K,truth,edges,SEAT=g['raw'],g['G'],g['K'],g['truth'],g['edges'],g['SEAT_PCT']
    ok=tp=fp=0; keptgood=kept=0
    for t in range(20):
        E,_=g['edges'](G[t],True); home=[raw[t].home_pct[s]<SEAT for s in range(K)]
        for (i,j) in E:
            if (i,j) in truth and home[i] and home[j]: ok+=1
            elif (i,j) in truth: tp+=1
            else: fp+=1
        # SARe keeps components; here: component containing the anchor
        C=g['comps'](E); c0=next((c for c in C if 0 in c),[0])
        kept+=len(c0)-1; keptgood+=sum(home[s] for s in c0 if s)
    print(f'tol {tol} mm minpts {mp:2d} | answer-key joins found {len(truth):2d}/18 | passed edges over 20 draws: real join, both home {ok:3d}; real join, misplaced {tp:3d}; not a join {fp:3d} | anchor group: {kept} non-anchor sherds kept, {keptgood} home')
