# Fresh import of the Ashen Forest into the layout editor.
#   python3 build_ashen_editor2.py <map state before the forest (json)> <out html>
# Nothing is filtered: every room of the area, every spacer room joined to it, every exit between them.
import sys, os, json, math
from collections import defaultdict, Counter, deque
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ashen_forest as AF

w = json.load(open(sys.argv[1])); out = sys.argv[2]
rooms, exits = AF._world()
DV = AF.DV
DN = {1: 'n', 2: 'e', 4: 's', 8: 'w', 3: 'ne', 9: 'nw', 6: 'se', 12: 'sw', 16: 'u', 32: 'd', 0: '?'}
tr = w['track']

# ---- 1. what is in the area, straight from the map ----
A = {v for v, r in rooms.items() if r['area'] == 'The Ashen Forest'}
isspacer = lambda v: bool(rooms[v]['flags'] & 8) and rooms[v]['area'] == ''
rev = defaultdict(list)
for v, l in exits.items():
    for e in l: rev[e['to']].append(v)
S = set(A); dq = deque(A)
while dq:                                                       # every spacer room joined to the area by spacer rooms only, however long the chain
    v = dq.popleft()
    for t in [e['to'] for e in exits.get(v, [])] + rev[v]:
        if t not in S and isspacer(t): S.add(t); dq.append(t)
SPACERS = S - A

# ---- 2. the fixed rooms: rooms already on the finished map that the forest connects to, with the whole chain of rooms between ----
SRC = {'town': 'DH', 'grove': 'Grove', 'woods': 'FW'}
fixed = {}
for i, a in enumerate(w['ashlinks']):
    for k, p in enumerate(a['chain']):
        if p in fixed: continue
        q = tr[f'chain{i}_{k}']
        fixed[p] = dict(x=q[0], y=q[1], src=SRC[a['area']])
BURROWS = {v for v in A if rooms[v]['terrain'] == 'Underground'}  # the underground burrow rooms are left out, as you asked
_rf = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ashen_removed_rooms.json')
PILES = set(json.load(open(_rf))['ids']) if os.path.exists(_rf) else set()   # the two piles of stacked rooms you set aside: removed with all their exits
LEFT_OUT = BURROWS | (PILES & A)
for _k, _r in enumerate(w.get('dhx', [])):                     # Darkhaven's road east from the Cross Roads to A Rock Strewn Trail: fixed rooms too
    if _r not in fixed: fixed[_r] = dict(x=tr[f'dhx{_k}'][0], y=tr[f'dhx{_k}'][1], src='DH')
FREE = S - set(fixed) - LEFT_OUT - PILES                       # every other room of the area and every other spacer room: free to move
_nb = defaultdict(set)
for v in FREE | set(fixed):
    for e in exits.get(v, []):
        if e['to'] in FREE | set(fixed): _nb[v].add(e['to']); _nb[e['to']].add(v)
# spacer rooms that are left with no real room to join (alone, or only to each other) have nothing left to connect
ORPHANS = set(); _seen = set()
for v in sorted(FREE):
    if v in _seen: continue
    comp = set(); st = [v]
    while st:
        x = st.pop()
        if x in comp: continue
        comp.add(x); st += [y for y in _nb[x] if y not in comp and (y in FREE or y in fixed)]
    _seen |= comp
    if all((c not in A and c not in fixed) for c in comp) and not any(c in fixed for c in comp): ORPHANS |= comp
FREE -= ORPHANS
A_KEPT = A - LEFT_OUT
NODES = FREE | set(fixed)

# ---- 3. the layout TinTin's own exits give: north is up, every compass exit is one step ----
nb = defaultdict(list)
for v in NODES:
    for e in exits.get(v, []):
        t = e['to']
        if t in NODES and e['dir'] in DV:
            d = DV[e['dir']]; nb[v].append((t, d)); nb[t].append((v, (-d[0], -d[1], -d[2])))
door = AF.WEST_DOOR
pos = {door: (0, 0, 0)}; dq = deque([door])
while dq:
    v = dq.popleft()
    for t, d in nb[v]:
        if t not in pos: pos[t] = (pos[v][0] + d[0], pos[v][1] + d[1], pos[v][2] + d[2]); dq.append(t)
