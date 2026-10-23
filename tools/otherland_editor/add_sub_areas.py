# Adds rooms to the published Otherland layout editor (owner, Oct 23), without rebuilding it:
#   python3 add_sub_areas.py      (run from anywhere; edits otherland_editor.html beside it)
# grp 'sa', area 'OL', movable:
#   - 13285, 13282 (The Ziggurat), 13283, 13284, 15749 (The Valley of Crucifixion): shown, for the owner to arrange. They join 13271 (s) and 13274 (e);
#     their other exits (13282 s -> 17092, 15749 -> 20281) are left off.
#   - 13072 and 15259 (The Blood Sea, 'Adrift off the Coast'): HIDDEN (hidden0), only so the North routes can be traced through them. Their links to
#     22524 / 5981 are hidden with them; their links up to 5967 / 5970 (far north, not in this editor) are left off: no path.
# The editor's loadLayout keeps a room in hidden0 hidden when a save (or browser autosave) does not list it yet.
# Starting spots: the five in a row 2 apart from (71, 179) (>= 2.06 from every room in the save of Oct 22 19:24Z); 13072 2 NW of 22524, 15259 2 SE of 5981.
import sys, os, json, re
from collections import defaultdict
here = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.normpath(os.path.join(here, '..', '..', 'src')); sys.path[:0] = [SRC]
import maplib

DV = {1: (0, -1, 0), 2: (1, 0, 0), 4: (0, 1, 0), 8: (-1, 0, 0), 3: (1, -1, 0), 9: (-1, -1, 0), 6: (1, 1, 0), 12: (-1, 1, 0), 16: (0, 0, 1), 32: (0, 0, -1)}
DN = {1: 'n', 2: 'e', 4: 's', 8: 'w', 3: 'ne', 9: 'nw', 6: 'se', 12: 'sw', 16: 'u', 32: 'd', 0: '?'}
START = {13285: (71, 179), 13282: (71, 181), 13283: (69, 181), 13284: (67, 181), 15749: (73, 181), 13072: (83.5, 185), 15259: (39, 248.5)}
HIDE = [13072, 15259]
SAC = '#E7A3C4'

rooms, exits = maplib.world()
isspacer = lambda v: bool(rooms[v]['flags'] & 8) and rooms[v]['area'] == ''
F = os.path.join(here, 'otherland_editor.html'); h = open(F, encoding='utf-8').read()
m = re.search(r'const D=(\{.*?\});\n', h); D = json.loads(m.group(1))
byid = {r['id']: r for r in D['rooms']}
assert not any(r.get('grp') == 'sa' for r in D['rooms']), 'already added'
S = set(START); assert not S & set(byid)
V = S | set(byid)
FLATP = {frozenset((v, e['to'])) for v, l in exits.items() for e in l if e['dir'] in DV and e['dir'] not in (16, 32) and e['to'] != v}
use = lambda v, e: e['dir'] in DV and e['to'] != v and not (e['dir'] in (16, 32) and frozenset((v, e['to'])) in FLATP)

def exl(v, keep):
    res = []
    for e in exits.get(v, []):
        r = rooms.get(e['to'])
        if not r: continue
        ok = keep(e['to'])
        why = '' if ok else ' · left off'
        if ok and not use(v, e) and e['dir'] in (16, 32): why = ' · ignored (flat exit used)'
        res.append(f"{DN.get(e['dir'], e['name'])} → {r['name'] or 'spacer room'}" + (f" ({r['area']})" if r['area'] and r['area'] != rooms[v]['area'] else '') + why)
    return res

piece = len(D['secs'])
D['secs'].append(dict(i=piece, name='Sub-area rooms and Blood Sea links (added Oct 23)', n=len(S)))
for v in sorted(S):
    r = rooms[v]; sp = isspacer(v); x, y = START[v]
    D['rooms'].append(dict(id=v, name='' if sp else r['name'], terrain='' if sp else r['terrain'], void=sp, lvl=0, area='OL', grp='sa', piece=piece,
                           ga=r['area'] or ('spacer' if sp else 'unnamed'), x=x, y=y, x0=x, y0=y, ex=exl(v, lambda t: t in V)))
