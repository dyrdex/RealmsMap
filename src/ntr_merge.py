"""Puts the Northern Trade Route you arranged in the layout editor on the map.
The road is drawn exactly like the Eastern Trade Route (the same formal road). Where it meets a room that is already on the map (Darkhaven's gate,
the Shadow Grove, the Forgotten Woods) a short dirt connector joins them. Hidden rooms get no trail. The road runs over the top of anything under it,
including the Maze of Trees; a maze's name is moved to a clear spot if the road would cross it."""
import math
import numpy as np
from collections import defaultdict
from scipy import ndimage as ndi
from scipy.spatial import cKDTree


def _chains(G, pos, pinned, sigma, exact=()):
    chains = []; seen = set()
    for v in [v for v in G if len(G[v]) != 2 or v in pinned] + list(G):
        for u in G[v]:
            k = (min(v, u), max(v, u))
            if k in seen: continue
            ch = [v, u]; seen.add(k)
            while len(G[ch[-1]]) == 2 and ch[-1] not in pinned:
                nx = [q for q in G[ch[-1]] if q != ch[-2]][0]; k = (min(ch[-1], nx), max(ch[-1], nx))
                if k in seen: break
                seen.add(k); ch.append(nx)
            chains.append(ch)
    out = []
    for ch in chains:
        p = [[pos[v][0], pos[v][1]] for v in ch]
        if len(p) >= 4:
            xs = ndi.gaussian_filter1d(np.array([q[0] for q in p]), sigma, mode='nearest'); ys = ndi.gaussian_filter1d(np.array([q[1] for q in p]), sigma, mode='nearest')
            q = [[float(a), float(b)] for a, b in zip(xs, ys)]; q[0] = p[0]; q[-1] = p[-1]
            for i_, v_ in enumerate(ch):
                if v_ in exact: q[i_] = p[i_]                    # (rooms the owner wants the road to run through exactly)
            p = q
        out.append([[round(a, 2), round(b, 2)] for a, b in p])
    return out


def _samples(lines, step=0.15):
    out = []
    for ln in lines:
        for a, b in zip(ln[:-1], ln[1:]):
            n = max(1, int(math.dist(a, b) / step)); out += [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n + 1)]
    return np.array(out) if out else np.zeros((0, 2))


def _inside(poly, x, y):
    c = False; n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1: c = not c
    return c


def _nearest_on(lines, p):
    """The point on any of the polylines that is closest to p."""
    best = None
    for ln in lines:
        for a, b in zip(ln[:-1], ln[1:]):
            dx, dy = b[0] - a[0], b[1] - a[1]; L2 = dx * dx + dy * dy
            t = 0 if L2 == 0 else max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
            q = (a[0] + t * dx, a[1] + t * dy); d = math.dist(p, q)
            if best is None or d < best[0]: best = (d, q)
    return best[1]


