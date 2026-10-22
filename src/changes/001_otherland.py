"""Owner's Otherland save of Oct 21 (23:28Z, `legacy/ol_layout_final.json`; editor data `legacy/ol_editor_edges.json`). A basic render only (owner, Oct 21:
customised later):
  - the shown Otherland rooms placed where saved (hidden rooms left off); the 28 unlocked map rooms moved to their saved spots, and the sea lines
    through them (`seawaysfaint` straight, `seawaves` re-waved) follow them;
  - every exit of a shown Otherland room (spacers included) a plain dirt trail (`fwtracks`), straight room to room; not drawn (owner, Oct 21): up/down
    exits and one-way exits (both dashed in the editor), then spacer rooms left as dead ends by that, repeatedly;
  - snow ground (`geo.snow`, template --snow) on a new land piece round the rooms and trails, kept off the existing land and sea; on it (owner, Oct 21:
    a soft white snow texture with little drifts and icy spots; `wild.olsnow`, template OLSNOW): sparkle grain and faint wind wisps, snow drifts,
    icy patches, all clear of the trails and rooms (their own random.Random);
  - the north coast (owner, Oct 22), inside NBOX only: the water rooms there (swimming, underwater, water; 'Over the Cliff', a maze for later, as
    water) and their exits are sea: the sea carried from the Sea of Sorrows and the Azure Sea strip south to the island's north coast (the land
    rooms' edge, inlets to the 3 'The Sea of Sorrows' rooms in the Tundra Fields), at most SEA_W off the land, drawn as `seafill` + `seashore`;
    their exits faint wavy water routes (`seawaves`) instead of trails. The iceberg 22531-22535 its own little snow island, a sliver of sea
    (SLIVER) between it and 22530 on the mainland; the snow texture outside the new land dropped (none moved);
  - Winterlight Island's drawing (`snowisles`) removed for now (owner: to be re-fitted later); its marker stays."""
import json, math, os, random
from collections import defaultdict
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__)); LEG = os.path.join(HERE, '..', 'legacy')
SNOW_R = 1.6                                        # snow reaches this far round each room and trail
CLOSE = 3.0                                         # gaps narrower than 6 rooms between pieces filled
WAVE_AMP, WAVE_LEN = 0.12, 2.5                       # as applied/v2.3/001
DRIFT_AREA, DRIFT_GAP, DRIFT_CLEAR = 14.0, 1.6, 0.7  # one drift per this many square rooms; apart; from trails and rooms
ICE_N, ICE_GAP, ICE_CLEAR = 30, 4.0, 1.0            # icy patches: how many; apart; from trails and rooms
WBOX = unary_union([box(-34, 177, -6, 238)])                            # the Harbor of Icebergs on the west coast (owner, Oct 22: open to the sea)
SBOX = box(-12, 228, 56, 264)                       # the south shore (owner, Oct 22): its sea, a frozen beach, floating ice
NBOX = unary_union([box(-22, 144, 82, 177), box(-22, 177, -6, 189), box(60, 177, 82, 187), WBOX, SBOX])     # the north coast (with 'Over the Cliff' 683 on the
                                                    # west coast; east, down to the Azure Sea strip's south end)
WET = {'Swimming', 'Underwater', 'Water', 'Seafloor'}
CLIFF = 'Over the Cliff'
ICEBERG = [22531, 22532, 22533, 22534, 22535, 6166, 13379, 13380, 6180]   # owner (Oct 22): The Iceberg, its own little white island; 22530 on the mainland
ZONE_R, TIGHT_R, TIGHT_TR = 5.0, 0.75, 0.55          # near the iceberg the mainland hugs its rooms (this far) and trails (this far)
FILL_S = Polygon([(3.4, 243.2), (10.8, 243.2), (10.9, 246.5), (9.6, 249.6), (7.6, 251.6), (3.4, 251.6)])   # owner (Oct 22): south of 6143, land
FILL1 = unary_union([box(68.5, 174.6, 70.5, 183.0), box(65.5, 176.0, 70.5, 183.0),
                     Polygon([(70.5, 174.6), (72.3, 174.6), (72.75, 176.4), (72.35, 178.2), (72.9, 180.0), (72.5, 181.7), (72.8, 183.0), (70.5, 183.0)]),   # (an uneven east shore)
                     Polygon([(-20.7, 207.6), (-20.6, 208.8), (-19.4, 210.8), (-17.3, 213.3), (-15.0, 215.4), (-12.6, 216.9), (-10.0, 217.9),   # owner (Oct 22): the bay
                              (-6.0, 218.8), (-3.0, 219.3), (2.0, 219.3), (2.0, 207.6)]), FILL_S,                                                       # north of the harbour, from 13150 to its north-east shore: land
                     Polygon([(-11.8, 217.2), (-10.6, 217.65), (-9.8, 218.5), (-9.4, 219.6), (-9.8, 221.6), (-10.8, 223.2), (-11.25, 223.85), (-11.35, 224.35), (-11.0, 224.95), (-9.0, 226.4), (-3.0, 226.4), (-3.0, 217.2)])])   # (owner, Oct 22: a smooth coast down to just north of the dock)   # owner (Oct 22): land west and south of 13287, its sea inlets gone
FAINT_CHAIN = [6180, 15418, 15417, 15416, 15415, 15414, 15413, 15412, 15411, 15410, 6650, 15128]   # owner (Oct 22): drawn as the Sea of Sorrows' routes
TRACK_A, TRACK_L = 0.16, 7.0                        # Otherland's trails: a gentle long wave (owner, Oct 22): a smooth warp this strong, this long
CLEAR_SEEDS = {13492: 'The Tundra Fields', 13322: 'A Tunnel in the Snow / A Cold Lair'}   # owner (Oct 22): these two clumps only
CLEAR_D, CLEAR_R, CLEAR_TR = 1.5, 0.62, 0.45        # a clump: rooms this close joined by an exit; its clearing this far round its rooms and exits
CLEAR_FILL, CLEAR_EDGE = '#97A1A6', '#6B767C'       # packed snow, a little lighter than the snow
SHACKS = {'The Desolate Outpost': ([13087, 13089, 13090, 13091, 13092, 13093], 0.5, 0.55),    # owner (Oct 22): a log shack over its main section (rooms;
           "The Hunter's Outpost": ([14419, 14420, 14421], 0.55, 0.6)}   # (owner, Oct 22: twice as big, over the trails of 14419, Supplication 14420, the Tanner's Lodge 14421)                                       #  margin round them across, down), its back door trail west/south clear
WATER_LINKS = [(22530, 22531)]                      # owner (Oct 22): a water path (as the Sea of Sorrows routes), though one-way in TinTin
DOCK = [13100, 13101, 13102, 13105]                # owner (Oct 22): a wooden dock, snow covered and frozen, from Before the Dock out through the
DOCK_W = 0.55                                       #  3 Harbor of Icebergs rooms (they count as water); its width
HARBOR = box(-25.5, 217.5, -12.2, 234.8)            # the harbour: ice along its shores, icebergs in its open water
ICE_SHORE, N_BERGS = 1.3, 26                        # shore ice reaches this far out (clear of the routes and rooms); icebergs
HWAVE_A, HWAVE_L = 0.05, 1.6                        # the harbour's water routes (owner, Oct 22): extremely thin, nearly transparent, slightly wavy
MP_NAMES = {'Nestled Between the Peaks', 'Upon the Roof', 'Platforms of Sacrifice', 'An Icy Pass', 'A Snow Clogged Pass', "Dead Man's Pass", 'The Drop-Off',
            'The Sudden Stop', 'Entombed in Ice', 'A Cavern of Ice', 'An Icy Burrow', 'The Cave', 'Home of the Jarl', 'A Crisp Path', 'Scratching the Surface',
            'Lost in the Darkness', 'The Last of the Foothills'}               # owner (Oct 22): Morte's Peak (+ every "...Morte's Peak" room but its View), east of x 50
MP_INSIDE = {"Deep within the Heart of Morte's Peak", "Within the Heart of Morte's Peak", "Entombed within Morte's Peak", 'Entombed in Ice', 'A Cavern of Ice',
             'An Icy Burrow', 'The Cave', "The Concealed Horror of Morte's Peak", 'Lost in the Darkness'}   # inside the mountain: their trails dashed passages
