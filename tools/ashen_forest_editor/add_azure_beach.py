# Adds the Azure Sea rooms along the Ashen Forest beach (owner, Oct 23: "additional rooms in my map from the Azure Sea area that are connected to
# the rooms along the beach") to the published Ashen Forest layout editor, without rebuilding it:
#   python3 add_azure_beach.py      (run from anywhere; edits ashen_forest_editor.html beside it)
# The rooms (area 'AZ', movable): every room not on the map and not in the editor, in the Azure Sea or unnamed, reached from the editor's rooms
# through such rooms, then dead-end spacer stubs pruned. Their exits to rooms elsewhere (Graphical, rooms already on the map) are left off.
# Starting spots: editor_spread.spread grown from the editor rooms they join, where the owner's save (src/legacy/ashen_layout_final.json) has them.
import sys, os, json, re, math
from collections import deque, defaultdict
here = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.normpath(os.path.join(here, '..', '..', 'src')); sys.path[:0] = [SRC]
import maplib, editor_spread as ES

DV = {1: (0, -1, 0), 2: (1, 0, 0), 4: (0, 1, 0), 8: (-1, 0, 0), 3: (1, -1, 0), 9: (-1, -1, 0), 6: (1, 1, 0), 12: (-1, 1, 0), 16: (0, 0, 1), 32: (0, 0, -1)}
DN = {1: 'n', 2: 'e', 4: 's', 8: 'w', 3: 'ne', 9: 'nw', 6: 'se', 12: 'sw', 16: 'u', 32: 'd', 0: '?'}
STEP = float(os.environ.get('STEP', 1.0))                                       # (as the editor's own rooms)

rooms, exits = maplib.world()
isspacer = lambda v: bool(rooms[v]['flags'] & 8) and rooms[v]['area'] == ''
F = os.path.join(here, 'ashen_forest_editor.html'); h = open(F, encoding='utf-8').read()
m = re.search(r'const D=(\{.*?\});\n', h); D = json.loads(m.group(1))
byid = {r['id']: r for r in D['rooms']}
assert not any(r.get('area') == 'AZ' for r in D['rooms']), 'already added'
B = json.load(open(os.path.join(SRC, 'base', 'map.json'))); track = B['wild'].get('track', {})
onmap = lambda v: str(v) in B['room_pos'] or f'cx{v}' in track

# ---- the rooms ----
nb = defaultdict(set)
for v, l in exits.items():
    for e in l: nb[v].add(e['to']); nb[e['to']].add(v)
ok = lambda t: t in rooms and t not in byid and not onmap(t) and rooms[t]['area'] in ('Azure Sea', '')
S = {e['to'] for v in byid for e in exits.get(v, []) if ok(e['to']) and rooms[e['to']]['area'] == 'Azure Sea'}
q = deque(S)
while q:
    v = q.popleft()
    for e in exits.get(v, []):
        t = e['to']
        if t not in S and ok(t): S.add(t); q.append(t)
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
L = json.load(open(os.path.join(SRC, 'legacy', 'ashen_layout_final.json'))); spos = dict(zip(L['ids'], zip(L['xs'], L['ys'])))
fixed = {v: (spos[v] if v in spos else (r['x'], r['y'])) for v, r in byid.items()}
roots = sorted({t for v in S for t, _ in links(v) if t in fixed}, key=lambda t: fixed[t][1])
# Starting spots (owner, Oct 23: "lay them out based on their east/west connections to shore and ignore their other connections"): grown out
# from the editor's rooms along e/w exits only, one step east or west at the same height; a spot already taken: the next free one further along.
EW = {2: 1, 8: -1}
start = {}; allp = dict(fixed)
taken = lambda p: any(math.dist(p, q) < 0.95 * STEP for q in allp.values())
for ways in ((1,), (1, -1)):                                                                 # eastward from the shore first; westward only for what's left
    q = deque(sorted([t for t in allp if t in roots or t in start], key=lambda t: allp[t][1]))
    while q:
        v = q.popleft()
        for t, d in [(e['to'], EW[e['dir']]) for e in exits.get(v, []) if e['dir'] in EW] + [(u, -EW[e['dir']]) for u in rev[v] for e in exits.get(u, []) if e['to'] == v and e['dir'] in EW]:
            if t not in S or t in start or d not in ways: continue
            p = [allp[v][0] + d * STEP, allp[v][1]]
            while taken(p): p[0] += d * STEP
            start[t] = p; allp[t] = p; q.append(t)
