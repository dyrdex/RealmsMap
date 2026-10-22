"""The Azure Sea along Otherland's east coast (owner, Oct 22; the rooms placed in the Otherland editor, save `legacy/ol_layout_final.json`, grp 'az':
the save's rooms that are not in `legacy/ol_editor_edges.json`):
  - the coast, worked out once (owner, Oct 22: no fill-then-cut): inside ZONE_R of the sea rooms and their routes the land is the part nearer to
    Otherland's land rooms and trails than to the sea rooms and routes (the Voronoi line between the two), within the old land, the round CAP
    round an east-coast room the save moved off it, and the notches closed by CLOSE_R (pieces wholly inside the zone); smoothed SMOOTH; outside the
    zone the land is as it was. Pieces without a land room become sea;
  - The Iceberg 15154 (owner, Oct 22): an iceberg the size of one room (ICE1_R), sea between it and the mainland (it counts as a sea room for the coast);
  - the sea round them: SEA_W off the new coast and about AZ_R round every sea room and route, joined to the sea there, `seafill` + `seashore`; the
    sea fills now under land give way to it; the snow texture, plants and shore ice in the new sea dropped, drifts added on new land at the snow's
    density; shore ice on new land or touching a room or route dropped (owner: no coastal additions for now, so none added);
  - routes: the coastal path (the chain nearest the mainland, 6179 .. 15250, 15255, 15606) as the Sea of Sorrows' routes (`seawaysfaint`), as straight
    room-to-room segments, exactly on the layout (owner, Oct 22); the routes leading east off it as the Desert of Despair east coast's (`seawaves`,
    fainter, wavy). Exits between a sea room and a land room (up/down ones included, owner Oct 22) change at the coast, exactly: the water route up to
    it (in the style of the sea room's side), an Otherland trail (`oltracks`, to the room's warped spot) on from it. Not drawn: 5987-22496 (owner),
    up/down exits that a flat exit between the same rooms replaces; 15606's exits to the Grey Beach (Northern Plains) are left off.
  - the rooms join `pos` (room_pos)."""
import json, math, os, random, heapq
from collections import defaultdict
import shapely
from shapely import STRtree
from shapely.geometry import Polygon, LineString, Point, MultiPoint, box
from shapely.ops import unary_union, voronoi_diagram
import maplib

HERE = os.path.dirname(os.path.abspath(__file__)); LEG = os.path.join(HERE, '..', 'legacy')
WET = {'Swimming', 'Underwater', 'Water', 'Seafloor'}
ICEBERG = [22531, 22532, 22533, 22534, 22535, 6166, 13379, 13380, 6180]      # land: the Iceberg island (applied/v2.4/001)
AS_LAND = {6147, 6148}
ICE1, ICE1_R = 15154, 0.55                                                     # owner (Oct 22): a one-room iceberg
NOT_DRAWN = {(5987, 22496)}                                                   # owner (Oct 22)
COAST_END = [6179, 15606]
ZONE_R, SAMPLE = 6.0, 0.2                                                     # the coast is worked out this near the sea rooms; feature sampling
CAP, CLOSE_R, SMOOTH = 1.6, 3.5, 0.6
EAST = box(60, 175, 110, 232)                                                 # notches closed only on the east coast (not the south shore's inlets)
SEA_W, SEA_CLOSE, AZ_R = 6.0, 6.0, 3.0
ICE_CLEAR = 0.6                                                               # shore ice this far from rooms and routes
WAVE_AMP, WAVE_LEN = 0.12, 2.5                                                # as applied/v2.4/001's seawaves
CLIMBS = {(6173, 13276), (6186, 15657), (22524, 15659), (15154, 15738), (15171, 13351), (15175, 13341), (15187, 13336), (15195, 15739),
          (15741, 13327), (13143, 13198), (13144, 13291)}                     # owner (Oct 22): these go "up the cliff" (low room, high room)
CLIFF_W, CLIFF_L = 0.55, 0.8                                                  # the cliff face: width; past the end climbs along the coast (13289's flat
                                                                              #  landing, 1.4 past 6173's, stays off it)
STEP_D, STEP_W = 0.14, 0.17                                                   # steps: apart, half width
TRACK_A, TRACK_L = 0.16, 7.0                                                  # applied/v2.4/001's trail warp (its rooms are on the warped spots)


