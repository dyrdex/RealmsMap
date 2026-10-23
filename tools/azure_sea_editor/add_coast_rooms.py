# Adds the Azure Sea rooms joined to the Azure Sea Coast path (owner, Oct 23: "all unmapped Azure rooms", to arrange before the path is redrawn)
# to the published Azure Sea Coast layout editor, without rebuilding it:
#   python3 add_coast_rooms.py      (run from anywhere; edits azure_sea_editor.html beside it)
# The rooms (area 'AZ', grp 'ad', movable): every room not on the map and not in the editor, in the Azure Sea or a spacer, reached from the
# editor's 49 path rooms through such rooms (24 'Azure and Green' / 'A Beautiful Coastline' / 'Looking Over the Ocean' rooms + 2 spacers).
# Starting spots: editor_spread.spread grown from the path rooms they join, at the owner's save (src/legacy/az_layout_final.json).
import sys, os, json, re
from collections import deque, defaultdict
here = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.normpath(os.path.join(here, '..', '..', 'src')); sys.path[:0] = [SRC]
import maplib, editor_spread as ES

DV = {1: (0, -1, 0), 2: (1, 0, 0), 4: (0, 1, 0), 8: (-1, 0, 0), 3: (1, -1, 0), 9: (-1, -1, 0), 6: (1, 1, 0), 12: (-1, 1, 0), 16: (0, 0, 1), 32: (0, 0, -1)}
DN = {1: 'n', 2: 'e', 4: 's', 8: 'w', 3: 'ne', 9: 'nw', 6: 'se', 12: 'sw', 16: 'u', 32: 'd', 0: '?'}

rooms, exits = maplib.world()
isspacer = lambda v: bool(rooms[v]['flags'] & 8) and rooms[v]['area'] == ''
F = os.path.join(here, 'azure_sea_editor.html'); h = open(F, encoding='utf-8').read()
m = re.search(r'const D=(\{.*?\});\n', h); D = json.loads(m.group(1))
byid = {r['id']: r for r in D['rooms']}
assert not any(r.get('grp') == 'ad' for r in D['rooms']), 'already added'
B = json.load(open(os.path.join(SRC, 'base', 'map.json'))); track = B['wild'].get('track', {})
onmap = lambda v: str(v) in B['room_pos'] or f'cx{v}' in track
PATH = {v for v, r in byid.items() if not r.get('fixed')}

# ---- the rooms ----
ok = lambda t: t in rooms and t not in byid and not onmap(t) and (rooms[t]['area'] == 'Azure Sea' or isspacer(t))
nb = defaultdict(set)
for v, l in exits.items():
    for e in l: nb[v].add(e['to']); nb[e['to']].add(v)
S = {t for v in PATH for t in nb[v] if ok(t)}
q = deque(S)
while q:
    v = q.popleft()
    for t in nb[v]:
        if t not in S and ok(t): S.add(t); q.append(t)
V = S | set(byid)
rev = defaultdict(list)
for v, l in exits.items():
    for e in l: rev[e['to']].append(v)
def links(v):
    res = [(e['to'], DV[e['dir']]) for e in exits.get(v, []) if e['dir'] in DV and e['to'] != v and e['to'] in V and (v in S or e['to'] in S)]
    for u in rev[v]:
        if u not in V or u == v or not (u in S or v in S): continue
        for e in exits.get(u, []):
            if e['to'] == v and e['dir'] in DV: d = DV[e['dir']]; res.append((u, (-d[0], -d[1], -d[2])))
    return res

# ---- starting spots ----
L = json.load(open(os.path.join(SRC, 'legacy', 'az_layout_final.json'))); spos = dict(zip(L['ids'], zip(L['xs'], L['ys'])))
fixed = {v: tuple(spos[v]) if v in spos else (r['x'], r['y']) for v, r in byid.items()}
roots = sorted({t for v in S for t, _ in links(v) if t in PATH}, key=lambda t: fixed[t][1])
start = ES.spread(S, links, fixed, roots)
start = {v: [round(p[0], 2), round(p[1], 2)] for v, p in start.items()}
rep = ES.report(start, fixed, links)

