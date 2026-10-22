# Otherland's whole shore (owner, Oct 22): the south shore's floating ice and little icebergs (olsouth floes, olharbor bergs) all along the
# island's sea coast, The Iceberg's included, as dense as off the south shore, the same shapes and sizes; clear of every room, sea route,
# maze and the ice already there.
import math, random
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union
from maplib import world

REACH = 3.5                                     # out to this far from the coast
SOUTH_ICE = {'An Ocean of Floating Ice', 'Among the Icebergs'}
SBOX = box(-12 + 3.0, 228, 56, 264)                  # (its west edge 3 east with the rooms: owner's save of Oct 22 18:39Z)


def apply(town, wild, pos):
    return place(wild, pos, 23231)


def place(wild, pos, seed, only=None):          # only: limit the new ice to this area (008, the east coast)
    rooms, _ = world()
    rr = random.Random(seed)
    G = wild['geo']
    snow = unary_union([Polygon(p).buffer(0) for p in G['snow'] if len(p) > 2])
    sea = unary_union([Polygon(p).buffer(0) for k in ('seafill', 'water') for p in G[k] if len(p) > 2]).difference(snow)
    coast = snow.boundary.intersection(sea.buffer(0.3))
    zone = sea.intersection(coast.buffer(REACH)).buffer(-0.3)
    # the south shore's ice, as placed (for its density), and everything already there to keep clear of
    ir = [pos[str(v)] for v, r in rooms.items() if r['name'] in SOUTH_ICE and str(v) in pos]
    szone = unary_union([Point(q).buffer(5.0) for q in ir]).intersection(sea.intersection(SBOX)).buffer(-0.3)
    floes0 = [Polygon(f) for f in wild['olsouth']['floes']]
    bergs0 = [Polygon(b[0]) for b in wild['olharbor']['bergs']]
    n_south = sum(1 for g in floes0 + bergs0 if szone.contains(g.centroid))
    dens = n_south / szone.area
    old = unary_union(floes0 + bergs0 + [Polygon(p).buffer(0) for p in wild['olharbor']['ice']])
    zone = zone.difference(szone.buffer(0.5)).difference(old.buffer(0.4))
    if only is not None: zone = zone.intersection(only)
    lines = [l for k in ('seaways', 'seawaysfaint', 'seawaves', 'olharborways', 'seadash') for l in wild.get(k, []) if len(l) > 1]
    lines += [c['pts'] for c in wild.get('seacurrents', []) if len(c.get('pts', [])) > 1]
    zb = zone.buffer(1.0)
    keep = unary_union([LineString(l).buffer(0.25) for l in lines if zb.intersects(LineString(l))] +
                       [Point(q).buffer(0.6) for q in pos.values() if zb.contains(Point(q))] +
                       [Polygon(m['poly']).buffer(0.3) for m in wild['fwmazes'] if zb.intersects(Polygon(m['poly']))])
    d = wild['olharbor'].get('dock')
    if d: keep = keep.union(LineString(d['pts']).buffer(d['w'] / 2 + 0.3))
    target = int(round(dens * zone.area))
    from shapely.prepared import prep
    land = prep(snow.buffer(0.1)); pk = prep(keep); ok = {}
    def allowed(s):                               # where an ice piece of this size may sit (sizes in steps of 0.05)
        k = round(s / 0.05)
        if k not in ok: ok[k] = prep(zone.buffer(-k * 0.05 * 0.8).difference(keep.buffer(k * 0.05 * 0.9)).difference(old.buffer(0.3 + 1.1 * k * 0.05)))
        return ok[k]
    x0, y0, x1, y1 = zone.bounds; floes, sb = [], []; cell = {}
    for _ in range(200000):
        if len(floes) + len(sb) >= target: break
        x, y = rr.uniform(x0, x1), rr.uniform(y0, y1); s = round(0.12 + 1.3 * rr.random() ** 2.8, 3)
        if not allowed(s).contains(Point(x, y)): continue
        near = [b for i in range(int(x) - 3, int(x) + 4) for j in range(int(y) - 3, int(y) + 4) for b in cell.get((i, j), [])]
        if any(math.dist((x, y), b[:2]) < 0.3 + 1.1 * (s + b[2]) for b in near): continue
        n = rr.randint(6, 9); poly = []
        for i in range(n):
            a = 2 * math.pi * i / n + rr.uniform(-.3, .3); r = s * rr.uniform(0.65, 1.15)
            poly.append([round(x + r * math.cos(a), 3), round(y + 0.75 * r * math.sin(a), 3)])
        if land.intersects(Polygon(poly)) or pk.intersects(Polygon(poly)): continue
        it = [x, y, s, poly]
        if s > 0.45: it.append([[round(x - .07 * s + (q[0] - x) * .68, 3), round(y - .12 * s + (q[1] - y) * .62, 3)] for q in poly]); sb.append(it)
        else: floes.append(it)
        cell.setdefault((int(x), int(y)), []).append(it)
    wild['olsouth']['floes'] = list(wild['olsouth']['floes']) + [f[3] for f in floes]
    wild['olharbor']['bergs'] = list(wild['olharbor']['bergs']) + [[b[3], b[4]] for b in sb]
    allp = [Polygon(f[3]) for f in floes] + [Polygon(b[3]) for b in sb]
    return {'shore ice (coast length, zone area, south density per sq room, floes, icebergs, target; on land, near a room/route, outside the zone)':
            (round(coast.length, 1), round(zone.area, 1), round(dens, 3), len(floes), len(sb), target,
             sum(1 for g in allp if g.intersects(snow)), sum(1 for g in allp if g.intersects(keep)), sum(1 for g in allp if not zone.buffer(0.05).contains(g.centroid)))}
