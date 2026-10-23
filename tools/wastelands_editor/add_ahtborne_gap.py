# Adds the 4 rooms the mob South routes cross between 17991 and 18040 (owner, Oct 23) to the published Wastelands layout editor, without rebuilding it:
#   python3 add_ahtborne_gap.py      (run from anywhere; edits wastelands_editor.html beside it)
# 18041 (spacer), 18039 The Ahtborne Straights, 18042, 18043 (spacers): grp 'ss' (new sea rooms, movable), the chain
# 17991 -sw- 18041 -sw- 18039 -e- 18042 -e- 18043 -e- 18040. 18039's other exits (17872, 17876, 17885, 17888: not on the map) are left off.
# Starting spots: evenly on the line from 17991 to 18040, at their spots in the owner's save (src/legacy/wl3_layout_final.json).
import sys, os, json, re, math
from collections import defaultdict
here = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.normpath(os.path.join(here, '..', '..', 'src')); sys.path[:0] = [SRC]
import maplib

DV = {1: (0, -1, 0), 2: (1, 0, 0), 4: (0, 1, 0), 8: (-1, 0, 0), 3: (1, -1, 0), 9: (-1, -1, 0), 6: (1, 1, 0), 12: (-1, 1, 0), 16: (0, 0, 1), 32: (0, 0, -1)}
DN = {1: 'n', 2: 'e', 4: 's', 8: 'w', 3: 'ne', 9: 'nw', 6: 'se', 12: 'sw', 16: 'u', 32: 'd', 0: '?'}
CHAIN = [17991, 18041, 18039, 18042, 18043, 18040]
NEW = CHAIN[1:-1]

rooms, exits = maplib.world()
isspacer = lambda v: bool(rooms[v]['flags'] & 8) and rooms[v]['area'] == ''
F = os.path.join(here, 'wastelands_editor.html'); h = open(F, encoding='utf-8').read()
m = re.search(r'const D=(\{.*?\});', h); D = json.loads(m.group(1))
byid = {r['id']: r for r in D['rooms']}
assert not set(NEW) & set(byid), 'already added'
L = json.load(open(os.path.join(SRC, 'legacy', 'wl3_layout_final.json'))); sp = dict(zip(L['ids'], zip(L['xs'], L['ys'])))
a, b = sp[CHAIN[0]], sp[CHAIN[-1]]
START = {v: (round(a[0] + (b[0] - a[0]) * (i + 1) / (len(NEW) + 1), 2), round(a[1] + (b[1] - a[1]) * (i + 1) / (len(NEW) + 1), 2)) for i, v in enumerate(NEW)}
S = set(NEW); V = S | set(byid)
FLATP = {frozenset((v, e['to'])) for v, l in exits.items() for e in l if e['dir'] in DV and e['dir'] not in (16, 32) and e['to'] != v}
use = lambda v, e: e['dir'] in DV and e['to'] != v and not (e['dir'] in (16, 32) and frozenset((v, e['to'])) in FLATP)

def exl(v, keep):
    res = []
    for e in exits.get(v, []):
        r = rooms.get(e['to'])
        if not r: continue
        ok = keep(e['to'])
        why = '' if ok else ' · left off'
        if ok and not use(v, e) and e['dir'] in (16, 32): why = ' · ignored (flat exit used)'
        res.append(f"{DN.get(e['dir'], e['name'])} → {r['name'] or 'spacer room'}" + (f" ({r['area']})" if r['area'] and r['area'] != rooms[v]['area'] else '') + why)
    return res

for v in NEW:
    r = rooms[v]; s = isspacer(v); x, y = START[v]
    D['rooms'].append(dict(id=v, name='' if s else r['name'], terrain='' if s else r['terrain'], void=s, lvl=0, area='WL', grp='ss',
                           ga=r['area'] or ('spacer' if s else 'unnamed'), x=x, y=y, x0=x, y0=y, ex=exl(v, lambda t: t in V)))
nfix = []
for v, r in byid.items():                                                               # the joined rooms' hover lists: their exits here are shown now
    if 'ex' in r and any(e['to'] in S for e in exits.get(v, [])): r['ex'] = exl(v, lambda t: t in V); nfix.append(v)
pair = {}
for v in V:
    for e in exits.get(v, []):
        t = e['to']
        if t not in V or t == v or not (v in S or t in S) or not use(v, e) and e['dir'] in (16, 32): continue
        k = (min(v, t), max(v, t)); f = pair.setdefault(k, [False, False, False]); f[0 if v == k[0] else 1] = True
        if e['dir'] not in (16, 32): f[2] = True
new = [[a_, b_, 'two' if (f and r and flat) else ('one' if flat else 'ud')] for (a_, b_), (f, r, flat) in sorted(pair.items())]
D['edges'] += new
h = h[:m.start(1)] + json.dumps(D, separators=(',', ':')) + h[m.end(1):]
def sub(x, y):
    global h
    assert h.count(x) == 1, x; h = h.replace(x, y)
sub('<span>New sea room (movable)</span>', '<span>New sea room (movable). Added Oct 23: 18041, The Ahtborne Straights 18039, 18042 and 18043, between 17991 and 18040 (the mob routes go through them); they start on the line between those two</span>')
open(F, 'w', encoding='utf-8').write(h)
allp = {**{v: sp.get(v, (r['x'], r['y'])) for v, r in byid.items()}}
print('rooms', START, '| edges', new, '| hover lists updated', nfix,
      '| nearest other room', {v: round(min(math.dist(START[v], p) for u, p in allp.items() if u not in CHAIN), 2) for v in NEW})