# ---- into the editor ----
def exl(v):
    res = []
    for e in exits.get(v, []):
        r = rooms.get(e['to'])
        if not r: continue
        res.append(f"{DN.get(e['dir'], e['name'])} → {r['name'] or 'spacer room'}" + (f" ({r['area']})" if r['area'] and r['area'] != 'Azure Sea' else '')
                   + ('' if e['to'] in V else ' · left off'))
    return res
for v in sorted(S):
    r = rooms[v]; sp = isspacer(v); x, y = start[v]
    D['rooms'].append(dict(id=v, name='' if sp else r['name'], terrain='' if sp else r['terrain'], void=sp, lvl=0, area='AZ', grp='ad',
                           x=x, y=y, x0=x, y0=y, ex=exl(v)))
old = {(a, b) for a, b, _ in D['edges']}
pair = {}
for v in V:
    for e in exits.get(v, []):
        t = e['to']
        if t not in V or t == v or not (v in S or t in S): continue
        k = (min(v, t), max(v, t)); f = pair.setdefault(k, [False, False, False]); f[0 if v == k[0] else 1] = True
        if e['dir'] not in (16, 32): f[2] = True
new = [[a, b, 'two' if (f and r and flat) else ('one' if flat else 'ud')] for (a, b), (f, r, flat) in sorted(pair.items()) if (a, b) not in old]
D['edges'] += new
D['audit']['added'] = dict(rooms=sum(1 for v in S if not isspacer(v)), spacers=sum(1 for v in S if isspacer(v)))
h = h[:m.start(1)] + json.dumps(D, separators=(',', ':')) + h[m.end(1):]

ADC = '#5FC8E8'
def sub(a, b):
    global h
    assert h.count(a) == 1, a; h = h.replace(a, b)
sub('.nd.ed rect,.nd.ed circle.shape{stroke:#D98AD0}', '.nd.ed rect,.nd.ed circle.shape{stroke:#D98AD0}\n.nd.ad rect,.nd.ad circle.shape{stroke:' + ADC + '}')
sub("ed:' (path to the Village of Edo)'}", "ed:' (path to the Village of Edo)',ad:' (added Oct 23)'}")
sub('<button id="selEd">Select the path to Edo</button>', '<button id="selEd">Select the path to Edo</button><button id="selAd">Select the rooms added Oct 23</button>')
sub("$('selEd').onclick=", "$('selAd').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.grp==='ad')sel.add(r.id)});refreshSel()};\n$('selEd').onclick=")
sub('<span>Azure Sea path to the Village of Edo (movable)</span>\n',
    '<span>Azure Sea path to the Village of Edo (movable)</span>\n'
    f'    <i style="background:var(--t-Forest);border:2px solid {ADC}"></i><span>Added Oct 23: the Azure Sea rooms joined to the path that weren\'t on the map '
    f'({D["audit"]["added"]["rooms"]} rooms, {D["audit"]["added"]["spacers"]} spacer rooms). Movable; they start next to the rooms they join</span>\n')
sub("Path from 4317 to the Village of Edo: ${a.edo}<br>", "Path from 4317 to the Village of Edo: ${a.edo}<br>${a.added?`Added Oct 23 (joined to the path, not on the map): ${a.added.rooms} rooms + ${a.added.spacers} spacer rooms<br>`:''}")
open(F, 'w', encoding='utf-8').write(h)

print('rooms', len(S), '| named', D['audit']['added']['rooms'], '| spacers', D['audit']['added']['spacers'], '| new exits', len(new), '| joins', len(roots), 'path rooms:', roots)
print('report (close, far, wrong, thru):', rep)
for v in sorted(S): print(v, (rooms[v]['name'] or 'spacer')[:24].ljust(24), start[v])
