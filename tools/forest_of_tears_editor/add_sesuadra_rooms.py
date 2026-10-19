# Adds the owner's rooms for a new area (Oct 19: Sesuad'ra Rift and the Asgard Nexus rooms on the way to it) to the published Forest of Tears
# layout editor, without rebuilding it:  python3 add_sesuadra_rooms.py   (run from anywhere; edits forest_of_tears_editor.html beside it)
# The rooms: 2112, 21974, 21973, 13608, 21972, 21971, 21970, 13607, 2088, 2090 (grp 'sr', area 'FT', movable). None of them has an exit to a room on
# the map: the way in is Forest of Tears room 1659 -> n -> 2086 'The Platform of Sacrifice' (Asgard Nexus, not added) -> cauldron -> 2112. So 2112 is
# linked to 1659 in the editor (a dashed line, as if north of it) and the group starts next to 1659, clear of the map (editor_spread.spread_clear).
# Fixed for the spread: the Forest of Tears rooms where the owner's save has them (src/legacy/ft_layout_final.json), within NEAR of 1659.
import sys, os, json, re, math
here = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.normpath(os.path.join(here, '..', '..', 'src')); sys.path[:0] = [SRC]
import maplib, editor_spread as ES

ROOMS = [2112, 21974, 21973, 13608, 21972, 21971, 21970, 13607, 2088, 2090]
JOIN, VIA = 1659, 2086
NEAR = 30
DV = {1: (0, -1, 0), 2: (1, 0, 0), 4: (0, 1, 0), 8: (-1, 0, 0), 3: (1, -1, 0), 9: (-1, -1, 0), 6: (1, 1, 0), 12: (-1, 1, 0), 16: (0, 0, 1), 32: (0, 0, -1)}
DN = {1: 'n', 2: 'e', 4: 's', 8: 'w', 3: 'ne', 9: 'nw', 6: 'se', 12: 'sw', 16: 'u', 32: 'd', 0: '?'}

rooms, exits = maplib.world()
F = os.path.join(here, 'forest_of_tears_editor.html'); h = open(F, encoding='utf-8').read()
m = max(re.finditer(r'(\{"[^\n]{1000,}?\})(?=[;\n<])', h), key=lambda m: len(m.group(1))); D = json.loads(m.group(1))
have = {r['id'] for r in D['rooms']}
assert not have & set(ROOMS), 'already added'
L = json.load(open(os.path.join(SRC, 'legacy', 'ft_layout_final.json'))); fpos = dict(zip(L['ids'], zip(L['xs'], L['ys'])))
j = fpos[JOIN]
fixed = {v: p for v, p in fpos.items() if math.dist(p, j) < NEAR}
for r in D['rooms']:
    if r.get('fixed') and math.dist((r['x'], r['y']), j) < NEAR: fixed.setdefault(r['id'], (r['x'], r['y']))
S = set(ROOMS)

def links(v):
    res = [(e['to'], DV[e['dir']]) for e in exits.get(v, []) if e['dir'] in DV and e['to'] in S | {JOIN}]
    res += [(u, tuple(-c for c in DV[e['dir']])) for u, l in exits.items() if u in S for e in l if e['to'] == v and e['dir'] in DV and u != v]
    if v == 2112: res.append((JOIN, (0, 1, 0)))                       # (the way in through 2086: 2112 as if one step north of 1659)
    if v == JOIN: res.append((2112, (0, -1, 0)))
    return res

start = ES.spread_clear(S, links, fixed, [JOIN])
rep = ES.report(start, fixed, links)
lv = {}
for v in ROOMS:                                                       # (levels as TinTin has them, from 2112)
    lv.setdefault(v, 0)
for v in ROOMS:
    for e in exits.get(v, []):
        if e['to'] in S and e['dir'] in (16, 32): lv[e['to']] = lv[v] + (1 if e['dir'] == 16 else -1)