GORGE_NAMES = {"The Floor of Tirebaen's Gorge", 'The Fissure', 'Deep within the Shadows of the Fissure', 'Within the Fissure'}   # owner (Oct 22): the ravine
MP_R, GORGE_R = 2.3, 3.0                             # the mountain this far round its rooms; the gorge this wide each side of its trails
SOUTH_ICE = {'An Ocean of Floating Ice', 'Among the Icebergs'}      # floating ice offshore round these
CRAMPED = 'A Dark, Cramped Tunnel'                  # owner (Oct 22): these rooms (and those that lead only to them) a tunnel under the snow (template OLTUNNEL)
CLIFF_MAZE = (14428, 683)                           # owner (Oct 22): one long maze along the coast, "Over the Cliff Maze"
MANSION = [22248, 22249, 22250]                     # owner (Oct 22): Frost Mansion, very ancient, stone, frosty (template OLMANSION), inside the Maze of Ice
MANSION_W, MANSION_H = 2.7, 2.6
LEDGE = [6102, 6101, 6096]                          # owner (Oct 22): The Ledge of Life, a south-facing cliff path (template OLLEDGE)
AS_LAND = {6147, 6148}                              # owner (Oct 22): south of 6143 all regular land again (these two water rooms drawn as land)
NW_X = 50.0                                         # water routes wholly west of this: drawn as the Sea of Sorrows' routes (`seawaysfaint`)
LAND_R, LTRAIL_R, CLOSE_N = 1.3, 0.9, 3.0           # the mainland's north edge: this far round its rooms and trails, gaps narrower than 6 closed
WET_R, WTRAIL_R = 1.2, 0.8                          # sea at least this far round the water rooms and their routes
ICE_R, SLIVER = 0.9, 0.45                           # the iceberg: this far round its rooms; the sea between it and the mainland
SEA_W, SEA_CLOSE = 6.0, 6.0                         # the sea reaches this far off the land and the old sea; gaps narrower than 12 filled


def _wave(line, amp=None, wl=None):
    amp = WAVE_AMP if amp is None else amp; wl = WAVE_LEN if wl is None else wl
    pts = [line[0]] + [q for a, q in zip(line, line[1:]) if math.dist(a, q) > 1e-6]
    out = [[round(pts[0][0], 3), round(pts[0][1], 3)]]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        L = math.hypot(bx - ax, by - ay); n = max(1, round(L / wl)); m = max(4, int(L / 0.06))
        nx, ny = -(by - ay) / L, (bx - ax) / L
        for i in range(1, m + 1):
            t = i / m; o = amp * math.sin(2 * math.pi * n * t) * min(1, L / 0.8)
            out.append([round(ax + (bx - ax) * t + nx * o, 3), round(ay + (by - ay) * t + ny * o, 3)])
    return out


def _chains(G, P):
    """lines between junctions, each inner room given twice so the template's curve runs straight from room to room (as applied/v2.3/001)"""
    chains = []; seen = set()
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
        out.append(line)
    return out


