"""The Azure Sea along Otherland's east coast (owner, Oct 22; the rooms placed in the Otherland editor, save `legacy/ol_layout_final.json`, grp 'az':
the save's rooms that are not in `legacy/ol_editor_edges.json`):
  - its shown rooms are water rooms out at sea and the Otherland rooms along the east coast are on land, so the coast runs between them: the land
    (Otherland's snow pieces) is cut back, inside ZONE_R of the sea rooms and their routes, wherever a point is nearer to them than to Otherland's
    land rooms and trails (the Voronoi line between the two, smoothed SMOOTH); slivers without a room become sea. Before that the bay east of Morte's
    Peak is closed again (applied/v2.5/007's rule, whose box no longer covers it after the save moved the rooms east), without a box line;
  - the sea round them: SEA_W off the new coast and at least AZ_R round every sea room and route, joined to the sea there, `seafill` + `seashore`;
    the snow texture, plants and shore ice in the new sea dropped, and shore ice touching a room or route dropped (owner: no coastal additions
    for now, so none added);
  - their routes are water routes: the coastal path (the chain nearest the mainland, from the Iceberg 6179/6167 to 15250, then 15255, 15606) as
    the Sea of Sorrows' routes (`seawaysfaint`), the routes leading east off it as the Desert of Despair east coast's (`seawaves`, fainter, wavy).
    Exits to Otherland rooms on land are drawn too (in the style of the azure room's side). Not drawn: 5987-22496 (owner), up/down exits (as
    Otherland's) except 15250-15255, the way on to the last room; 15606's exits to the Grey Beach (Northern Plains) are left off.
  - the rooms join `pos` (room_pos)."""
import json, math, os, random
from collections import defaultdict
import heapq
from shapely.geometry import Polygon, LineString, Point, MultiPoint, box
from shapely.ops import unary_union, voronoi_diagram
import maplib

HERE = os.path.dirname(os.path.abspath(__file__)); LEG = os.path.join(HERE, '..', 'legacy')
WET = {'Swimming', 'Underwater', 'Water', 'Seafloor'}
ICEBERG = [22531, 22532, 22533, 22534, 22535, 6166, 13379, 13380, 6180]      # land (applied/v2.4/001)
AS_LAND = {6147, 6148}
NOT_DRAWN = {(5987, 22496)}                                                   # owner (Oct 22)
UD_DRAWN = {(15250, 15255)}
COAST_END = [6179, 15606]
BAY = box(74, 180, 100, 228)                                                  # the east coast's bays and notches (the bay east of Morte's Peak; box lines
                                                                              # left by the move): closed pieces wholly inside this, then the coast cut back to the sea rooms
CLOSE_R = 5.0
ZONE_R, SAMPLE = 6.0, 0.2                                                     # the coast moves only this near the sea rooms; feature sampling
SMOOTH = 0.6
LAND_R = 1.6                                                                  # land this far round an east-coast room the move left off it
SEA_W, SEA_CLOSE, AZ_R = 6.0, 6.0, 3.0
ICE_CLEAR = 0.6                                                               # shore ice this far from rooms and routes
WAVE_AMP, WAVE_LEN = 0.12, 2.5                                                # as applied/v2.4/001's seawaves


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
    if geom.geom_type == 'Point': return [geom.coords[0]]
    n = max(1, int(geom.length / step)); return [geom.interpolate(i / n, normalized=True).coords[0] for i in range(n + 1)]


