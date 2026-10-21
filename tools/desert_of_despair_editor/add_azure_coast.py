# Adds the Azure Sea coast south of the Docks to the Desert of Despair layout editor (owner, Oct 21): starting from 6329, 6307 and 12986, the string
# of rooms named "A Pale, Sandy Coastline" / "Salt and waves...." running south (joined through spacer rooms), plus the "Azure and Green" rooms
# joined to them, and the spacer rooms that join two of the shown rooms.
#   python3 add_azure_coast.py   (edits desert_of_despair_editor.html beside it; run once)
# The rooms of the string already in the editor stay where the owner's save has them. The new rooms (grp 'az') start next to the rooms they join in
# the owner's saved layout (src/legacy/dd_layout_final.json, = ddlayout/current of Oct 20 18:25Z), spread from there by editor_spread.spread.
import sys, os, json, re, math
from collections import deque, defaultdict
here = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.normpath(os.path.join(here, '..', '..', 'src')); sys.path[:0] = [SRC]
import maplib, editor_spread as ES

STEP = 2.0
DV = {1: (0, -1, 0), 2: (1, 0, 0), 4: (0, 1, 0), 8: (-1, 0, 0), 3: (1, -1, 0), 9: (-1, -1, 0), 6: (1, 1, 0), 12: (-1, 1, 0), 16: (0, 0, 1), 32: (0, 0, -1)}
DN = {1: 'n', 2: 'e', 4: 's', 8: 'w', 3: 'ne', 9: 'nw', 6: 'se', 12: 'sw', 16: 'u', 32: 'd'}
rooms, exits = maplib.world()
isspacer = lambda v: v in rooms and bool(rooms[v]['flags'] & 8) and rooms[v]['area'] == ''
F = os.path.join(here, 'desert_of_despair_editor.html'); h = open(F, encoding='utf-8').read()
m = re.search(r'const D=(\{.*?\});?\n', h); D = json.loads(m.group(1))
by = {r['id']: r for r in D['rooms']}
assert not any(r.get('grp') == 'az' for r in D['rooms']), 'already added'
L = json.load(open(os.path.join(SRC, 'legacy', 'dd_layout_final.json'))); saved = {v: (x, y) for v, x, y in zip(L['ids'], L['xs'], L['ys'])}

def real(v):                                    # the named rooms an exit of v reaches, through spacer rooms (keeping the spacers passed)
    out = []
    for e in exits.get(v, []):
        t, path, seen = e['to'], [], {v}
        while isspacer(t) and len(path) < 40:
            seen.add(t); path.append(t)
            nx = [x['to'] for x in exits.get(t, []) if x['name'] == e['name']] or [x['to'] for x in exits.get(t, []) if x['to'] not in seen]
            if not nx: t = None; break
            t = nx[0]
        if t in rooms and not isspacer(t): out.append((t, path))
    return out
key = lambda v: rooms[v]['name'].startswith(('A Pale, Sandy Coastline', 'Salt and waves'))
START = [6329, 6307, 12986]
chain = set(START); q = deque(START)
while q:
    v = q.popleft()
    for t, _ in real(v):
        if t not in chain and key(t): chain.add(t); q.append(t)
green = {t for v in chain for t, _ in real(v) if rooms[t]['name'].startswith('Azure and Green')} - chain
NAMED = chain | green
ADD = sorted(v for v in NAMED if v not in by)
shown = set(by) | set(ADD)
SP = set()                                      # spacers joining two shown rooms, at least one of them new
for v in ADD:
    for t, path in real(v):
        if t in shown: SP |= {s for s in path if s not in by}
ADD = sorted(set(ADD) | SP)

ALL = shown | SP; LK = defaultdict(list)
for u in ALL:
    for e in exits.get(u, []):
        if e['to'] in ALL:
            d = DV.get(e['dir'], (0, 0, 0)); LK[u].append((e['to'], d)); LK[e['to']].append((u, tuple(-c for c in d)))
links = lambda v: LK[v]
roots = sorted({t for v in ADD for t, _ in links(v) if t in saved})
start = ES.spread(set(ADD), links, saved, roots, step=STEP)
close, far, wrong, thru = ES.report(start, saved, links, step=STEP)

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
V = {r['id'] for r in D['rooms']}
have = {tuple(e[:2]) for e in D['edges']}
pair = defaultdict(lambda: [False, False, False])
for v in V:
    for e in exits.get(v, []):
        t = e['to']
        if t not in V or t == v: continue
        k = (min(v, t), max(v, t))
        if k in have or not (k[0] in ADD or k[1] in ADD): continue
        pair[k][0 if v == k[0] else 1] = True
        if e['dir'] not in (16, 32): pair[k][2] = True
new = [[a, b, 'two' if (f and r and flat) else ('one' if flat else 'ud')] for (a, b), (f, r, flat) in sorted(pair.items())]
D['edges'] += new
D['audit']['az'] = len(ADD)
h = h[:m.start(1)] + json.dumps(D, separators=(',', ':')) + h[m.end(1):]
# the editor's own wording: style, legend line, select button
css = ".nd.ge rect,.nd.ge circle.shape{stroke:#B58CE6}\n"
assert h.count(css) == 1; h = h.replace(css, css + ".nd.az rect,.nd.az circle.shape{stroke:#5FD3C4}\n")
leg = "<span>Added Oct 20: the Great Eastern Desert's tunnel 6549-9070, 9057 and spacers 22630, 22145 (movable, start next to the rooms they join in your saved layout)</span>\n"
assert h.count(leg) == 1
h = h.replace(leg, leg + f'    <i style="background:var(--t-Desert);border:2px solid #5FD3C4"></i><span>Added Oct 21: the Azure Sea coast south of the Docks, '
              f'{sum(1 for v in ADD if not isspacer(v))} rooms ("A Pale, Sandy Coastline", "Azure and Green") and {len(SP)} spacer rooms between them '
              f'(movable, start next to the rooms they join in your saved layout)</span>\n')
btn = '<button id="selGe">Select the added rooms</button>'
assert h.count(btn) == 1; h = h.replace(btn, btn + '<button id="selAz">Select the Azure Sea coast rooms</button>')
js = "$('selGe').onclick=()=>selGrp('ge');"
assert h.count(js) == 1; h = h.replace(js, js + "$('selAz').onclick=()=>selGrp('az');")
open(F, 'w', encoding='utf-8').write(h)
near = min(math.dist(start[v], p) for v in ADD for u, p in saved.items() if u not in {t for t, _ in links(v)})
print('string', len(chain), '(in the editor already', len(chain & set(by)), ') | Azure and Green joined', len(green), '(already', len(green & set(by)), ')')
print('added', len(ADD), '| named', len(ADD) - len(SP), '| spacers', len(SP), '| edges added', len(new), '| roots', roots)
print('start: close pairs', close, '| stretched past 2 steps', far, '| wrong way', wrong, '| lines through a room', thru, '| nearest saved room not joined %.2f' % near)
xs = [start[v][0] for v in ADD]; ys = [start[v][1] for v in ADD]
print('box x %.1f..%.1f y %.1f..%.1f' % (min(xs), max(xs), min(ys), max(ys)))
