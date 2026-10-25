# Adds 6733 'A Narrow Trail' (Mount Krozloy) and 6736 'The hills' (Kingdom of Juargan) to the Barren Peaks + Forgotten Woods layout
# editor (owner, Oct 24), with 6732 'The hills' (Kingdom of Juargan), the room that joins them to the editor (6731 e 6732, 6732 n 6733, e 6736):
#   python3 add_juargan.py <the owner's save (bplayout/current)>   (edits barren_peaks_editor.html beside it)
# Their other exits (6733 n 6734, 6736 u 6737) are left off. Area 'JK' (movable, its own outline), starting where editor_spread grows them
# from 6731, at the owner's save of Oct 24 14:58Z.
import sys, os, json, re, math
here = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.normpath(os.path.join(here, '..', '..', 'src')); sys.path[:0] = [SRC]
import maplib, editor_spread as ES

NEW = [6732, 6733, 6736]
DV = {1: (0, -1, 0), 2: (1, 0, 0), 4: (0, 1, 0), 8: (-1, 0, 0), 3: (1, -1, 0), 9: (-1, -1, 0), 6: (1, 1, 0), 12: (-1, 1, 0), 16: (0, 0, 1), 32: (0, 0, -1)}
DN = {1: 'n', 2: 'e', 4: 's', 8: 'w', 3: 'ne', 9: 'nw', 6: 'se', 12: 'sw', 16: 'u', 32: 'd'}
COL = '#7FC2B4'
rooms, exits = maplib.world()
F = os.path.join(here, 'barren_peaks_editor.html'); h = open(F, encoding='utf-8').read()
m = re.search(r'const D=(\{.*?\});\n', h); D = json.loads(m.group(1))
by = {r['id']: r for r in D['rooms']}
assert not set(NEW) & set(by), 'already added'
SAVE = sys.argv[1] if len(sys.argv) > 1 else None          # the owner's save (bplayout/current), else the rooms' spots in the editor
fpos = {}
if SAVE: L = json.load(open(SAVE)); fpos = dict(zip(L['ids'], zip(L['xs'], L['ys'])))
P = lambda v: fpos.get(v, (by[v]['x'], by[v]['y']))
fixed = {v: P(v) for v in by}
S = set(NEW); V = S | set(by)
def links(v):
    res = [(e['to'], DV[e['dir']]) for e in exits.get(v, []) if e['dir'] in DV and e['to'] in V and e['to'] != v and (v in S or e['to'] in S)]
    for u, l in exits.items():
        if u in V and u != v and (u in S or v in S):
            res += [(u, tuple(-c for c in DV[e['dir']])) for e in l if e['to'] == v and e['dir'] in DV]
    return res
start = ES.spread(S, links, fixed, [6731])
start = {v: (round(p[0], 2), round(p[1], 2)) for v, p in start.items()}
rep = ES.report(start, fixed, links)
def exl(v):
    return [f"{DN.get(e['dir'], e['cmd'])} → {rooms[e['to']]['name'] or 'spacer room'}" + (f" ({rooms[e['to']]['area']})" if rooms[e['to']]['area'] else '')
            + ('' if e['to'] in V else ' · left off') for e in exits[v]]
for v in NEW:
    r = rooms[v]; x, y = start[v]
    D['rooms'].append(dict(id=v, name=r['name'], terrain=r['terrain'], void=False, lvl=0, area='JK', x=x, y=y, x0=x, y0=y, ex=exl(v)))
pair = {}
for v in V:
    for e in exits.get(v, []):
        t = e['to']
        if t not in V or t == v or not (v in S or t in S): continue
        k = (min(v, t), max(v, t)); f = pair.setdefault(k, [False, False, False]); f[0 if v == k[0] else 1] = True
        if e['dir'] not in (16, 32): f[2] = True
new = [[a, b, 'two' if (f and r and flat) else ('one' if flat else 'ud')] for (a, b), (f, r, flat) in sorted(pair.items())]
D['edges'] += new
D['audit']['jk'] = len(NEW)
r6731 = next(r for r in D['rooms'] if r['id'] == 6731); r6731['ex'] = [s.replace(' · not in this editor', '') for s in r6731.get('ex', [])]
h = h[:m.start(1)] + json.dumps(D, separators=(',', ':')) + h[m.end(1):]
def sub(a, b):
    global h
    assert h.count(a) == 1, a; h = h.replace(a, b)
sub('.nd.bt rect,.nd.bt circle.shape{stroke:#D98E5A;stroke-width:.17}', '.nd.bt rect,.nd.bt circle.shape{stroke:#D98E5A;stroke-width:.17}\n.nd.jk rect,.nd.jk circle.shape{stroke:' + COL + ';stroke-width:.17}')
sub("r.area==='BT'?' bt':''", "r.area==='BT'?' bt':r.area==='JK'?' jk':''")
sub("r.area==='BT'?' · below 5644 (added Oct 23)':", "r.area==='BT'?' · below 5644 (added Oct 23)':r.area==='JK'?' · Juargan / Mount Krozloy (added Oct 24)':")
sub('<button id="selBt">Select the rooms below 5644</button>', '<button id="selBt">Select the rooms below 5644</button><button id="selJk">Select 6732, 6733, 6736</button>')
sub("$('selKr').onclick=", "$('selJk').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.area==='JK')sel.add(r.id)});refreshSel()};\n$('selKr').onclick=")
a = '<span>Added Oct 23: 13640, 13641, 13642, below Forgotten Woods room 5644 (movable)</span>'
sub(a, a + f'\n    <i style="background:var(--t-other);border:2px solid {COL}"></i><span>Added Oct 24: 6733 A Narrow Trail (Mount Krozloy), 6736 The hills and 6732 The hills joining them (Kingdom of Juargan), east of Barren Peaks room 6731 (movable)</span>')
open(F, 'w', encoding='utf-8').write(h)
print('spots', start, '| edges', new)
print('editor_spread report (close pairs, stretched, pointing backwards, lines through rooms):', rep)
print('nearest other room to each:', {v: round(min(math.dist(start[v], p) for p in fixed.values()), 2) for v in NEW}, '| 6731', P(6731))
