# Adds the Azure Sea rooms along Otherland's east coast (owner, Oct 22: "from the iceberg down to the southern tip of Otherland", ending with the
# room that leads to the Northern Plains) to the published Otherland layout editor, without rebuilding it:
#   python3 add_azure_east.py      (run from anywhere; edits otherland_editor.html beside it)
# The rooms (grp 'az', area 'OL', movable): every room not on the map, in the Azure Sea or unnamed, reached from Among the Icebergs (6180/6166)
# through such rooms, then dead-end spacer stubs pruned; + the way out at the south end: 15250 'Adrift off the Coast' -d-> 15255 (Blood Sea,
# same name) -s-> 15606 'Off the Northern Coast' (Blood Sea), whose exits to the Grey Beach (Northern Plains 4407, 4408) are left off.
# Their exits to rooms in the editor (Otherland, 6180, 6166) are shown; an up/down exit to the same room as a flat exit is ignored (as the editor).
# Starting spots: editor_spread.spread grown from the editor rooms they join, where the owner's save (src/legacy/ol_layout_final.json) has them.
import sys, os, json, re, math
from collections import deque, defaultdict
here = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.normpath(os.path.join(here, '..', '..', 'src')); sys.path[:0] = [SRC]
import maplib, editor_spread as ES

DV = {1: (0, -1, 0), 2: (1, 0, 0), 4: (0, 1, 0), 8: (-1, 0, 0), 3: (1, -1, 0), 9: (-1, -1, 0), 6: (1, 1, 0), 12: (-1, 1, 0), 16: (0, 0, 1), 32: (0, 0, -1)}
DN = {1: 'n', 2: 'e', 4: 's', 8: 'w', 3: 'ne', 9: 'nw', 6: 'se', 12: 'sw', 16: 'u', 32: 'd', 0: '?'}
END = [15255, 15606]
STEP = float(os.environ.get('STEP', 2.0))                                       # (as the editor's own rooms)

rooms, exits = maplib.world()
isspacer = lambda v: bool(rooms[v]['flags'] & 8) and rooms[v]['area'] == ''
F = os.path.join(here, 'otherland_editor.html'); h = open(F, encoding='utf-8').read()
m = re.search(r'const D=(\{.*?\});\n', h); D = json.loads(m.group(1))
byid = {r['id']: r for r in D['rooms']}
assert not any(r.get('grp') == 'az' for r in D['rooms']), 'already added'
B = json.load(open(os.path.join(SRC, 'base', 'map.json'))); track = B['wild'].get('track', {})
onmap = lambda v: str(v) in B['room_pos'] or f'cx{v}' in track

# ---- the rooms ----
nb = defaultdict(set)
for v, l in exits.items():
    for e in l: nb[v].add(e['to']); nb[e['to']].add(v)
S = {6179, 6167}; q = deque(S)
while q:
    v = q.popleft()
    for e in exits.get(v, []):
        t = e['to']
        if t in rooms and t not in S and t not in byid and not onmap(t) and rooms[t]['area'] in ('Azure Sea', ''): S.add(t); q.append(t)
S |= set(END)
cand = len(S)
while True:                                                                              # dead-end spacer stubs
    leaf = {s for s in S if isspacer(s) and len({u for u in nb[s] if u in S or u in byid} - {s}) <= 1}
    if not leaf: break
    S -= leaf
V = S | set(byid)
FLATP = {frozenset((v, e['to'])) for v, l in exits.items() for e in l if e['dir'] in DV and e['dir'] not in (16, 32) and e['to'] != v}
use = lambda v, e: e['dir'] in DV and e['to'] != v and not (e['dir'] in (16, 32) and frozenset((v, e['to'])) in FLATP)
rev = defaultdict(list)
for v, l in exits.items():
    for e in l: rev[e['to']].append(v)
def links(v):
    res = [(e['to'], DV[e['dir']]) for e in exits.get(v, []) if use(v, e) and e['to'] in V and (v in S or e['to'] in S)]
    for u in rev[v]:
        if u not in V or not (u in S or v in S): continue
        for e in exits.get(u, []):
            if e['to'] == v and use(u, e): d = DV[e['dir']]; res.append((u, (-d[0], -d[1], -d[2])))
    return res

# ---- starting spots ----
L = json.load(open(os.path.join(SRC, 'legacy', 'ol_layout_final.json'))); spos = dict(zip(L['ids'], zip(L['xs'], L['ys'])))
fixed = {v: (spos[v] if v in spos else (r['x'], r['y'])) for v, r in byid.items()}
roots = sorted({t for v in S for t, _ in links(v) if t in fixed}, key=lambda t: (t not in (6180, 6166), fixed[t][1]))
# the drawn land is kept clear (they are sea rooms): a blocker every LANDSTEP over it (land, evenodd, + snow, less the sea filled over it)
from matplotlib.path import Path
import numpy as np
geo = B['wild']['geo']; LANDSTEP = 0.8
xs0 = [p[0] for p in fixed.values()]; ys0 = [p[1] for p in fixed.values()]
gx, gy = np.meshgrid(np.arange(min(xs0) - 10, max(xs0) + 30, LANDSTEP), np.arange(min(ys0) - 10, max(ys0) + 30, LANDSTEP)); P = np.c_[gx.ravel(), gy.ravel()]
inside = lambda polys: [Path(p).contains_points(P) for p in polys if len(p) > 2]
land = np.logical_xor.reduce(inside(geo['land'])) | np.logical_or.reduce(inside(geo['snow']))
land &= ~np.logical_or.reduce(inside(geo['seafill']))
blk = {-(i + 1): tuple(p) for i, p in enumerate(P[land])}
start = ES.spread(S, lambda v: [(t, d) for t, d in links(v) if t in S or t in fixed], {**fixed, **blk}, roots, step=STEP)
onland = sum(1 for v in S if land[np.argmin(np.hypot(P[:, 0] - start[v][0], P[:, 1] - start[v][1]))])
rep = ES.report(start, fixed, links, step=STEP)

