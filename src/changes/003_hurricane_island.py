"""Owner, Oct 25: Hurricane Island, about 10 rooms west of The Blood Sea's marker.
  - size: 2/3 of Fireball Island's mean diameter (changes/002), made irregular; its centre 10 west of the Blood Sea marker, moved further west
    (0.5 at a time) until the island is 2 clear of the coast (the marker sits in a bay, with headlands north and south of it);
  - a land piece + a hole in the sea (as 002); sandy all over, a mountain ridge, wind-swept (streaks, bent grass), a boat wreck on its
    west coast (template HURRICANE; own Random);
  - the place: directions the owner's '#53 w;se;d;u;d;u' (the route reaches 14220 Hurricane Island); its line: the drawn part of '#53 w'
    (to The Misery of Mourning 1638, as The Blood Sea's), then straight to the marker on the island's east beach (owner); a large name (1.4)
    centred under the island."""
import math, random
from shapely.geometry import Polygon, LineString, Point

ROUTE = '#53 w;se;d;u;d;u'
FROM = 'The Blood Sea'
SCALE = 2 / 3
CLEAR = 2.0


def _parity(rings):
    A = Polygon()
    for p in rings:
        if len(p) > 2: A = A.symmetric_difference(Polygon(p).buffer(0))
    return A


def _radial(c, r, n=144):
    return Polygon([(c[0] + r(2 * math.pi * i / n) * math.cos(2 * math.pi * i / n), c[1] + r(2 * math.pi * i / n) * math.sin(2 * math.pi * i / n)) for i in range(n)])


def apply(town, wild, pos):
    rng = random.Random(14220)
    G = wild['geo']; land = _parity(G['land'])
    fb = wild['fireball']; fbi = Polygon(fb['isle'])
    Rfb = math.sqrt(fbi.area / math.pi)                    # Fireball's mean radius (by area)
    R = Rfb * SCALE
    bs = next(p for p in wild['places'] if p['name'] == FROM); mk = bs['at']
    ph = [rng.uniform(0, 2 * math.pi) for _ in range(6)]
    rf = lambda t: R * (1 + 0.13 * math.sin(2 * t + ph[0]) + 0.08 * math.sin(3 * t + ph[1]) + 0.05 * math.sin(5 * t + ph[2]) + 0.03 * math.sin(7 * t + ph[3]))
    cx = mk[0] - 10
    while True:
        C = (round(cx, 2), mk[1]); isle = _radial(C, rf).buffer(0.35).buffer(-0.35)
        if isle.distance(land) >= CLEAR: break
        cx -= 0.5
    cy = C[1]
    assert isle.distance(fbi) > 20
    ring = lambda g: [[round(x, 3), round(y, 3)] for x, y in list(g.exterior.coords)[:-1]]
    poly = ring(isle)
    G['land'] = list(G['land']) + [poly]; G['water'] = list(G['water']) + [poly]
    wash = [ring(isle.buffer(-d)) for d in (0.18, 0.38)]
    # ---- the marker on the east beach, the line straight to it ----
    a = math.radians(8); pin = [round(C[0] + (rf(a) - 0.55) * math.cos(a), 2), round(cy + (rf(a) - 0.55) * math.sin(a), 2)]
    end = bs['path'][-1]
    seg = LineString([end, pin]); off = seg.difference(isle).difference(land.buffer(0.01))
    # ---- wind: streaks over the sand (from the west), bent grass, gusts off the lee shore ----
    inner = isle.buffer(-0.45); streaks = []; tufts = []
    x0, y0, x1, y1 = isle.bounds
    for _ in range(400):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1); L = rng.uniform(0.6, 1.5)
        if inner.contains(Point(x, y)) and inner.contains(Point(x + L, y + L * 0.12)) and len(streaks) < 70:
            streaks.append([round(x, 2), round(y, 2), round(L, 2), round(rng.uniform(-.12, .12), 2)])
    for _ in range(300):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        if inner.contains(Point(x, y)) and len(tufts) < 46: tufts.append([round(x, 2), round(y, 2), round(rng.uniform(.7, 1.1), 2)])
    # ---- the wreck: on the west beach ----
    aw = math.radians(183); rw = rf(aw) - 0.85
    wreck = [round(C[0] + rw * math.cos(aw), 2), round(cy + rw * math.sin(aw), 2)]
    ridge = [round(C[0] + 0.7, 2), round(cy + 0.9, 2)]                    # the ridge's foot centre
    # ---- the place ----
    wild['places'].append({'name': 'Hurricane Island', 'route': ROUTE, 'room': 'Hurricane Island', 'dir': 'here', 'group': bs.get('group'),
                           'where': 'in the Blood Sea', 'card': 'Island in the Blood Sea', 'note': None,
                           'path': [list(q) for q in bs['path']] + [pin], 'segs': [[list(q) for q in bs['path']] + [pin]], 'at': pin, 'fs': 1.4})
    wild['hurricane'] = {'isle': poly, 'wash': wash, 'streaks': streaks, 'tufts': tufts, 'wreck': wreck, 'ridge': ridge, 'c': list(C), 'r': round(R, 2)}
    lab_y = round(isle.bounds[3] + 1.25, 2)
    return {'Fireball mean diameter -> this': (round(2 * Rfb, 2), round(2 * R, 2)), 'Blood Sea marker, centre (moved west by)': (mk, C, round(mk[0] - 10 - C[0], 2)),
            'island box, to the coast': ([round(c, 2) for c in isle.bounds], round(isle.distance(land), 2)), 'marker': pin,
            'line from 1638: length, over sea, crosses land outside the route': (round(seg.length, 2), round(off.length, 2), round(LineString([end, pin]).intersection(land).length, 2)),
            'streaks, tufts': (len(streaks), len(tufts)), 'wreck': wreck, 'name baseline y': lab_y}
