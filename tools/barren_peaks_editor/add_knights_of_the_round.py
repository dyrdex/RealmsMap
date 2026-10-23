# Adds every Knights of the Round room to the Barren Peaks + Forgotten Woods layout editor, joined at 11743 (owner, Oct 23):
#   python3 add_knights_of_the_round.py [save.json]   (edits barren_peaks_editor.html beside it; run after add_blood_sea_cave.py)
# The 87 rooms of area 'Knights of the Round' (11743 is already in, from add_blood_sea_cave.py) + the 5 unnamed rooms that join its pieces
# (20715 The Bridge of Death, 21065-21068). Left off: 21065 n 771 (Darkhaven), 14078 sw 21075 (Sailing the Seas), 5872 enter/d 11736 (the painting).
# Area 'KR' (movable). Starting spots: editor_spread.spread_clear from 11743 (laid out on its own, then moved as one block clear of the map's rooms),
# at the owner's save (bplayout/current), else the rooms' spots in the editor.
import sys, os, json, re, math
here = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.normpath(os.path.join(here, '..', '..', 'src')); sys.path[:0] = [SRC]
import maplib, editor_spread as ES

DV = {1: (0, -1, 0), 2: (1, 0, 0), 4: (0, 1, 0), 8: (-1, 0, 0), 3: (1, -1, 0), 9: (-1, -1, 0), 6: (1, 1, 0), 12: (-1, 1, 0), 16: (0, 0, 1), 32: (0, 0, -1)}
DN = {1: 'n', 2: 'e', 4: 's', 8: 'w', 3: 'ne', 9: 'nw', 6: 'se', 12: 'sw', 16: 'u', 32: 'd'}
COL = '#C9A0E8'
JOIN = [20715, 21065, 21066, 21067, 21068]
OFF = {(771, 21065)}
rooms, exits = maplib.world()
isspacer = lambda v: (bool(rooms[v]['flags'] & 8) or not rooms[v]['name']) and rooms[v]['area'] == ''
F = os.path.join(here, 'barren_peaks_editor.html'); h = open(F, encoding='utf-8').read()
m = re.search(r'const D=(\{.*?\});\n', h); D = json.loads(m.group(1))
by = {r['id']: r for r in D['rooms']}
assert 11743 in by, 'run add_blood_sea_cave.py first'
assert not any(r.get('area') == 'KR' for r in D['rooms']), 'already added'
S = {v for v, r in rooms.items() if r['area'] == 'Knights of the Round' and v not in by} | set(JOIN)
SAVE = sys.argv[1] if len(sys.argv) > 1 else None
fpos = {}
if SAVE: L = json.load(open(SAVE)); fpos = dict(zip(L['ids'], zip(L['xs'], L['ys'])))
fixed = {v: fpos.get(v, (r['x'], r['y'])) for v, r in by.items()}
V = S | set(by)
ok = lambda a, b: a in V and b in V and a != b and (a in S or b in S) and (min(a, b), max(a, b)) not in OFF
def links(v):
    res = [(e['to'], DV[e['dir']]) for e in exits.get(v, []) if e['dir'] in DV and ok(v, e['to'])]
    for u, l in exits.items():
        if ok(u, v): res += [(u, tuple(-c for c in DV[e['dir']])) for e in l if e['to'] == v and e['dir'] in DV]
    return res
start = ES.spread_clear(S, links, fixed, [11743])                    # (step 1.5)
rep = ES.report(start, fixed, links, step=1.5)
def exl(v):
    return [f"{DN.get(e['dir'], e['cmd'])} → {rooms[e['to']]['name'] or 'spacer room'}"
            + (f" ({rooms[e['to']]['area']})" if rooms[e['to']]['area'] and rooms[e['to']]['area'] != 'Knights of the Round' else '')
            + ('' if ok(v, e['to']) or (e['to'] in by and v in by) else ' · left off') for e in exits.get(v, [])]
for v in sorted(S):
    r = rooms[v]; sp = isspacer(v); x, y = start[v]
    D['rooms'].append(dict(id=v, name='' if sp else r['name'], terrain='' if sp else r['terrain'], void=sp, lvl=0, area='KR', x=x, y=y, x0=x, y0=y, ex=exl(v)))
by[11743]['ex'] = exl(11743)
pair = {}
for v in V:
    for e in exits.get(v, []):
        t = e['to']
        if not ok(v, t): continue
        k = (min(v, t), max(v, t)); f = pair.setdefault(k, [False, False, False]); f[0 if v == k[0] else 1] = True
        if e['dir'] not in (16, 32): f[2] = True
old = {(a, b) for a, b, _ in D['edges']}
new = [[a, b, 'two' if (f and r and flat) else ('one' if flat else 'ud')] for (a, b), (f, r, flat) in sorted(pair.items()) if (a, b) not in old]
D['edges'] += new
D['audit']['kr'] = len(S)
h = h[:m.start(1)] + json.dumps(D, separators=(',', ':')) + h[m.end(1):]
def sub(a, b):
    global h
    assert h.count(a) == 1, a; h = h.replace(a, b)
a = '.nd.bs rect,.nd.bs circle.shape{stroke:#C46A8A;stroke-width:.17}'
sub(a, a + '\n.nd.kr rect,.nd.kr circle.shape{stroke:' + COL + ';stroke-width:.17}')
sub("+(r.area==='BS'?' bs':'')", "+(r.area==='BS'?' bs':r.area==='KR'?' kr':'')")
sub("r.area==='BS'?' · below 5639 (added Oct 23)':", "r.area==='BS'?' · below 5639 (added Oct 23)':r.area==='KR'?' · Knights of the Round (added Oct 23)':")
sub('<button id="selBs">Select the rooms added Oct 23</button>', '<button id="selBs">Select the rooms below 5639</button><button id="selKr">Select the Knights of the Round</button>')
sub("$('selBs').onclick=", "$('selKr').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.area==='KR')sel.add(r.id)});refreshSel()};\n$('selBs').onclick=")
a = '<span>Added Oct 23: 11745, 11744, 11743, below Forgotten Woods room 5639 (movable)</span>'
nk = sum(1 for v in S if rooms[v]['area'] == 'Knights of the Round')
sub(a, a + f'\n    <i style="background:var(--t-other);border:2px solid {COL}"></i><span>Added Oct 23: the Knights of the Round ({nk} rooms + {len(S) - nk} joining rooms), from 11743 (movable)</span>')
open(F, 'w', encoding='utf-8').write(h)
xs = [p[0] for p in start.values()]; ys = [p[1] for p in start.values()]
print('rooms', len(S), '(Knights', nk, '+ joining', len(S) - nk, ') | new exits', len(new))
print('block x', min(xs), max(xs), 'y', min(ys), max(ys), '| 11743 at', fixed[11743])
print('nearest new room to 11743:', min((round(math.dist(start[v], fixed[11743]), 2), v) for v in S))
print('nearest new room to a room already in the editor:', round(min(math.dist(start[v], p) for v in S for p in fixed.values()), 2))
print('report (close pairs, stretched, pointing backwards, lines through rooms):', rep)