dt = [sum(tr[f'ash{i}'][0] for i, a in enumerate(w['ashlinks']) if a['ash'] == door) / sum(1 for a in w['ashlinks'] if a['ash'] == door),
      sum(tr[f'ash{i}'][1] for i, a in enumerate(w['ashlinks']) if a['ash'] == door) / sum(1 for a in w['ashlinks'] if a['ash'] == door)]
place = {v: [p[0] + dt[0], p[1] + dt[1], p[2]] for v, p in pos.items() if v in FREE}
# pieces that join the rest only through other areas (the moat) get a small layout of their own
left = [v for v in FREE if v not in place]
seen = set(); groups = []
for v in sorted(left):
    if v in seen: continue
    comp = {v: (0, 0, 0)}; q = [v]
    while q:
        x = q.pop(0)
        for t, d in nb[x]:
            if t in FREE and t not in comp: comp[t] = (comp[x][0] + d[0], comp[x][1] + d[1], comp[x][2] + d[2]); q.append(t)
    seen |= set(comp); groups.append(comp)
maxx = max(p[0] for p in place.values()); miny = min(p[1] for p in place.values()); stack = 0
for comp in groups:
    near = 2868 in place and any(r in comp for r in (2874, 2875, 2876))   # the moat lies just east of the slime rivulet's last room
    bx, by = (place[2868][0] + 2.5, place[2868][1]) if near else (maxx + 6, miny + stack)
    for v, p in comp.items(): place[v] = [bx + p[0], by + p[1], p[2]]
    if not near: stack += 6
assert all(v in place for v in FREE), 'a room has no position'

# rooms on other levels start a little off the ground rooms they sit over; rooms that land on exactly the same spot are nudged apart
LV = 0.55
xy = {}
for v, p in place.items(): xy[v] = [p[0] + LV * p[2], p[1] - LV * p[2]]
cells = defaultdict(list)
for v in sorted(xy): cells[(round(xy[v][0] / 0.3), round(xy[v][1] / 0.3))].append(v)
nudged = 0
for c, vs in cells.items():
    for k, v in enumerate(vs[1:], 1): xy[v][0] += 0.42 * k; xy[v][1] += 0.42 * k; nudged += 1

# ---- 4. rooms and exits for the editor ----
def exlist(v):
    res = []
    for e in exits.get(v, []):
        r = rooms[e['to']]; res.append(f"{DN.get(e['dir'], '?')} → {r['name'] or 'spacer room'}" + (f" ({r['area']})" if r['area'] and r['area'] != 'The Ashen Forest' else ''))
    return res
R = []
for v in sorted(FREE):
    r = rooms[v]
    R.append(dict(id=v, name=r['name'] if v in A else '', terrain=r['terrain'] if v in A else '', void=(v not in A), lvl=place[v][2],
                  x=round(xy[v][0], 2), y=round(xy[v][1], 2), x0=round(xy[v][0], 2), y0=round(xy[v][1], 2), ex=exlist(v)))
for v, f in fixed.items():
    r = rooms[v]
    R.append(dict(id=v, name=r['name'] or 'spacer room', terrain='', void=False, lvl=0, x=round(f['x'], 2), y=round(f['y'], 2), x0=round(f['x'], 2), y0=round(f['y'], 2), fixed=True, src=f['src'], ex=exlist(v)))
_sf = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ashen_layout_final.json')
if os.path.exists(_sf):                                        # your arrangement is the starting point
    _sv = json.load(open(_sf)); _at = {v: (x, y) for v, x, y in zip(_sv['ids'], _sv['xs'], _sv['ys'])}
    for r in R:
        if not r.get('fixed') and r['id'] in _at: r['x'] = r['x0'] = round(_at[r['id']][0], 2); r['y'] = r['y0'] = round(_at[r['id']][1], 2)