unplaced = sorted(S - set(start))
for v in unplaced:                                                                            # (no e/w way to the shore: east of the rest)
    p = [max(x for x, _ in allp.values()) + STEP, sum(fixed[t][1] for t in roots) / len(roots)]
    while taken(p): p[1] += STEP
    start[v] = p; allp[v] = p
start = {v: [round(p[0], 2), round(p[1], 2)] for v, p in start.items()}
rep = ES.report(start, fixed, links, step=STEP)

# ---- into the editor ----
def exl(v, keep):
    res = []
    for e in exits.get(v, []):
        r = rooms.get(e['to'])
        if not r: continue
        why = '' if keep(e['to']) else ' · left off'
        if not why and not use(v, e) and e['dir'] in (16, 32): why = ' · ignored (flat exit used)'
        res.append(f"{DN.get(e['dir'], e['name'])} → {r['name'] or 'spacer room'}" + (f" ({r['area']})" if r['area'] and r['area'] != rooms[v]['area'] else '') + why)
    return res
for v in sorted(S):
    r = rooms[v]; sp = isspacer(v); x, y = start[v]
    D['rooms'].append(dict(id=v, name='' if sp else r['name'], terrain='' if sp else r['terrain'], void=sp, lvl=0, area='AZ', areaName=r['area'],
                           x=x, y=y, x0=x, y0=y, ex=exl(v, lambda t: t in V)))
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
D['audit']['az'] = dict(rooms=sum(1 for v in S if not isspacer(v)), spacers=sum(1 for v in S if isspacer(v)))
h = h[:m.start(1)] + json.dumps(D, separators=(',', ':')) + h[m.end(1):]

AZC = '#3FC1A6'
def sub(a, b):
    global h
    assert h.count(a) == 1, a; h = h.replace(a, b)
sub('.nd.ex rect,.nd.ex circle.shape{stroke:#2A8C8C;stroke-width:.16}',
    '.nd.ex rect,.nd.ex circle.shape{stroke:#2A8C8C;stroke-width:.16}\n.nd.az rect,.nd.az circle.shape{stroke:' + AZC + ';stroke-width:.16}')
sub("(r.area==='EX'?' ex':'')", "(r.area==='EX'?' ex':'')+(r.area==='AZ'?' az':'')")
sub("${r.area==='EX'?' · '+esc(r.areaName||'another area'):''}", "${r.area==='EX'||r.area==='AZ'?' · '+esc(r.areaName||'another area'):''}")
sub('<button id="selAdded">Select the single rooms I added</button>', '<button id="selAdded">Select the single rooms I added</button><button id="selAz">Select the Azure Sea beach rooms</button>')
sub("$('selAdded').onclick=", "$('selAz').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.area==='AZ')sel.add(r.id)});refreshSel()};\n$('selAdded').onclick=")
sub("r.area!=='ETR'&&r.area!=='KC'&&r.area!=='EX'&&!r.fixed", "r.area!=='ETR'&&r.area!=='KC'&&r.area!=='EX'&&r.area!=='AZ'&&!r.fixed")
sub('<span>Teal outline: a single room added from another area (Ocean Keep, Azure Sea)</span>\n',
    '<span>Teal outline: a single room added from another area (Ocean Keep, Azure Sea)</span>\n'
    f'    <i style="background:var(--t-Water);border:2px solid {AZC}"></i><span>Added Oct 23: the Azure Sea rooms along the beach '
    f'({D["audit"]["az"]["rooms"]} rooms, {D["audit"]["az"]["spacers"]} spacer rooms). Movable; they start next to the rooms they join</span>\n')
open(F, 'w', encoding='utf-8').write(h)

named = [v for v in S if not isspacer(v)]
print('rooms', len(S), '(found', cand, ', dead-end spacers left off', cand - len(S), ') | named', len(named), '| spacers', len(S) - len(named), '| edges', len(new),
      '| joins', len(roots), 'editor rooms:', roots)
print('report (close, far, wrong, thru):', rep, '| no e/w way to the shore:', unplaced)
xs = [p[0] for p in start.values()]; ys = [p[1] for p in start.values()]
print('box x %.1f..%.1f y %.1f..%.1f' % (min(xs), max(xs), min(ys), max(ys)))
print('names', sorted({rooms[v]['name'] for v in named}))
