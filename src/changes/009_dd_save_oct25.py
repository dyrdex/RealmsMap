"""Owner, Oct 25: the Desert of Despair editor save of Oct 25 05:31Z (`legacy/dd_layout_oct25.json`):
  - 33 rooms moved (the canyon 6543-6567 and its spacers 22629-22631, the Great Eastern Desert tunnel 6548, 6549, 9058-9070), 19 of them now
    shown (were hidden), and the 6 rooms added that day (9077-9079, 9081, 12994, 12995; all shown) placed where saved;
  - desert trails (`fwtracks`, straight room to room, as applied/v2.3/001) for every exit between two shown rooms where one of them is newly
    shown or new (up/down exits included: the climbs into the canyon); none were drawn before (all those rooms were hidden); 12993-12994-12995 in
    the sea: the east coast's water path (B, `seawaysfaint`, `maplib.warpline`), going on from 12993;
  - Thul Ab'hara's two routes (River, East) re-traced over the moved rooms (same directions)."""
import json, math, os, maplib

R = lambda q: [round(q[0], 3), round(q[1], 3)]
NEWROOMS = [9077, 9078, 9079, 9081, 12994, 12995]


def _chains(G, P):
    chains, seen = [], set()
    for v in [v for v in G if len(G[v]) != 2] + sorted(G):
        for u in sorted(G[v]):
            k = (min(v, u), max(v, u))
            if k in seen: continue
            ch = [v, u]; seen.add(k)
            while len(G[ch[-1]]) == 2:
                nx = [q for q in G[ch[-1]] if q != ch[-2]][0]; k = (min(ch[-1], nx), max(ch[-1], nx))
                if k in seen: break
                seen.add(k); ch.append(nx)
            chains.append(ch)
    out = []
    for ch in chains:
        line = []
        for i, v in enumerate(ch):
            q = [round(P[v][0], 2), round(P[v][1], 2)]
            line += [q, list(q)] if 0 < i < len(ch) - 1 else [q]
        out.append((ch, line))
    return out


def apply(town, wild, pos):
    here = os.path.dirname(os.path.abspath(__file__))
    o = json.load(open(os.path.join(here, '..', 'legacy', 'dd_layout_oct25.json')))
    sv = dict(zip(o['ids'], zip(o['xs'], o['ys']))); hid = set(o['hidden'])
    prev = json.load(open(os.path.join(here, '..', 'legacy', 'dd_layout_az.json')))          # the save before (Oct 21 14:20Z, drawn by applied/v2.3/001)
    pv = dict(zip(prev['ids'], zip(prev['xs'], prev['ys']))); old_hidden = set(prev['hidden'])
    moved = [v for v in sv if v in pv and math.dist(sv[v], pv[v]) > 1e-6]       # only what the owner moved (21 map rooms differ from the save on purpose)
    assert all(str(v) in pos and math.dist(pos[str(v)], pv[v]) < 1e-6 for v in moved)
    for v in moved: pos[str(v)] = R(sv[v])
    for v in NEWROOMS:
        assert str(v) not in pos; pos[str(v)] = R(sv[v])
    rooms, exits = maplib.world()
    shown = lambda v: str(v) in pos and (v not in sv or v not in hid)
    newly = {v for v in moved if v not in hid and v in old_hidden} | set(NEWROOMS)
    G = {}
    for v in newly:
        for e in exits.get(v, []):
            u = e['to']
            if u != v and shown(u): G.setdefault(v, set()).add(u); G.setdefault(u, set()).add(v)
    for u, l in exits.items():                                         # (and exits from shown rooms into the new ones: 12993 s 12994)
        if not shown(u): continue
        for e in l:
            if e['to'] in newly and e['to'] != u: G.setdefault(u, set()).add(e['to']); G.setdefault(e['to'], set()).add(u)
    SEA = {12993, 12994, 12995}                                       # the east coast's water path: on from 12993, as its B line (seawaysfaint, bent)
    Gs = {v: {u for u in n if (u in SEA) == (v in SEA)} for v, n in G.items()}
    Gl = {v: n for v, n in Gs.items() if v not in SEA and n}; Gw = {v: n for v, n in Gs.items() if v in SEA and n}
    P = {v: pos[str(v)] for v in G}
    lines = _chains(Gl, P); water = _chains(Gw, P)
    wild['fwtracks'].extend(l for _, l in lines)
    wild['seawaysfaint'].extend(maplib.warpline(l) for _, l in water)
    walk, at = maplib.tracer(pos, wild)
    p = next(p for p in wild['places'] if p['name'] == "Thul Ab'hara")
    def trace(route):
        path = []
        for v in walk(route):
            if at(v) and (not path or path[-1] != R(at(v))): path.append(R(at(v)))
        return path
    for opt in p['opts']: opt['segs'] = [trace(opt['route'])]
    p['path'] = trace(p['route']); p['segs'] = [p['path']]
    return {'moved': len(moved), 'newly shown': sorted(newly), 'trail pieces': [c for c, _ in lines], 'water path': [c for c, _ in water], 'exits drawn': sum(len(s) for s in G.values()) // 2,
            "Thul Ab'hara": [len(opt['segs'][0]) for opt in p['opts']], 'its end': p['path'][-1]}