# ---- into the editor ----
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
piece = len(D['secs'])
D['secs'].append(dict(i=piece, name='Azure Sea, east coast (added Oct 22)', n=len(S)))
for v in sorted(S):
    r = rooms[v]; sp = isspacer(v); x, y = start[v]
    D['rooms'].append(dict(id=v, name='' if sp else r['name'], terrain='' if sp else r['terrain'], void=sp, lvl=0, area='OL', grp='az', piece=piece,
                           ga=r['area'] or ('spacer' if sp else 'unnamed'), x=x, y=y, x0=x, y0=y, ex=exl(v, lambda t: t in V)))
nfix = 0
for v, r in byid.items():                                                               # the joined editor rooms' hover lists: their exits here are shown now
    if 'ex' in r and any(t in S for t in nb[v]):
        old = r['ex']; new = exl(v, lambda t: True)
        if len(old) == len(new): r['ex'] = [n if (o.endswith(' · left off') and not n.endswith(' · left off') and t in S) else o for o, n, t in zip(old, new, [e['to'] for e in exits.get(v, []) if e['to'] in rooms])]; nfix += 1
pair = {}
for v in V:
    for e in exits.get(v, []):
        t = e['to']
        if t not in V or t == v or not (v in S or t in S) or not use(v, e) and e['dir'] in (16, 32): continue
        k = (min(v, t), max(v, t)); f = pair.setdefault(k, [False, False, False]); f[0 if v == k[0] else 1] = True
        if e['dir'] not in (16, 32): f[2] = True
for (a, b), f in pair.items():
    if f[2] and not (f[0] and f[1]):
        f[0] = f[0] or any(e['to'] == b for e in exits.get(a, [])); f[1] = f[1] or any(e['to'] == a for e in exits.get(b, []))
new = [[a, b, 'two' if (f and r and flat) else ('one' if flat else 'ud')] for (a, b), (f, r, flat) in sorted(pair.items())]
D['edges'] += new
D['audit']['az'] = len(S)
offc = {a: int(n) for a, n in (x.rsplit(' ', 1) for x in D['audit']['off'].split(', '))}                # Otherland's exits left off: less those shown now
for v, r in byid.items():
    if r.get('grp') in ('ol', 'an'):
        for e in exits.get(v, []):
            if e['to'] in S: k = rooms[e['to']]['area'] or 'unnamed/spacer rooms'; offc[k] -= 1
D['audit']['off'] = ', '.join(f'{a} {n}' for a, n in sorted(offc.items()) if n)
h = h[:m.start(1)] + json.dumps(D, separators=(',', ':')) + h[m.end(1):]

AZC = '#3FC1A6'
def sub(a, b):
    global h
    assert h.count(a) == 1, a; h = h.replace(a, b)
sub('.nd.un rect,.nd.un circle.shape{stroke:#6FC3E8}', '.nd.un rect,.nd.un circle.shape{stroke:#6FC3E8}\n.nd.az rect,.nd.az circle.shape{stroke:' + AZC + '}')
sub('<button id="selUn">Select the unlocked map rooms</button>', '<button id="selUn">Select the unlocked map rooms</button><button id="selAz">Select the Azure Sea rooms</button>')
sub('Afloat on the Azure Sea 6650 and 15410-15418 (movable, start at their spots on the map)</span>\n',
    'Afloat on the Azure Sea 6650 and 15410-15418 (movable, start at their spots on the map)</span>\n'
    f'    <i style="background:var(--t-Water);border:2px solid {AZC}"></i><span>Added Oct 22: the Azure Sea along Otherland\'s east coast, from the Iceberg (6179, 6167) south to 15250, then 15255 and 15606 (Blood Sea), which leads on to the Grey Beach in the Northern Plains (that exit left off). Movable; they start next to the rooms they join</span>\n')
sub("$('selUn').onclick=()=>selGrp('un');", "$('selUn').onclick=()=>selGrp('un');$('selAz').onclick=()=>selGrp('az');")
sub("unlocked map rooms ${a.un} ·", "unlocked map rooms ${a.un} · added Azure Sea rooms ${a.az} ·")
open(F, 'w', encoding='utf-8').write(h)

named = [v for v in S if not isspacer(v)]
print('rooms', len(S), '(found', cand, ', dead-end spacers left off', cand - len(S), ') | named/unnamed', len(named), '| spacers', len(S) - len(named), '| edges', len(new),
      '| to editor rooms', sorted({t for v in S for t, _ in links(v) if t in byid}), '| hover lists updated', nfix)
print('roots', roots[:4], '... | report (close, far, wrong, thru):', rep, '| starting on land', onland, '| land blockers', len(blk))
xs = [p[0] for p in start.values()]; ys = [p[1] for p in start.values()]
print('box x %.1f..%.1f y %.1f..%.1f' % (min(xs), max(xs), min(ys), max(ys)), '| nearest editor room not joined %.2f' % min(math.dist(start[v], p) for v in S for u, p in fixed.items() if u not in {t for t, _ in links(v)}))
json.dump({str(v): start[v] for v in sorted(S)}, open(os.path.join(os.environ.get('OUT', '/tmp'), 'az_start.json'), 'w'))
