"""The Northern Trade Route where it crosses from the Forgotten Woods into the Barren Peaks, from the owner's Barren Peaks save of Oct 23 20:50Z
(legacy/bp_layout_oct23.json): the long bridge 4133-4135 and Entering the Barren Peaks 4136 moved. The road is redrawn the way the legacy
merges drew it (ntr_merge: the road from the entrance to the bridge's end 4135; bp_merge: on from 4135 into the Peaks; both smoothed, sigma
0.8), now passing exactly through the four moved rooms (EXACT), and only the points that change are replaced (the rest of each line is kept
point for point, later edits included). The two off-ramps on this stretch (pads + their dirt connectors: 5090 below 4136, 5747 by 4131) move
to the nearest point of the new road; trees and tufts within the road's verge (1.15, as ntr_merge) are cleared; route lines through the moved
rooms' old spots follow them."""
import json, math, os, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__)); LEG = os.path.join(HERE, '..', 'legacy')
sys.path.insert(0, LEG)
from ntr_merge import _chains, _nearest_on, _samples                     # noqa: E402
from scipy.spatial import cKDTree                                         # noqa: E402

MOVED = [4133, 4134, 4135, 4136]
EXACT = set(MOVED)
JOINS = {5090: 4136, 5747: 4131}                                          # off-ramp: the room off the road, the road room it joins
VERGE = 1.15
SPRITES = ('trees', 'tufts', 'hills', 'thorns')


def _ntr_line(pos, exact=()):
    L = json.load(open(os.path.join(LEG, 'ntr_layout_final.json'))); E = json.load(open(os.path.join(LEG, 'ntr_editor_edges.json')))
    p = dict(zip(L['ids'], zip(L['xs'], L['ys']))); p.update(pos)
    info = {r['id']: r for r in E['rooms']}; hidden = set(L.get('hidden', []))
    nodes = {v for v, r in info.items() if not r.get('fixed') and v in p and v not in hidden}
    G = defaultdict(set)
    for a, b, k in E['edges']:
        if k != 'ud' and a in nodes and b in nodes: G[a].add(b); G[b].add(a)
    dist = {1334: 0}; q = [1334]
    for x in q:
        for u in G[x]:
            if u not in dist: dist[u] = dist[x] + 1; q.append(u)
    keep = {1334, max(dist, key=dist.get)}
    while True:
        sp = [v for v in G if len(G[v]) <= 1 and v not in keep]
        if not sp: break
        for v in sp:
            for u in list(G[v]): G[u].discard(v)
            del G[v]
    out = _chains(G, p, set(), 0.8, exact)
    assert len(out) == 1
    return out[0]


def _bp_line(pos, exact=()):
    L = json.load(open(os.path.join(LEG, 'bp_layout_final.json'))); E = json.load(open(os.path.join(LEG, 'bp_editor_edges.json')))
    p = dict(zip(L['ids'], zip(L['xs'], L['ys']))); p.update(pos)
    hidden = set(L.get('hidden', [])); info = {r['id']: r for r in E['rooms']}
    shown = lambda v: v in p and v not in hidden; void = lambda v: bool(info[v].get('void'))
    road = {v for v, r in info.items() if r.get('area') == 'RD' and shown(v) and v not in (4133, 4134)}
    peaks = {v for v, r in info.items() if r.get('area') == 'BP' and shown(v)}
    rn = lambda v: v in road or v == 4135 or (v in peaks and void(v))
    G = defaultdict(set)
    for a, b, k in E['edges']:
        if k != 'ud' and shown(a) and shown(b) and rn(a) and rn(b): G[a].add(b); G[b].add(a)
    def comp(s):
        seen = {s}; q = [s]
        for x in q:
            for u in G[x]:
                if u not in seen: seen.add(u); q.append(u)
        return seen
    keep = road | {4135}
    while True:
        sp = [v for v in G if len(G[v]) <= 1 and v not in keep]
        if not sp: break
        for v in sp:
            for u in list(G[v]): G[u].discard(v)
            del G[v]
    main = comp(4135)
    return _chains({v: G[v] for v in main}, p, {4135}, 0.8, exact)[0]


