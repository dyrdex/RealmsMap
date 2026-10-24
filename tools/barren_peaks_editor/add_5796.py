# Adds 5796 'A Dark Hole' (The Forgotten Woods, a deathtrap) to the Barren Peaks + Forgotten Woods layout editor (owner, Oct 24: it wasn't in it;
# southwest of 5795): movable, as the Woods rooms (green outline), one room south-west of Burrowing into the Hills 5795 (where the map has it).
#   python3 add_5796.py <the owner's save (bplayout/current)>   (edits barren_peaks_editor.html beside it)
import sys, os, json, re
here = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [os.path.normpath(os.path.join(here, '..', '..', 'src'))]
import maplib
DN = {1: 'n', 2: 'e', 4: 's', 8: 'w', 3: 'ne', 9: 'nw', 6: 'se', 12: 'sw', 16: 'u', 32: 'd'}
rooms, exits = maplib.world()
F = os.path.join(here, 'barren_peaks_editor.html'); h = open(F, encoding='utf-8').read()
m = re.search(r'const D=(\{.*?\});\n', h); D = json.loads(m.group(1)); by = {r['id']: r for r in D['rooms']}
assert 5796 not in by and 5795 in by
L = json.load(open(sys.argv[1])); sp = dict(zip(L['ids'], zip(L['xs'], L['ys'])))
x0, y0 = sp.get(5795, (by[5795]['x'], by[5795]['y'])); x, y = round(x0 - 0.71, 2), round(y0 + 0.71, 2)
D['rooms'].append(dict(id=5796, name=rooms[5796]['name'], terrain='', void=False, lvl=0, x=x, y=y, x0=x, y0=y, fixed=False, src='FW',
                       ex=[f"{DN.get(e['dir'], e['cmd'])} → {rooms[e['to']]['name']}" for e in exits[5796]]))
by[5795]['ex'] = [s.replace(' · not in this editor', '') for s in by[5795].get('ex', [])]
D['edges'].append([5795, 5796, 'two'])
h = h[:m.start(1)] + json.dumps(D, separators=(',', ':')) + h[m.end(1):]
open(F, 'w', encoding='utf-8').write(h)
print('5796 at', (x, y), '| 5795', (x0, y0))