def _wave(line, amp=WAVE_AMP, wl=WAVE_LEN):
    pts = [line[0]] + [q for a, q in zip(line, line[1:]) if math.dist(a, q) > 1e-6]
    out = [[round(pts[0][0], 3), round(pts[0][1], 3)]]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        L = math.hypot(bx - ax, by - ay); n = max(1, round(L / wl)); m = max(4, int(L / 0.06))
        nx, ny = -(by - ay) / L, (bx - ax) / L
        for i in range(1, m + 1):
            t = i / m; s = amp * math.sin(math.pi * n * t * 2) * (1 if L > 0.8 else 0)
            out.append([round(ax + (bx - ax) * t + nx * s, 3), round(ay + (by - ay) * t + ny * s, 3)])
    return out


def _sample(geom, step):
    if geom.geom_type == 'Point' or geom.length < 1e-9: return [geom.coords[0]]
    n = max(1, int(geom.length / step)); return [geom.interpolate(i / n, normalized=True).coords[0] for i in range(n + 1)]


def _polys(g):
    return [q for q in getattr(g, 'geoms', [g]) if q.geom_type == 'Polygon' and not q.is_empty]


def apply(town, wild, pos):
    rooms, exits = maplib.world()
    S = json.load(open(os.path.join(LEG, 'ol_layout_final.json'))); E = json.load(open(os.path.join(LEG, 'ol_editor_edges.json')))
    P = {v: (x, y) for v, x, y in zip(S['ids'], S['xs'], S['ys'])}; H = set(S['hidden']); R = {r['id'] for r in E['rooms']}
    AZ = {v for v in P if v not in R and v not in H}
    for v in sorted(AZ): pos[str(v)] = [P[v][0], P[v][1]]
    at = lambda v: tuple(pos[str(v)])
    geo = wild['geo']; rd = lambda g: [[round(x, 3), round(y, 3)] for x, y in list(g.exterior.coords)[:-1]]
    rings = lambda g: [rd(q) for q in _polys(g)] + [[[round(x, 3), round(y, 3)] for x, y in list(h.coords)[:-1]] for q in _polys(g) for h in q.interiors]
    ph = random.Random(13287); a1, a2, a3, a4 = (ph.uniform(0, 2 * math.pi) for _ in range(4))
    warp = lambda x, y: (x + TRACK_A * (0.7 * math.sin(2 * math.pi * y / TRACK_L + a1) + 0.3 * math.sin(2 * math.pi * (x + y) / (TRACK_L * 1.6) + a3)),
                         y + TRACK_A * (0.7 * math.sin(2 * math.pi * x / TRACK_L + a2) + 0.3 * math.sin(2 * math.pi * (x - y) / (TRACK_L * 1.6) + a4)))

    # ---- the exits drawn ----
    FLATP = {frozenset((v, e['to'])) for v, l in exits.items() for e in l if e['dir'] not in (0, 16, 32) and e['to'] != v}
    olroom = {int(k) for k in pos if int(k) not in AZ and rooms.get(int(k), {}).get('area') == 'Otherland'}
    island = set(ICEBERG)
    pair = {}
    for v in AZ | olroom | island:
        for e in exits.get(v, []):
            t = e['to']; k = (min(v, t), max(v, t))
            if t == v or not (v in AZ or t in AZ) or t not in AZ | olroom | island or k in NOT_DRAWN: continue
            if e['dir'] in (16, 32) and frozenset(k) in FLATP: continue
            pair[k] = pair.get(k, False) or e['dir'] in (16, 32)
    edges = sorted(pair); nud = sum(1 for k in edges if pair[k])
    landr = {v for v in olroom | island if (rooms[v]['terrain'] not in WET or v in AS_LAND) and v != ICE1}
    wetr = {v for v in olroom if v not in landr and v != ICE1}
    seaR = {v for v in AZ if min((math.dist(at(v), at(u)) for u in landr), default=9) > 0.3} | wetr | {ICE1}
    onland = {v for v in AZ if min(math.dist(at(v), at(u)) for u in landr | {ICE1}) <= 0.3}           # (15172 sits on 15154: its routes change there)
    seaside = (AZ | wetr) - onland                                                              # (the rooms whose exits are water routes)
    sea_lines = [LineString([at(a), at(b)]) for a, b in edges if a in seaR and b in seaR]

    # ---- 1. the coast, once ----
    snowp = [Polygon(p).buffer(0) for p in geo['snow'] if len(p) > 2]
    key = lambda p: (round(Polygon(p).area, 1), tuple(round(c, 1) for c in Polygon(p).bounds))
    Z = unary_union([Point(at(v)) for v in seaR if v in AZ] + sea_lines).buffer(ZONE_R)
    old = unary_union([g for g in snowp if g.intersects(Z)])
    oldkeys = {key(p) for p, g in zip([p for p in geo['snow'] if len(p) > 2], snowp) if g.intersects(Z)}
    land_lines = [LineString(t) for t in wild.get('oltracks', []) + wild.get('oltunnels', []) if len(t) > 1]
    zb = Z.buffer(ZONE_R * 2).bounds
    inzb = lambda q: zb[0] <= q[0] <= zb[2] and zb[1] <= q[1] <= zb[3]
    lpts = {(round(x, 2), round(y, 2)) for x, y in [warp(*at(v)) for v in landr] + [at(v) for v in landr] + [q for l in land_lines for q in _sample(l, SAMPLE)] if inzb((x, y))}
    spts = {(round(x, 2), round(y, 2)) for x, y in [at(v) for v in seaR] + [q for l in sea_lines for q in _sample(l, SAMPLE)] if inzb((x, y))} - lpts
    allp = sorted(lpts) + sorted(spts); tag = {p: 0 for p in lpts}; tag.update({p: 1 for p in spts})
    cg = list(voronoi_diagram(MultiPoint(allp), envelope=box(*zb).buffer(20)).geoms)
    idx = STRtree([Point(p) for p in allp]).query(cg, predicate='contains')
    seav = shapely.union_all([shapely.make_valid(cg[i]).buffer(0.002) for i, j in zip(*idx) if tag[allp[j]] == 1]).buffer(-0.002)
    offl = sorted(v for v in landr - island if Z.buffer(ZONE_R).contains(Point(at(v))) and not old.buffer(-0.3).contains(Point(at(v))))
    Z = unary_union([Z] + [Point(at(v)).buffer(CAP + 2 * CLOSE_R) for v in offl])                    # (the coast round them worked out too)
    base = unary_union([old] + [Point(warp(*at(v))).buffer(CAP) for v in offl])
    closed = base.buffer(CLOSE_R).buffer(-CLOSE_R).difference(base)
    isle = unary_union([g for g in snowp if g.contains(Point(at(22531)))])
    notches = [g for g in _polys(closed) if g.area > 0.05 and g.intersects(Z) and Z.buffer(ZONE_R).contains(g) and EAST.contains(g) and g.distance(isle) > 1.0]
    Z = unary_union([Z] + [g.buffer(0.5) for g in notches])
    cand = unary_union([base] + [g.buffer(0.02) for g in notches]).difference(seav.intersection(Z))
    sm = cand.buffer(SMOOTH).buffer(-2 * SMOOTH).buffer(SMOOTH)
    newl = unary_union([cand.difference(Z), sm.intersection(Z)]).buffer(0)
    keep = [g for g in _polys(newl) if g.area > 0.01 and any(g.buffer(0.05).contains(Point(at(v))) for v in landr)]
    dropped = [g for g in _polys(newl) if g.area > 0.01 and g not in keep]
    berg = Point(at(ICE1)).buffer(ICE1_R, 6).simplify(0.02)                                     # the one-room iceberg
    newl = unary_union(keep); land_new = unary_union([newl, berg])
    lost = [v for v in landr if Z.contains(Point(at(v))) and not newl.contains(Point(warp(*at(v))))]
    wetin = [v for v in seaR - {ICE1} if newl.contains(Point(at(v)))]
    other_land = [Polygon(p).buffer(0) for p in geo['land'] if len(p) > 2 and key(p) not in oldkeys]
    for k in ('snow', 'land'):
        geo[k] = [p for p in geo[k] if not (len(p) > 2 and key(p) in oldkeys)] + rings(land_new)
    o = wild['olsnow']; o['poly'] = [p for p in o['poly'] if not (len(p) > 2 and key(p) in oldkeys)] + rings(land_new)
    gone = old.difference(land_new); added = land_new.difference(old)
    nd0, ni0 = len(o['drifts']), len(o['ice'])
    o['drifts'] = [d for d in o['drifts'] if not gone.contains(Point(d[0], d[1]))]
    o['ice'] = [p for p in o['ice'] if not gone.intersects(Polygon(p).buffer(0))]
    rr = random.Random(26001); nd = round(nd0 / old.area * added.area); dr = []
    inner = added.difference(berg).buffer(-0.5)
    if not inner.is_empty:
        x0, y0, x1, y1 = inner.bounds
        for _ in range(4000):
            if len(dr) >= nd: break
            x, y = rr.uniform(x0, x1), rr.uniform(y0, y1)
            if inner.contains(Point(x, y)) and all(math.dist((x, y), d[:2]) > 2.0 for d in o['drifts'] + dr):
                dr.append([round(x, 3), round(y, 3), round(rr.uniform(0.7, 1.0), 2), round(rr.uniform(-0.2, 0.2), 3)])
    o['drifts'] = list(o['drifts']) + dr
    nf0 = len(wild.get('olflora', [])); wild['olflora'] = [f for f in wild.get('olflora', []) if not gone.contains(Point(f[0], f[1]))]

    # ---- 2. the sea ----
    inl = land_new.buffer(-0.03)                                                                # every sea fill and water ring trimmed to the final coast
    cutsf = 0                                                                                   #  (each ring on its own, so the evenodd holes stay right):
    for k in ('seafill', 'water'):                                                              #  nothing blue left under the land (owner, Oct 22)
        out = []
        for p in geo[k]:
            g = Polygon(p).buffer(0) if len(p) > 2 else None
            if g is not None and g.intersects(inl) and g.intersection(inl).area > 1e-4:
                cutsf += 1; out += rings(g.difference(inl))
            else: out.append(p)
        geo[k] = out
    land = unary_union(other_land + [land_new])
    W = unary_union([Polygon(p).buffer(0) for p in geo['water'] if len(p) > 2])
    SF = unary_union([Polygon(p).buffer(0) for p in geo['seafill'] if len(p) > 2])
    oldsea = unary_union([W, SF])
    rn = lambda x, y: 0.9 * math.sin(x / 3.1 + 1.3) * math.cos(y / 2.7 - 0.4) + 0.5 * math.sin((x + y) / 4.3)     # (a smooth wobble: no straight edges along straight routes)
    blobs = [Point(q).buffer(AZ_R + 0.8 + 0.8 * rn(*q), 24) for g in [Point(at(v)) for v in AZ] + [LineString([at(a), at(b)]) for a, b in edges if a in AZ and b in AZ] for q in _sample(g, 0.4)]
    reach = unary_union([newl.intersection(Z).buffer(SEA_W), berg.buffer(SEA_W), unary_union(blobs), gone, oldsea.intersection(Z.buffer(SEA_W))])
    region = reach.buffer(SEA_CLOSE).buffer(-SEA_CLOSE)
    fill = region.difference(land.buffer(-0.03)).difference(oldsea)
    fills = [g for g in _polys(fill) if g.area > 0.05]
    geo['seafill'] = list(geo['seafill']) + rings(unary_union(fills))
    sea_all = unary_union([oldsea] + fills)
    chg = unary_union([Z, added.buffer(0.5), gone.buffer(0.5)])                                 # shore lines: dropped off the changed coast, the new ones added
    ns0 = len(wild['seashore']); keepsh = []
    for l in wild['seashore']:
        g = LineString(l).difference(chg.buffer(0.05)) if len(l) > 1 else None
        for q in (getattr(g, 'geoms', [g]) if g is not None and not g.is_empty else []):
            if q.geom_type == 'LineString' and q.length > 0.2: keepsh.append([[round(x, 3), round(y, 3)] for x, y in q.coords])
    coast = unary_union([q.exterior for q in _polys(land_new)]).intersection(chg.buffer(0.05)).intersection(sea_all.buffer(0.1))
    newsh = [[[round(x, 3), round(y, 3)] for x, y in l.simplify(0.02).coords] for l in getattr(coast, 'geoms', [coast]) if l.geom_type == 'LineString' and l.length > 0.2]
    wild['seashore'] = keepsh + newsh
    b = wild['bounds']; fb = unary_union(fills).bounds if fills else b
    wild['bounds'] = [min(b[0], math.floor(fb[0] - 0.5)), b[1], max(b[2], math.ceil(fb[2] + 0.5)), max(b[3], math.ceil(fb[3] + 0.5))]

    # ---- 3. the coastal path ----
    cl = unary_union([q.exterior for q in _polys(newl)])
    G = defaultdict(list)
    for a, b in edges:
        if a in seaside and b in seaside:
            L = math.dist(at(a), at(b)); m = Point((at(a)[0] + at(b)[0]) / 2, (at(a)[1] + at(b)[1]) / 2)
            w = L * (1 + cl.distance(m)) ** 2; G[a].append((b, w)); G[b].append((a, w))
    dist = {COAST_END[0]: 0}; prev = {}; hq = [(0, COAST_END[0])]
    while hq:
        d, v = heapq.heappop(hq)
        if d > dist.get(v, 1e18): continue
        for t, w in G[v]:
            if d + w < dist.get(t, 1e18): dist[t] = d + w; prev[t] = v; heapq.heappush(hq, (d + w, t))
    spine = [COAST_END[1]]
    while spine[-1] != COAST_END[0]: spine.append(prev[spine[-1]])
    spine = spine[::-1]; onsp = set(spine)
    coastal = {(min(a, b), max(a, b)) for a, b in zip(spine, spine[1:])}

    # ---- 4. the routes: water up to the coast, trail on land ----
    adj = defaultdict(set)
    for a, b in edges:
        if a in seaside and b in seaside: adj[a].add(b); adj[b].add(a)
    used = set(coastal); chains = []
    def walk(a, b):
        line = [a, b]; used.add((min(a, b), max(a, b)))
        while len(adj[line[-1]]) == 2 and line[-1] not in onsp:
            nx = [t for t in adj[line[-1]] if (min(t, line[-1]), max(t, line[-1])) not in used]
            if not nx: break
            used.add((min(nx[0], line[-1]), max(nx[0], line[-1]))); line.append(nx[0])
        return line
    for a, b in edges:
        if (a, b) in used or not (a in seaside and b in seaside): continue
        s = a if (len(adj[a]) != 2 or a in onsp) else b if (len(adj[b]) != 2 or b in onsp) else a
        t = b if s == a else a
        line = walk(s, t)
        if len(adj[s]) == 2 and s not in onsp:                                                  # (a loop or a run started mid-way)
            back = [x for x in adj[s] if (min(x, s), max(x, s)) not in used]
            if back: line = walk(s, back[0])[::-1][:-1] + line
        chains.append(line)
    rp = lambda q: [round(q[0], 3), round(q[1], 3)]
    faint = [[rp(at(a)), rp(at(b))] for a, b in zip(spine, spine[1:])]                         # (straight room to room: exactly on the layout)
    waves = [_wave([list(at(v)) for v in ch]) for ch in chains if LineString([at(v) for v in ch]).length > 1e-6]
    trails, nsplit, ncross = [], 0, []
    lg = land_new.buffer(0)
    def split(p0, p1, style):                                                                   # a straight exit: water off the land, trail on it,
        line = LineString([p0, p1]); hit = line.intersection(lg.boundary)                       #  changing exactly at the coast
        ds = sorted({0.0, line.length} | {line.project(q) for q in getattr(hit, 'geoms', [hit]) if q.geom_type == 'Point'})
        out = []
        for d0, d1 in zip(ds, ds[1:]):
            if d1 - d0 < 1e-6: continue
            a_, b_ = line.interpolate(d0).coords[0], line.interpolate(d1).coords[0]
            if lg.contains(line.interpolate((d0 + d1) / 2)):
                n = max(2, int(math.dist(a_, b_) / 0.2)); tr = [rp((a_[0] + (b_[0] - a_[0]) * i / n, a_[1] + (b_[1] - a_[1]) * i / n)) for i in range(n + 1)]
                trails.append(tr); out.append(('land', tr))
            elif style == 'faint': faint.append([rp(a_), rp(b_)])
            else: waves.append(_wave([list(a_), list(b_)]))
        return out
    endp = lambda v: warp(*at(v)) if v in landr else at(v)
    landing = {}                                                                                # (sea room, land room) -> its trail pieces on land
    for a, b in edges:                                                                          # sea room - land room
        if (a in seaside) == (b in seaside): continue
        s, l = (a, b) if a in seaside else (b, a)
        parts = split(at(s), endp(l), 'faint' if s in onsp else 'waves'); nsplit += 1
        if not parts: ncross.append((s, l))
        landing[(s, l)] = [tr for _, tr in parts]
    for lo, hi in sorted(CLIMBS):                                                               # the climbs from a room not out at sea (owner, Oct 22)
        drawn = any(min(math.dist(l[0], endp(lo)), math.dist(l[-1], endp(lo))) < 0.05 and min(math.dist(l[0], endp(hi)), math.dist(l[-1], endp(hi))) < 0.05
                    for l in wild['oltracks'] if len(l) > 1)
        if (lo, hi) in landing or drawn: continue                                               # (22524 - 15659: already a trail)
        landing[(lo, hi)] = [tr for _, tr in split(endp(lo), endp(hi), 'waves')]; nsplit += 1   # (15154 up to 15738; 15741 up to 13327, on land)

    # ---- 4b. the cliff (owner, Oct 22): one cliff face along the east coast's edge, from the northernmost climb's landing to the southernmost;
    #      the climbs that start on land (22524, 15741) go up where their room's exit from the sea comes ashore (owner: 'pretend that's where
    #      things go up'); every exit that comes ashore across the face gets steps on it, on the face only ----
    mainl = max(_polys(newl), key=lambda g: g.area); ring = LineString(mainl.exterior.coords); RL = ring.length
    def crossing(lo, hi):                                                                      # where an exit comes onto the mainland
        line = LineString([endp(lo), endp(hi)]); hit = line.intersection(ring)
        q = [g for g in getattr(hit, 'geoms', [hit]) if g.geom_type == 'Point']
        return max(q, key=lambda g: line.project(g)) if q else None
    seaup = {s: l for s, l in landing}                                                          # (each land room's way up from the sea)
    anchors = {}
    for lo, hi in CLIMBS:
        c = crossing(lo, hi)
        if c is None:                                                                           # (a climb on land: where its room's exit from the sea comes ashore)
            k = next(((s, l) for s, l in landing if l == lo and s in seaside), None); c = crossing(*k) if k else None
        if c is not None: anchors[(lo, hi)] = ring.project(c)
    sv_ = sorted(anchors.values()); gaps = [(sv_[(i + 1) % len(sv_)] - sv_[i]) % RL for i in range(len(sv_))]
    i0 = max(range(len(sv_)), key=lambda i: gaps[i])                                            # the arc that holds them all: round from after the widest gap
    a_, b_ = sv_[(i0 + 1) % len(sv_)] - CLIFF_L, sv_[(i0 + 1) % len(sv_)] - CLIFF_L + (RL - gaps[i0]) + 2 * CLIFF_L
    from shapely.ops import substring
    def arc(a_, b_):
        a_ %= RL; b2 = a_ + (b_ - a_ if b_ > a_ else b_ - a_ + RL)
        return substring(ring, a_, b2) if b2 <= RL else LineString(list(substring(ring, a_, RL).coords) + list(substring(ring, 0, b2 - RL).coords)[1:])
    sub = arc(a_, b_)
    cr = random.Random(26002); hach, rl = [], []
    band = sub.buffer(CLIFF_W, cap_style='flat').intersection(mainl)
    n = max(2, int(sub.length / 0.16))
    for i in range(n + 1):
        d = sub.length * i / n; p = sub.interpolate(d).coords[0]; p2 = sub.interpolate(min(sub.length, d + 0.05)).coords[0]; p1 = sub.interpolate(max(0, d - 0.05)).coords[0]
        L_ = math.dist(p1, p2) or 1; tx, ty = (p2[0] - p1[0]) / L_, (p2[1] - p1[1]) / L_
        nx_, ny_ = (-ty, tx) if mainl.contains(Point(p[0] - ty * 0.2, p[1] + tx * 0.2)) else (ty, -tx)
        rl.append(rp((p[0] + nx_ * CLIFF_W, p[1] + ny_ * CLIFF_W)))
        if 0 < i < n: k = cr.uniform(0.55, 0.95); hach.append([rp((p[0] + nx_ * CLIFF_W * 0.95, p[1] + ny_ * CLIFF_W * 0.95)), rp((p[0] + nx_ * CLIFF_W * (0.95 - k), p[1] + ny_ * CLIFF_W * (0.95 - k)))])
    rim = [rl]; faceu = unary_union([q for q in _polys(band) if q.area > 0.01])
    steps = []; upk = set()
    for k, trs in landing.items():
        for tr in trs:
            if len(tr) < 2: continue
            g = LineString(tr).intersection(faceu.buffer(0.05))
            for seg in [q for q in getattr(g, 'geoms', [g]) if q.geom_type == 'LineString' and q.length > 0.05]:
                upk.add(k); n = max(2, int(seg.length / STEP_D))
                for i in range(1, n):
                    d = seg.length * i / n; p = seg.interpolate(d).coords[0]; p2 = seg.interpolate(min(seg.length, d + 0.03)).coords[0]; p1 = seg.interpolate(max(0, d - 0.03)).coords[0]
                    L_ = math.dist(p1, p2) or 1; nx_, ny_ = -(p2[1] - p1[1]) / L_, (p2[0] - p1[0]) / L_
                    steps.append([rp((p[0] - nx_ * STEP_W, p[1] - ny_ * STEP_W)), rp((p[0] + nx_ * STEP_W, p[1] + ny_ * STEP_W))])
    wild['olcliff'] = {'face': [rd(q) for q in _polys(faceu)], 'hach': hach, 'rim': rim, 'steps': steps}
    nostep = sorted(k for k in CLIMBS if k not in anchors)
    wild['seawaysfaint'] = list(wild['seawaysfaint']) + faint
    wild['seawaves'] = list(wild['seawaves']) + waves
    wild['oltracks'] = list(wild['oltracks']) + trails
    over = round(sum(LineString(l).intersection(land_new.buffer(-0.02)).length for l in faint + waves if len(l) > 1), 3)

    # ---- 5. shore ice: none on the new land or on a room or route (owner: no coastal additions for now) ----
    routes = unary_union([LineString(l) for l in faint + waves if len(l) > 1] + [Point(at(v)) for v in AZ]).buffer(ICE_CLEAR)
    def keep_ice(p):
        g = Polygon(p[0] if isinstance(p[0][0], list) else p).buffer(0); return not (g.intersects(routes) or g.intersects(land_new))
    f0, b0 = len(wild['olsouth']['floes']), len(wild['olharbor']['bergs'])
    wild['olsouth']['floes'] = [p for p in wild['olsouth']['floes'] if keep_ice(p)]
    wild['olharbor']['bergs'] = [p for p in wild['olharbor']['bergs'] if keep_ice(p)]

    nlen = lambda ls: round(sum(LineString(l).length for l in ls if len(l) > 1), 1)
    return {'Azure Sea east coast: rooms placed; exits drawn (up/down); coastal path (rooms, segments, length); east routes (lines, length); '
            'sea-land exits split at the coast (trails added, length; no crossing found); water route length over land':
            (len(AZ), len(edges), nud, (len(spine), len(faint), nlen(faint)), (len(waves), nlen(waves)), (nsplit, nlen(trails), ncross), over),
            'coast (land cut, added; notches closed (pieces, area); rooms the move left off the land; pieces dropped; land rooms off the land, sea rooms on it)':
            (round(gone.area, 1), round(added.area, 1), (len(notches), round(sum(g.area for g in notches), 1)), offl, len(dropped), lost, wetin),
            'cliff (length, from-to y; face area; hachures; exits going up it (with steps): count, steps; climbs without a landing)':
            (round(sub.length, 1), (round(sub.coords[0][1], 1), round(sub.coords[-1][1], 1)), round(faceu.area, 2), len(hach), (len(upk), sorted(upk)), len(steps), nostep),
            'iceberg 15154 (area, gap to the mainland)': (round(berg.area, 2), round(berg.distance(newl), 2)),
            'snow (drifts dropped, added; ice patches, plants dropped)': (nd0 - len(o['drifts']) + len(dr), len(dr), ni0 - len(o['ice']), nf0 - len(wild['olflora'])),
            'sea (fills added: pieces, area; old fills cut; shore lines before -> after; ice dropped floes, bergs; bounds)':
            (len(fills), round(sum(g.area for g in fills), 1), cutsf, (ns0, len(wild['seashore'])), (f0 - len(wild['olsouth']['floes']), b0 - len(wild['olharbor']['bergs'])), wild['bounds']),
            'spine': spine}
