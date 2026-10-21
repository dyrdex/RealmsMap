# Adds rooms the owner names to the Desert of Despair layout editor (grp 'az', the Azure Sea coast; owner, Oct 21), after add_azure_coast.py:
#   python3 add_dd_rooms.py 15038 12988 ...   (edits desert_of_despair_editor.html beside it)
# They start next to the rooms they join: the owner's saved layout (src/legacy/dd_layout_final.json) for saved rooms, the editor's starting spots
# for the rest; spread from there by editor_spread.spread. Their exits to every room in the editor are added.
import sys, os, json, re, math
from collections import defaultdict
here = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.normpath(os.path.join(here, '..', '..', 'src')); sys.path[:0] = [SRC]
import maplib, editor_spread as ES

STEP = 2.0
DV = {1: (0, -1, 0), 2: (1, 0, 0), 4: (0, 1, 0), 8: (-1, 0, 0), 3: (1, -1, 0), 9: (-1, -1, 0), 6: (1, 1, 0), 12: (-1, 1, 0), 16: (0, 0, 1), 32: (0, 0, -1)}
DN = {1: 'n', 2: 'e', 4: 's', 8: 'w', 3: 'ne', 9: 'nw', 6: 'se', 12: 'sw', 16: 'u', 32: 'd'}
rooms, exits = maplib.world()
isspacer = lambda v: v in rooms and bool(rooms[v]['flags'] & 8) and rooms[v]['area'] == ''
ADD = sorted({int(a) for a in sys.argv[1:]})
F = os.path.join(here, 'desert_of_despair_editor.html'); h = open(F, encoding='utf-8').read()
m = re.search(r'const D=(\{.*?\});?\n', h); D = json.loads(m.group(1))
by = {r['id']: r for r in D['rooms']}
assert not set(ADD) & set(by), sorted(set(ADD) & set(by))
L = json.load(open(os.path.join(SRC, 'legacy', 'dd_layout_final.json'))); saved = {v: (x, y) for v, x, y in zip(L['ids'], L['xs'], L['ys'])}
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
    D['rooms'].append(dict(id=v, name=r['name'], terrain='' if isspacer(v) else r['terrain'], void=isspacer(v), lvl=0, area='DD', grp='az', piece=None,
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
D['audit']['az'] = D['audit'].get('az', 0) + len(ADD)
h = h[:m.start(1)] + json.dumps(D, separators=(',', ':')) + h[m.end(1):]
leg = re.search(r'Added Oct 21: the Azure Sea coast south of the Docks, (\d+) rooms (.*?) and (\d+) spacer rooms', h); assert leg
nr = int(leg.group(1)) + sum(1 for v in ADD if not isspacer(v)); ns = int(leg.group(3)) + sum(1 for v in ADD if isspacer(v))
h = h[:leg.start()] + f'Added Oct 21: the Azure Sea coast south of the Docks, {nr} rooms {leg.group(2)} and {ns} spacer rooms' + h[leg.end():]
open(F, 'w', encoding='utf-8').write(h)
near = min(math.dist(start[v], p) for v in ADD for u, p in fixed.items() if u not in {t for t, _ in links(v)})
print('added', ADD, '| edges added', len(new), new, '| roots', roots)
print('start', {v: start[v] for v in ADD})
print('close pairs', close, '| stretched past 2 steps', far, '| wrong way', wrong, '| lines through a room', thru, '| nearest room not joined %.2f' % near)
