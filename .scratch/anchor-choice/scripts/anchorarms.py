# per-sherd home counts for the anchor-choice arms; run from C:\PR\tora
import sys; sys.path.insert(0,'scripts')
from pathlib import Path
from own_place import score_object, SEAT_PCT
J=sys.argv[1]
NB={0:[1,2,3,7,8],6:[3,4,5,8],4:[2,5,6,7]}
base=[20,15,3,4,2,2,0,14,0]
print('job 30130049 baseline  ', base)
for arm,a in [('anchor0',0),('anchor6',6),('anchor4',4)]:
    f=Path(f'artifacts/anchor/anchor_{arm}_{J}/clouds/juglet_gt_sample00000.npz')
    if not f.exists(): print(arm,'missing'); continue
    _,sc=score_object(f); raw=sc['raw']
    home=[sum(d.home_pct[s]<SEAT_PCT for d in raw) for s in range(raw[0].n)]
    held=max(d.home_pct[a] for d in raw)
    print(f'{arm:8s} held={a} worst held-sherd offset {held:.3f}%  ',home,
          ' neighbours',{s:home[s] for s in NB[a]}, ' total non-held', sum(home)-home[a])