def apply(town, wild, pos):
    rooms, exits = maplib.world()
    S = json.load(open(os.path.join(LEG, 'ol_layout_final.json'))); E = json.load(open(os.path.join(LEG, 'ol_editor_edges.json')))
    P = {v: (x, y) for v, x, y in zip(S['ids'], S['xs'], S['ys'])}; H = set(S['hidden']); R = {r['id'] for r in E['rooms']}
    AZ = {v for v in P if v not in R and v not in H}
    for v in sorted(AZ): pos[str(v)] = [P[v][0], P[v][1]]
    at = lambda v: tuple(pos[str(v)])
    geo = wild['geo']; rd = lambda g: [[round(x, 3), round(y, 3)] for x, y in list(g.exterior.coords)[:-1]]

    # ---- the routes drawn ----
    FLATP = {frozenset((v, e['to'])) for v, l in exits.items() for e in l if e['dir'] not in (0, 16, 32) and e['to'] != v}
    pair = {}
    for v in list(AZ) + [int(k) for k in pos if int(k) not in AZ]:
        for e in exits.get(v, []):
            t = e['to']; k = (min(v, t), max(v, t))
            if t == v or not (v in AZ or t in AZ) or str(t) not in pos or k in NOT_DRAWN: continue
            if e['dir'] in (16, 32) and (frozenset(k) in FLATP or k not in UD_DRAWN): continue
            pair[k] = True
    olroom = {int(k) for k in pos if int(k) not in AZ and rooms.get(int(k), {}).get('area') == 'Otherland'}
    island = set(ICEBERG)
    edges = sorted(k for k in pair if all(v in AZ | olroom | island for v in k))                    # (15606's exits to the Grey Beach left off)
    landr = {v for v in olroom | island if (rooms[v]['terrain'] not in WET or v in AS_LAND)}
    wetr = {v for v in olroom if v not in landr}
    seaR = {v for v in AZ if min((math.dist(at(v), at(u)) for u in landr), default=9) > 0.3} | wetr          # (15172 sits on 15154)
    sea_lines = [LineString([at(a), at(b)]) for a, b in edges if a in seaR and b in seaR]

    # ---- 1. the bay east of Morte's Peak closed again ----
    snowp = [Polygon(p).buffer(0) for p in geo['snow'] if len(p) > 2]
    main = max(snowp, key=lambda g: g.area)
    key = lambda p: (round(Polygon(p).area, 1), tuple(round(c, 1) for c in Polygon(p).bounds))
    keys = {key(p): g for p, g in zip([p for p in geo['snow'] if len(p) > 2], snowp)}
    add = main.buffer(CLOSE_R).buffer(-CLOSE_R).difference(main)
    add = [g for g in getattr(add, 'geoms', [add]) if g.area > 0.05 and BAY.contains(g)]
    feat_sea = unary_union([Point(at(v)) for v in seaR] + sea_lines)
    bay = unary_union(add) if add else Polygon()
    main2 = unary_union([main, bay.buffer(0.02)]).buffer(0)
    from shapely.ops import nearest_points
    zone0 = unary_union([Point(at(v)) for v in AZ]).buffer(ZONE_R * 2)
    offl = sorted(v for v in landr - island if zone0.contains(Point(at(v))) and not main2.buffer(-0.3).contains(Point(at(v))))
    bridges = []
    for v in offl:                                                                                      # (owner: the east coast's rooms are on land)
        p = Point(at(v)); q = nearest_points(main2, p)[0]
        bridges.append(unary_union([p.buffer(LAND_R), LineString([p.coords[0], q.coords[0]]).buffer(LAND_R * 0.8)]))
    if bridges:
        main2 = unary_union([main2] + bridges); main2 = main2.buffer(0.8).buffer(-0.8)
        main2 = Polygon(main2.exterior) if main2.geom_type == 'Polygon' else Polygon(max(main2.geoms, key=lambda g: g.area).exterior)
    bay = unary_union([bay] + bridges).difference(main) if bridges else bay

    # ---- 2. the coast between the sea rooms and the land rooms ----
    land_lines = [LineString(t) for t in wild.get('oltracks', []) + wild.get('oltunnels', []) if len(t) > 1]
    lpts = [q for v in landr for q in [at(v)]] + [q for l in land_lines for q in _sample(l, SAMPLE)]
    spts = [at(v) for v in seaR] + [q for l in sea_lines for q in _sample(l, SAMPLE)]
    Z = unary_union([Point(at(v)) for v in seaR if v in AZ] + [l for l in sea_lines]).buffer(ZONE_R)
    zb = Z.buffer(ZONE_R * 2).bounds
    lpts = [q for q in lpts if zb[0] <= q[0] <= zb[2] and zb[1] <= q[1] <= zb[3]]
    lpts = list({(round(x, 2), round(y, 2)) for x, y in lpts}); spts = list({(round(x, 2), round(y, 2)) for x, y in spts} - set(lpts))
    allp = lpts + spts; tag = {p: 0 for p in lpts}; tag.update({p: 1 for p in spts})
    cells = voronoi_diagram(MultiPoint(allp), envelope=box(*zb).buffer(20))
    from shapely import STRtree
    tree = STRtree([Point(p) for p in allp]); cg = list(cells.geoms)
    idx = tree.query(cg, predicate='contains')
    import shapely
    sc = [shapely.make_valid(cg[i]).buffer(0.002) for i, j in zip(*idx) if tag[allp[j]] == 1]
    seav = shapely.union_all(sc).buffer(-0.002)
    cut = seav.intersection(Z)
    cut = cut.buffer(SMOOTH).buffer(-2 * SMOOTH).buffer(SMOOTH)
    landall = unary_union([main2] + [g for g in snowp if g is not main])
    newl = landall.difference(cut)
    pieces = [g for g in getattr(newl, 'geoms', [newl]) if g.area > 0.01]
    keep = [g for g in pieces if any(g.buffer(0.05).contains(Point(at(v))) for v in landr)]
    dropped = [g for g in pieces if g not in keep]
    newl = unary_union(keep)
    lost = [v for v in landr if not newl.contains(Point(at(v)))]
    wetin = [v for v in seaR if newl.buffer(-0.05).contains(Point(at(v)))]

    # swap the snow pieces (snow, land, the texture's rings)
    oldkeys = {key(p) for p in geo['snow'] if len(p) > 2}
    newpolys = [rd(g) for g in getattr(newl, 'geoms', [newl])]
    holes = [[[round(x, 3), round(y, 3)] for x, y in list(h.coords)[:-1]] for g in getattr(newl, 'geoms', [newl]) for h in g.interiors]
    for k in ('snow', 'land'):
        geo[k] = [p for p in geo[k] if not (len(p) > 2 and key(p) in oldkeys)] + newpolys + holes
    o = wild['olsnow']; o['poly'] = [p for p in o['poly'] if not (len(p) > 2 and key(p) in oldkeys)] + newpolys + holes
    gone = landall.difference(newl)
    inside = lambda x, y, g=gone: g.contains(Point(x, y))
    nd0, ni0 = len(o['drifts']), len(o['ice'])
    o['drifts'] = [d for d in o['drifts'] if not inside(d[0], d[1])]
    o['ice'] = [p for p in o['ice'] if not gone.intersects(Polygon(p).buffer(0))]
    rr = random.Random(26001); nd = round(nd0 / landall.area * bay.area) if bay.area else 0; dr = []
    inner = bay.intersection(newl).buffer(-0.5)
    if not inner.is_empty:
        x0, y0, x1, y1 = inner.bounds
        for _ in range(3000):
            if len(dr) >= nd: break
            x, y = rr.uniform(x0, x1), rr.uniform(y0, y1)
            if inner.contains(Point(x, y)) and all(math.dist((x, y), d[:2]) > 2.0 for d in o['drifts'] + dr):
                dr.append([round(x, 3), round(y, 3), round(rr.uniform(0.7, 1.0), 2), round(rr.uniform(-0.2, 0.2), 3)])
    o['drifts'] = list(o['drifts']) + dr
    nf0 = len(wild.get('olflora', [])); wild['olflora'] = [f for f in wild.get('olflora', []) if not inside(f[0], f[1])]

    # ---- 3. the sea ----
    land = unary_union([Polygon(p).buffer(0) for p in geo['land'] if len(p) > 2 and key(p) not in {key(q) for q in holes}]).difference(unary_union([Polygon(h) for h in holes]) if holes else Polygon())
    W = unary_union([Polygon(p).buffer(0) for p in geo['water'] if len(p) > 2])
    SFp = [Polygon(p).buffer(0) for p in geo['seafill'] if len(p) > 2]
    # existing sea fills now under the land (the bay) give way to it
    nsf, cutsf = [], 0
    for p, g in zip([p for p in geo['seafill'] if len(p) > 2], SFp):
        if g.intersects(bay) and g.intersection(bay).area > 0.01:
            d = g.difference(bay); cutsf += 1
            for q in getattr(d, 'geoms', [d]):
                if q.area > 0.01: nsf.append(rd(q)); nsf += [[[round(x, 3), round(y, 3)] for x, y in list(h.coords)[:-1]] for h in q.interiors]
        else: nsf.append(p)
    geo['seafill'] = nsf
    SF = unary_union([Polygon(p).buffer(0) for p in geo['seafill'] if len(p) > 2])
    old = unary_union([W, SF])
    azf = unary_union([Point(at(v)) for v in AZ] + sea_lines)
    rn = lambda x, y: 0.9 * math.sin(x / 3.1 + 1.3) * math.cos(y / 2.7 - 0.4) + 0.5 * math.sin((x + y) / 4.3)     # (a smooth wobble: no straight edges along straight routes)
    blobs = [Point(q).buffer(AZ_R + 0.8 + 0.8 * rn(*q), 24) for g in [Point(at(v)) for v in AZ] + sea_lines + [LineString([at(a), at(b)]) for a, b in edges if a in AZ and b in AZ] for q in _sample(g, 0.4)]
    reach = unary_union([newl.intersection(Z).buffer(SEA_W), unary_union(blobs), gone, old.intersection(Z.buffer(SEA_W))])
    region = reach.buffer(SEA_CLOSE).buffer(-SEA_CLOSE)
    fill = region.difference(land.buffer(-0.03)).difference(old)
    fills = [g for g in getattr(fill, 'geoms', [fill]) if g.area > 0.05]
    geo['seafill'] = list(geo['seafill']) + [rd(g) for g in fills] + [[[round(x, 3), round(y, 3)] for x, y in list(h.coords)[:-1]] for g in fills for h in g.interiors]
    sea_all = unary_union([old] + fills)
    # shore lines: the old ones off the changed coast dropped, the new coast's added
    chg = unary_union([Z, bay.buffer(0.5)])
    ns0 = len(wild['seashore']); keepsh = []
    for l in wild['seashore']:
        g = LineString(l).difference(chg.buffer(0.05)) if len(l) > 1 else None
        for q in (getattr(g, 'geoms', [g]) if g is not None and not g.is_empty else []):
            if q.geom_type == 'LineString' and q.length > 0.2: keepsh.append([[round(x, 3), round(y, 3)] for x, y in q.coords])
    coast = unary_union([g.exterior for g in getattr(newl, 'geoms', [newl])]).intersection(chg.buffer(0.05)).intersection(sea_all.buffer(0.1))
    newsh = [[[round(x, 3), round(y, 3)] for x, y in l.simplify(0.02).coords] for l in getattr(coast, 'geoms', [coast]) if l.geom_type == 'LineString' and l.length > 0.2]
    wild['seashore'] = keepsh + newsh
    b = wild['bounds']; fb = unary_union(fills).bounds if fills else b
    wild['bounds'] = [min(b[0], math.floor(fb[0] - 0.5)), b[1], max(b[2], math.ceil(fb[2] + 0.5)), max(b[3], math.ceil(fb[3] + 0.5))]

    # ---- 4. the coastal path and the routes off it ----
    G = defaultdict(list)
    for a, b in edges:
        if a in AZ | wetr and b in AZ | wetr:
            L = math.dist(at(a), at(b)); m = ((at(a)[0] + at(b)[0]) / 2, (at(a)[1] + at(b)[1]) / 2)
            d = newl.exterior.distance(Point(m)) if newl.geom_type == 'Polygon' else min(g.exterior.distance(Point(m)) for g in newl.geoms)
            w = L * (1 + d) ** 2; G[a].append((b, w)); G[b].append((a, w))
    dist = {COAST_END[0]: 0}; prev = {}; hq = [(0, COAST_END[0])]
    while hq:
        d, v = heapq.heappop(hq)
        if d > dist.get(v, 1e18): continue
        for t, w in G[v]:
            if d + w < dist.get(t, 1e18): dist[t] = d + w; prev[t] = v; heapq.heappush(hq, (d + w, t))
    spine = [COAST_END[1]]
    while spine[-1] != COAST_END[0]: spine.append(prev[spine[-1]])
    spine = spine[::-1]; onsp = set(spine)
    coastal_e = {(min(a, b), max(a, b)) for a, b in zip(spine, spine[1:])} | {(6179, 6180), (6166, 6179), (6166, 6167)}
    # chains: runs of drawn edges through rooms with two drawn edges (not on the spine's joints)
    adj = defaultdict(set)
    for a, b in edges: adj[a].add(b); adj[b].add(a)
    used = set(); chains = []
    def walk(a, b):
        line = [a, b]; used.add((min(a, b), max(a, b)))
        while len(adj[line[-1]]) == 2 and line[-1] not in onsp and line[-1] not in landr:
            nx = [t for t in adj[line[-1]] if (min(t, line[-1]), max(t, line[-1])) not in used]
            if not nx: break
            used.add((min(nx[0], line[-1]), max(nx[0], line[-1]))); line.append(nx[0])
        return line
    for a, b in zip(spine, spine[1:]): used.add((min(a, b), max(a, b)))
    chains.append(('coast', spine))
    for a, b in edges:
        k = (a, b)
        if k in used: continue
        if k in coastal_e: used.add(k); chains.append(('coast', [a, b])); continue
        s = a if (len(adj[a]) != 2 or a in onsp or a in landr) else b if (len(adj[b]) != 2 or b in onsp or b in landr) else a
        t = b if s == a else a
        line = walk(s, t)
        if len(adj[s]) == 2 and s not in onsp and s not in landr:                                  # (a loop or a run started mid-way)
            back = [x for x in adj[s] if (min(x, s), max(x, s)) not in used]
            if back: line = walk(s, back[0])[::-1][:-1] + line
        chains.append(('east', line))
    faint, waves = [], []
    for kind, ch in chains:
        pts = [list(at(v)) for v in ch]
        if kind == 'coast': faint.append([[round(x, 3), round(y, 3)] for x, y in pts])
        else: waves.append(_wave(pts))
    wild['seawaysfaint'] = list(wild['seawaysfaint']) + faint
    wild['seawaves'] = list(wild['seawaves']) + waves

    # ---- 5. shore ice: none in the new sea's changed part on a room or route (owner: no coastal additions for now) ----
    routes = unary_union([LineString(l) for l in faint + waves if len(l) > 1] + [Point(at(v)) for v in AZ]).buffer(ICE_CLEAR)
    def keep_ice(p):
        g = Polygon(p[0] if isinstance(p[0][0], list) else p).buffer(0); return not (g.intersects(routes) or g.intersects(gone) or g.intersects(newl))
    f0, b0 = len(wild['olsouth']['floes']), len(wild['olharbor']['bergs'])
    wild['olsouth']['floes'] = [p for p in wild['olsouth']['floes'] if keep_ice(p)]
    wild['olharbor']['bergs'] = [p for p in wild['olharbor']['bergs'] if keep_ice(p)]

    nlen = lambda ls: round(sum(LineString(l).length for l in ls if len(l) > 1), 1)
    return {'Azure Sea east coast: rooms placed; routes drawn (coastal path rooms, its lines / length; east routes lines / length)':
            (len(AZ), len(edges), (len(spine), len(faint), nlen(faint)), (len(waves), nlen(waves))),
            'bay closed again (pieces, area incl. land joined to rooms left off it, drifts added; old sea fills cut by it); rooms joined to the land': (len(add), round(bay.area, 1), len(dr), cutsf, offl),
            'coast moved (land cut, pieces dropped (area), land rooms off the land, sea rooms on the land; drifts/ice/plants dropped)':
            (round(gone.area, 1), (len(dropped), round(sum(g.area for g in dropped), 1)), lost, wetin, nd0 - len(o['drifts']) + len(dr), ni0 - len(o['ice']), nf0 - len(wild['olflora'])),
            'sea added (pieces, area; shore lines before -> after; ice dropped floes, bergs; bounds)':
            (len(fills), round(sum(g.area for g in fills), 1), (ns0, len(wild['seashore'])), (f0 - len(wild['olsouth']['floes']), b0 - len(wild['olharbor']['bergs'])), wild['bounds']),
            'spine': spine}
