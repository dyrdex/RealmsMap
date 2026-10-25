"""Owner, Oct 25: seven small docks like Fireball Island's (changes/002), each from 0.3 inside the shore out 1.0 past it (`wild.smalldocks`,
drawn by template FIREBALL's dock):
  King's Castle: on the coast due east of 3245; Ocean Keep: due north of 3069; Raven Tor: north-east of its marker; Solace: due north of its
  marker; Wild Tundra: north-west off 14444; Edo: off its island's south-east corner, running south-east.
  Azure Sea: on the coast due north of 12956 (owner, Oct 25; first given as 12982, out at sea with no coast north of it)."""
import math
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import nearest_points

INLAND, OUT = 0.3, 1.0
DIRS = {'e': (1, 0), 'n': (0, -1), 'ne': (1, -1), 'nw': (-1, -1), 'se': (1, 1)}
DOCKS = [("King's Castle", 'room', 3245, 'e'), ('Ocean Keep', 'room', 3069, 'n'), ('Raven Tor', 'pin', 'Raven Tor', 'ne'),
         ('Solace', 'pin', 'Town of Solace', 'n'), ('Wild Tundra', 'room', 14444, 'nw'), ('Azure Sea', 'room', 12956, 'n'),
         ('Edo', 'corner', 'Village of Edo', 'se')]
DIRV = {'n': (0, -1), 's': (0, 1), 'e': (1, 0), 'w': (-1, 0), 'ne': (.7071, -.7071), 'nw': (-.7071, -.7071), 'se': (.7071, .7071), 'sw': (-.7071, .7071)}


def _parity(rings):
    A = Polygon()
    for p in rings:
        if len(p) > 2: A = A.symmetric_difference(Polygon(p).buffer(0))
    return A


def _pin(p):                                          # the marker as the template places it
    if p.get('at'): return tuple(p['at'])
    e = p['path'][-1]
    if p['dir'] == 'here': return tuple(e)
    if p['dir'] == 'd': return (e[0] + .62, e[1] + .05)
    v = DIRV[p['dir']]; return (e[0] + v[0] * .62, e[1] + v[1] * .62)


def apply(town, wild, pos):
    land = _parity(wild['geo']['land']); out = {}; docks = []
    pl = {p['name']: p for p in wild['places']}
    for name, kind, ref, dn in DOCKS:
        ux, uy = DIRS[dn]; L = math.hypot(ux, uy); ux, uy = ux / L, uy / L
        if kind == 'room': o = tuple(pos[str(ref)][:2])
        elif kind == 'pin': o = _pin(pl[ref])
        else:
            e = Point(_pin(pl[ref])); piece = min(land.geoms, key=lambda g: g.distance(e))
            o = max(piece.exterior.coords, key=lambda q: q[0] * ux + q[1] * uy)
            o = (o[0] - ux * 0.01, o[1] - uy * 0.01)
        onland = land.contains(Point(o))
        ray = LineString([o, (o[0] + ux * 40, o[1] + uy * 40)]); hit = ray.intersection(land.boundary)
        if hit.is_empty: raise ValueError((name, o, onland))
        c = nearest_points(hit, Point(o))[0]
        s = 1 if onland else -1                       # out to sea: along the ray from land, back against it from the sea
        a = (c.x - s * ux * INLAND, c.y - s * uy * INLAND); b = (c.x + s * ux * OUT, c.y + s * uy * OUT)
        assert land.contains(Point(a)) and not land.contains(Point(b)), name
        docks.append([round(a[0], 2), round(a[1], 2), round(b[0], 2), round(b[1], 2)])
        out[name] = ([round(v, 2) for v in o], 'origin on land' if onland else 'origin at sea', round(Point(o).distance(c), 2), docks[-1],
                     'end to other land %.2f' % LineString([c, b]).buffer(0.01).difference(land.buffer(0.02)).distance(land.difference(Point(c.x, c.y).buffer(1.5))))
    wild['smalldocks'] = docks
    return out
