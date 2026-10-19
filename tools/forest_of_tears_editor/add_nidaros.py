# Adds the Nidaros Shortcut's rooms to the Forest of Tears layout editor (owner, Oct 19):   python3 add_nidaros.py   (edits forest_of_tears_editor.html)
# The shortcut (e.g. the route to the Valley of Mysts): Forgotten Woods 5307 -> nw -> 5317 'A Hidden Path' -> n -> 935 -> n -> 936 'Crossing the Brook'
# (Vale of Nidaros) -> sw -> spacer 5511 -> 5507 'A Bubbling Creek' (Valley of Mysts) -> e -> Forgotten Woods 5510, far across the map to the west.
# Like the Ofcol Shortcut, the 5511 -> 5507 step is a long line. Group 'ns' (movable; not 'nd', the editor's class for every room). Starting spots: 5317, 935, 936 and 5511 grown from 5307,
# 5507 from 5510 (editor_spread.spread, each group on its own, so the long link doesn't pull them together).
# (The owner's list said 5007, a Pixie Forest pond room; the room across the map that 936's sw exit leads to is 5507: added instead.)
import sys, os, json, re, math
here = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.normpath(os.path.join(here, '..', '..', 'src')); sys.path[:0] = [SRC]
import maplib, editor_spread as ES

EAST, WEST = [5317, 935, 936, 5511], [5507]
DV = {1: (0, -1, 0), 2: (1, 0, 0), 4: (0, 1, 0), 8: (-1, 0, 0), 3: (1, -1, 0), 9: (-1, -1, 0), 6: (1, 1, 0), 12: (-1, 1, 0), 16: (0, 0, 1), 32: (0, 0, -1)}
DN = {1: 'n', 2: 'e', 4: 's', 8: 'w', 3: 'ne', 9: 'nw', 6: 'se', 12: 'sw', 16: 'u', 32: 'd'}
rooms, exits = maplib.world()
F = os.path.join(here, 'forest_of_tears_editor.html'); h = open(F, encoding='utf-8').read()
m = max(re.finditer(r'(\{"[^\n]{1000,}?\})(?=[;\n<])', h), key=lambda m: len(m.group(1))); D = json.loads(m.group(1))
by = {r['id']: r for r in D['rooms']}
NEW = EAST + WEST
assert not set(NEW) & set(by), 'already added'
P = lambda v: (by[v]['x'], by[v]['y'])

def spread(group, root):
    S = set(group); fixed = {v: P(v) for v in by if math.dist(P(v), P(root)) < 12}
    def links(v):
        res = [(e['to'], DV[e['dir']]) for e in exits.get(v, []) if e['dir'] in DV and (e['to'] in S or (v in S and e['to'] == root))]
        res += [(u, tuple(-c for c in DV[e['dir']])) for u, l in exits.items() if u in S or u == root for e in l
                if e['to'] == v and e['dir'] in DV and u != v and (u in S or v in S)]
        return res
    st = ES.spread(S, links, fixed, [root])
    return st, ES.report(st, fixed, links), {v: round(min(math.dist(st[v], p) for p in fixed.values()), 2) for v in group}

se, re_, ne_ = spread(EAST, 5307); sw_, rw, nw_ = spread(WEST, 5510)
start = {**se, **sw_}
pc = max(r['piece'] for r in D['rooms'] if r.get('piece') is not None) + 1
for v in NEW:
    r = rooms[v]; sp = bool(r['flags'] & 8) and r['area'] == ''; x, y = start[v]
    ex = [f"{DN.get(e['dir'], e['cmd'])} → {rooms[e['to']]['name'] or 'spacer room'}" + (f" ({rooms[e['to']]['area']})" if rooms[e['to']]['area'] else '') for e in exits[v]]
    D['rooms'].append(dict(id=v, name='' if sp else r['name'], terrain='' if sp else r['terrain'], void=sp, lvl=0, area='FT', grp='ns', piece=pc,
                           x=round(x, 2), y=round(y, 2), x0=round(x, 2), y0=round(y, 2), ex=ex))
V = set(by) | set(NEW); pair = {}
for v in V:
    for e in exits.get(v, []):
        t = e['to']
        if t in V and t != v and (v in NEW or t in NEW):
            k = (min(v, t), max(v, t)); f = pair.setdefault(k, [False, False, False]); f[0 if v == k[0] else 1] = True
            if e['dir'] not in (16, 32): f[2] = True
new = [[a, b, 'two' if (f and r and flat) else ('one' if flat else 'ud')] for (a, b), (f, r, flat) in sorted(pair.items())]
D['edges'] += new
h = h[:m.start()] + json.dumps(D, separators=(',', ':')) + h[m.end():]
def sub(a, b):
    global h
    assert h.count(a) == 1, a; h = h.replace(a, b)
sub('.nd.sh rect,.nd.sh circle.shape{stroke:#7FD3E0}', '.nd.sh rect,.nd.sh circle.shape{stroke:#7FD3E0}\n.nd.ns rect,.nd.ns circle.shape{stroke:#F2C94C}')
sub("sh:'The Shire (added Oct 19)'", "sh:'The Shire (added Oct 19)',ns:'the Nidaros Shortcut (added Oct 19)'")
a = "between Forest of Tears room 1088 and the Western Trade Route (added Oct 19, movable)</span>"
sub(a, a + '\n    <i style="background:var(--t-Forest);border:2px solid #F2C94C"></i><span>The Nidaros Shortcut (added Oct 19, movable): Vale of Nidaros 5317, 935, 936 by Forgotten Woods room 5307, spacer 5511, and Valley of Mysts 5507 by room 5510 far to the west (the long line)</span>')
open(F, 'w', encoding='utf-8').write(h)
print('spots', {v: [round(c, 2) for c in start[v]] for v in NEW}, '| edges', new)
print('editor_spread (close pairs, stretched, pointing backwards, lines through rooms): east', re_, 'west', rw, '| nearest map room', {**ne_, **nw_})
