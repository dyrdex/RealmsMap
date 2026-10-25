# Adds 19 rooms to the Forest of Tears layout editor (owner, Oct 25):   python3 add_oct25_rooms.py   (edits forest_of_tears_editor.html)
# Three short chains, each grown (editor_spread.spread) from the room already here that it joins, at that room's spot in the owner's save
# (ftlayout/current; else its starting spot): The Graveyard 1944, 7807, 7808, 7809 + Abishai's Morgue 7834 from 1943 (1943 s 1944);
# Bartok Grove 1526, 9997, 10000 + New Hope Farm 10015 from 2315 (2315 s 1526); Kontaur 1561, 4002-4004, 4007-4011 + The Underworld 878
# from 1560 (1560 s 1561; 4009 d 4010 an up/down line). Group 'o25' (movable). Exits to rooms not in the editor are listed in each
# room's hover text only.
import sys, os, json, re, math
here = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.normpath(os.path.join(here, '..', '..', 'src')); sys.path[:0] = [SRC]
import maplib, editor_spread as ES

CHAINS = [(1943, [1944, 7807, 7808, 7809, 7834]), (2315, [1526, 9997, 10000, 10015]), (1560, [1561, 4002, 4003, 4004, 4007, 4008, 4009, 4010, 4011, 878])]
SAVE = sys.argv[1] if len(sys.argv) > 1 else None                     # the owner's save (ftlayout/current, as JSON), for the joining rooms' spots
DV = {1: (0, -1, 0), 2: (1, 0, 0), 4: (0, 1, 0), 8: (-1, 0, 0), 3: (1, -1, 0), 9: (-1, -1, 0), 6: (1, 1, 0), 12: (-1, 1, 0), 16: (0, 0, 1), 32: (0, 0, -1)}
DN = {1: 'n', 2: 'e', 4: 's', 8: 'w', 3: 'ne', 9: 'nw', 6: 'se', 12: 'sw', 16: 'u', 32: 'd'}
rooms, exits = maplib.world()
F = os.path.join(here, 'forest_of_tears_editor.html'); h = open(F, encoding='utf-8').read()
m = max(re.finditer(r'(\{"[^\n]{1000,}?\})(?=[;\n<])', h), key=lambda m: len(m.group(1))); D = json.loads(m.group(1))
by = {r['id']: r for r in D['rooms']}
NEW = [v for _, g in CHAINS for v in g]
assert not set(NEW) & set(by), 'already added'
sv = {}
if SAVE:
    o = json.load(open(SAVE)); o = o.get('data', o); sv = dict(zip(o['ids'], zip(o['xs'], o['ys'])))
P = lambda v: sv.get(v, (by[v]['x'], by[v]['y']))

def spread(group, root):
    S = set(group); fixed = {v: P(v) for v in by if math.dist(P(v), P(root)) < 12}
    def links(v):
        res = [(e['to'], DV[e['dir']]) for e in exits.get(v, []) if e['dir'] in DV and (e['to'] in S or (v in S and e['to'] == root))]
        res += [(u, tuple(-c for c in DV[e['dir']])) for u, l in exits.items() if u in S or u == root for e in l
                if e['to'] == v and e['dir'] in DV and u != v and (u in S or v in S)]
        return res
    st = ES.spread(S, links, fixed, [root])
    return st, ES.report(st, fixed, links), {v: round(min(math.dist(st[v], p) for p in fixed.values()), 2) for v in group}

start, reps, near = {}, {}, {}
for root, g in CHAINS:
    st, rp, nr = spread(g, root); start.update(st); reps[root] = rp; near.update(nr)
pc = max(r['piece'] for r in D['rooms'] if r.get('piece') is not None) + 1
for root, g in CHAINS:
    piece = by[root].get('piece', pc)
    for v in g:
        r = rooms[v]; sp = bool(r['flags'] & 8) and r['area'] == ''; x, y = start[v]
        ex = [f"{DN.get(e['dir'], e['cmd'])} → {rooms[e['to']]['name'] or 'spacer room'}" + (f" ({rooms[e['to']]['area']})" if rooms[e['to']]['area'] else '') for e in exits[v]]
        D['rooms'].append(dict(id=v, name='' if sp else r['name'], terrain='' if sp else r['terrain'], void=sp, lvl=0, area='FT', grp='o25', piece=piece,
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
sub('.nd.ns rect,.nd.ns circle.shape{stroke:#F2C94C}', '.nd.ns rect,.nd.ns circle.shape{stroke:#F2C94C}\n.nd.o25 rect,.nd.o25 circle.shape{stroke:#5FD39A}')
sub("ns:'the Nidaros Shortcut (added Oct 19)'", "ns:'the Nidaros Shortcut (added Oct 19)',o25:'rooms added Oct 25'")
a = "and Valley of Mysts 5507 by room 5510 far to the west (the long line)</span>"
sub(a, a + '\n    <i style="background:var(--t-Forest);border:2px solid #5FD39A"></i><span>Added Oct 25 (movable): The Graveyard 1944, 7807-7809 and Abishai\'s Morgue 7834 south of 1943; Bartok Grove 1526, 9997, 10000 and New Hope Farm 10015 south of 2315; Kontaur 1561, 4002-4004, 4007-4011 and The Underworld 878 south of 1560</span>')
open(F, 'w', encoding='utf-8').write(h)
print('spots', {v: [round(c, 2) for c in start[v]] for v in NEW})
print('edges', len(new), new)
print('editor_spread (close pairs, stretched, pointing backwards, lines through rooms):', reps, '| nearest other room', near)
