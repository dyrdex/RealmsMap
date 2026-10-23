# Adds 21075 'The Royal Jetty of Camelot' (Sailing the Seas) to the Barren Peaks + Forgotten Woods layout editor (owner, Oct 23):
#   python3 add_21075.py   (edits barren_peaks_editor.html beside it; run after add_knights_of_the_round.py)
# Its one exit: ne 14078 'Before the Grounds of Camelot' (14078 sw 21075). Area 'KR' (with the Knights of the Round, movable),
# starting 2.7 rooms south-west of 14078 (editor_spread put it north-east: its south-west is full of its own rooms; this spot is the nearest
# within 30 degrees of sw that is 1.5 clear of every room, its line crossing one exit line).
import sys, os, json, re, math
here = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.normpath(os.path.join(here, '..', '..', 'src')); sys.path[:0] = [SRC]
import maplib, editor_spread as ES

V0 = 21075
DV = {1: (0, -1, 0), 2: (1, 0, 0), 4: (0, 1, 0), 8: (-1, 0, 0), 3: (1, -1, 0), 9: (-1, -1, 0), 6: (1, 1, 0), 12: (-1, 1, 0), 16: (0, 0, 1), 32: (0, 0, -1)}
DN = {1: 'n', 2: 'e', 4: 's', 8: 'w', 3: 'ne', 9: 'nw', 6: 'se', 12: 'sw', 16: 'u', 32: 'd'}
rooms, exits = maplib.world()
F = os.path.join(here, 'barren_peaks_editor.html'); h = open(F, encoding='utf-8').read()
m = re.search(r'const D=(\{.*?\});\n', h); D = json.loads(m.group(1))
by = {r['id']: r for r in D['rooms']}
assert 14078 in by and V0 not in by
fixed = {v: (r['x'], r['y']) for v, r in by.items()}
def links(v):
    res = [(e['to'], DV[e['dir']]) for e in exits.get(v, []) if e['dir'] in DV and e['to'] in by and v == V0]
    res += [(u, tuple(-c for c in DV[e['dir']])) for u, l in exits.items() if u in by and v == V0 for e in l if e['to'] == v and e['dir'] in DV]
    return res
start = {V0: [-65.98, -48.25]}
rep = ES.report(start, fixed, links, step=1.5)
r = rooms[V0]; x, y = start[V0]
D['rooms'].append(dict(id=V0, name=r['name'], terrain=r['terrain'], void=False, lvl=0, area='KR', x=x, y=y, x0=x, y0=y,
                       ex=[f"{DN[e['dir']]} → {rooms[e['to']]['name']}" for e in exits[V0]]))
by[14078]['ex'] = [s.replace(' (Sailing the Seas) · left off', ' (Sailing the Seas)') for s in by[14078]['ex']]
D['edges'].append([14078, V0, 'two'])
h = h[:m.start(1)] + json.dumps(D, separators=(',', ':')) + h[m.end(1):]
a = 'the Knights of the Round (86 rooms + 5 joining rooms), from 11743'
assert h.count(a) == 1; h = h.replace(a, 'the Knights of the Round (86 rooms + 5 joining rooms + 21075 The Royal Jetty of Camelot), from 11743')
open(F, 'w', encoding='utf-8').write(h)
print('21075 at', start[V0], '| 14078 at', fixed[14078], '| dist', round(math.dist(start[V0], fixed[14078]), 2),
      '| nearest other room', round(min(math.dist(start[V0], p) for v, p in fixed.items() if v != 14078), 2), '| report', rep)
print('14078 exits now:', by[14078]['ex'])
