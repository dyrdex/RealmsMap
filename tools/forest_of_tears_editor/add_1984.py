# Adds The Shire room 1984 'A Dimly Lit Path' and the spacer room 21127 to the Forest of Tears layout editor (owner, Oct 19):
#   python3 add_1984.py   (edits forest_of_tears_editor.html beside it)
# 1984 is the one-room gap in the routes west of the forest: 1088 (Forest of Tears) -> nw -> 1984 -> w -> 21127 -> w -> 2319 (Western Trade Route);
# its third exit, n to 3724 (The Shire, not on the map), is left off. Group 'sh' (movable), starting where editor_spread grows them from 1088.
import sys, os, json, re, math
here = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.normpath(os.path.join(here, '..', '..', 'src')); sys.path[:0] = [SRC]
import maplib, editor_spread as ES

NEW = [1984, 21127]
DV = {1: (0, -1, 0), 2: (1, 0, 0), 4: (0, 1, 0), 8: (-1, 0, 0), 3: (1, -1, 0), 9: (-1, -1, 0), 6: (1, 1, 0), 12: (-1, 1, 0), 16: (0, 0, 1), 32: (0, 0, -1)}
DN = {1: 'n', 2: 'e', 4: 's', 8: 'w', 3: 'ne', 9: 'nw', 6: 'se', 12: 'sw', 16: 'u', 32: 'd'}
rooms, exits = maplib.world()
F = os.path.join(here, 'forest_of_tears_editor.html'); h = open(F, encoding='utf-8').read()
m = max(re.finditer(r'(\{"[^\n]{1000,}?\})(?=[;\n<])', h), key=lambda m: len(m.group(1))); D = json.loads(m.group(1))
by = {r['id']: r for r in D['rooms']}
assert not set(NEW) & set(by), 'already added'
L = json.load(open(os.path.join(SRC, 'legacy', 'ft_layout_final.json'))); fpos = dict(zip(L['ids'], zip(L['xs'], L['ys'])))
P = lambda v: fpos.get(v, (by[v]['x'], by[v]['y']))
fixed = {v: P(v) for v in by if math.dist(P(v), P(1088)) < 12}
S = set(NEW)
def links(v):
    res = [(e['to'], DV[e['dir']]) for e in exits.get(v, []) if e['dir'] in DV and e['to'] in by and (v in S or e['to'] in S)]
    res += [(u, tuple(-c for c in DV[e['dir']])) for u, l in exits.items() if (u in S or v in S) and (u in by or u in S) for e in l if e['to'] == v and e['dir'] in DV and u != v and (u in S or v in S)]
    return res
start = ES.spread(S, links, fixed, [1088])
rep = ES.report(start, fixed, links)
print('editor_spread would put them at', {v: [round(c, 2) for c in start[v]] for v in NEW}, rep, '(the gap 1088-2319 is only 2.2 rooms: too tight for its 1.6 clearance)')
start = {1984: (-30.25, -1.55), 21127: (-30.95, -1.6)}               # (so: on the line 1088 -> nw -> 1984 -> w -> 21127 -> w -> 2319, as the exits run)
pc = max(r['piece'] for r in D['rooms'] if r.get('piece') is not None) + 1
for v in NEW:
    r = rooms[v]; sp = bool(r['flags'] & 8) and r['area'] == ''; x, y = start[v]
    ex = [f"{DN.get(e['dir'], e['cmd'])} → {rooms[e['to']]['name'] or 'spacer room'}" + (f" ({rooms[e['to']]['area']})" if rooms[e['to']]['area'] else '') for e in exits[v]]
    D['rooms'].append(dict(id=v, name='' if sp else r['name'], terrain='' if sp else r['terrain'], void=sp, lvl=0, area='FT', grp='sh', piece=pc,
                           x=round(x, 2), y=round(y, 2), x0=round(x, 2), y0=round(y, 2), ex=ex))
pair = {}
for v in S:
    for e in exits[v]:
        t = e['to']
        if t in by or t in S: k = (min(v, t), max(v, t)); pair.setdefault(k, [False, False])[0 if v == k[0] else 1] = True
for u, l in exits.items():
    if u in by:
        for e in l:
            if e['to'] in S: k = (min(u, e['to']), max(u, e['to'])); pair.setdefault(k, [False, False])[0 if u == k[0] else 1] = True
new = [[a, b, 'two' if f and r else 'one'] for (a, b), (f, r) in sorted(pair.items())]
D['edges'] += new
h = h[:m.start()] + json.dumps(D, separators=(',', ':')) + h[m.end():]
def sub(a, b):
    global h
    assert h.count(a) == 1, a; h = h.replace(a, b)
sub('.nd.sr rect,.nd.sr circle.shape{stroke:#E4574B}', '.nd.sr rect,.nd.sr circle.shape{stroke:#E4574B}\n.nd.sh rect,.nd.sh circle.shape{stroke:#7FD3E0}')
sub("sr:'new area (added Oct 19)'", "sr:'new area (added Oct 19)',sh:'The Shire (added Oct 19)'")
a = "and the spacer rooms between (movable)</span>"
sub(a, a + '\n    <i style="background:var(--t-Forest);border:2px solid #7FD3E0"></i><span>The Shire room 1984 (A Dimly Lit Path) and spacer room 21127, between Forest of Tears room 1088 and the Western Trade Route (added Oct 19, movable)</span>')
open(F, 'w', encoding='utf-8').write(h)
print('spots', {v: [round(c, 2) for c in start[v]] for v in NEW}, '| edges', new)
print('editor_spread report (close pairs, stretched, pointing backwards, lines through rooms):', rep)
print('nearest other room to each:', {v: round(min(math.dist(start[v], p) for p in fixed.values()), 2) for v in NEW}, '| 1088', P(1088), '2319', P(2319))