nfix = []
for v, r in byid.items():                                                               # the joined editor rooms' hover lists: their exits here are shown now
    if 'ex' in r and any(e['to'] in S for e in exits.get(v, [])):
        r['ex'] = exl(v, lambda t: t in V); nfix.append(v)
pair = {}
for v in V:
    for e in exits.get(v, []):
        t = e['to']
        if t not in V or t == v or not (v in S or t in S) or not use(v, e) and e['dir'] in (16, 32): continue
        k = (min(v, t), max(v, t)); f = pair.setdefault(k, [False, False, False]); f[0 if v == k[0] else 1] = True
        if e['dir'] not in (16, 32): f[2] = True
for (a, b), f in pair.items():
    if f[2] and not (f[0] and f[1]):
        f[0] = f[0] or any(e['to'] == b for e in exits.get(a, [])); f[1] = f[1] or any(e['to'] == a for e in exits.get(b, []))
new = [[a, b, 'two' if (f and r and flat) else ('one' if flat else 'ud')] for (a, b), (f, r, flat) in sorted(pair.items())]
D['edges'] += new
D['hidden0'] = sorted(set(D.get('hidden0') or []) | set(HIDE))
D['audit']['sa'] = len(S)
offc = {a: int(n) for a, n in (x.rsplit(' ', 1) for x in D['audit']['off'].split(', '))}                # Otherland's exits left off: less those shown now
for v, r in byid.items():
    if r.get('grp') in ('ol', 'an', 'un', 'az'):
        for e in exits.get(v, []):
            if e['to'] in S:
                k = rooms[e['to']]['area'] or 'unnamed/spacer rooms'
                if k in offc: offc[k] -= 1
D['audit']['off'] = ', '.join(f'{a} {n}' for a, n in sorted(offc.items()) if n)
h = h[:m.start(1)] + json.dumps(D, separators=(',', ':')) + h[m.end(1):]

def sub(a, b):
    global h
    assert h.count(a) == 1, a; h = h.replace(a, b)
sub('.nd.az rect,.nd.az circle.shape{stroke:#3FC1A6}', '.nd.az rect,.nd.az circle.shape{stroke:#3FC1A6}\n.nd.sa rect,.nd.sa circle.shape{stroke:' + SAC + '}')
sub('<button id="selAz">Select the Azure Sea rooms</button>', '<button id="selAz">Select the Azure Sea rooms</button><button id="selSa">Select the sub-area rooms</button>')
sub("Movable; they start next to the rooms they join</span>\n",
    "Movable; they start next to the rooms they join</span>\n"
    f'    <i style="background:var(--t-other);border:2px solid {SAC}"></i><span>Added Oct 23: 13285, The Ziggurat 13282, 13283, 13284 and The Monument of Remembrance 15749 (Valley of Crucifixion), joined to 13271 and 13274, to arrange; and, hidden, Adrift off the Coast 13072 and 15259 (Blood Sea), there only so the North routes can be traced (their links to 22524 and 5981 hidden; up to 5967 and 5970 left off). Movable</span>\n')
sub("$('selAz').onclick=()=>selGrp('az');", "$('selAz').onclick=()=>selGrp('az');$('selSa').onclick=()=>selGrp('sa');")
sub("added Azure Sea rooms ${a.az} ·", "added Azure Sea rooms ${a.az} · added sub-area rooms ${a.sa} ·")
sub("if(o.hidden){hidden.clear();o.hidden.forEach(id=>{if(pos.has(id))hidden.add(id)});refreshHidden()}",
    "if(o.hidden){hidden.clear();o.hidden.forEach(id=>{if(pos.has(id))hidden.add(id)});(D.hidden0||[]).forEach(id=>{if(pos.has(id)&&!o.ids.includes(id))hidden.add(id)});refreshHidden()}")   # (rooms added since that save keep their start)
open(F, 'w', encoding='utf-8').write(h)
print('rooms', len(S), '| edges', new, '| hidden', D['hidden0'], '| hover lists updated', nfix, '| exits left off', D['audit']['off'])
