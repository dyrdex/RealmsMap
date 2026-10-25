# Adds Forest of Tears room 1669 'Lost Between Woods' to the Barren Peaks + Forgotten Woods editor (owner, Oct 23: to shape the long trail
# 1669 ne 5491), movable (area 'FT', blue outline), where the map has it; and its other neighbour 1668 'Lost Between Woods' (w of 1669) as a
# fixed dot (src 'FT'), so both of 1669's lines show:   python3 add_1669.py   (edits barren_peaks_editor.html beside it)
# Once the owner saves, 1669's spot from this editor wins over the Forest of Tears editor's (update that editor's 1669 to match).
import sys, os, json, re
here = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [os.path.normpath(os.path.join(here, '..', '..', 'src'))]
import maplib
DN = {1: 'n', 2: 'e', 4: 's', 8: 'w', 3: 'ne', 9: 'nw', 6: 'se', 12: 'sw', 16: 'u', 32: 'd'}
COL, CX = '#6FA8D6', '#6FA8D6'
rooms, exits = maplib.world()
M = json.load(open(os.path.join(here, '..', '..', 'src', 'base', 'map.json'))); R = M['room_pos']
F = os.path.join(here, 'barren_peaks_editor.html'); h = open(F, encoding='utf-8').read()
m = re.search(r'const D=(\{.*?\});\n', h); D = json.loads(m.group(1)); by = {r['id']: r for r in D['rooms']}
assert 1669 not in by and 1668 not in by and 5491 in by
V = set(by) | {1668, 1669}
exl = lambda v: [f"{DN.get(e['dir'], e['cmd'])} → {rooms[e['to']]['name'] or 'spacer room'}" + (f" ({rooms[e['to']]['area']})" if rooms[e['to']]['area'] != rooms[v]['area'] else '')
                 + ('' if e['to'] in V else ' · not in this editor') for e in exits[v]]
for v, kw in ((1669, dict(area='FT')), (1668, dict(fixed=True, src='FT'))):
    x, y = [round(c, 2) for c in R[str(v)][:2]]
    D['rooms'].append(dict(id=v, name=rooms[v]['name'], terrain='', void=False, lvl=0, x=x, y=y, x0=x, y0=y, ex=exl(v), **kw))
by[5491]['ex'] = exl(5491)
D['edges'] += [[1668, 1669, 'two'], [1669, 5491, 'two']]
h = h[:m.start(1)] + json.dumps(D, separators=(',', ':')) + h[m.end(1):]
def sub(a, b):
    global h
    assert h.count(a) == 1, a; h = h.replace(a, b)
sub('.nd.kr rect,.nd.kr circle.shape{stroke:#C9A0E8;stroke-width:.17}', '.nd.kr rect,.nd.kr circle.shape{stroke:#C9A0E8;stroke-width:.17}\n.nd.ft rect,.nd.ft circle.shape{stroke:' + COL + ';stroke-width:.17}')
sub("r.area==='KR'?' kr':''", "r.area==='KR'?' kr':r.area==='FT'?' ft':''")
sub("r.area==='KR'?' · Knights of the Round (added Oct 23)':", "r.area==='KR'?' · Knights of the Round (added Oct 23)':r.area==='FT'?' · Forest of Tears (added Oct 23, movable)':")
sub("NTR:'Northern Trade Route'}", "NTR:'Northern Trade Route',FT:'Forest of Tears'}")
sub('--cx-FW:#6E9A6C;', '--cx-FW:#6E9A6C;--cx-FT:' + CX + ';')
a = '<span>Fixed room on the Northern Trade Route (up to the bridge)</span>'
sub(a, a + f'\n    <i style="background:var(--t-other);border:2px solid {COL}"></i><span>Added Oct 23: Forest of Tears room 1669 Lost Between Woods (movable; its trail runs ne to 5491)</span>'
       + f'\n    <i style="background:{CX};border-radius:50%"></i><span>Fixed: Forest of Tears room 1668, the other end of 1669\'s west trail</span>')
open(F, 'w', encoding='utf-8').write(h)
print('added 1669 at', R['1669'][:2], '(movable) and 1668 at', R['1668'][:2], '(fixed); edges 1668-1669, 1669-5491; 5491 exits', by[5491]['ex'])