# ---- the Eastern Trade Route: every room of the area and every spacer room joined to it ----
_sv2 = json.load(open(_sf)); HIDDEN0 = [i for i in _sv2.get('hidden', [])]
_at_all = {v: (x, y) for v, x, y in zip(_sv2['ids'], _sv2['xs'], _sv2['ys'])}
ETR = {v for v, r in rooms.items() if r['area'] == 'Eastern Trade Route'}
def _closure(base):
    s = set(base); q = deque(base)
    while q:
        v = q.popleft()
        for t_ in [e['to'] for e in exits.get(v, [])] + rev[v]:
            if t_ not in s and isspacer(t_): s.add(t_); q.append(t_)
    return s
SE = _closure(ETR)
AF_NODES = {r['id'] for r in R}                                 # what the forest editor already holds (your layout)
REMOVED_AF = S - AF_NODES                                       # forest rooms and spacers you removed (burrows, the two piles, the leftovers)
shared = (SE - ETR) & S                                         # spacer rooms that both areas' chains reach
new_sp = (SE - ETR) - S                                         # spacer rooms only the Trade Route reaches
raw_nb = defaultdict(set)
for v, l in exits.items():
    for e in l: raw_nb[v].add(e['to']); raw_nb[e['to']].add(v)
keep_sp = set(new_sp); dropped_sp = set()
while True:                                                     # a spacer chain that ran into a removed forest room is a broken link: drop its stub
    kept = AF_NODES | ETR | keep_sp
    bad = {v for v in keep_sp if sum(1 for u in raw_nb[v] if u in kept) < 2 and any(u in REMOVED_AF for u in raw_nb[v])}
    if not bad: break
    keep_sp -= bad; dropped_sp |= bad
etr_nodes = ETR | keep_sp
ANCH = AF_NODES                                                 # the forest rooms the Trade Route can connect to
# layout from TinTin's own exits, north is up
nbE = defaultdict(list)
for v in etr_nodes | (shared & AF_NODES):
    for e in exits.get(v, []):
        t_ = e['to']
        if t_ in (etr_nodes | (shared & AF_NODES)) and e['dir'] in DV:
            d = DV[e['dir']]; nbE[v].append((t_, d)); nbE[t_].append((v, (-d[0], -d[1], -d[2])))
posE = {}; comps = []
for v in sorted(etr_nodes):
    if v in posE: continue
    comp = {v: (0, 0, 0)}; q = [v]
    while q:
        x = q.pop(0)
        for t_, d in nbE[x]:
            if t_ not in comp: comp[t_] = (comp[x][0] + d[0], comp[x][1] + d[1], comp[x][2] + d[2]); q.append(t_)
    comps.append(comp); posE.update({k: p for k, p in comp.items() if k in etr_nodes})
# one connected piece is placed by its first room; later pieces are tied to it through the forest links below
_AFpos = {r['id']: (r['x'], r['y']) for r in R}
_vec = lambda e: DV[e['dir']]
links = []                                                      # (trade-route node, forest node, vector from forest node to the trade-route node)
for v in etr_nodes:
    for e in exits.get(v, []):
        if e['to'] in ANCH and e['dir'] in DV: d = _vec(e); links.append((v, e['to'], (-d[0], -d[1])))
for u in ANCH:
    for e in exits.get(u, []):
        if e['to'] in etr_nodes and e['dir'] in DV: d = _vec(e); links.append((e['to'], u, (d[0], d[1])))
# each connected piece of the Trade Route is moved as a whole to the spot its own forest links point to
final = {}
for comp in comps:
    cl = [(v, f, vv) for v, f, vv in links if v in comp and v in etr_nodes]
    cl = [x for x in cl if fixed.get(x[1], {}).get('src') == 'DH'] or cl      # the fixed Darkhaven rooms are the surest guide to where the entrance goes
    if cl: off = (sum(_AFpos[f][0] + vv[0] - comp[v][0] for v, f, vv in cl) / len(cl), sum(_AFpos[f][1] + vv[1] - comp[v][1] for v, f, vv in cl) / len(cl))
    else:  off = None
    final[id(comp)] = off
# where the exits suggest (x0,y0); then everything is moved off to the east of the forest so nothing lands on a forest room
raw_xy = {}
for comp in comps:
    off = final[id(comp)]
    if off is None: off = (max(p[0] for p in _AFpos.values()) + 10, min(p[1] for p in _AFpos.values()))
    for v, p in comp.items():
        if v in etr_nodes: raw_xy[v] = [p[0] + off[0], p[1] + off[1], p[2]]
