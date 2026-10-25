# Adds Moria 3347, 3348 and the Land of the Fire Newts 3352-3360 to the Ashen Forest layout editor (owner, Oct 25):
#   python3 add_moria.py [owner's save as JSON]   (edits ashen_forest_editor.html beside it)
# One chain south of Within the Ashen Forest 1255 (1255 s 3347), area 'MO' (movable, its own outline), laid straight along its exits (0.75 a step) from
# 1255's spot in the owner's save (ashlayout2/current; else its starting spot). Exits to rooms not in the editor (3346, 3349, 3361, 3362,
# 3424, 3442) are listed in each room's hover text only.
import sys, os, json, re, math
here = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.normpath(os.path.join(here, '..', '..', 'src')); sys.path[:0] = [SRC]
import maplib, editor_spread as ES

ROOT, NEW = 1255, [3347, 3348, 3352, 3353, 3354, 3355, 3356, 3357, 3358, 3359, 3360]
DV = {1: (0, -1, 0), 2: (1, 0, 0), 4: (0, 1, 0), 8: (-1, 0, 0), 3: (1, -1, 0), 9: (-1, -1, 0), 6: (1, 1, 0), 12: (-1, 1, 0), 16: (0, 0, 1), 32: (0, 0, -1)}
DN = {1: 'n', 2: 'e', 4: 's', 8: 'w', 3: 'ne', 9: 'nw', 6: 'se', 12: 'sw', 16: 'u', 32: 'd'}
MOC = '#E0703C'
rooms, exits = maplib.world()
F = os.path.join(here, 'ashen_forest_editor.html'); h = open(F, encoding='utf-8').read()
m = re.search(r'const D=(\{.*?\});\n', h); D = json.loads(m.group(1))
by = {r['id']: r for r in D['rooms']}
assert not set(NEW) & set(by), 'already added'
sv = {}
if len(sys.argv) > 1:
    o = json.load(open(sys.argv[1])); o = o.get('data', o); sv = dict(zip(o['ids'], zip(o['xs'], o['ys'])))
P = lambda v: sv.get(v, (by[v]['x'], by[v]['y']))
S = set(NEW); fixed = {v: P(v) for v in by if math.dist(P(v), P(ROOT)) < 12}
def links(v):
    res = [(e['to'], DV[e['dir']]) for e in exits.get(v, []) if e['dir'] in DV and (e['to'] in S or (v in S and e['to'] == ROOT))]
    res += [(u, tuple(-c for c in DV[e['dir']])) for u, l in exits.items() if u in S or u == ROOT for e in l
            if e['to'] == v and e['dir'] in DV and u != v and (u in S or v in S)]
    return res
STEP = 0.75                                                           # straight along the exits (editor_spread crowded this chain and turned
start, q = {ROOT: P(ROOT)}, [ROOT]                                    # 12 of its steps backwards): every step points the way its exit goes
while q:
    u = q.pop(0)
    for e in exits.get(u, []):
        if e['to'] in S and e['to'] not in start and e['dir'] in DV:
            d = DV[e['dir']]; start[e['to']] = (start[u][0] + d[0] * STEP, start[u][1] + d[1] * STEP); q.append(e['to'])
assert set(NEW) <= set(start)
rep = ES.report({v: start[v] for v in NEW}, fixed, links)
for v in NEW:
    r = rooms[v]; x, y = start[v]
    ex = [f"{DN.get(e['dir'], e['cmd'])} → {rooms[e['to']]['name'] or 'spacer room'}" + (f" ({rooms[e['to']]['area']})" if rooms[e['to']]['area'] != r['area'] else '')
          + ('' if e['to'] in by or e['to'] in S else ' · not in the editor') for e in exits[v]]
    D['rooms'].append(dict(id=v, name=r['name'], terrain=r['terrain'], void=False, lvl=0, area='MO', areaName=r['area'],
                           x=round(x, 2), y=round(y, 2), x0=round(x, 2), y0=round(y, 2), ex=ex))
V = set(by) | S; pair = {}
for v in V:
    for e in exits.get(v, []):
        t = e['to']
        if t in V and t != v and (v in S or t in S):
            k = (min(v, t), max(v, t)); f = pair.setdefault(k, [False, False, False]); f[0 if v == k[0] else 1] = True
            if e['dir'] not in (16, 32): f[2] = True
new = [[a, b, 'two' if (f and r and flat) else ('one' if flat else 'ud')] for (a, b), (f, r, flat) in sorted(pair.items())]
D['edges'] += new
h = h[:m.start(1)] + json.dumps(D, separators=(',', ':')) + h[m.end(1):]
def sub(a, b):
    global h
    assert h.count(a) == 1, a; h = h.replace(a, b)
sub('.nd.az rect,.nd.az circle.shape{stroke:#3FC1A6;stroke-width:.16}', '.nd.az rect,.nd.az circle.shape{stroke:#3FC1A6;stroke-width:.16}\n.nd.mo rect,.nd.mo circle.shape{stroke:' + MOC + ';stroke-width:.16}')
sub("(r.area==='AZ'?' az':'')", "(r.area==='AZ'?' az':'')+(r.area==='MO'?' mo':'')")
sub("${r.area==='EX'||r.area==='AZ'?' · '+esc(r.areaName||'another area'):''}", "${r.area==='EX'||r.area==='AZ'||r.area==='MO'?' · '+esc(r.areaName||'another area'):''}")
sub('<button id="selAz">Select the Azure Sea beach rooms</button>', '<button id="selAz">Select the Azure Sea beach rooms</button><button id="selMo">Select Moria + the Land of the Fire Newts</button>')
sub("$('selAz').onclick=", "$('selMo').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.area==='MO')sel.add(r.id)});refreshSel()};\n$('selAz').onclick=")
sub("r.area!=='ETR'&&r.area!=='KC'&&r.area!=='EX'&&r.area!=='AZ'&&!r.fixed", "r.area!=='ETR'&&r.area!=='KC'&&r.area!=='EX'&&r.area!=='AZ'&&r.area!=='MO'&&!r.fixed")
a = 'Movable; they start next to the rooms they join</span>\n'
sub(a, a + f'    <i style="background:var(--t-Mountains);border:2px solid {MOC}"></i><span>Added Oct 25: Moria 3347, 3348 and the Land of the Fire Newts 3352-3360, south of Within the Ashen Forest 1255. Movable</span>\n')
open(F, 'w', encoding='utf-8').write(h)
print('spots', {v: [round(c, 2) for c in start[v]] for v in NEW})
print('edges', new)
print('editor_spread (close pairs, stretched, pointing backwards, lines through rooms):', rep, '| nearest other room', {v: round(min(math.dist(start[v], p) for p in fixed.values()), 2) for v in NEW})