isspacer = lambda v: bool(rooms[v]['flags'] & 8) and rooms[v]['area'] == ''
def exlist(v):
    return [f"{DN.get(e['dir'], e['cmd'])} → {rooms[e['to']]['name'] or 'spacer room'}" + (f" ({rooms[e['to']]['area']})" if rooms[e['to']]['area'] else '')
            for e in exits.get(v, []) if e['to'] in rooms]
pieces = max(r.get('piece', 0) or 0 for r in D['rooms'] if r.get('piece') is not None) + 1
for v in ROOMS:
    r = rooms[v]; sp = isspacer(v); x, y = start[v]
    D['rooms'].append(dict(id=v, name='' if sp else r['name'], terrain='' if sp else r['terrain'], void=sp, lvl=lv[v], area='FT', grp='sr', piece=pieces,
                           x=round(x, 2), y=round(y, 2), x0=round(x, 2), y0=round(y, 2), ex=exlist(v) + ([f"(the way in: 1659 → n → 2086 The Platform of Sacrifice → cauldron → here)"] if v == 2112 else [])))
pair = {}
for v in ROOMS:
    for e in exits.get(v, []):
        t = e['to']
        if t in S and t != v:
            k = (min(v, t), max(v, t)); f = pair.setdefault(k, [False, False, False]); f[0 if v == k[0] else 1] = True
            if e['dir'] not in (16, 32): f[2] = True
new = [[a, b, 'two' if (f and r and flat) else ('one' if flat else 'ud')] for (a, b), (f, r, flat) in sorted(pair.items())] + [[min(2112, JOIN), max(2112, JOIN), 'one']]
D['edges'] += new
D['audit']['sr'] = len(ROOMS)
h = h[:m.start()] + json.dumps(D, separators=(',', ':')) + h[m.end():]

# the group's outline, legend line, select button and hover text
def sub(a, b):
    global h
    assert h.count(a) == 1, a; h = h.replace(a, b)
sub('.nd.fw rect,.nd.fw circle.shape{stroke:#D98AD0}', '.nd.fw rect,.nd.fw circle.shape{stroke:#D98AD0}\n.nd.sr rect,.nd.sr circle.shape{stroke:#E4574B}')
sub('<button id="selFw">Select rooms 5634-5638</button>', '<button id="selFw">Select rooms 5634-5638</button><button id="selSr">Select the new area\'s rooms</button>')
sub('<span>Forgotten Woods rooms 5634-5638 (unlocked, movable)</span>',
    '<span>Forgotten Woods rooms 5634-5638 (unlocked, movable)</span>\n    <i style="background:var(--t-Inside);border:2px solid #E4574B"></i><span>New area (added Oct 19): Asgard Nexus 2112, 2088, 2090, Sesuad\'ra Rift 13608 and the spacer rooms between (movable; the dashed line to 1659 is the way in through 2086, The Platform of Sacrifice)</span>')
sub("({ft:'Forest of Tears',lk:\"Lake of Tich'Pyga\",wt:'Western Trade Route',fw:'Forgotten Woods (unlocked)'})[r.grp]",
    "({ft:'Forest of Tears',lk:\"Lake of Tich'Pyga\",wt:'Western Trade Route',fw:'Forgotten Woods (unlocked)',sr:'new area (added Oct 19)'})[r.grp]")
sub("$('selFw').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.grp==='fw')sel.add(r.id)});refreshSel()};",
    "$('selFw').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.grp==='fw')sel.add(r.id)});refreshSel()};\n$('selSr').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.grp==='sr')sel.add(r.id)});refreshSel()};")
open(F, 'w', encoding='utf-8').write(h)
print('added', len(ROOMS), 'rooms,', len(new), 'edges | spots', {v: [round(c, 2) for c in start[v]] for v in ROOMS})
print('editor_spread report:', rep)
print('nearest fixed room to the group:', round(min(math.dist(start[v], p) for v in ROOMS for p in fixed.values()), 2), '| 2112 to 1659:', round(math.dist(start[2112], j), 2))