def apply(town, wild, pos):
    from maplib import world
    _rooms = world()[0]
    rooms_name = lambda v: _rooms[v]['name']
    S = json.load(open(os.path.join(LEG, 'ol_layout_final.json'))); E = json.load(open(os.path.join(LEG, 'ol_editor_edges.json')))
    R = {r['id']: r for r in E['rooms']}
    P = {v: (x, y) for v, x, y in zip(S['ids'], S['xs'], S['ys'])}; H = set(S['hidden'])
    OL = {v for v, r in R.items() if not r.get('fixed') and r['grp'] != 'un' and v not in H}
    UN = {v for v, r in R.items() if r.get('grp') == 'un'}
    assert all(str(v) not in pos for v in OL)
    # ---- unlocked map rooms moved, and the sea lines through them ----
    old = {v: tuple(pos[str(v)][:2]) if str(v) in pos else tuple(wild['track']['cx%d' % v][:2]) for v in UN}
    moved = {v for v in UN if math.dist(old[v], P[v]) > 0.01}
    near = lambda q: [v for v in moved if math.dist(q[:2], old[v]) < 0.003]
    nf = 0
    for l in wild['seawaysfaint']:
        for q in l:
            m = near(q)
            if m: q[0], q[1] = P[m[0]][0], P[m[0]][1]; nf += 1
    rp = {}
    for p in list(pos.values()) + list(wild['track'].values()): rp[(round(p[0], 2), round(p[1], 2))] = tuple(p[:2])
    nw = 0; icesegs = []; extra = []; faintsegs = []
    isice = lambda q: any(math.dist(q[:2], P[v]) < 0.003 for v in ICEBERG)
    FP = [tuple(P[v]) if v in P else tuple(pos[str(v)][:2]) for v in FAINT_CHAIN]
    isfaint = lambda q: any(math.dist(q[:2], f) < 0.003 for f in FP)
    for j, l in enumerate(wild['seawaves']):
        if not any(near(q) for q in l): continue
        vs = [q for q in l if (round(q[0], 2), round(q[1], 2)) in rp and math.dist(q, rp[(round(q[0], 2), round(q[1], 2))]) < 0.003]
        assert _wave(vs) == l, j
        vs = [list(P[near(q)[0]]) if near(q) else q for q in vs]
        runs = [[vs[0]]]                                # stretches between two iceberg rooms: trails on the iceberg (owner, Oct 22)
        for a, b in zip(vs, vs[1:]):
            if isice(a) and isice(b):
                if math.dist(a, b) > 1e-6: icesegs.append([list(a), list(b)])
                runs.append([b])
            elif isfaint(a) and isfaint(b):
                if math.dist(a, b) > 1e-6: faintsegs.append([list(a), list(b)])
                runs.append([b])
            else: runs[-1].append(b)
        runs = [r for r in runs if len(r) > 1]
        wild['seawaves'][j] = _wave(runs[0]) if runs else []; extra += [_wave(r) for r in runs[1:]]; nw += 1
    wild['seawaves'] = [l for l in wild['seawaves'] if l] + extra
    wild['seawaysfaint'] = list(wild['seawaysfaint']) + faintsegs
    wild['oltracks'] = list(wild.get('oltracks') or []) + icesegs     # Otherland's own trails (owner, Oct 22: tracks in the snow; template OLTRACK)
    for v in moved:
        if str(v) in pos: pos[str(v)] = [P[v][0], P[v][1]]
        else: wild['track']['cx%d' % v] = [P[v][0], P[v][1]]
    for v in OL: pos[str(v)] = [P[v][0], P[v][1]]
    # ---- exits: plain trails ----
    G = defaultdict(set); ud = one = 0
    for a, b, k in E['edges']:
        if not ({a, b} & OL) or {a, b} & H: continue
        if k == 'ud': ud += 1; continue
        if k == 'one': one += 1; continue
        G[a].add(b); G[b].add(a)
    stub = 0
    while True:                                         # spacer rooms left as dead ends
        dead = [v for v in G if R[v]['void'] and v in OL and len(G[v]) <= 1]
        if not dead: break
        for v in dead:
            for u in G.pop(v): G[u].discard(v)
            stub += 1
    G = defaultdict(set, {v: n for v, n in G.items() if n})
    trails = _chains(G, P)                              # (all of them shape the snow, so its texture stays put)
    inb = lambda v: NBOX.contains(Point(P[v]))
    wet = lambda v: inb(v) and v not in ICEBERG and v not in AS_LAND and ((v in OL and not R[v]['void'] and (R[v]['terrain'] in WET or rooms_name(v) == CLIFF or v in DOCK[1:])) or v in UN)   # (the unlocked rooms: sea, but the iceberg's)
    def ends(v, came):                                  # the real rooms a spacer leads to, through other spacers
        out, seen, st = set(), {came, v}, [v]
        while st:
            u = st.pop()
            for x in G[u]:
                if x in seen: continue
                seen.add(x)
                if R[x]['void']: st.append(x)
                else: out.add(x)
        return out
    def wetedge(a, b):
        for v, o in ((a, b), (b, a)):
            if wet(v): return True
            if R[v]['void'] and inb(v) and any(wet(x) for x in ends(v, o)): return True
        return False
    GL, GW = defaultdict(set), defaultdict(set)
    dockp = {frozenset(q) for q in zip(DOCK, DOCK[1:])}
    for a in G:
        for b in G[a]:
            if frozenset((a, b)) in dockp: continue     # (the dock itself)
            (GW if wetedge(a, b) else GL)[a].add(b)
    ltrails = _chains(GL, P); wroutes = _chains(GW, P)
    wild['oltracks'] = list(wild['oltracks']) + ltrails
    nwr = [l for l in wroutes if all(q[0] < NW_X for q in l)]
    inharb = lambda l: all(HARBOR.buffer(0.6).contains(Point(q)) for q in l)
    hways = [l for l in nwr if inharb(l)]
    wild['olharborways'] = [_wave(l, HWAVE_A, HWAVE_L) for l in hways]
    wild['seawaysfaint'] = list(wild['seawaysfaint']) + [l for l in nwr if not inharb(l)]
    wild['seawaves'] = list(wild['seawaves']) + [_wave(l) for l in wroutes if not all(q[0] < NW_X for q in l)]
    # ---- snow ground ----
    geo = wild['geo']
    land0 = unary_union([Polygon(p).buffer(0) for p in geo['land'] if len(p) > 2])
    water = unary_union([Polygon(p).buffer(0) for p in geo['water'] if len(p) > 2] + [Polygon(p).buffer(0) for p in geo.get('seafill') or [] if len(p) > 2])
    snow = unary_union([Point(P[v]).buffer(SNOW_R) for v in OL] + [LineString(l).buffer(SNOW_R) for l in trails if len(l) > 1])
    snow = snow.buffer(CLOSE).buffer(-CLOSE).difference(land0.buffer(0.3)).difference(water.buffer(0.3))
    pieces = sorted([g for g in getattr(snow, 'geoms', [snow]) if g.area > 1.0], key=lambda g: -g.area)
    holes = sum(len(g.interiors) for g in pieces)
    pieces = [Polygon(g.exterior).difference(land0.buffer(0.3)).difference(water.buffer(0.3)) for g in pieces]
    pieces = [h for g in pieces for h in getattr(g, 'geoms', [g]) if h.area > 1.0]
    rd = lambda g: [[round(x, 3), round(y, 3)] for x, y in list(g.simplify(0.03).exterior.coords)[:-1]]
    geo['land'] = list(geo['land']) + [rd(g) for g in pieces]
    geo['snow'] = [rd(g) for g in pieces]
    allsnow = unary_union(pieces)
    b = wild['bounds']; xb = allsnow.bounds
    wild['bounds'] = [min(b[0], math.floor(xb[0] - 1)), b[1], max(b[2], math.ceil(xb[2] + 1)), max(b[3], math.ceil(xb[3] + 1))]
    # ---- the snow's texture ----
    rng = random.Random(22534)
    lines = unary_union([LineString(l) for l in trails if len(l) > 1] + [Point(P[v]) for v in OL])
    inner = allsnow.buffer(-0.5)
    x0, y0, x1, y1 = inner.bounds
    def spots(n, gap, clear, tries):
        out = []
        for _ in range(tries):
            if len(out) >= n: break
            q = (rng.uniform(x0, x1), rng.uniform(y0, y1))
            if not inner.contains(Point(q)) or lines.distance(Point(q)) < clear or any(math.dist(q, o) < gap for o in out): continue
            out.append(q)
        return out
    ice = []
    for x, y in spots(ICE_N, ICE_GAP, ICE_CLEAR, 20000):
        rx, ry, r = rng.uniform(0.35, 0.8), rng.uniform(0.2, 0.45), rng.uniform(0, math.pi)
        poly = []
        for i in range(10):
            a = 2 * math.pi * i / 10; k = rng.uniform(0.8, 1.15)
            px, py = rx * k * math.cos(a), ry * k * math.sin(a)
            poly.append([round(x + px * math.cos(r) - py * math.sin(r), 3), round(y + px * math.sin(r) + py * math.cos(r), 3)])
        if lines.distance(Polygon(poly)) >= 0.4 and inner.contains(Polygon(poly)): ice.append(poly)
    icy = unary_union([Polygon(p).buffer(0.6) for p in ice]) if ice else Point(-9e9, -9e9)
    drifts = [[round(x, 3), round(y, 3), round(rng.uniform(0.7, 1.25), 2), round(rng.uniform(-0.35, 0.35), 3)]
              for x, y in spots(int(allsnow.area / DRIFT_AREA), DRIFT_GAP, DRIFT_CLEAR, 60000) if not icy.contains(Point(x, y))]
    wild['olsnow'] = {'poly': [list(map(list, p)) for p in geo['snow']], 'drifts': drifts, 'ice': ice}
    # ---- the north coast ----
    WR = {v for v in OL if wet(v)}
    ice_r = [v for v in ICEBERG if v in OL or v in UN]
    landr = [v for v in OL if inb(v) and not R[v]['void'] and v not in WR and v not in ice_r]
    core = unary_union([Point(P[v]).buffer(LAND_R) for v in landr] + [LineString(l).buffer(LTRAIL_R) for l in ltrails if len(l) > 1 and NBOX.intersects(LineString(l))])
    wetreach = unary_union([Point(P[v]).buffer(WET_R) for v in WR] + [LineString(l).buffer(WTRAIL_R) for l in wroutes if len(l) > 1]
                           + [Point(P[v]).buffer(WET_R) for v in moved if v not in ICEBERG])
    icetr = [l for l in ltrails + icesegs if len(l) > 1 and all(any(math.dist(q, P[v]) < 0.01 for v in ice_r) for q in (l[0], l[-1]))]
    iceberg = unary_union([Point(P[v]).buffer(ICE_R) for v in ice_r] + [LineString(l).buffer(ICE_R * 0.8) for l in icetr]).buffer(0.4).buffer(-0.4)
    land_all = unary_union([Polygon(p).buffer(0) for p in geo['land'][:-len(pieces)] if len(p) > 2])
    W = unary_union([Polygon(p).buffer(0) for p in geo['water'] if len(p) > 2])
    SF = unary_union([Polygon(p).buffer(0) for p in geo.get('seafill') or [] if len(p) > 2])
    protect = unary_union([Point(P[v]).buffer(0.55) for v in landr] + [LineString(l).buffer(0.3) for l in ltrails if len(l) > 1 and NBOX.intersects(LineString(l))
                                                                           and not any(math.dist(q, P[v]) < 0.01 for v in ice_r for q in (l[0], l[-1]))])
    ZONE = iceberg.buffer(ZONE_R)                       # near the iceberg: the mainland hugs its rooms and trails (owner, Oct 22)
    tight = unary_union([Point(P[v]).buffer(TIGHT_R) for v in landr] + [LineString(l).buffer(TIGHT_TR) for l in ltrails if len(l) > 1 and ZONE.intersects(LineString(l))]).intersection(ZONE)
    closed = unary_union([core.buffer(CLOSE_N).buffer(-CLOSE_N).difference(ZONE), tight])
    mainland = unary_union([closed.difference(wetreach), protect.difference(iceberg.buffer(0.01))]).difference(iceberg.buffer(SLIVER).difference(protect))
    mainland = mainland.intersection(allsnow.buffer(0.01))   # (where the old snow kept off the old sea, sea now: no gap)
    fill1 = FILL1.difference(W.buffer(0.3)).difference(iceberg.buffer(SLIVER))
    fill1 = unary_union([fill1, mainland.intersection(FILL1.buffer(1.0))]).buffer(0.3).buffer(-0.3).intersection(FILL1.buffer(0.5)).difference(W.buffer(0.3)).difference(iceberg.buffer(SLIVER))
    mainland = unary_union([mainland, fill1])
    solid = unary_union([land_all, mainland, iceberg, allsnow.difference(NBOX)])     # (outside the boxes the snow stays as it is)
    reach = unary_union([allsnow.intersection(NBOX).buffer(SEA_W), W.buffer(SEA_W).intersection(NBOX), wetreach])        # the sea: up to SEA_W off the land inside the boxes (so it ends in a
    region = unary_union([reach, W.intersection(NBOX)]).buffer(SEA_CLOSE).buffer(-SEA_CLOSE)   # round edge, never a box's straight line), joined to the old sea
    sea = region.difference(solid)                      # (exactly up to the land: no hairline gaps)
    sea = unary_union([g for g in getattr(sea, 'geoms', [sea]) if g.distance(W) < 0.05 or g.distance(wetreach) < 0.05 and g.area > 1.0])
    # the snow: the old snow minus the new sea (the mainland's north edge), plus the iceberg
    newsnow = unary_union([allsnow.difference(ZONE), allsnow.intersection(tight), fill1]).difference(sea).difference(iceberg.buffer(SLIVER).difference(protect))
    snowp = [g for g in getattr(newsnow, 'geoms', [newsnow]) if g.area > 0.5 and any(g.contains(Point(P[v])) for v in OL)]
    stray = round(sum(g.area for g in getattr(newsnow, 'geoms', [newsnow]) if g.area > 0.5) - sum(g.area for g in snowp), 2)
    pock = round(sum(Polygon(h).area for g in snowp for h in g.interiors if not Polygon(h).intersects(sea)), 2)
    snowp = [Polygon(g.exterior, [h for h in g.interiors if Polygon(h).intersects(sea)]) for g in snowp]   # pockets inside the snow that aren't sea: snow   # (bits of the old snow with no room: sea now)
    sea = unary_union([sea] + [g for g in getattr(newsnow, 'geoms', [newsnow]) if g.area > 0.5 and g not in snowp and NBOX.contains(g)])
    dropped = round(sum(g.area for g in getattr(newsnow, 'geoms', [newsnow]) if g.area <= 0.5), 2)
    ice_p = iceberg.difference(land_all.buffer(0.3)).difference(W.buffer(0.05))
    ice_p = [g for g in getattr(ice_p, 'geoms', [ice_p]) if g.area > 0.3]
    newp = snowp + ice_p
    rings = lambda gs: [r for g in gs for r in [rd(g)] + [[[round(x, 3), round(y, 3)] for x, y in list(h.coords)[:-1]] for h in g.simplify(0.03).interiors]]   # (holes: rings of their own, the paths are evenodd)
    geo['land'] = list(geo['land'][:-len(pieces)]) + rings(newp)
    geo['snow'] = rings(snowp + ice_p)                  # (the iceberg in the mainland's snow: owner, Oct 22)
    geo['iceisle'] = []
    allsnow2 = unary_union(newp)
    # the sea drawn: seafill (over the old sea's edge where they meet, hiding its shore line there), its own shore lines
    fill = sea.difference(W)
    fill = unary_union([fill, W.intersection(fill.buffer(0.3))]).difference(SF).difference(land_all.buffer(0.05)).difference(allsnow2.buffer(-0.03))   # (just over the snow's edge: no gap)
    fills = [g for g in getattr(fill, 'geoms', [fill]) if g.area > 0.05]
    allwet = unary_union([W, SF, land_all, allsnow2] + fills)                    # small pockets of bare ground shut in by the land and the new sea: sea
    near_b = NBOX.buffer(SEA_W + SEA_CLOSE)
    pockets = [Polygon(h) for g in getattr(allwet, 'geoms', [allwet]) for h in g.interiors if Polygon(h).area < 30 and near_b.contains(Polygon(h))]
    pockets = [h.difference(allwet) for h in pockets]; pockets = [h for h in pockets if h.area > 0.05]
    if pockets: fill = unary_union([fill] + [h.buffer(0.03) for h in pockets]).difference(allsnow2.buffer(-0.03)); fills = [g for g in getattr(fill, 'geoms', [fill]) if g.area > 0.05]
    geo['seafill'] = list(geo.get('seafill') or []) + rings(fills)
    total = unary_union([W, SF] + fills)
    shore = total.boundary.difference(W.boundary.buffer(0.03)).difference(SF.boundary.buffer(0.03)).intersection(sea.buffer(0.1))
    shore = [l for l in getattr(shore, 'geoms', [shore]) if l.geom_type == 'LineString' and l.length > 0.2]
    wild['seashore'] = list(wild.get('seashore') or []) + [[[round(x, 3), round(y, 3)] for x, y in l.simplify(0.02).coords] for l in shore]
    b = wild['bounds']; sb_ = unary_union(fills).bounds                # the map grows to fit the new sea (the south shore's runs past y 253)
    wild['bounds'] = [min(b[0], math.floor(sb_[0] - 0.5)), b[1], max(b[2], math.ceil(sb_[2] + 0.5)), max(b[3], math.ceil(sb_[3] + 0.5))]
    keep = unary_union(snowp).buffer(-0.3)
    nd, ni = len(drifts), len(ice)
    wild['olsnow'] = {'poly': [list(map(list, p)) for p in geo['snow']], 'drifts': [d for d in drifts if keep.contains(Point(d[:2]))],
                      'ice': [p for p in ice if keep.contains(Polygon(p))]}
    seawet = [v for v in WR if not total.buffer(0.01).contains(Point(P[v]))]
    landwet = [v for v in landr if total.buffer(-0.01).contains(Point(P[v]))]
    icepos = {v: round(Point(P[v]).distance(unary_union(ice_p).exterior if ice_p else Point(0, 0)), 2) for v in ice_r}
    gap = round(unary_union(ice_p).distance(unary_union(snowp)), 2) if ice_p else None
    trail_sea = [(round(LineString(l).intersection(sea.buffer(-0.05)).length, 2), l[0], l[-1]) for l in ltrails if len(l) > 1 and LineString(l).intersection(sea.buffer(-0.05)).length > 0.01]
    north = {'water rooms in the box (sea; not in it)': (len(WR), seawet), 'land rooms in the sea': landwet,
             'water routes (lines, exits); land trails (lines)': (len(wroutes), sum(len(GW[v]) for v in GW) // 2, len(ltrails)),
             'sea added (area, pieces, shore lines; shut-in pockets filled)': (round(sea.difference(W).area, 1), len(fills), len(shore), [round(h.area, 2) for h in pockets]),
             'iceberg (pieces, area, its rooms to its shore, sea to the mainland)': (len(ice_p), round(sum(g.area for g in ice_p), 2), icepos, gap),
             'snow (pieces, area; slivers dropped, bits with no room made sea, pockets filled)': ([round(g.area, 1) for g in snowp], round(unary_union(snowp).area, 1), dropped, stray, pock),
             'texture kept (drifts, ice)': ((len(wild['olsnow']['drifts']), nd), (len(wild['olsnow']['ice']), ni)),
             'trail length over the sea': trail_sea, 'Azure stretches 6180-15128 as Sea of Sorrows routes': len(faintsegs), 'NW water routes as the Sea of Sorrows routes (of; in the harbour, thin and wavy)': (len(nwr), len(wroutes), len(hways)),
             'iceberg trails from the old sea lines': len(icesegs),
             'mainland near the iceberg (rooms, nearest land room to the iceberg)': (sum(1 for v in landr if ZONE.contains(Point(P[v]))),
                 round(min(Point(P[v]).distance(unary_union(ice_p)) for v in landr), 2) if ice_p else None)}
    # ---- Winterlight Island's drawing, for now ----
    # ---- Otherland's trails: a gentle long wave, one smooth warp for all, so they still meet at the rooms they share ----
    ph = random.Random(13287); a1, a2, a3, a4 = (ph.uniform(0, 2 * math.pi) for _ in range(4))
    def warp(x, y):
        return (x + TRACK_A * (0.7 * math.sin(2 * math.pi * y / TRACK_L + a1) + 0.3 * math.sin(2 * math.pi * (x + y) / (TRACK_L * 1.6) + a3)),
                y + TRACK_A * (0.7 * math.sin(2 * math.pi * x / TRACK_L + a2) + 0.3 * math.sin(2 * math.pi * (x - y) / (TRACK_L * 1.6) + a4)))
    nm = lambda v: rooms_name(v)
    MPR = [v for v in OL if P[v][0] > 50 and 180 <= P[v][1] <= 209 and (nm(v) in MP_NAMES or ("Morte's Peak" in nm(v) and 'View' not in nm(v)))]
    INS = {v for v in MPR if nm(v) in MP_INSIDE}
    GZ = {v for v in OL if nm(v) in GORGE_NAMES}
    insp = {tuple(P[v]) for v in INS} | {tuple(P[v]) for v in OL if R[v]['void'] and ends(v, -1) and ends(v, -1) <= INS}
    gzp = {tuple(P[v]) for v in GZ} | {tuple(P[v]) for v in OL if R[v]['void'] and ends(v, -1) and ends(v, -1) <= GZ}
    at = lambda q, S: any(math.dist(q, s) < 0.01 for s in S)
    def wline(pts):
        out = []
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            n = max(2, int(math.dist((ax, ay), (bx, by)) / 0.2))
            out += [[round(c, 3) for c in warp(ax + (bx - ax) * i / n, ay + (by - ay) * i / n)] for i in range(0 if not out else 1, n + 1)]
        return out
    TN = {v for v in OL if nm(v).startswith(CRAMPED)}
    while True:                                         # + the rooms that lead only to them (spacers included)
        more = {v for v in G if v not in TN and v in OL and G[v] and G[v] <= TN}
        if not more: break
        TN |= more
    tunp = {tuple(P[v]) for v in TN}
    npts = 0; wav = []; tun = []; gsegs = []
    for l in wild['oltracks']:
        pts = [l[0]] + [q for a, q in zip(l, l[1:]) if math.dist(a, q) > 1e-6]
        runs = [[pts[0], False]]; cur = [pts[0]]                       # split where the trail goes inside the mountain (owner, Oct 22: dashed passages)
        segs = []
        for a, b in zip(pts, pts[1:]):
            inside = at(a, tunp) and at(b, tunp)        # the Cramped Tunnel (owner, Oct 22): drawn as a tunnel seen into the snow
            if at(a, gzp) and at(b, gzp): gsegs.append((a, b))
            if segs and segs[-1][0] == inside: segs[-1][1].append(b)
            else: segs.append([inside, [a, b]])
        for inside, sp in segs:
            o = wline(sp)
            if len(o) > 1: (tun if inside else wav).append(o); npts += len(o)
    wild['oltracks'] = wav; wild['oltunnels'] = tun
    # ---- clearings (owner, Oct 22): the two clumps of rooms side by side, packed snow (template CLEAR) ----
    ex = {(a, b) for a, b, k in E['edges'] if k != 'ud'}; ex |= {(b, a) for a, b in ex}
    solo = [v for v in OL if not R[v]['void']]
    nb = defaultdict(set)
    for i, a in enumerate(solo):
        for b in solo[i + 1:]:
            if (a, b) in ex and math.dist(P[a], P[b]) <= CLEAR_D: nb[a].add(b); nb[b].add(a)
    onsnow = unary_union(snowp).buffer(-0.15); clr = {}
    for seed, name in CLEAR_SEEDS.items():
        c, st = {seed}, [seed]
        while st:
            for u in nb[st.pop()] - c: c.add(u); st.append(u)
        g = unary_union([Point(P[v]).buffer(CLEAR_R) for v in c] + [LineString([P[a], P[b]]).buffer(CLEAR_TR) for a in c for b in nb[a] if a < b])
        g = g.buffer(0.25).buffer(-0.25).intersection(onsnow)
        gs = [Polygon(h.exterior) for h in getattr(g, 'geoms', [g]) if h.area > 0.2]
        if seed == 13322:                               # owner (Oct 22): A Tunnel in the Snow is a maze: an icy maze blob filling exactly that clearing's outline
            for h in gs: wild['fwmazes'] = list(wild['fwmazes']) + [{'name': '', 'nolabel': True, 'style': 'ice', 'poly': rd(h), 'cx': round(h.centroid.x, 2), 'cy': round(h.centroid.y, 2)}]
        else: wild['clearings'] = list(wild.get('clearings') or []) + [{'polys': [rd(h) for h in gs], 'fill': CLEAR_FILL, 'edge': CLEAR_EDGE}]
        clr[name] = (len(c), round(sum(h.area for h in gs), 1), len(gs), sorted(v for v in c if not onsnow.contains(Point(P[v]))))
    cl_all = unary_union([Polygon(h) for c in wild['clearings'][-1:] for h in c['polys']] + [Polygon(m['poly']) for m in wild['fwmazes'] if m.get('style') == 'ice']).buffer(0.5)
    o = wild['olsnow']; n0 = (len(o['drifts']), len(o['ice']))
    o['drifts'] = [d for d in o['drifts'] if not cl_all.contains(Point(d[:2]))]; o['ice'] = [q for q in o['ice'] if not cl_all.intersects(Polygon(q))]
    clr['texture under them dropped (drifts, ice)'] = (n0[0] - len(o['drifts']), n0[1] - len(o['ice']))
    # ---- water paths and shacks (owner, Oct 22) ----
    wild['seawaysfaint'] = list(wild['seawaysfaint']) + [[list(P[a]), list(P[b])] for a, b in WATER_LINKS]
    shk = {}; tl = [LineString(l) for l in wild['oltracks']]
    for name, (vs, mx, my) in SHACKS.items():
        xs = [P[v][0] for v in vs]; ys = [P[v][1] for v in vs]
        x0, x1, y0, y1 = min(xs) - mx, max(xs) + mx, min(ys) - my - 0.35, max(ys) + my     # (the roof rises a little above the top rooms)
        wild['olshacks'] = list(wild.get('olshacks') or []) + [[round((x0 + x1) / 2, 3), round((y0 + y1) / 2, 3), round(x1 - x0, 3), round(y1 - y0, 3)]]
        r = box(x0, y0, x1, y1); inside = set(vs)
        outside = [l for l in tl if not any(math.dist(l.coords[0], P[v]) < 0.25 or math.dist(l.coords[-1], P[v]) < 0.25 for v in inside)]
        shk[name] = {'box': [round(c, 2) for c in (x0, y0, x1, y1)], 'nearest trail not its own': round(min(r.distance(l) for l in outside), 2),
                     'drifts/ice under it': sum(1 for d in wild['olsnow']['drifts'] if r.buffer(0.4).contains(Point(d[:2]))) + sum(1 for q in wild['olsnow']['ice'] if r.buffer(0.4).intersects(Polygon(q)))}
        o = wild['olsnow']; o['drifts'] = [d for d in o['drifts'] if not r.buffer(0.4).contains(Point(d[:2]))]; o['ice'] = [q for q in o['ice'] if not r.buffer(0.4).intersects(Polygon(q))]
    # ---- the Harbor of Icebergs (owner, Oct 22): shore ice with cracks, icebergs, the dock ----
    hr = random.Random(13105)
    hsea = sea.intersection(HARBOR)
    routes = unary_union([LineString(l) for l in wild['seawaysfaint'] + wild['seawaves'] + hways if len(l) > 1 and HARBOR.intersects(LineString(l))])
    dline = LineString([P[v] for v in DOCK])
    hrooms = [v for v in OL if HARBOR.contains(Point(P[v]))]
    keepoff = unary_union([routes.buffer(0.32), dline.buffer(DOCK_W / 2 + 0.3)] + [Point(P[v]).buffer(0.45) for v in hrooms])
    near_r = unary_union([dline.buffer(DOCK_W / 2 + 0.3)] + [Point(P[v]).buffer(0.5) for v in hrooms])     # (owner, Oct 22: no erratic bits: the ice follows the
    ice_s = sea.intersection(HARBOR.buffer(2.5)).intersection(solid.buffer(ICE_SHORE)).difference(near_r)   #  real shore, past the harbour's box, with no thin spikes)
    ice_s = ice_s.buffer(-0.4).buffer(0.4).intersection(sea).difference(near_r)
    ice_s = [g for g in getattr(ice_s, 'geoms', [ice_s]) if g.area > 1.0]        # (no small slivers)
    cracks = []
    for g in ice_s:
        for _ in range(max(1, int(g.area / 1.2))):
            c = g.representative_point(); a0 = hr.uniform(0, math.pi); L = hr.uniform(0.4, 0.9)
            pts = [(c.x - L / 2 * math.cos(a0), c.y - L / 2 * math.sin(a0))]
            for k in range(1, 4): pts.append((pts[0][0] + L * k / 3 * math.cos(a0) + hr.uniform(-.08, .08), pts[0][1] + L * k / 3 * math.sin(a0) + hr.uniform(-.08, .08)))
            cl = LineString(pts).intersection(g.buffer(-0.08))
            cracks += [[[round(x, 3), round(y, 3)] for x, y in s.coords] for s in getattr(cl, 'geoms', [cl]) if s.geom_type == 'LineString' and s.length > 0.15]
    open_w = sea.intersection(HARBOR.buffer(3.0)).difference(unary_union(ice_s).buffer(0.25) if ice_s else Point(0, 0)).difference(near_r.buffer(0.15)).buffer(-0.2)
    bergs = []; x0, y0, x1, y1 = HARBOR.buffer(3.0).bounds              # (owner, Oct 22: more icebergs round the harbour, little ones and big ones)
    for _ in range(20000):
        if len(bergs) >= N_BERGS: break
        x, y = hr.uniform(x0, x1), hr.uniform(y0, y1); s = round(0.14 + 1.55 * hr.random() ** 2.6, 3)
        if not open_w.buffer(-s * 0.8).contains(Point(x, y)) or any(math.dist((x, y), b[:2]) < 0.35 + 1.15 * (s + b[4]) for b in bergs): continue
        n = hr.randint(6, 8); poly = []
        for i in range(n):
            a = 2 * math.pi * i / n + hr.uniform(-.25, .25); r = s * hr.uniform(0.7, 1.1)
            poly.append([round(x + r * math.cos(a), 3), round(y + 0.75 * r * math.sin(a), 3)])
        top = [[round(x - .07 * s + (q[0] - x) * .68, 3), round(y - .12 * s + (q[1] - y) * .62, 3)] for q in poly]
        bergs.append([x, y, poly, top, s])
    pp = list(dline.coords); posts = []
    for (ax, ay), (bx, by) in zip(pp, pp[1:]):
        L = math.dist((ax, ay), (bx, by)); n = max(1, int(L / 0.8)); nx, ny = -(by - ay) / L, (bx - ax) / L
        for i in range(n + 1):
            cx, cy = ax + (bx - ax) * i / n, ay + (by - ay) * i / n
            for sgn in (-1, 1): posts.append([round(cx + sgn * nx * DOCK_W / 2, 3), round(cy + sgn * ny * DOCK_W / 2, 3)])
    wild['olharbor'] = {'ice': [rd(g) for g in ice_s], 'cracks': cracks, 'bergs': [[b[2], b[3]] for b in bergs],
                        'dock': {'pts': [[round(x, 3), round(y, 3)] for x, y in pp], 'w': DOCK_W, 'posts': posts}}
    ondock = dline.buffer(DOCK_W / 2 + 0.3); o = wild['olsnow']
    o['drifts'] = [d for d in o['drifts'] if not ondock.contains(Point(d[:2]))]; o['ice'] = [q for q in o['ice'] if not ondock.intersects(Polygon(q))]
    landdock = round(dline.intersection(unary_union(snowp)).length, 2)
    harbor = {'water rooms in the harbour in the sea': (sum(1 for v in hrooms if total.buffer(0.01).contains(Point(P[v]))), len(hrooms)),
              'shore ice (pieces, area), cracks': (len(ice_s), round(sum(g.area for g in ice_s), 1), len(cracks)), 'icebergs': len(bergs),
              'dock (length, of it on land, posts)': (round(dline.length, 2), landdock, len(posts)),
              'harbour open to the sea (the bay joins the coast sea)': hsea.intersects(sea.difference(HARBOR).buffer(0.01))}
    # ---- Morte's Peak (owner, Oct 22): no objects; the snow itself shaded as seen from above: a soft height field rising to its heart, lit from the
    #      north-west, slopes facing the light a little lighter, the others a little darker, fading out at its foot (template OLHILL, blurred) ----
    import numpy as np
    land_now = unary_union(snowp).buffer(-0.4)
    hx = sum(P[v][0] for v in INS if 'Heart' in nm(v)) / max(1, sum(1 for v in INS if 'Heart' in nm(v)))
    hy = sum(P[v][1] for v in INS if 'Heart' in nm(v)) / max(1, sum(1 for v in INS if 'Heart' in nm(v)))
    M = unary_union([Point(P[v]).buffer(MP_R + 1.5) for v in MPR]).buffer(1.5).buffer(-1.5).intersection(land_now)
    RES = 0.25; bx0, by0, bx1, by1 = M.bounds
    gx = np.arange(bx0, bx1 + RES, RES); gy = np.arange(by0, by1 + RES, RES); X, Y = np.meshgrid(gx, gy)
    # height from the trails (owner, Oct 22): each room as high as the climb to it along the trails from where they enter the mountain, the heart the
    # top; every trail stretch a sharp ridge between its rooms' heights; a broad base under it all; steep sides, so it reads as a very tall mountain
    MS = set(MPR) | {v for v in G if R[v]['void'] and ends(v, -1) and ends(v, -1) <= set(MPR)}
    import heapq
    dep = {}; hq = [(0.0, v) for v in MS if any(u not in MS for u in G[v])]
    for d0, v in hq: dep[v] = 0.0
    heapq.heapify(hq)
    while hq:
        d0, v = heapq.heappop(hq)
        if d0 > dep.get(v, 9e9): continue
        for u in G[v]:
            if u in MS and d0 + math.dist(P[v], P[u]) < dep.get(u, 9e9): dep[u] = d0 + math.dist(P[v], P[u]); heapq.heappush(hq, (dep[u], u))
    dmax = max(dep.values()) if dep else 1.0
    hv = {v: (dep.get(v, 0.0) / dmax) ** 0.8 for v in MS}
    for v in MS:
        if v in INS and 'Heart' in nm(v): hv[v] = max(hv[v], 0.9)
    Hh = 0.55 * np.exp(-((X - hx) ** 2 + (Y - hy) ** 2) / 6.5 ** 2)
    samp = []
    for a in MS:
        for b in G[a]:
            if b in MS and a < b:
                L = math.dist(P[a], P[b]); n = max(1, int(L / 0.4))
                samp += [(P[a][0] + (P[b][0] - P[a][0]) * i / n, P[a][1] + (P[b][1] - P[a][1]) * i / n, hv[a] + (hv[b] - hv[a]) * i / n) for i in range(n + 1)]
    for sx, sy, sh in samp:
        Hh = np.maximum(Hh, (0.25 + 0.95 * sh) * np.exp(-np.hypot(X - sx, Y - sy) / 1.9))
    ph = random.Random(5990); f1, f2, f3, f4 = (ph.uniform(0, 6.3) for _ in range(4))
    Hh += 0.03 * np.sin(X * 1.9 + f1) * np.sin(Y * 1.6 + f2) + 0.02 * np.sin((X + Y) * 2.7 + f3) + 0.02 * np.sin((X - Y) * 2.3 + f4)
    dy_, dx_ = np.gradient(Hh, RES); Z = 16.0
    nx_, ny_, nz_ = -dx_ * Z, -dy_ * Z, np.ones_like(Hh); nn = np.sqrt(nx_ ** 2 + ny_ ** 2 + nz_ ** 2)
    lx, ly, lz = -0.62, -0.62, 0.48; ln = math.sqrt(lx * lx + ly * ly + lz * lz)
    shade = (nx_ * lx + ny_ * ly + nz_ * lz) / nn / ln - lz / ln          # 0 on the flat
    env = np.clip((Hh - 0.06) / 0.2, 0, 1)                               # nothing at its foot
    V = shade * env
    BINS = [(-9, -0.6, '#252D32', .42), (-0.6, -0.42, '#252D32', .32), (-0.42, -0.26, '#252D32', .22), (-0.26, -0.12, '#252D32', .12),
            (0.12, 0.26, '#E6ECEE', .10), (0.26, 0.42, '#E6ECEE', .17), (0.42, 0.6, '#E6ECEE', .24), (0.6, 9, '#E6ECEE', .31)]
    hstat = {'heights (rooms, climb to the top)': (len(hv), round(dmax, 1)), 'shade spread (min, max)': (round(float(V.min()), 2), round(float(V.max()), 2))}
    def shade_levels(V, gx, gy, clipM, bins):
        out = []
        for lo, hi, col, op in bins:
            m = (V > lo) & (V <= hi)
            cells = [box(gx[j] - RES / 2, gy[i] - RES / 2, gx[j] + RES / 2, gy[i] + RES / 2) for i, j in zip(*np.nonzero(m))]
            if not cells: continue
            g = unary_union(cells).buffer(0.08).buffer(-0.08).intersection(clipM)
            gs = [h for h in getattr(g, 'geoms', [g]) if h.area > 0.1]
            if gs: out.append({'fill': col, 'op': op, 'rings': rings(gs)})
        return out
    levels = shade_levels(V, gx, gy, M, BINS)
    wild['olhill'] = {'levels': levels}
    # ---- Tirebaen's Gorge and the Fissure (owner, Oct 22): a shadowed floor along its trails, snowy cliff rims with hachures (template OLGORGE) ----
    gl = unary_union([LineString(wline([a, b])).buffer(GORGE_R if math.dist(a, b) <= 3.5 else GORGE_R * 0.73) for a, b in gsegs])   # (long connectors: a narrower cut;
                                                                                                                                   #  owner, Oct 22: wide, room either side of its trails)
    band = gl.buffer(0.3).buffer(-0.3).intersection(land_now)
    floor = band.buffer(-0.8)
    hach = []
    for g in getattr(band, 'geoms', [band]):
        for ring in [g.exterior] + list(g.interiors):
            n = int(ring.length / 0.2)
            for i in range(n):
                q = ring.interpolate(i * 0.2); f = floor.boundary.interpolate(floor.boundary.project(q)) if not floor.is_empty else q
                d = math.dist((q.x, q.y), (f.x, f.y))
                if 0.15 < d < 1.3:
                    k = (0.55 + 0.35 * (i % 2)) * d
                    hach.append([[round(q.x, 3), round(q.y, 3)], [round(q.x + (f.x - q.x) / d * k, 3), round(q.y + (f.y - q.y) / d * k, 3)]])
    wild['olgorge'] = {'band': rings([g for g in getattr(band, 'geoms', [band]) if g.area > 0.3]),
                       'floor': rings([g for g in getattr(floor, 'geoms', [floor]) if g.area > 0.1]), 'hach': hach}
    cover = band.buffer(0.2); o = wild['olsnow']; n0 = (len(o['drifts']), len(o['ice']))
    o['drifts'] = [d for d in o['drifts'] if not cover.contains(Point(d[:2]))]; o['ice'] = [q for q in o['ice'] if not cover.intersects(Polygon(q))]
    # ---- more relief (owner, Oct 22: all of them), each its own height field shaded like Morte's Peak, clipped to the snow, off the gorge ----
    def relief(Hfun, area, Z, lo, span, scale):
        bx0, by0, bx1, by1 = area.bounds
        gx = np.arange(bx0, bx1 + RES, RES); gy = np.arange(by0, by1 + RES, RES); X, Y = np.meshgrid(gx, gy)
        Hh = Hfun(X, Y)
        dy_, dx_ = np.gradient(Hh, RES)
        nx_, ny_ = -dx_ * Z, -dy_ * Z; nn = np.sqrt(nx_ ** 2 + ny_ ** 2 + 1)
        V = ((nx_ * lx + ny_ * ly + lz) / nn / ln - lz / ln) * np.clip((Hh - lo) / span, 0, 1)
        bins = [(a, b, c, round(o * scale, 3)) for a, b, c, o in BINS]
        return shade_levels(V, gx, gy, area.intersection(land_now).difference(band.buffer(0.3)), bins), round(float(V.min()), 2), round(float(V.max()), 2)
    def dline_np(X, Y, pts):                            # distance from the grid to a polyline
        D = np.full(X.shape, 1e9)
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            vx, vy = bx - ax, by - ay; L2 = vx * vx + vy * vy or 1e-9
            u = np.clip(((X - ax) * vx + (Y - ay) * vy) / L2, 0, 1)
            D = np.minimum(D, np.hypot(X - ax - u * vx, Y - ay - u * vy))
        return D
    rel = {}; rr = random.Random(23010); tl = unary_union([LineString(l) for l in wild['oltracks'] if len(l) > 1])
    # (the Gods' plateau, the hills, the Mountain over the tunnels and the Den: taken out again, owner Oct 22: no relief on the west and south land)
    # the Base of Death's Spire: one very sharp rise; A Spacious Den in the Snow: a small mound
    for name, amp, r, Z_, lab in (("The Base of Death's Spire", 0.9, 0.85, 18.0, "Death's Spire"),):
        vs = [v for v in OL if nm(v) == name]
        if not vs: continue
        sx, sy = P[vs[0]]; sx += 0.8 if lab == "Death's Spire" else 0
        lv, a, b = relief(lambda X, Y, sx=sx, sy=sy: amp * np.exp(-np.hypot(X - sx, Y - sy) / r), Point(sx, sy).buffer(4.0), Z_, 0.04, 0.12, 0.9)
        levels += lv; rel[lab + ' (levels)'] = len(lv)
    wild['olhill'] = {'levels': levels}
    # Bed of the Runoff: a short frozen streambed from the room down to the nearest sea (template OLRUNOFF)
    rv = [v for v in OL if nm(v) == 'Bed of the Runoff']
    if rv:
        a0 = Point(P[rv[0]]); s0 = sea.boundary.interpolate(sea.boundary.project(a0)); L = a0.distance(s0)
        pts = [(a0.x + (s0.x - a0.x) * i / 10 + 0.12 * math.sin(i * 1.3) * (i not in (0, 10)), a0.y + (s0.y - a0.y) * i / 10 + 0.1 * math.cos(i * 1.7) * (i not in (0, 10))) for i in range(11)]
        wild['olrunoff'] = [[round(x, 3), round(y, 3)] for x, y in pts]; rel['Bed of the Runoff (length to the sea)'] = round(L, 1)
    # the south shore: a frozen beach along its coast, pack ice and icebergs offshore round An Ocean of Floating Ice and Among the Icebergs
    s_sea = sea.intersection(SBOX); s_land = unary_union(snowp).intersection(SBOX.buffer(1))
    beach = s_land.intersection(s_sea.buffer(0.9)).difference(near_r if False else Point(0, 0)).buffer(0.1).buffer(-0.2).buffer(0.1)
    beach = [h for g in getattr(beach, 'geoms', [beach]) for h in getattr(g.difference(FILL_S.buffer(1.5)), 'geoms', [g.difference(FILL_S.buffer(1.5))]) if h.area > 0.3]   # (no beach south of 6143)
    ir = [P[v] for v in OL if nm(v) in SOUTH_ICE]
    zone = unary_union([Point(q).buffer(5.0) for q in ir]).intersection(s_sea).buffer(-0.3)
    floes = []; sb = []
    rooms_s = unary_union([Point(P[v]).buffer(0.6) for v in OL if SBOX.contains(Point(P[v]))] + [LineString(l).buffer(0.25) for l in wild['seawaysfaint'] + wild['seawaves'] if len(l) > 1 and SBOX.intersects(LineString(l))])
    zx0, zy0, zx1, zy1 = zone.bounds if not zone.is_empty else (0, 0, 0, 0)
    for _ in range(20000):
        if len(floes) + len(sb) >= 60 or zone.is_empty: break
        x, y = rr.uniform(zx0, zx1), rr.uniform(zy0, zy1); s = round(0.12 + 1.3 * rr.random() ** 2.8, 3)
        if not zone.buffer(-s * 0.8).contains(Point(x, y)) or rooms_s.distance(Point(x, y)) < s * 0.9 or any(math.dist((x, y), b_[:2]) < 0.3 + 1.1 * (s + b_[2]) for b_ in floes + sb): continue
        n = rr.randint(6, 9); poly = []
        for i in range(n):
            a_ = 2 * math.pi * i / n + rr.uniform(-.3, .3); r_ = s * rr.uniform(0.65, 1.15)
            poly.append([round(x + r_ * math.cos(a_), 3), round(y + 0.75 * r_ * math.sin(a_), 3)])
        if s > 0.45: sb.append([x, y, s, poly, [[round(x - .07 * s + (q[0] - x) * .68, 3), round(y - .12 * s + (q[1] - y) * .62, 3)] for q in poly]])
        else: floes.append([x, y, s, poly])
    wild['olsouth'] = {'beach': rings(beach), 'floes': [f[3] for f in floes]}
    wild['olharbor']['bergs'] = list(wild['olharbor']['bergs']) + [[b_[3], b_[4]] for b_ in sb]
    o = wild['olsnow']; bz = unary_union(beach).buffer(0.2) if beach else Point(0, 0); n1 = len(o['drifts'])
    o['drifts'] = [d for d in o['drifts'] if not bz.contains(Point(d[:2]))]
    rel['south shore (beach pieces, area; floes; icebergs; drifts dropped)'] = (len(beach), round(sum(g.area for g in beach), 1), len(floes), len(sb), n1 - len(o['drifts']))
    rel['south sea water rooms (in the sea, of)'] = (sum(1 for v in OL if SBOX.contains(Point(P[v])) and wet(v) and total.buffer(0.01).contains(Point(P[v]))), sum(1 for v in OL if SBOX.contains(Point(P[v])) and wet(v)))
    # ---- mazes (owner, Oct 22): Over the Cliff Maze along the coast; the Maze of Ice round its hidden rooms and Frost Mansion (style 'ice') ----
    from shapely.ops import substring, polylabel
    main = max(snowp, key=lambda g: g.area); ring_ = LineString(main.exterior.coords)
    d1, d2 = sorted(ring_.project(Point(P[v])) for v in CLIFF_MAZE)
    arc = substring(ring_, d1, d2)
    if arc.length > ring_.length / 2: arc = unary_union([substring(ring_, d2, ring_.length), substring(ring_, 0, d1)])
    ctr = [l for l in wild['seawaysfaint'] + wild['oltracks'] if len(l) > 1 and any(math.dist(q, P[v]) < 0.05 for v in CLIFF_MAZE for q in (l[0], l[-1]))]
    blob0 = unary_union([arc.buffer(2.4)] + [Point(P[v]).buffer(1.4) for v in CLIFF_MAZE] + [LineString(l).buffer(0.9) for l in ctr])   # (owner, Oct 22: its paths inside)
    from shapely.affinity import translate as _tr
    stick = max(0.0, -(blob0.bounds[0] - arc.buffer(2.4).bounds[0]))                                  # how far its entry paths stick out west
    kx = max(stick + 0.8, 1.5)                                                                           # (owner, Oct 22: extended westward, no bulges)
    blob = unary_union([blob0, _tr(arc, -kx, 0).buffer(2.4), unary_union([arc, _tr(arc, -kx, 0)]).convex_hull.intersection(arc.buffer(2.4 + kx))]).buffer(2.0).buffer(-2.0)
    bulge = round(blob.difference(blob.buffer(-1.2).buffer(1.2)).area, 2)
    lab = blob.centroid if blob.buffer(-1.2).contains(blob.centroid) else polylabel(blob, 0.05)                                             # (owner, Oct 22: the label at its centre)
    mzs = [{'name': 'Over the Cliff Maze', 'lines': ['Over', 'the Cliff', 'Maze'], 'style': 'ice', 'poly': rd(blob), 'cx': round(lab.x, 2), 'cy': round(lab.y, 2), 'fs': 0.55}]
    mx_ = sum(P[v][0] for v in MANSION) / 3; my_ = sum(P[v][1] for v in MANSION) / 3 - 0.3
    mbox = box(mx_ - MANSION_W / 2, my_ - MANSION_H / 2, mx_ + MANSION_W / 2, my_ + MANSION_H / 2)
    MZ = [v for v in P if v in H and nm(v) == 'The Maze of Ice']
    blob2 = unary_union([mbox.buffer(0.7)] + [Point(P[v]).buffer(0.95) for v in MZ]).buffer(1.0).buffer(-1.0)
    ly_ = max(P[v][1] for v in MZ) - 0.35
    mzs.append({'name': 'The Maze of Ice', 'style': 'ice', 'poly': rd(blob2), 'cx': round(sum(P[v][0] for v in MZ) / len(MZ), 2), 'cy': round(ly_, 2), 'fs': 0.42})
    wild['fwmazes'] = list(wild['fwmazes']) + mzs
    wild['olmansion'] = [round(mx_, 3), round(my_, 3), MANSION_W, MANSION_H]
    shown_in = lambda g: sorted(v for v in OL if g.contains(Point(P[v])) and not R[v]['void'])
    mazes = {'Over the Cliff Maze (westward, area, its rooms in it, other rooms in it, its paths fully inside, label at centroid; bulges left)': ((round(stick, 2), round(kx, 2), bulge), round(blob.area, 1), [v for v in CLIFF_MAZE if blob.contains(Point(P[v]))], [v for v in shown_in(blob) if v not in CLIFF_MAZE], f'{sum(1 for l in ctr if blob.contains(LineString(l)))}/{len(ctr)}', lab.equals(blob.centroid)),
             'Maze of Ice (area, hidden rooms in it, the mansion inside it, other shown rooms in it)': (round(blob2.area, 1), sum(1 for v in MZ if blob2.contains(Point(P[v]))), blob2.buffer(-0.05).contains(mbox), [v for v in shown_in(blob2) if v not in MANSION]),
             'Cramped Tunnel (rooms, tunnel lines)': (len(TN), len(tun))}
    # ---- The Ledge of Life (owner, Oct 22): a cliff face falling away south of its path, the path marked as dangerous ----
    lp = [P[v] for v in LEDGE]; lx0, lx1 = min(q[0] for q in lp) - 0.7, max(q[0] for q in lp) + 0.7; ly0 = max(q[1] for q in lp) + 0.32
    lr = random.Random(6101); top = [(lx0, ly0)]; bot = []
    n = int((lx1 - lx0) / 0.25)
    for i in range(n + 1):
        x = lx0 + (lx1 - lx0) * i / n; e = min(1, (x - lx0) / 0.9, (lx1 - x) / 0.9)
        top.append((x, ly0 + lr.uniform(-.03, .05))); bot.append((x, ly0 + (0.35 + 0.65 * e) + lr.uniform(-.1, .1)))
    face = Polygon(top[1:] + bot[::-1]).buffer(0.04).buffer(-0.04)
    hach = []
    for i in range(int((lx1 - lx0) / 0.13)):
        x = lx0 + 0.07 + i * 0.13
        L = LineString([(x, ly0 - .05), (x + lr.uniform(-.04, .04), ly0 + 2)]).intersection(face)
        if not L.is_empty and L.geom_type == 'LineString': hach.append([[round(c, 3) for c in L.coords[0]], [round(L.coords[-1][0], 3), round(L.coords[0][1] + (L.coords[-1][1] - L.coords[0][1]) * lr.uniform(.45, 1), 3)]])
    wild['olledge'] = {'face': rd(face), 'hach': hach, 'path': wline(lp)}
    o = wild['olsnow']; fz = face.buffer(0.3); n2 = len(o['drifts'])
    o['drifts'] = [d for d in o['drifts'] if not fz.contains(Point(d[:2]))]; o['ice'] = [q for q in o['ice'] if not fz.intersects(Polygon(q))]
    mazes['Ledge of Life cliff (area, depth, rooms in it, drifts dropped)'] = (round(face.area, 2), round(face.bounds[3] - ly0, 2), shown_in(face), n2 - len(o['drifts']))
    feats = {"Morte's Peak (rooms, shaded area, shade levels)": (len(MPR), round(M.area, 1), len(levels)), 'more relief': rel, 'Morte heights': hstat,
             'gorge: other rooms inside it': sum(1 for v in OL if v not in GZ and band.contains(Point(P[v]))), 'icebergs (sizes min/max)': (len(bergs), min(b[4] for b in bergs), max(b[4] for b in bergs)),
             'gorge (rooms, trail stretches, area, hachures)': (len(GZ), len(gsegs), round(band.area, 1), len(hach)),
             'texture under them dropped (drifts, ice)': (n0[0] - len(o['drifts']), n0[1] - len(o['ice']))}
    isles = len(wild.get('snowisles') or []); wild['snowisles'] = []
    # ---- checks ----
    offsnow = sorted(v for v in OL if not allsnow.buffer(0.01).contains(Point(P[v])))
    inwater = sorted(v for v in offsnow if water.contains(Point(P[v])))
    return {'rooms placed (Otherland shown; hidden; unlocked moved)': (len(OL), len(H), len(moved)),
            'trails added (lines, exits; not drawn: up/down, one-way, dead-end spacer rooms)': (len(trails), sum(len(G[v]) for v in G) // 2, ud, one, stub),
            'snow texture (drifts, icy patches)': (len(drifts), len(ice)),
            'sea lines moved with their rooms (faint points, wave lines)': (nf, nw),
            'snow (pieces, area; holes filled)': (len(pieces), round(allsnow.area, 1), holes),
            'rooms not on the snow (in the sea; elsewhere)': (inwater, [v for v in offsnow if v not in inwater]),
            'north coast': north, 'harbor': harbor, 'features': feats, 'mazes, tunnel, ledge': mazes, 'shacks': shk, 'clearings (rooms, area, pieces, rooms not on the snow)': clr, 'Winterlight Island drawings removed': isles, 'bounds': wild['bounds']}
