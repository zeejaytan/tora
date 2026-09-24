# per-sherd home counts, two-held arms; run from C:\PR\tora, arg = job id
import sys; sys.path.insert(0,'scripts')
from pathlib import Path
from own_place import score_object, SEAT_PCT
J=sys.argv[1]
for arm,held in [('held0',[0]),('held0_6',[0,6]),('held0_4',[0,4])]:
    f=Path(f'artifacts/twoheld/twoheld_{arm}_{J}/clouds/juglet_gt_sample00000.npz')
    if not f.exists(): print(arm,'missing'); continue
    _,sc=score_object(f); raw=sc['raw']; n=raw[0].n
    home=[sum(d.home_pct[s]<SEAT_PCT for d in raw) for s in range(n)]
    worst=max(d.home_pct[h] for d in raw for h in held)
    per=[sum(d.home_pct[s]<SEAT_PCT for s in range(n) if s not in held) for d in raw]
    free=n-len(held)
    print(f'{arm:8s} held={held} worst held offset {worst:.3f}% | home per sherd {home} | non-held home {sum(per)}/{free*len(raw)} | per draw {sorted(per)}')
