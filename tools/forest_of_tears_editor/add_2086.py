# Adds room 2086 'The Platform of Sacrifice' (Asgard Nexus; owner, Oct 19) to the Forest of Tears layout editor, after add_sesuadra_rooms.py:
#   python3 add_2086.py   (edits forest_of_tears_editor.html beside it)
# 2086 is the way in to the new area: 1659 -> n -> 2086 -> cauldron (or enter) -> 2112. It joins the 'sr' group and starts one step north of 1659
# (editor_spread.spread from 1659, keeping clear of the other rooms); its exits are drawn as they are (one-way to 1660, 1836, 1838 and to 2112);
# the dashed stand-in line 1659 - 2112 is removed.
import sys, os, json, re, math
here = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.normpath(os.path.join(here, '..', '..', 'src')); sys.path[:0] = [SRC]
import maplib, editor_spread as ES

V, JOIN = 2086, 1659
DV = {1: (0, -1, 0), 2: (1, 0, 0), 4: (0, 1, 0), 8: (-1, 0, 0), 3: (1, -1, 0), 9: (-1, -1, 0), 6: (1, 1, 0), 12: (-1, 1, 0), 16: (0, 0, 1), 32: (0, 0, -1)}
DN = {1: 'n', 2: 'e', 4: 's', 8: 'w', 3: 'ne', 9: 'nw', 6: 'se', 12: 'sw', 16: 'u', 32: 'd'}
rooms, exits = maplib.world()
F = os.path.join(here, 'forest_of_tears_editor.html'); h = open(F, encoding='utf-8').read()
m = max(re.finditer(r'(\{"[^\n]{1000,}?\})(?=[;\n<])', h), key=lambda m: len(m.group(1))); D = json.loads(m.group(1))
by = {r['id']: r for r in D['rooms']}
assert V not in by and 2112 in by, 'run add_sesuadra_rooms.py first (once)'
L = json.load(open(os.path.join(SRC, 'legacy', 'ft_layout_final.json'))); fpos = dict(zip(L['ids'], zip(L['xs'], L['ys'])))
fixed = {v: fpos.get(v, (r['x'], r['y'])) for v, r in by.items() if math.dist(fpos.get(v, (r['x'], r['y'])), fpos[JOIN]) < 12}
links = lambda v: [(JOIN, (0, 1, 0))] if v == V else [(V, (0, -1, 0))] if v == JOIN else []
start = ES.spread({V}, links, fixed, [JOIN])
x, y = start[V]
ex = [f"{DN.get(e['dir'], e['cmd'])} → {rooms[e['to']]['name'] or 'spacer room'}" + (f" ({rooms[e['to']]['area']})" if rooms[e['to']]['area'] not in ('Forest of Tears',) else '') for e in exits[V]]
D['rooms'].append(dict(id=V, name=rooms[V]['name'], terrain=rooms[V]['terrain'], void=False, lvl=0, area='FT', grp='sr', piece=by[2112]['piece'],
                       x=round(x, 2), y=round(y, 2), x0=round(x, 2), y0=round(y, 2), ex=ex))
n0 = len(D['edges']); D['edges'] = [e for e in D['edges'] if sorted(e[:2]) != [JOIN, 2112]]; removed = n0 - len(D['edges'])
for r in by.values():                                                # (2112's hover text: the way in is now drawn)
    if r['id'] == 2112: r['ex'] = [s for s in r['ex'] if not s.startswith('(the way in')]
pair = {}
for v in by:
    for e in exits.get(v, []):
        if e['to'] == V: pair.setdefault(v, [False, False])[1] = True
for e in exits[V]:
    if e['to'] in by: pair.setdefault(e['to'], [False, False])[0] = True
new = [[min(V, t), max(V, t), 'two' if a and b else 'one'] for t, (a, b) in sorted(pair.items())]
D['edges'] += new
D['audit']['sr'] = D['audit'].get('sr', 10) + 1
h = h[:m.start()] + json.dumps(D, separators=(',', ':')) + h[m.end():]
a = "New area (added Oct 19): Asgard Nexus 2112, 2088, 2090, Sesuad'ra Rift 13608 and the spacer rooms between (movable; the dashed line to 1659 is the way in through 2086, The Platform of Sacrifice)"
assert h.count(a) == 1
h = h.replace(a, "New area (added Oct 19): Asgard Nexus 2086 (The Platform of Sacrifice, the way in from 1659), 2112, 2088, 2090, Sesuad'ra Rift 13608 and the spacer rooms between (movable)")
open(F, 'w', encoding='utf-8').write(h)
near = min((math.dist(start[V], p), v) for v, p in fixed.items() if v != JOIN)
print('2086 starts at', [round(x, 2), round(y, 2)], '| to 1659', round(math.dist(start[V], fpos[JOIN]), 2), '| nearest other room', round(near[0], 2), near[1],
      '| edges added', new, '| stand-in line removed', removed)