def merge_ntr(w, layout, edges):
    pos = dict(zip(layout['ids'], zip(layout['xs'], layout['ys'])))
    hidden = set(layout.get('hidden', []))
    info = {r['id']: r for r in edges['rooms']}
    road_nodes = {v for v, r in info.items() if r.get('area') == 'NTR'}
    GR = defaultdict(set); LINKS = []; skipped = 0
    for a, b, k in edges['edges']:
        if k == 'ud' or a not in pos or b not in pos: continue
        if a in hidden or b in hidden: skipped += 1; continue
        if a in road_nodes and b in road_nodes: GR[a].add(b); GR[b].add(a)
        else: LINKS.append((a, b) if a in road_nodes else (b, a))       # (a road room, a room already on the map)
    # the road is one continuous line from its entrance to the far end of the bridge: short dead-end spurs (spacer rooms that only lead off toward
    # areas that are not mapped, a side room whose far end you hid) are left off, so nothing looks like a loose piece of road
    ENTRANCE = 1334
    dist = {ENTRANCE: 0}; q = [ENTRANCE]
    for x in q:
        for u in GR[x]:
            if u not in dist: dist[u] = dist[x] + 1; q.append(u)
    END = max(dist, key=dist.get); keep_ends = {ENTRANCE, END}
    pruned = set()
    while True:
        spurs = [v for v in GR if len(GR[v]) <= 1 and v not in keep_ends]
        if not spurs: break
        for v in spurs:
            for u in list(GR[v]): GR[u].discard(v)
            del GR[v]; pruned.add(v)
    assert all(len(GR[v]) == 2 for v in GR if v not in keep_ends), 'the road has a branch or loop'
    assert len(dist) >= len(GR), 'the road is in pieces'
    road = _chains(GR, pos, set(), 0.8)                                # one smooth line
    assert len(road) == 1, f'{len(road)} pieces of road'
    # dirt connectors to the rooms already on the map: each runs from that room to the nearest point on the road
    links = []
    for r_, c_ in LINKS:
        p = _nearest_on(road, pos[r_]); links.append([[round(pos[c_][0], 2), round(pos[c_][1], 2)], [round(p[0], 2), round(p[1], 2)]])
    # the off-ramps: where the road joins a path in the Forgotten Woods or the Shadow Grove (each gets a small junction pad)
    joins = []
    for r_, c_ in LINKS:
        if info[c_].get('src') in ('FW', 'Grove'):
            p = _nearest_on(road, pos[r_]); joins.append([round(p[0], 2), round(p[1], 2)])
    w['ntrjoins'] = joins
    w['etrtracks'] = list(w.get('etrtracks', [])) + road             # the same formal road as the Eastern Trade Route
    w['ntrroad'] = road                                              # (kept for the sub-area links that leave it)
    w['fwtracks'] = list(w['fwtracks']) + links                      # short dirt connectors to the rooms already on the map
    # nothing grows on the road or on its cleared verge
    rs = _samples(road); cleared = 0
    if len(rs):
        rt = cKDTree(rs)
        for key in ('trees', 'tufts', 'hills', 'thorns'):
            keep = [q for q in w[key] if rt.query([q[0], q[1]])[0] > 1.15]; cleared += len(w[key]) - len(keep); w[key] = keep
    # a maze's name moves to a clear spot (smaller if it has to be) when the road crosses it
    moved = []
    if len(rs):
        rt = cKDTree(rs)
        for m in w['fwmazes']:
            name = m['name']
            def fits(x, y, fs):
                half = 0.5 * 0.446 * fs * len(name) + 0.2                    # the name's half width at this size (measured: about 0.446 x the size per letter)
                top, bot = -0.8 * fs - 0.1, 0.3 * fs + 0.1
                for dx in np.linspace(-half, half, 11):
                    for dy in np.linspace(top, bot, 4):
                        if rt.query([x + dx, y + dy])[0] < 0.66: return False        # clear of the road itself (the name is drawn on top of the road's pale edge)
                        if not _inside(m['poly'], x + dx, y + dy): return False
                return True
            if fits(m['cx'], m['cy'], 0.7): continue                         # the road does not touch it
            xs = [p[0] for p in m['poly']]; ys = [p[1] for p in m['poly']]; done = False
            for fs in (0.7, 0.62, 0.55, 0.5, 0.45, 0.4):
                cand = [(math.hypot(x - m['cx'], y - m['cy']), x, y) for x in np.arange(min(xs), max(xs), 0.2) for y in np.arange(min(ys), max(ys), 0.2) if fits(x, y, fs)]
                if cand:
                    _, x, y = min(cand); m['lx'], m['ly'], m['fs'] = round(float(x), 2), round(float(y), 2), fs
                    moved.append((name, round(float(x), 2), round(float(y), 2), 'size ' + str(fs))); done = True; break
            if not done: moved.append((name, 'no clear spot inside the maze'))
    return w, dict(road_lines=len(road), road_rooms_drawn=len(GR), spur_rooms_left_off=sorted(pruned), connectors=len(links), off_ramps=len(joins), hidden_trails_skipped=skipped, trees_cleared=cleared, maze_labels_moved=moved)