def _patch(line, old, new):
    """line: the drawn line; old: the legacy line from the old spots (must match line where unchanged); new: from the new spots"""
    assert len(old) == len(new) <= len(line)
    ch = [i for i in range(len(old)) if old[i] != new[i]]
    assert all(line[i] == old[i] for i in range(max(ch) + 2)), 'the drawn line differs from the legacy line near the change'
    for i in ch: line[i] = list(new[i])
    return ch


def apply(town, wild, pos):
    S = json.load(open(os.path.join(LEG, 'bp_layout_oct23.json'))); P = dict(zip(S['ids'], zip(S['xs'], S['ys'])))
    oldat = {v: tuple(pos[str(v)][:2]) for v in MOVED}
    newat = {v: (P[v][0], P[v][1]) for v in MOVED}
    # ---- the road ----
    nr = wild['ntrroad'][0]; e14 = next(i for i, l in enumerate(wild['etrtracks']) if l == nr)
    o1, n1 = _ntr_line(oldat), _ntr_line(newat, EXACT)
    ch1 = _patch(nr, o1, n1); wild['etrtracks'][e14] = [list(q) for q in nr]
    bpo = _bp_line(oldat)
    e15 = next(i for i, l in enumerate(wild['etrtracks']) if i != e14 and l[:len(bpo) // 2] == bpo[:len(bpo) // 2])
    ch2 = _patch(wild['etrtracks'][e15], bpo, _bp_line(newat, EXACT))
    road = [nr, wild['etrtracks'][e15]]
    # ---- the off-ramps on this stretch ----
    moved_j = []
    for v, r in JOINS.items():
        rv = tuple(pos[str(v)][:2])
        k = next(i for i, l in enumerate(wild['fwtracks']) if len(l) == 2 and tuple(l[0]) == rv and list(l[1]) in wild['ntrjoins'])
        j = wild['ntrjoins'].index(list(wild['fwtracks'][k][1]))
        q = _nearest_on(road, rv); q = [round(q[0], 2), round(q[1], 2)]
        moved_j.append((v, wild['ntrjoins'][j], q, round(math.dist(rv, q), 2)))
        wild['ntrjoins'][j] = q; wild['fwtracks'][k] = [list(wild['fwtracks'][k][0]), q]
    # ---- the verge ----
    rt = cKDTree(_samples([l[:max(ch1 + ch2) + 3] for l in road])); gone = {}
    for k in SPRITES:
        n0 = len(wild[k]); wild[k] = [q for q in wild[k] if rt.query([q[0], q[1]])[0] > VERGE]
        if n0 - len(wild[k]): gone[k] = n0 - len(wild[k])
    # ---- rooms and route lines ----
    nfix = [0]
    def fix(o):
        if isinstance(o, list):
            if len(o) >= 2 and all(isinstance(t, (int, float)) for t in o[:2]):
                for v, q in oldat.items():
                    if abs(o[0] - q[0]) < 0.006 and abs(o[1] - q[1]) < 0.006: o[0], o[1] = newat[v]; nfix[0] += 1; return
                return
            for x in o: fix(x)
        elif isinstance(o, dict):
            for x in o.values(): fix(x)
    fix(wild['places'])
    for v in MOVED: pos[str(v)] = [newat[v][0], newat[v][1]]
    off = {v: round(min(math.dist(newat[v], q) for l in road for q in l), 3) for v in MOVED}
    return {'rooms moved (old -> new)': {v: (oldat[v], newat[v]) for v in MOVED}, 'road points replaced (to the bridge, past it)': (len(ch1), len(ch2)),
            'moved rooms: distance to the road line': off, 'off-ramps moved (room, old pad, new pad, connector length)': moved_j,
            'sprites cleared on the verge': gone, 'route points moved': nfix[0]}