afx = max(p[0] for p in _AFpos.values())
minx = min(p[0] for p in raw_xy.values()); ty = sum(f_[1] for f_ in [_AFpos[f] for v, f, vv in links if v in etr_nodes]) / max(1, len([1 for v, f, vv in links if v in etr_nodes])) - sum(p[1] for p in raw_xy.values()) / len(raw_xy)
sx = afx + 8 - minx
for v in sorted(etr_nodes):
    x0, y0, z = raw_xy[v]; r_ = rooms[v]
    R.append(dict(id=v, name=r_['name'] if v in ETR else '', terrain=r_['terrain'] if v in ETR else '', void=(v not in ETR), lvl=z, area='ETR',
                  x=round(x0 + sx + LV * z, 2), y=round(y0 + ty - LV * z, 2), x0=round(x0 + LV * z, 2), y0=round(y0 - LV * z, 2), ex=exlist(v)))
KC_ROOM, KC_LINKS = 2981, (2982, 3261)                          # "A Narrow Path of Dirt and Stone": it joins The King's Crossing (Trade Route) and a forest room
_at = {r['id']: r for r in R}
assert all(l in _at for l in KC_LINKS), 'a room it should connect to is not in the editor'
_vec = None
for e in exits.get(KC_ROOM, []):
    if e['to'] == 2982 and e['dir'] in DV: _vec = DV[e['dir']]               # 2981 lies this way from 2982
_vec = (-_vec[0], -_vec[1]) if _vec else (1, 0)
_kc_from = [e for e in exits.get(2982, []) if e['to'] == KC_ROOM and e['dir'] in DV]
_d = DV[_kc_from[0]['dir']] if _kc_from else (1, 0, 0)
R.append(dict(id=KC_ROOM, name=rooms[KC_ROOM]['name'], terrain=rooms[KC_ROOM]['terrain'], void=False, lvl=0, area='KC',
              x=round(_at[2982]['x'] + _d[0], 2), y=round(_at[2982]['y'] + _d[1], 2), x0=round(_at[2982]['x0'] + _d[0], 2), y0=round(_at[2982]['y0'] + _d[1], 2), ex=exlist(KC_ROOM)))
# ---- single rooms from other areas, with just the exits you listed ----
EXTRA = {   # room: the exits to show ('all' = every exit)
    3080: ('sw', 'e'), 14252: 'all', 14253: ('w', 'se'), 14254: ('nw', 'se'), 14382: ('nw', 'se'), 14378: ('nw', 'w'), 14377: 'all'}
DNAME = {1: 'n', 2: 'e', 4: 's', 8: 'w', 3: 'ne', 9: 'nw', 6: 'se', 12: 'sw', 16: 'u', 32: 'd'}
def _chain(start, first):                                       # the spacer rooms from `start` through its exit `first`, up to the real room at the end
    path = []; prev = start; cur = first
    while isspacer(cur):
        path.append(cur); nxt = [e['to'] for e in exits.get(cur, []) if e['to'] != prev and e['to'] not in path]
        if not nxt: return path, None
        prev, cur = cur, nxt[0]
    return path, cur
allowed = set(); ex_sp = []                                     # pairs of rooms to show; spacer rooms to bring along
for v, dirs in EXTRA.items():
    for e in exits.get(v, []):
        if dirs != 'all' and DNAME.get(e['dir']) not in dirs: continue
        t_ = e['to']
        if isspacer(t_):
            path, end = _chain(v, t_); ex_sp += [p for p in path if p not in ex_sp]
            seq = [v] + path + ([end] if end else [])
            for a_, b_ in zip(seq[:-1], seq[1:]): allowed.add((min(a_, b_), max(a_, b_)))
        else: allowed.add((min(v, t_), max(v, t_)))
