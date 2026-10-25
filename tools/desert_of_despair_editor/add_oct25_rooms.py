# Adds rooms to the Desert of Despair layout editor (owner, Oct 25; grp 'o25', movable, its own outline):
#   python3 add_oct25_rooms.py <owner's save as JSON> 12994 12995 ...   (edits desert_of_despair_editor.html beside it)
# Rooms already in the editor are skipped (listed). The new ones start next to the rooms they join, at those rooms' spots in the owner's save
# (ddlayout/current), spread by editor_spread.spread; their exits to every room in the editor are added. (From add_dd_rooms.py.)
import sys, os, json, re, math
from collections import defaultdict
here = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.normpath(os.path.join(here, '..', '..', 'src')); sys.path[:0] = [SRC]
import maplib, editor_spread as ES

STEP = 2.0
DV = {1: (0, -1, 0), 2: (1, 0, 0), 4: (0, 1, 0), 8: (-1, 0, 0), 3: (1, -1, 0), 9: (-1, -1, 0), 6: (1, 1, 0), 12: (-1, 1, 0), 16: (0, 0, 1), 32: (0, 0, -1)}
DN = {1: 'n', 2: 'e', 4: 's', 8: 'w', 3: 'ne', 9: 'nw', 6: 'se', 12: 'sw', 16: 'u', 32: 'd'}
rooms, exits = maplib.world()
isspacer = lambda v: v in rooms and bool(rooms[v]['flags'] & 8) and rooms[v]['area'] == ''
SAVE = sys.argv[1]; ASK = sorted({int(a) for a in sys.argv[2:]})
F = os.path.join(here, 'desert_of_despair_editor.html'); h = open(F, encoding='utf-8').read()
m = re.search(r'const D=(\{.*?\});?\n', h); D = json.loads(m.group(1))
by = {r['id']: r for r in D['rooms']}
HAVE = [v for v in ASK if v in by]; ADD = [v for v in ASK if v not in by]
L = json.load(open(SAVE)); L = L.get('data', L); saved = {v: (x, y) for v, x, y in zip(L['ids'], L['xs'], L['ys'])}
fixed = {v: saved.get(v, (r['x0'], r['y0'])) for v, r in by.items()}
ALL = set(by) | set(ADD); LK = defaultdict(list)
for u in ALL:
    for e in exits.get(u, []):
        if e['to'] in ALL:
            d = DV.get(e['dir'], (0, 0, 0)); LK[u].append((e['to'], d)); LK[e['to']].append((u, tuple(-c for c in d)))
links = lambda v: LK[v]
roots = sorted({t for v in ADD for t, _ in links(v) if t in fixed})
start = ES.spread(set(ADD), links, fixed, roots, step=STEP)
close, far, wrong, thru = ES.report(start, fixed, links, step=STEP)

def exlist(v):
    res = []
    for e in exits.get(v, []):
        r = rooms.get(e['to'])
        if r: res.append(f"{DN.get(e['dir'], e['name'])} → {r['name'] or 'spacer room'}" + (f" ({r['area']})" if r['area'] and r['area'] != rooms[v]['area'] else ''))
    return res
for v in ADD:
    r = rooms[v]; x, y = round(start[v][0], 2), round(start[v][1], 2)
    D['rooms'].append(dict(id=v, name=r['name'], terrain='' if isspacer(v) else r['terrain'], void=isspacer(v), lvl=0, area='DD', grp='o25', piece=None,
                           ga=r['area'] or 'spacer', x=x, y=y, x0=x, y0=y, ex=exlist(v)))
have = {tuple(e[:2]) for e in D['edges']}
pair = defaultdict(lambda: [False, False, False])
for v in ALL:
    for e in exits.get(v, []):
        t = e['to']
        if t not in ALL or t == v: continue
        k = (min(v, t), max(v, t))
        if k in have or not (k[0] in ADD or k[1] in ADD): continue
        pair[k][0 if v == k[0] else 1] = True
        if e['dir'] not in (16, 32): pair[k][2] = True
new = [[a, b, 'two' if (f and r and flat) else ('one' if flat else 'ud')] for (a, b), (f, r, flat) in sorted(pair.items())]
D['edges'] += new
D['audit']['o25'] = len(ADD)
h = h[:m.start(1)] + json.dumps(D, separators=(',', ':')) + h[m.end(1):]
C = '#F07FB0'
def sub(a, b):
    global h
    assert h.count(a) == 1, a; h = h.replace(a, b)
sub('.nd.az rect,.nd.az circle.shape{stroke:#5FD3C4}', '.nd.az rect,.nd.az circle.shape{stroke:#5FD3C4}\n.nd.o25 rect,.nd.o25 circle.shape{stroke:' + C + '}')
sub('<button id="selAz">Select the Azure Sea coast rooms</button>', '<button id="selAz">Select the Azure Sea coast rooms</button><button id="selO25">Select the rooms added Oct 25</button>')
sub("$('selAz').onclick=()=>selGrp('az');", "$('selAz').onclick=()=>selGrp('az');$('selO25').onclick=()=>selGrp('o25');")
a = 'and 78 spacer rooms between them (movable, start next to the rooms they join in your saved layout)</span>\n'
names = ', '.join(f"{rooms[v]['area']} {v}" for v in ADD)
sub(a, a + f'    <i style="background:var(--t-Desert);border:2px solid {C}"></i><span>Added Oct 25 (movable, start next to the rooms they join in your saved layout): {names}</span>\n')
open(F, 'w', encoding='utf-8').write(h)
near = min(math.dist(start[v], p) for v in ADD for u, p in fixed.items() if u not in {t for t, _ in links(v)})
print('already in the editor', HAVE, '| added', ADD, '| edges added', len(new), new, '| roots', roots)
print('start', {v: start[v] for v in ADD})
print('close pairs', close, '| stretched past 2 steps', far, '| wrong way', wrong, '| lines through a room', thru, '| nearest room not joined %.2f' % near)
