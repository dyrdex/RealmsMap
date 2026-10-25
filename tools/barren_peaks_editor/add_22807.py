# Adds 22807 'The Crimson Caverns' (The Crimson Caverns) to the Barren Peaks + Forgotten Woods layout editor (owner, Oct 24):
#   python3 add_22807.py <the owner's save (bplayout/current)>   (edits barren_peaks_editor.html beside it)
# Its exits: w 6998 'A Dark Valley' (Barren Peaks, in the editor), e 22808 (left off). Area 'CC' (movable, its own outline), starting where
# editor_spread grows it from 6998, at the owner's save of Oct 24 15:44Z.
import sys, os, json, re, math
here = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.normpath(os.path.join(here, '..', '..', 'src')); sys.path[:0] = [SRC]
import maplib, editor_spread as ES

NEW = [22807]
DV = {1: (0, -1, 0), 2: (1, 0, 0), 4: (0, 1, 0), 8: (-1, 0, 0), 3: (1, -1, 0), 9: (-1, -1, 0), 6: (1, 1, 0), 12: (-1, 1, 0), 16: (0, 0, 1), 32: (0, 0, -1)}
DN = {1: 'n', 2: 'e', 4: 's', 8: 'w', 3: 'ne', 9: 'nw', 6: 'se', 12: 'sw', 16: 'u', 32: 'd'}
COL = '#C9707A'
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
start = ES.spread(S, links, fixed, [6998])
start = {v: (round(p[0], 2), round(p[1], 2)) for v, p in start.items()}
rep = ES.report(start, fixed, links)
def exl(v):
    return [f"{DN.get(e['dir'], e['cmd'])} → {rooms[e['to']]['name'] or 'spacer room'}" + (f" ({rooms[e['to']]['area']})" if rooms[e['to']]['area'] else '')
            + ('' if e['to'] in V else ' · left off') for e in exits[v]]
for v in NEW:
    r = rooms[v]; x, y = start[v]
    D['rooms'].append(dict(id=v, name=r['name'], terrain=r['terrain'], void=False, lvl=0, area='CC', x=x, y=y, x0=x, y0=y, ex=exl(v)))
pair = {}
for v in V:
    for e in exits.get(v, []):
        t = e['to']
        if t not in V or t == v or not (v in S or t in S): continue
        k = (min(v, t), max(v, t)); f = pair.setdefault(k, [False, False, False]); f[0 if v == k[0] else 1] = True
        if e['dir'] not in (16, 32): f[2] = True
new = [[a, b, 'two' if (f and r and flat) else ('one' if flat else 'ud')] for (a, b), (f, r, flat) in sorted(pair.items())]
D['edges'] += new
D['audit']['cc'] = len(NEW)
r6998 = next(r for r in D['rooms'] if r['id'] == 6998); r6998['ex'] = [s.replace(' · not in this editor', '') for s in r6998.get('ex', [])]
h = h[:m.start(1)] + json.dumps(D, separators=(',', ':')) + h[m.end(1):]
def sub(a, b):
    global h
    assert h.count(a) == 1, a; h = h.replace(a, b)
sub('.nd.jk rect,.nd.jk circle.shape{stroke:#7FC2B4;stroke-width:.17}', '.nd.jk rect,.nd.jk circle.shape{stroke:#7FC2B4;stroke-width:.17}\n.nd.cc rect,.nd.cc circle.shape{stroke:' + COL + ';stroke-width:.17}')
sub("r.area==='JK'?' jk':''", "r.area==='JK'?' jk':r.area==='CC'?' cc':''")
sub("r.area==='JK'?' · Juargan / Mount Krozloy (added Oct 24)':", "r.area==='JK'?' · Juargan / Mount Krozloy (added Oct 24)':r.area==='CC'?' · The Crimson Caverns (added Oct 24)':")
sub('<button id="selJk">Select 6732, 6733, 6736</button>', '<button id="selJk">Select 6732, 6733, 6736</button><button id="selCc">Select 22807</button>')
sub("$('selKr').onclick=", "$('selCc').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.area==='CC')sel.add(r.id)});refreshSel()};\n$('selKr').onclick=")
a = '<span>Added Oct 24: 6733 A Narrow Trail (Mount Krozloy), 6736 The hills and 6732 The hills joining them (Kingdom of Juargan), east of Barren Peaks room 6731 (movable)</span>'
sub(a, a + f'\n    <i style="background:var(--t-other);border:2px solid {COL}"></i><span>Added Oct 24: 22807 The Crimson Caverns, east of Barren Peaks room 6998 (movable)</span>')
open(F, 'w', encoding='utf-8').write(h)
print('spots', start, '| edges', new)
print('editor_spread report (close pairs, stretched, pointing backwards, lines through rooms):', rep)
print('nearest other room to each:', {v: round(min(math.dist(start[v], p) for p in fixed.values()), 2) for v in NEW}, '| 6998', P(6998))