EX_REAL = list(EXTRA); EX_ALL = EX_REAL + ex_sp
assert all(v not in AF_NODES for v in EX_ALL) or True
_at = {r['id']: r for r in R}
joins = sorted({x for p in allowed for x in p if x in _at and x not in EX_ALL})              # rooms already on the map that these join
# TinTin's own layout of the group, from 3079 (the room it hangs off)
rel = {3079: (0, 0)}; q = [3079]
while q:
    v = q.pop(0)
    for a_, b_ in allowed:
        for s_, t_ in ((a_, b_), (b_, a_)):
            if s_ != v or t_ in rel or t_ not in EX_ALL: continue
            vec = None
            for e in exits.get(s_, []):
                if e['to'] == t_ and e['dir'] in DV: vec = DV[e['dir']]
            if vec is not None: rel[t_] = (rel[s_][0] + vec[0], rel[s_][1] + vec[1]); q.append(t_)
            else:
                for e in exits.get(t_, []):
                    if e['to'] == s_ and e['dir'] in DV: d_ = DV[e['dir']]; rel[t_] = (rel[s_][0] - d_[0], rel[s_][1] - d_[1]); q.append(t_); break
assert all(v in rel for v in EX_ALL), [v for v in EX_ALL if v not in rel]
bx, by, bx0, by0 = _at[3079]['x'], _at[3079]['y'], _at[3079]['x0'], _at[3079]['y0']
_others = [(r['x'], r['y']) for r in R]
for shift in range(0, 60, 2):                                  # start where the group lands on no other room
    if all(min(math.hypot(bx + rel[v][0] + shift - ox, by + rel[v][1] - oy) for ox, oy in _others) >= 0.9 for v in EX_ALL): break
for v in EX_ALL:
    r_ = rooms[v]; real = v in EX_REAL
    R.append(dict(id=v, name=r_['name'] if real else '', terrain=r_['terrain'] if real else '', void=not real, lvl=0, area='EX', areaName=r_['area'] if real else '',
                  x=round(bx + rel[v][0] + shift, 2), y=round(by + rel[v][1], 2), x0=round(bx0 + rel[v][0], 2), y0=round(by0 + rel[v][1], 2), ex=exlist(v)))
# every real room outside the area that touches the forest through the fixed rooms is already in `fixed`; edges are drawn for every exit between rooms in the editor
V = {r['id'] for r in R}
pair = defaultdict(lambda: [False, False, False])               # [a to b exists, b to a exists, any non-vertical exit]
n_exits = 0
for v in V:
    for e in exits.get(v, []):
        t = e['to']
        if t not in V: continue
        k = (min(v, t), max(v, t))
        pair[k][0 if v == k[0] else 1] = True
        if e['dir'] not in (16, 32): pair[k][2] = True
        if v in FREE or t in FREE: n_exits += 1                 # exits of the area's own rooms and spacers
for k in [k for k in list(pair) if KC_ROOM in k and (set(k) - {KC_ROOM}).isdisjoint(KC_LINKS)]: del pair[k]
for r in R:                                                    # the editor opens on the layout that is on the map: every room starts where you left it
    if not r.get('fixed') and r['id'] in _at_all: r['x'] = round(_at_all[r['id']][0], 2); r['y'] = round(_at_all[r['id']][1], 2)
CUT = {tuple(sorted(p)) for p in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ashen_cut_links.json')))['pairs']}   # trails you disconnected
for k in CUT: pair.pop(k, None)
for k in [k for k in list(pair) if (k[0] in EX_ALL or k[1] in EX_ALL) and k not in allowed]: del pair[k]      # only the exits you listed
EDG = []
for (a, b), (f, r, flat) in pair.items():
    EDG.append([a, b, 'two' if (f and r and flat) else ('one' if flat else 'ud')])
# only exits that stay inside the area (and its spacers) count for the audit against the raw map
KEPT = S - LEFT_OUT - PILES - ORPHANS
raw_inside = sum(1 for v in KEPT for e in exits.get(v, []) if e['to'] in KEPT)
drawn_inside = sum(1 for v in KEPT for e in exits.get(v, []) if e['to'] in KEPT and (min(v, e['to']), max(v, e['to'])) in pair)
audit = dict(rooms=len([r for r in R if r['id'] in A]), rooms_total=len(A_KEPT), spacers=len([r for r in R if r['id'] in SPACERS]), spacers_total=len(SPACERS - ORPHANS - PILES), left_out=len(BURROWS), piles=len(PILES), remnants=len(ORPHANS),
             exits=drawn_inside, exits_total=raw_inside, fixed=len(fixed))
assert audit['rooms'] == audit['rooms_total'] and audit['spacers'] == audit['spacers_total'] and audit['exits'] == audit['exits_total'], audit

ETR_ALL = ETR | keep_sp | (shared & AF_NODES)
_pairs_etr = lambda: {(min(v, e['to']), max(v, e['to'])) for v in ETR_ALL for e in exits.get(v, []) if e['to'] in ETR_ALL}
_tot_exits = sum(1 for v in SE for e in exits.get(v, []) if e['to'] in SE)
_in_exits = sum(1 for v in SE for e in exits.get(v, []) if e['to'] in SE and (min(v, e['to']), max(v, e['to'])) in pair and v in ETR_ALL and e['to'] in ETR_ALL)
_dropped_exits = sum(1 for v in SE for e in exits.get(v, []) if e['to'] in SE and (v in dropped_sp or e['to'] in dropped_sp or (v in REMOVED_AF) or (e['to'] in REMOVED_AF)))
_lp = {(min(v, f), max(v, f)) for v, f, vv in links}
_removed_lp = {(min(v, e['to']), max(v, e['to'])) for v in ETR for e in exits.get(v, []) if e['to'] in A and e['to'] not in AF_NODES} | {(min(e['to'], u), max(e['to'], u)) for u in A if u not in AF_NODES for e in exits.get(u, []) if e['to'] in ETR}
audit['etr'] = dict(rooms=len([r for r in R if r.get('area') == 'ETR' and not r['void']]), rooms_total=len(ETR), spacers=len(keep_sp) + len(shared & AF_NODES), spacers_total=len(SE - ETR) - len(dropped_sp) - len(shared - AF_NODES),
                    spacers_dropped=len(dropped_sp) + len(shared - AF_NODES), exits=_in_exits, exits_total=_tot_exits - _dropped_exits, links=len({(min(v, f), max(v, f)) for v, f, vv in links if v in ETR and f in A} - CUT), links_cut=len({(min(v, f), max(v, f)) for v, f, vv in links if v in ETR and f in A} & CUT), links_hidden=len({(min(v, f), max(v, f)) for v, f, vv in links if v in ETR and f in A and f in HIDDEN0} - CUT), links_ignored=len(_removed_lp))
audit['ex'] = dict(rooms=len(EX_REAL), spacers=len(ex_sp), ids=EX_REAL, joins=joins)
audit['kc'] = dict(id=KC_ROOM, name=rooms[KC_ROOM]['name'], links=list(KC_LINKS))
print('ETR AUDIT', audit['etr'])
rd = lambda poly: [[round(x, 2), round(y, 2)] for x, y in poly]
ctx = dict(land=[rd(p) for p in w['geo']['land']], water=[rd(p) for p in w['geo']['water']],
           tracks=[rd(t) for t in list(w['fwtracks']) + list(w['swtracks']) + [w['road'], w['southpath'], w['link']] + list(w['ring']) if len(t) > 1],
           mazes=[dict(poly=rd(m['poly'])) for m in w['fwmazes']], town=[-7.4, -9.4, 7.4, 9.4],
           labels=[[0, 0.4, 'Darkhaven', 2.4], [3, -14.2, 'Shadow Grove', 1.5], [36, -40, 'Forgotten Woods', 2.4]])
D = dict(rooms=R, edges=EDG, groups=[], ctx=ctx, audit=audit, hidden0=HIDDEN0)
json.dump(D, open('ashen_editor2_data.json', 'w'), separators=(',', ':'))
t = open('/home/claude/fwbench/ashen_editor2.html').read()
open(out, 'w').write(t.replace('__DATA__', json.dumps(D, separators=(',', ':'))))
print('AUDIT', audit)
print('terrain of imported rooms:', dict(Counter(r['terrain'] for r in R if r['id'] in A)))
print('levels:', dict(Counter(r['lvl'] for r in R)), '| rooms nudged apart because they landed on the same spot:', nudged, '| edges', len(EDG), '| file', os.path.getsize(out) // 1024, 'KB')
